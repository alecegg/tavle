// Keyboard dispatch of the selectable views.
import { ARROWS, ARROWS_AND_ENDS, handleViewKey } from '@ui/static/view_keys.js';

const keyEvent = (key) => new KeyboardEvent('keydown', { key, cancelable: true });

describe('handleViewKey', () => {
  function actions(moveKeys = ARROWS_AND_ENDS) {
    return { clear: vi.fn(), activate: vi.fn(), move: vi.fn(), moveKeys };
  }

  it('Escape calls clear and is prevented', () => {
    const a = actions();
    const event = keyEvent('Escape');
    handleViewKey(event, a);
    expect(a.clear).toHaveBeenCalledWith('Escape');
    expect(event.defaultPrevented).toBe(true);
    expect(a.activate).not.toHaveBeenCalled();
  });

  it.each(['Enter', ' '])('%j calls activate and is prevented', (key) => {
    const a = actions();
    const event = keyEvent(key);
    handleViewKey(event, a);
    expect(a.activate).toHaveBeenCalledWith(key);
    expect(event.defaultPrevented).toBe(true);
  });

  it('a key in moveKeys calls move with the key and is prevented', () => {
    const a = actions();
    const event = keyEvent('End');
    handleViewKey(event, a);
    expect(a.move).toHaveBeenCalledWith('End');
    expect(event.defaultPrevented).toBe(true);
  });

  it('a key outside moveKeys is neither handled nor prevented', () => {
    const a = actions(['ArrowLeft']);
    const event = keyEvent('ArrowRight');
    handleViewKey(event, a);
    expect(a.move).not.toHaveBeenCalled();
    expect(event.defaultPrevented).toBe(false);
  });

  it.each(['a', 'Tab', 'Shift'])('other key %j calls nothing and is not prevented', (key) => {
    const a = actions();
    const event = keyEvent(key);
    handleViewKey(event, a);
    expect(a.clear).not.toHaveBeenCalled();
    expect(a.activate).not.toHaveBeenCalled();
    expect(a.move).not.toHaveBeenCalled();
    expect(event.defaultPrevented).toBe(false);
  });
});

describe('key lists', () => {
  it('ARROWS lists the four arrows in right, down, left, up order', () => {
    expect(ARROWS).toEqual(['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp']);
  });

  it('ARROWS_AND_ENDS is the arrows followed by Home and End', () => {
    expect(ARROWS_AND_ENDS).toEqual([...ARROWS, 'Home', 'End']);
  });
});
