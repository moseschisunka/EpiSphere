'use client';

import React from 'react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'glass';
  accent?: 'critical' | 'high' | 'moderate' | 'low' | 'none';
}

export function Card({ className, variant = 'default', accent = 'none', children, ...props }: CardProps) {
  const variants = {
    default: 'bg-card text-card-foreground border border-border shadow-sm',
    elevated: 'bg-card text-card-foreground shadow-lg border border-border',
    glass: 'glass',
  };

  const accents = {
    critical: 'border-t-4 border-t-severity-critical',
    high: 'border-t-4 border-t-severity-high',
    moderate: 'border-t-4 border-t-severity-moderate',
    low: 'border-t-4 border-t-severity-low',
    none: '',
  };

  return (
    <motion.div
      whileHover={{ y: -2 }}
      className={clsx('rounded-xl overflow-hidden transition-all', variants[variant], accents[accent], className)}
      {...props as any}
    >
      {children}
    </motion.div>
  );
}

export function CardHeader({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={clsx('flex flex-col space-y-1.5 p-6', className)} {...props}>
      {children}
    </div>
  );
}

export function CardContent({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={clsx('p-6 pt-0', className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={clsx('flex items-center p-6 pt-0', className)} {...props}>
      {children}
    </div>
  );
}
