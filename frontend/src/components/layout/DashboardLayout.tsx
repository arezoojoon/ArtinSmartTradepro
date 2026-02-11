import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

const DashboardLayout = ({ children }: { children: React.ReactNode }) => {
    return (
        <div className="flex h-screen overflow-hidden bg-background">
            <div className="hidden md:block">
                <Sidebar />
            </div>
            <div className="flex flex-1 flex-col overflow-hidden">
                <TopBar />
                <main className="flex-1 overflow-y-auto bg-navy-950 p-6 text-white">
                    {children}
                </main>
            </div>
        </div>
    );
};

export default DashboardLayout;
