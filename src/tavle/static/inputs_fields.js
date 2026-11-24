  const FIELD_TYPES = ['text', 'number', 'select', 'checkbox'];
  const FIELD_NAME = /^[a-z][a-z0-9_-]{0,47}$/; // the server's rule; bars `__proto__`

  function validField(raw) {
    return raw !== null && typeof raw === 'object' && typeof raw.name === 'string'
      && FIELD_TYPES.includes(raw.type) && FIELD_NAME.test(raw.name);
  }

  // Form field descriptors: only name, type, required, min and max survive; one
  // bad entry rejects the list, so the form never sends a partial answer.
  export function readFields(list) {
    const fields = [];
    for (const raw of list) {
      if (!validField(raw)) return undefined;
      const field = { name: raw.name, type: raw.type, required: raw.required === true };
      for (const key of ['min', 'max']) {
        if (typeof raw[key] === 'number' && Number.isFinite(raw[key])) field[key] = raw[key];
      }
      fields.push(field);
    }
    return fields;
  }


  // The value of one form control, or an Error (with `control`) naming what is wrong.
  export function fieldValue(field, control) {
    const bad = (message) => Object.assign(new Error(message), { control });
    if (!control) return bad('Form is incomplete.');
    if (field.type === 'checkbox') {
      return field.required && !control.checked ? bad(field.name + ' must be ticked.') : control.checked;
    }
    if (field.type !== 'number') {
      return field.required && !control.value.trim() ? bad(field.name + ' is required.') : control.value;
    }
    return numberValue(field, control, bad);
  }

  function numberValue(field, control, bad) {
    if (!control.value.trim()) return field.required ? bad(field.name + ' is required.') : null;
    const number = Number(control.value);
    if (!Number.isFinite(number)) return bad(field.name + ' must be a number.');
    if (field.min !== undefined && number < field.min) return bad(field.name + ' is below ' + field.min + '.');
    if (field.max !== undefined && number > field.max) return bad(field.name + ' is above ' + field.max + '.');
    return number;
  }

