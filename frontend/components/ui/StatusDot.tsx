'use client';

import React from 'react';
import { clsx } from 'clsx';

export interface StatusDotProps {
  status: 'active' | 'warning' | 'error' | 'inactive';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function StatusDot({ status, size = 'md', className }: StatusDotProps) {
  const colors = {
    active: 'bg-severity-low',
    warning: 'bg-severity-moderate',
    error: 'bg-severity-critical',
    inactive: 'bg-muted-foreground',
  };

  const sizes = {
    sm: 'h-1.5 w-1.5',
    md: 'h-2.5 w-2.5',
    lg: 'h-3.5 w-3.5',
  };

  return (
    <span className={clsx('relative flex', sizes[size], className)}>
      {status !== 'inactive' && (
        <span className={clsx("animate-ping absolute inline-flex h-full w-full rounded-full opacity-75", colors[status])}></span>
      )}
      <span className={clsx("relative inline-flex rounded-full h-full w-full", colors[status])}></span>
    </span>
  );
}
