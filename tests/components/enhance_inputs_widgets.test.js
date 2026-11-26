import { beforeEach, describe, expect, it, vi } from 'vitest';
import '@ui/static/inputs_fields.js';
import '@ui/static/inputs_widgets.js';

const { readFields, fieldValue } = globalThis.tavlePageParts.inputFields;

describe('input fields', () => {
  it('validates the entire list and retains only supported properties', () => {
    expect(
      readFields([
        { name: 'age', type: 'number', required: true, min: 0, max: 9, extra: 1 },
        { name: 'x', type: 'text', required: 1, min: Infinity, max: NaN }
      ])
    ).toEqual([
      { name: 'age', type: 'number', required: true, min: 0, max: 9 },
      { name: 'x', type: 'text', required: false }
    ]);
    for (const bad of [
      null,
      'x',
      { name: '__proto__', type: 'text' },
      { name: 'Bad', type: 'text' },
      { name: 'x', type: 'other' }
    ]) {
      expect(readFields([{ name: 'ok', type: 'text' }, bad])).toBeUndefined();
    }
  });

  it('validates values and attaches the failing control', () => {
    expect(fieldValue({ name: 'x', type: 'text' }, null).message).toBe('Form is incomplete.');
    const control = { value: '', checked: false };
    for (const type of ['text', 'select', 'checkbox']) {
      const error = fieldValue({ name: 'x', type, required: true }, control);
      expect(error).toBeInstanceOf(Error);
      expect(error.control).toBe(control);
    }
    expect(fieldValue({ name: 'x', type: 'number' }, control)).toBeNull();
    for (const value of ['abc', '-1', '11']) {
      control.value = value;
      expect(fieldValue({ name: 'x', type: 'number', min: 0, max: 10 }, control).control).toBe(control);
    }
    control.value = '5';
    expect(fieldValue({ name: 'x', type: 'number', min: 0, max: 10 }, control)).toBe(5);
  });
});

describe('input widgets', () => {
  let widgets, submit, fail, setNote, sendAnswer;
  beforeEach(() => {
    widgets = {};
    submit = {};
    fail = vi.fn();
    setNote = vi.fn();
    sendAnswer = vi.fn().mockResolvedValue(false);
    globalThis.tavlePageParts.inputWidgets({
      register: (name, widget) => {
        widgets[name] = widget;
      },
      onSubmit: (root, name, callback) => {
        submit[name] = callback;
      },
      fail,
      setNote,
      sendAnswer
    });
    vi.stubGlobal('CSS', { supports: vi.fn().mockReturnValue(false) });
  });

  it('validates choices and sends a single choice or an array with comment', () => {
    const root = document.createElement('form');
    root.innerHTML =
      '<div class="choice-group"><label class="choice-option"><input type="checkbox" value="a"></label><label class="choice-option"><input type="checkbox" value="b"></label></div><textarea class="choice-text">hello</textarea>';
    widgets.choice.hydrate(root, { multiple: false });
    submit.choice(root);
    const inputs = root.querySelectorAll('input');
    expect(fail).toHaveBeenCalledWith(root, 'choice', 'Pick an option.', inputs[0]);
    expect(inputs[1].getAttribute('aria-invalid')).toBe('true');
    inputs[0].checked = true;
    inputs[0].dispatchEvent(new Event('change', { bubbles: true }));
    expect(inputs[1].hasAttribute('aria-invalid')).toBe(false);
    submit.choice(root);
    expect(sendAnswer).toHaveBeenLastCalledWith(root, 'choice', 'a', 'hello');
    widgets.choice.hydrate(root, { multiple: true });
    inputs[1].checked = true;
    submit.choice(root);
    expect(sendAnswer).toHaveBeenLastCalledWith(root, 'choice', ['a', 'b'], 'hello');
  });

  it('counts and announces thresholds, grows, and handles comment submission', async () => {
    const root = document.createElement('div');
    root.innerHTML =
      '<textarea class="comment-text" maxlength="10"></textarea><span class="comment-count"></span><span class="comment-announce"></span>';
    const area = root.querySelector('textarea');
    Object.defineProperty(area, 'scrollHeight', { value: 42 });
    widgets.comment.hydrate(root);
    await submit.comment();
    expect(fail).toHaveBeenCalledWith(root, 'comment', 'A comment needs text.', area);
    area.value = '12345678';
    area.dispatchEvent(new Event('input'));
    expect(root.querySelector('.comment-count').textContent).toBe('8 / 10');
    expect(root.querySelector('.comment-announce').textContent).toBe('2 characters left.');
    expect(area.style.blockSize).toBe('42px');
    area.value = '123456789';
    area.dispatchEvent(new Event('input'));
    expect(root.querySelector('.comment-announce').textContent).toBe('2 characters left.');
    area.value = '1234567890';
    area.dispatchEvent(new Event('input'));
    expect(root.querySelector('.comment-announce').textContent).toBe('Character limit reached.');
    CSS.supports.mockReturnValue(true);
    area.style.blockSize = '7px';
    area.dispatchEvent(new Event('input'));
    expect(area.style.blockSize).toBe('7px');
    await submit.comment();
    expect(sendAnswer).toHaveBeenCalledWith(root, 'comment', 'commented', '1234567890');
    expect(setNote).toHaveBeenCalledWith(root, '.comment-state', 'Sending...');
    expect(setNote).toHaveBeenLastCalledWith(root, '.comment-state', '');
  });

  it('tracks required fields, marks errors, restores hints and sends values', () => {
    const root = document.createElement('div');
    root.innerHTML =
      '<input data-field="name" aria-describedby="hint"><input data-field="age"><div id="error" class="form-error"></div>';
    const fields = [
      { name: 'name', type: 'text', required: true },
      { name: 'age', type: 'number', required: true }
    ];
    widgets.form.hydrate(root, { fields });
    expect(setNote).toHaveBeenCalledWith(root, '.form-remaining', '2 required fields left');
    submit.form();
    const [name, age] = root.querySelectorAll('input');
    expect(name.getAttribute('aria-invalid')).toBe('true');
    expect(name.getAttribute('aria-describedby')).toBe('hint error');
    name.value = 'Ada';
    name.dispatchEvent(new Event('input', { bubbles: true }));
    expect(name.getAttribute('aria-describedby')).toBe('hint');
    expect(setNote).toHaveBeenCalledWith(root, '.form-remaining', '1 required field left');
    age.value = '4';
    age.dispatchEvent(new Event('change', { bubbles: true }));
    expect(setNote).toHaveBeenCalledWith(root, '.form-remaining', 'All required fields filled');
    submit.form();
    expect(sendAnswer).toHaveBeenCalledWith(root, 'form', { name: 'Ada', age: 4 }, '');
    setNote.mockClear();
    widgets.form.hydrate(document.createElement('div'), { fields: [] });
    expect(setNote).not.toHaveBeenCalled();
  });
});
