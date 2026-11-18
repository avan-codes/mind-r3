import React, { useState } from 'react';
import { Search, Menu, Bell, User } from 'lucide-react';
import Logo from '../Logo';
import ThemeToggle from '../ThemeToggle';
import { Link } from 'react-router-dom';

export default function TopBar() {
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-20 border-b border-border-default/60 bg-bg-secondary/80 backdrop-blur-md">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Logo size={26} />
          </div>
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium">
            <Link to="/" className="text-ink-primary font-semibold">Home</Link>
            <Link to="/history" className="text-ink-secondary hover:text-blue-600 dark:hover:text-blue-400 transition-colors">History</Link>
            <Link to="/documents" className="text-ink-secondary hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Documents</Link>
            <Link to="/settings" className="text-ink-secondary hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Settings</Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2 px-3 py-2 rounded-md text-ink-secondary hover:text-blue-600 dark:hover:text-blue-400 hover:bg-bg-subtle transition-colors"
            >
              <User size={18} />
              <span className="hidden sm:inline text-sm font-medium text-ink-primary">Profile</span>
            </button>
            {userMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-bg-white border border-border-default rounded-lg shadow-lg py-2 animate-fade-in z-50 dark:bg-bg-subtle dark:border-border-default">
                <div className="flex items-center gap-3 px-4 py-3 border-b border-border-default dark:border-border-default">
                  <div className="w-8 h-8 rounded-md bg-blue-50 flex items-center justify-center border border-blue-100 dark:bg-blue-900/20 dark:border-blue-800">
                    <span className="text-blue-600 font-medium text-xs dark:text-blue-400">U</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-ink-primary">Researcher</p>
                    <p className="text-xs text-ink-muted">mind-r3.ai</p>
                  </div>
                </div>
                <button
                  onClick={() => setUserMenuOpen(false)}
                  className="flex w-full items-center gap-3 px-4 py-2 text-sm text-ink-secondary hover:bg-bg-subtle transition-colors"
                >
                  <User size={16} />
                  <span>Account settings</span>
                </button>
                <button
                  className="flex w-full items-center gap-3 px-4 py-2 text-sm text-error hover:bg-error/10 hover:text-error-400 transition-colors"
                >
                  <User size={16} className="text-blue-600 dark:text-blue-400" />
                  <span>Sign out</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
