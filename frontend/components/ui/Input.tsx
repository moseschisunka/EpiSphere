'use client';

import React from 'react';
import { clsx } from 'clsx';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode;
  error?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, icon, error, ...props }, ref) => {
    return (
      <div className="relative w-full">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
            {icon}
          </div>
        )}
        <input
          ref={ref}
          className={clsx(
            'flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 focus-visible:border-transparent disabled:cursor-not-allowed disabled:opacity-50 transition-shadow',
            icon && 'pl-10',
            error && 'border-severity-critical focus-visible:ring-severity-critical',
            className
          )}
          {...props}
        />
        {error && (
          <p className="mt-1 text-sm text-severity-critical">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
