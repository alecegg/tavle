import { fieldValue } from './inputs_fields.js';

export function mountInputs({ register, onSubmit, fail, setNote, sendAnswer }) {
  function textOf(root, kind) {
    const area = root.querySelector('.' + kind + '-text');
    return area ? area.value : '';
  }

  // Clears a choice error: text, aria-invalid on the options and the group link.
  function clearChoiceError(root) {
    setNote(root, '.choice-error', '');
    root.querySelectorAll('.choice-option input').forEach((input) => input.removeAttribute('aria-invalid'));
  }

  register('choice', {
    props: { multiple: 'boolean', comment: 'boolean' },
    hydrate(root, props) {
      const group = root.querySelector('.choice-group');
      if (group) group.addEventListener('change', () => clearChoiceError(root));
      onSubmit(root, 'choice', (form) => {
        const picked = Array.from(form.querySelectorAll('input:checked')).map((input) => input.value);
        if (!picked.length) {
          const options = form.querySelectorAll('.choice-option input');
          options.forEach((input) => input.setAttribute('aria-invalid', 'true'));
          return fail(root, 'choice', 'Pick an option.', options[0]);
        }
        clearChoiceError(root);
        sendAnswer(root, 'choice', props.multiple ? picked : picked[0], textOf(root, 'choice'));
      });
    },
  });

  // Auto-grow only where `field-sizing: content` is missing; one read, one write per input.
  function autoGrow(area) {
    if (CSS.supports('field-sizing', 'content')) return;
    area.style.blockSize = 'auto';
    area.style.blockSize = area.scrollHeight + 'px';
  }

  function commentAnnouncement(level, remaining) {
    if (level === 2) return 'Character limit reached.';
    if (level === 1) return remaining + ' characters left.';
    return '';
  }

  // Updates the visible counter always; the live region speaks only at 80% and 100%.
  function countComment(root, area, state) {
    const max = area.maxLength;
    const length = area.value.length;
    const count = root.querySelector('.comment-count');
    if (count) count.textContent = length + ' / ' + max;
    const level = length >= max ? 2 : length >= max * 0.8 ? 1 : 0;
    if (level === state.level) return;
    state.level = level;
    const announce = root.querySelector('.comment-announce');
    if (announce) announce.textContent = commentAnnouncement(level, max - length);
  }

  register('comment', {
    hydrate(root) {
      const area = root.querySelector('.comment-text');
      const state = { level: 0 };
      if (area) area.addEventListener('input', () => { countComment(root, area, state); autoGrow(area); });
      onSubmit(root, 'comment', async () => {
        const text = textOf(root, 'comment');
        if (!text.trim()) return fail(root, 'comment', 'A comment needs text.', area);
        setNote(root, '.comment-state', 'Sending...');
        const saved = await sendAnswer(root, 'comment', 'commented', text);
        if (!saved) setNote(root, '.comment-state', '');
      });
    },
  });

  // True when a required field is still empty (unticked, blank or unselected).
  function unfilled(field, control) {
    if (!field.required || !control) return false;
    return field.type === 'checkbox' ? !control.checked : !control.value.trim();
  }

  function showRemaining(root, fields, controls) {
    const count = fields.filter((field) => unfilled(field, controls.get(field.name))).length;
    if (!fields.some((field) => field.required)) return;
    const text = count ? count + ' required ' + (count === 1 ? 'field' : 'fields') + ' left' : 'All required fields filled';
    setNote(root, '.form-remaining', text);
  }

  // Marks `control` invalid and keeps its hint beside the error in aria-describedby.
  function markInvalid(root, control) {
    const note = root.querySelector('.form-error');
    const hint = (control.dataset.hint || '');
    control.setAttribute('aria-invalid', 'true');
    if (note && note.id) control.setAttribute('aria-describedby', (hint + ' ' + note.id).trim());
  }

  function clearFieldError(target) {
    if (!target || !target.removeAttribute) return;
    target.removeAttribute('aria-invalid');
    if (!target.dataset || !('hint' in target.dataset)) return;
    if (target.dataset.hint) target.setAttribute('aria-describedby', target.dataset.hint);
    else target.removeAttribute('aria-describedby');
  }

  register('form', {
    props: { fields: 'fields' },
    hydrate(root, props) {
      const fields = props.fields || [];
      const controls = new Map();
      root.querySelectorAll('[data-field]').forEach((control) => {
        controls.set(control.dataset.field, control);
        control.dataset.hint = control.getAttribute('aria-describedby') || '';
      });
      const update = (event) => {
        clearFieldError(event && event.target);
        if (!root.querySelector('[aria-invalid]')) setNote(root, '.form-error', '');
        showRemaining(root, fields, controls);
      };
      root.addEventListener('input', update);
      root.addEventListener('change', update);
      showRemaining(root, fields, controls);
      onSubmit(root, 'form', () => {
        const value = Object.create(null);
        for (const field of fields) {
          const got = fieldValue(field, controls.get(field.name));
          if (got instanceof Error) {
            fail(root, 'form', got.message, got.control);
            if (got.control) markInvalid(root, got.control);
            return;
          }
          value[field.name] = got;
        }
        sendAnswer(root, 'form', value, '');
      });
    },
  });

  }
