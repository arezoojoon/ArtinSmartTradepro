import { TooltipProvider } from "@/components/ui/tooltip"

export default function ToolboxLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <div className="flex flex-col h-full">
            <div className="flex-1 space-y-4 p-8 pt-6">
                <div className="flex items-center justify-between space-y-2">
                    <h2 className="text-3xl font-bold tracking-tight">Trader Toolbox 🧰</h2>
                </div>
                <TooltipProvider>
                    {children}
                </TooltipProvider>
            </div>
        </div>
    )
}
