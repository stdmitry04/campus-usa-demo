'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function DocumentsEssaysLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();

    const isActive = (path: string) => {
        return pathname?.startsWith(path);
    };

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4">Documents & Essays</h1>

            {/* Tabs */}
            <div className="flex mb-1 space-x-4">
                <Link
                    href="/documents_essays/documents"
                    className={`relative inline-flex text-sm font-medium px-1 pt-1 ${
                        isActive('/documents_essays/documents')
                            ? 'text-blue-600 after:absolute after:bottom-[-4px] after:left-0 after:right-0 after:h-[2px] after:bg-blue-600'
                            : 'text-gray-500 hover:text-blue-600'
                    }`}
                >
                    My Documents
                </Link>
                <Link
                    href="/documents_essays/essays"
                    className={`relative inline-flex text-sm font-medium px-1 pt-1 ${
                        isActive('/documents_essays/essays')
                            ? 'text-blue-600 after:absolute after:bottom-[-4px] after:left-0 after:right-0 after:h-[2px] after:bg-blue-600'
                            : 'text-gray-500 hover:text-blue-600'
                    }`}
                >
                    My Essays
                </Link>
            </div>

            <div className="border-b mb-6 border-gray-300"/>

            {children}
        </div>
    );
}
