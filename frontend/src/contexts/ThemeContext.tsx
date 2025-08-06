import React, { createContext, useState, useMemo, useEffect } from 'react';

type Theme = string;
type ThemeMode = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode) => void;
}

export const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>('zinc');
  const [themeMode, setThemeMode] = useState<ThemeMode>('light');

  useEffect(() => {
    const storedTheme = localStorage.getItem('theme');
    const storedThemeMode = localStorage.getItem('themeMode');
    if (storedTheme) {
      setTheme(storedTheme);
    }
    if (storedThemeMode) {
      setThemeMode(storedThemeMode as ThemeMode);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('theme', theme);
    localStorage.setItem('themeMode', themeMode);
    document.documentElement.setAttribute('data-theme', `${theme}${themeMode === 'dark' ? '-dark' : ''}`);
    if (themeMode === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme, themeMode]);

  const value = useMemo(() => ({
    theme,
    setTheme,
    themeMode,
    setThemeMode,
  }), [theme, themeMode]);

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};
