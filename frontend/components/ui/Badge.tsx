'use client';

import React from 'react';
import { clsx } from 'clsx';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'critical' | 'high' | 'moderate' | 'low' | 'info' | 'default';
  pulse?: boolean;
}

export function Badge({ className, variant = 'default', pulse = false, children, ...props }: BadgeProps) {
  const variants = {
    critical: 'bg-severity-critical/10 text-severity-critical dark:bg-severity-critical/20 dark:text-severity-critical-light',
    high: 'bg-severity-high/10 text-severity-high dark:bg-severity-high/20 dark:text-severity-high-light',
    moderate: 'bg-severity-moderate/10 text-severity-moderate dark:bg-severity-moderate/20 dark:text-severity-moderate-light',
    low: 'bg-severity-low/10 text-severity-low dark:bg-severity-low/20 dark:text-severity-low-light',
    info: 'bg-accent-100 text-accent-700 dark:bg-accent-900/50 dark:text-accent-100',
    default: 'bg-muted text-muted-foreground',
  };

  const dotColors = {
    critical: 'bg-severity-critical',
    high: 'bg-severity-high',
    moderate: 'bg-severity-moderate',
    low: 'bg-severity-low',
    info: 'bg-accent-500',
    default: 'bg-muted-foreground',
  };

  return (
    <div
      className={clsx(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
        variants[variant],
        className
      )}
      {...props}
    >
      {pulse && (
        <span className="relative flex h-2 w-2 mr-1.5">
          <span className={clsx("animate-ping absolute inline-flex h-full w-full rounded-full opacity-75", dotColors[variant])}></span>
          <span className={clsx("relative inline-flex rounded-full h-2 w-2", dotColors[variant])}></span>
        </span>
      )}
      {children}
    </div>
  );
}
