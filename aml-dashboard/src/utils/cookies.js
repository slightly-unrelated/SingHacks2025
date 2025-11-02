// Simple cookie utilities with JSON support

/**
 * Set a browser cookie
 * @param {string} name
 * @param {string} value - raw string (will be URI encoded)
 * @param {number} days - expiration in days (default 7)
 */
export const setCookie = (name, value, days = 7) => {
  try {
    const expires = new Date(Date.now() + days * 24 * 60 * 60 * 1000).toUTCString();
    document.cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
  } catch {
    // ignore
  }
};

/**
 * Get a browser cookie value
 * @param {string} name
 * @returns {string | null}
 */
export const getCookie = (name) => {
  try {
    const target = encodeURIComponent(name) + '=';
    const parts = document.cookie.split(';');
    for (let part of parts) {
      part = part.trim();
      if (part.startsWith(target)) {
        return decodeURIComponent(part.substring(target.length));
      }
    }
  } catch {
    // ignore
  }
  return null;
};

/**
 * Delete a browser cookie
 * @param {string} name
 */
export const deleteCookie = (name) => {
  try {
    document.cookie = `${encodeURIComponent(name)}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
  } catch {
    // ignore
  }
};

/**
 * Save JSON payload to cookie (stringified)
 * @param {string} name
 * @param {any} obj
 * @param {number} days
 */
export const setCookieJSON = (name, obj, days = 7) => {
  try {
    const str = JSON.stringify(obj);
    setCookie(name, str, days);
  } catch {
    // If stringify fails, skip
  }
};

/**
 * Read and parse JSON from cookie
 * @param {string} name
 * @returns {any | null}
 */
export const getCookieJSON = (name) => {
  const str = getCookie(name);
  if (!str) return null;
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
};
