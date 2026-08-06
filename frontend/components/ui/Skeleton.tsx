'use client';

import React from 'react';
import { clsx } from 'clsx';

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  shape?: 'text' | 'circle' | 'card' | 'chart';
}

export function Skeleton({ className, shape = 'text', ...props }: SkeletonProps) {
  const shapes = {
    text: 'h-4 w-full rounded',
    circle: 'h-12 w-12 rounded-full',
    card: 'h-32 w-full rounded-xl',
    chart: 'h-64 w-full rounded-xl',
  };

  return (
    <div
      className={clsx(
        'animate-pulse bg-muted',
        shapes[shape],
        className
      )}
      {...props}
    />
  );
}
