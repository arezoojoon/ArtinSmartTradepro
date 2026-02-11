export default function AuthLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex min-h-screen items-center justify-center bg-navy-950 px-4 py-12 sm:px-6 lg:px-8">
            <div className="w-full max-w-md space-y-8">
                <div className="text-center">
                    <h2 className="mt-6 text-3xl font-extrabold text-white tracking-tight">
                        <span className="text-gold-400">Artin</span> Smart Trade
                    </h2>
                </div>
                {children}
            </div>
        </div>
    );
}
