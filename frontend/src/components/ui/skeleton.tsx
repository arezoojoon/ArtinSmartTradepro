import { cn } from "@/lib/utils"

type SkeletonProps = React.HTMLAttributes<HTMLDivElement>

function Skeleton({ className, ...props }: SkeletonProps) {
    return (
        <div
            className={cn(
                "animate-pulse rounded-md bg-gradient-to-r from-navy-900/40 via-navy-800/60 to-navy-900/40",
                className
            )}
            {...props}
        />
    )
}

export { Skeleton }
