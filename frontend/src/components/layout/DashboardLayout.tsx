import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import BottomNav from "./BottomNav";

const DashboardLayout = ({ children }: { children: React.ReactNode }) => {
    return (
        <div className="flex h-screen overflow-hidden bg-background">
            {/* Desktop Sidebar */}
            <div className="hidden md:block">
                <Sidebar />
            </div>

            <div className="flex flex-1 flex-col overflow-hidden">
                <TopBar />

                {/* Main Content - Add bottom padding on mobile for BottomNav */}
                <main className="flex-1 overflow-y-auto bg-navy-950 p-4 md:p-6 text-white pb-20 md:pb-6">
                    {children}
                </main>

                {/* Mobile Bottom Nav */}
                <BottomNav />
            </div>
        </div>
    );
};

export default DashboardLayout;
