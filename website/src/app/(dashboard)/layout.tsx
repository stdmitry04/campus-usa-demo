// dashboard layout to wrap all authenticated pages with navbar
import NavBar from '@/components/layout/NavBar';

export default function DashboardLayout({
                                            children,
                                        }: {
    children: React.ReactNode;
}) {
    return (
        <>
            <NavBar />
            <main className="pt-16">
                <div className="container mx-auto px-4 py-8 max-w-6xl">
                    {children}
                </div>
            </main>
        </>
    );
}