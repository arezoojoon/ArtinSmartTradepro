import DashboardLayout from "@/components/layout/DashboardLayout";
import RouteGuard from "@/components/auth/RouteGuard";

export default function Layout({ children }: { children: React.ReactNode }) {
    return (
        <RouteGuard>
            <DashboardLayout>{children}</DashboardLayout>
        </RouteGuard>
    );
}
