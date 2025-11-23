import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { SidebarProvider } from '@/components/layout/SidebarContext';
import { AuthProvider } from "@/context/AuthContext";

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    title: 'Campus USA - College Application Assistant',
    description: 'Your AI-powered college application assistant',
};

export default function RootLayout({
                                       children,
                                   }: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
        <body className={inter.className}>
        <AuthProvider>
        <SidebarProvider>
            <div className="min-h-screen bg-gray-50">
                {children}
            </div>
        </SidebarProvider>
        </AuthProvider>
        </body>
        </html>
    );
}