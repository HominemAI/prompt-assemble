import { useState, useEffect } from 'react';

type Theme = 'light' | 'dark';

const THEME_STORAGE_KEY = 'prompt-assemble-theme';

export const useTheme = () => {
  const [theme, setTheme] = useState<Theme>(() => {
    // Try to get from localStorage first
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') {
      return stored;
    }

    // Check for system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }

    return 'light';
  });

  // Apply theme to DOM (Tailwind) and persist to localStorage
  useEffect(() => {
    const html = document.documentElement;

    if (theme === 'dark') {
      html.classList.add('dark');
    } else {
      html.classList.remove('dark');
    }

    localStorage.setItem(THEME_STORAGE_KEY, theme);

    // Also set a cookie for server-side access
    document.cookie = `${THEME_STORAGE_KEY}=${theme}; path=/; max-age=31536000`; // 1 year
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  return { theme, toggleTheme };
};
