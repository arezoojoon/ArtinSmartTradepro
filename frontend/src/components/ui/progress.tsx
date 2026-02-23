import * as React from "react"
import { cn } from "@/lib/utils"

type ProgressProps = React.HTMLAttributes<HTMLDivElement> & {
    value?: number
    max?: number
    indicatorClassName?: string
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
    ({ className, value = 0, max = 100, indicatorClassName, ...props }, ref) => {
        const clamped = Math.min(Math.max(value, 0), max)
        const percentage = (clamped / max) * 100

        return (
            <div
                ref={ref}
                role="progressbar"
                aria-valuenow={Number(percentage.toFixed(2))}
                aria-valuemax={max}
                aria-valuemin={0}
                className={cn(
                    "relative h-3 w-full overflow-hidden rounded-full bg-[#0e1e33]/60",
                    className
                )}
                {...props}
            >
                <div
                    className={cn(
                        "h-full w-full origin-left rounded-full transition-transform duration-300",
                        indicatorClassName || "bg-gradient-to-r from-gold-500 via-amber-400 to-yellow-300"
                    )}
                    style={{ transform: `translateX(-${100 - percentage}%)` }}
                />
            </div>
        )
    }
)
Progress.displayName = "Progress"

export { Progress }
