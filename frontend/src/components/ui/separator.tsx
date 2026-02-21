'use client';

import * as React from 'react';

interface SeparatorProps {
    className?: string;
    orientation?: 'horizontal' | 'vertical';
    decorative?: boolean;
}

const Separator = React.forwardRef<HTMLDivElement, SeparatorProps>(
    ({ className = '', orientation = 'horizontal', decorative = true, ...props }, ref) => (
        <div
            ref={ref}
            role={decorative ? 'none' : 'separator'}
            aria-orientation={decorative ? undefined : orientation}
            className={
                `shrink-0 bg-border ${orientation === 'horizontal' ? 'h-[1px] w-full' : 'h-full w-[1px]'
                } ${className}`
            }
            {...props}
        />
    )
);
Separator.displayName = 'Separator';

export { Separator };
