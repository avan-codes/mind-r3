import React, { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';

export default function ThemeToggle() {
  const [dark, setDark] = useState(() => {
    if (typeof localStorage === 'undefined') return false;
    const saved = localStorage.getItem('mind-r3-theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (dark) root.classList.add('dark');
    else root.classList.remove('dark');
    try { localStorage.setItem('mind-r3-theme', dark ? 'dark' : 'light'); } catch { /* noop */ }
  }, [dark]);

  return (
    <button
      onClick={() => setDark((prev) => !prev)}
      className="btn-ghost p-2.5 text-ink-muted hover:text-blue-600 hover:bg-blue-50 dark:hover:text-blue-400 dark:hover:bg-blue-900/20 rounded-md transition-all"
      aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={dark ? 'Dark mode' : 'Light mode'}
    >
      {dark ? (
        <Sun size={18} className="text-blue-500" />
      ) : (
        <Moon size={18} className="text-ink-secondary" />
      )}
      <span className="sr-only">{dark ? 'Dark mode' : 'Light mode'}</span>
    </button>
  );
}
