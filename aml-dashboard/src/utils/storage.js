// Lightweight localStorage helpers with JSON support

/**
 * Save JSON serializable data into localStorage
 * @param {string} key
 * @param {any} value
 */
export const setLocalJSON = (key, value) => {
  try {
    const str = JSON.stringify(value);
    window.localStorage.setItem(key, str);
  } catch {
    // ignore
  }
};

/**
 * Read and parse JSON from localStorage
 * @param {string} key
 * @returns {any|null}
 */
export const getLocalJSON = (key) => {
  try {
    const str = window.localStorage.getItem(key);
    if (!str) return null;
    return JSON.parse(str);
  } catch {
    return null;
  }
};

/**
 * Remove a key from localStorage
 * @param {string} key
 */
export const removeLocal = (key) => {
  try {
    window.localStorage.removeItem(key);
  } catch {
    // ignore
  }
};
