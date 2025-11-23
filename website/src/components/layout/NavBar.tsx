'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSidebar } from './SidebarContext';
import { usePreload } from '@/hooks/usePreload';
import {
    BsList,
    BsBell,
    BsSearch,
    BsChatDots,
    BsFileEarmark,
    BsPerson,
    BsHouseDoor
} from 'react-icons/bs';

export default function NavBar() {
    const pathname = usePathname();
    const { isOpen, setIsOpen } = useSidebar();
    const {
        preloadRoute,
        preloadUniversities,
        preloadAIAssistant,
        preloadDocuments,
        preloadProfile
    } = usePreload();

    // preload dashboard
    const preloadDashboard = () => preloadRoute('/dashboard');

    const isActive = (path: string) => {
        return pathname?.startsWith(path);
    };

    return (
        <header className="relative top-0 left-0 right-0 bg-white border-b border-gray-200 z-30">
            <div className="container mx-auto px-4 max-w-6xl">
                <div className="flex h-16 items-center justify-between">
                    <div className="flex items-center">
                        <button
                            type="button"
                            className="text-gray-500 hover:text-gray-600 mr-4 focus:outline-none lg:hidden"
                            onClick={() => setIsOpen(!isOpen)}
                        >
                            <BsList className="h-6 w-6" />
                        </button>
                        <Link
                            href="/checklist"
                            className="flex items-center"
                            onMouseEnter={preloadDashboard}
                        >
                            <span className="bg-blue-600 text-white px-2 py-1 rounded text-sm mr-1">Campus</span>
                            <span className="font-bold text-sm">USA</span>
                        </Link>
                    </div>

                    <div className={`
                        flex transition-transform duration-300 ease-in-out z-20
                        px-4 py-4 bg-white shadow-md
                    
                        /* mobile sidebar styles */
                        absolute top-full left-0 w-[300px] flex-col space-y-4
                        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
                    
                        /* desktop horizontal navbar styles */
                        lg:relative lg:top-auto lg:left-auto lg:translate-x-0
                        lg:w-auto lg:flex-row lg:space-y-0 lg:space-x-4
                        lg:bg-transparent lg:shadow-none
                      `}>
                        <Link
                            href="/checklist"
                            className={`inline-flex items-center px-1 pt-1 text-sm font-medium ${
                                isActive('/checklist')
                                    ? 'text-blue-600 relative after:absolute after:bottom-[-6px] lg:after:bottom-[-20px] after:left-0 after:right-0 after:h-[2px] after:bg-blue-600'
                                    : 'text-gray-500 hover:text-gray-700'
                            }`}
                            onMouseEnter={preloadDashboard}
                        >
                            <BsHouseDoor className="mr-2 h-4 w-4" />
                            dashboard
                        </Link>
                        <Link
                            href="/universities"
                            className={`inline-flex items-center px-1 pt-1 text-sm font-medium ${
                                isActive('/universities')
                                    ? 'text-blue-600 relative after:absolute after:bottom-[-6px] lg:after:bottom-[-20px] after:left-0 after:right-0 after:h-[2px] after:bg-blue-600'
                                    : 'text-gray-500 hover:text-gray-700'
                            }`}
                            onMouseEnter={preloadUniversities}
                        >
                            <BsSearch className="mr-2 h-4 w-4" />
                            universities
                        </Link>
                        <Link
                            href="/ai-assistant"
                            className={`inline-flex items-center px-1 pt-1 text-sm font-medium ${
                                isActive('/ai-assistant')
                                    ? 'text-blue-600 relative after:absolute after:bottom-[-6px] lg:after:bottom-[-20px] after:left-0 after:right-0 after:h-[2px] after:bg-blue-600'
                                    : 'text-gray-500 hover:text-gray-700'
                            }`}
                            onMouseEnter={preloadAIAssistant}
                        >
                            <BsChatDots className="mr-2 h-4 w-4" />
                            AI assistant
                        </Link>
                        <Link
                            href="/documents_essays"
                            className={`inline-flex items-center px-1 pt-1 text-sm font-medium ${
                                isActive('/documents_essays')
                                    ? 'text-blue-600 relative after:absolute after:bottom-[-6px] lg:after:bottom-[-20px] after:left-0 after:right-0 after:h-[2px] after:bg-blue-600'
                                    : 'text-gray-500 hover:text-gray-700'
                            }`}
                            onMouseEnter={preloadDocuments}
                        >
                            <BsFileEarmark className="mr-2 h-4 w-4" />
                            documents & essays
                        </Link>
                        <Link
                            href="/profile"
                            className={`inline-flex items-center px-1 pt-1 text-sm font-medium ${
                                isActive('/profile')
                                    ? 'text-blue-600 relative after:absolute after:bottom-[-6px] lg:after:bottom-[-20px] after:left-0 after:right-0 after:h-[2px] after:bg-blue-600'
                                    : 'text-gray-500 hover:text-gray-700'
                            }`}
                            onMouseEnter={preloadProfile}
                        >
                            <BsPerson className="mr-2 h-4 w-4" />
                            profile
                        </Link>
                    </div>

                    <div className="flex items-center space-x-4">
                        <button className="p-1 rounded-full text-gray-500 hover:text-gray-600 focus:outline-none">
                            <BsBell className="h-6 w-6" />
                        </button>

                        <Link
                            href="/profile"
                            className="flex items-center"
                            onMouseEnter={preloadProfile}
                        >
                            <div className="h-8 w-8 bg-gray-300 rounded-full flex items-center justify-center text-gray-600 text-sm mr-1">
                                DS
                            </div>
                            <span className="hidden md:inline-block text-sm ml-1 font-medium">Dmitry</span>
                        </Link>
                    </div>
                </div>
            </div>
        </header>
    );
}