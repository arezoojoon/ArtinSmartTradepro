import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

export function formatCurrency(amount: number, currency: string = "AED"): string {
    return new Intl.NumberFormat("en-AE", {
        style: "currency",
        currency: currency,
    }).format(amount);
}
