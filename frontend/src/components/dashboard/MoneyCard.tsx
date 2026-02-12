import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface MoneyCardProps {
    title: string;
    value: number;
    icon: LucideIcon;
    trend?: string;
    trendUp?: boolean;
    color?: "gold" | "blue" | "green";
    isCount?: boolean;
    isCurrency?: boolean;
}

const MoneyCard = ({ title, value, icon: Icon, trend, trendUp, color = "blue", isCount, isCurrency }: MoneyCardProps) => {
    const colorClasses = {
        gold: "text-gold-400 bg-gold-400/10",
        blue: "text-blue-400 bg-blue-400/10",
        green: "text-green-400 bg-green-400/10",
    };

    const formatValue = () => {
        if (isCurrency) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
            }).format(value);
        } else if (isCount) {
            return value.toLocaleString();
        } else {
            return value.toLocaleString();
        }
    };

    return (
        <Card className="border-navy-800 bg-navy-900 text-white">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-400">
                    {title}
                </CardTitle>
                <div className={cn("rounded-full p-2", colorClasses[color])}>
                    <Icon className="h-4 w-4" />
                </div>
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold">{formatValue()}</div>
                {trend && (
                    <p className="text-xs text-gray-400 mt-1">
                        <span className={cn(trendUp ? "text-green-500" : "text-red-500", "font-medium")}>
                            {trend}
                        </span>{" "}
                        from last month
                    </p>
                )}
            </CardContent>
        </Card>
    );
};

export default MoneyCard;
