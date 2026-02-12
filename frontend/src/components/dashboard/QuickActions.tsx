'use client';

import {
    Zap,
    Search,
    Plus,
    FileText,
    Users,
    Settings,
    Mail,
    Phone,
    BarChart,
    Truck
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

interface QuickActionsProps {
    className?: string; // Correctly added className to props
}

const quickActions = [
    {
        title: 'New Lead',
        icon: Plus,
        href: '/leads/new',
        variant: 'default',
        color: 'bg-primary text-primary-foreground'
    },
    {
        title: 'Search Prospects',
        icon: Search,
        href: '/hunter',
        variant: 'secondary',
        color: 'bg-secondary text-secondary-foreground'
    },
    {
        title: 'AI Analysis',
        icon: Zap,
        href: '/brain/opportunities',
        variant: 'outline',
        color: 'bg-background hover:bg-accent'
    },
    {
        title: 'Campaigns',
        icon: Mail,
        href: '/crm/campaigns',
        variant: 'ghost',
        color: 'bg-transparent hover:bg-accent'
    }
];

export default function QuickActions({ className }: QuickActionsProps) {
    return (
        <div className={`grid grid-cols-2 gap-4 sm:grid-cols-4 ${className || ''}`}>
            {quickActions.map((action) => {
                const Icon = action.icon;
                return (
                    <Link key={action.title} href={action.href}>
                        <Button
                            variant={action.variant as any}
                            className="h-24 w-full flex-col gap-2 shadow-sm transition-all hover:scale-105"
                        >
                            <Icon className="h-6 w-6" />
                            <span className="text-xs font-semibold">{action.title}</span>
                        </Button>
                    </Link>
                );
            })}
        </div>
    );
}
