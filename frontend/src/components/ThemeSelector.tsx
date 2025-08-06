import React, { useContext } from 'react';
import { ThemeContext } from '../contexts/ThemeContext';
import { Sun, Moon, Palette } from 'lucide-react';

const themes = [
  'zinc',
  'slate',
  'stone',
  'gray',
  'blue',
  'orange',
  'pink',
  'bubblegum-pop',
  'cyberpunk-neon',
  'retro-arcade',
  'tropical-paradise',
  'steampunk-cogs',
  'neon-synthwave',
  'pastel-kawaii',
  'space-odyssey',
  'vintage-vinyl',
  'zen-garden',
  'misty-harbor',
];

export const ThemeSelector: React.FC = () => {
  const context = useContext(ThemeContext);

  if (!context) {
    return null;
  }

  const { theme, setTheme, themeMode, setThemeMode } = context;

  return (
    <div className="flex items-center gap-4">
      <div className="relative">
        <Palette className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
        <select
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
          className="pl-10 pr-4 py-2 border rounded-md bg-white dark:bg-gray-800"
        >
          {themes.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>
      <button
        onClick={() => setThemeMode(themeMode === 'light' ? 'dark' : 'light')}
        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        aria-label="Toggle theme"
      >
        {themeMode === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
      </button>
    </div>
  );
};
