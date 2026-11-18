import React from 'react'

export default function Logo({ size = 30, className = '' }) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="drop-shadow-[0_0_12px_rgb(14,165,233,0.35)]"
      >
        <defs>
          <linearGradient id="mindLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="100%" stopColor="#0284c7" />
          </linearGradient>
        </defs>
        <path
          d="M6 20V4"
          stroke="url(#mindLogoGrad)"
          strokeWidth="2.2"
          strokeLinecap="round"
        />
        <path
          d="M6 4 L10 16"
          stroke="url(#mindLogoGrad)"
          strokeWidth="2.2"
          strokeLinecap="round"
        />
        <path
          d="M10 16V8"
          stroke="url(#mindLogoGrad)"
          strokeWidth="2.2"
          strokeLinecap="round"
        />
        <path
          d="M10 8 L14 20"
          stroke="url(#mindLogoGrad)"
          strokeWidth="2.2"
          strokeLinecap="round"
        />
        <path
          d="M14 20V12"
          stroke="url(#mindLogoGrad)"
          strokeWidth="2.2"
          strokeLinecap="round"
        />
        <circle cx="6" cy="16" r="1.1" fill="url(#mindLogoGrad)" />
        <circle cx="10" cy="12" r="0.9" fill="#FFFFFF" stroke="url(#mindLogoGrad)" strokeWidth="1.5" />
        <circle cx="14" cy="16" r="1.1" fill="url(#mindLogoGrad)" />
        <path d="M6 16 L10 12" stroke="#0EA5E9" strokeOpacity="0.25" strokeWidth="1" />
        <path d="M10 12 L14 16" stroke="#0EA5E9" strokeOpacity="0.25" strokeWidth="1" />
      </svg>
      <div>
        <div className="flex items-baseline gap-0.5">
          <span className="text-sm font-bold text-ink-primary tracking-tight">Mind</span>
          <span className="text-sm font-bold text-blue-600 dark:text-blue-400 tracking-tight">R3</span>
        </div>
        <div className="text-[9px] uppercase tracking-[0.14em] text-ink-muted font-medium leading-tight">
          Research &amp; Knowledge
        </div>
      </div>
    </div>
  )
}
