'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X, Shield, Moon, Sun, LogOut, User } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useSession, signOut } from 'next-auth/react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import ConnectionStatusIndicator from './ConnectionStatusIndicator';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const { theme, setTheme } = useTheme();
  const pathname = usePathname();
  const { data: session, status } = useSession();
  const isAuthenticated = !!session?.user;

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  const closeMenu = () => {
    setIsOpen(false);
  };

  const isActive = (path: string) => {
    return pathname === path;
  };

  const handleSignOut = () => {
    signOut({ callbackUrl: '/' });
  };

  return (
    <nav className="bg-white dark:bg-gray-900 shadow-sm border-b border-gray-200 dark:border-gray-800">
      <div className="container mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Link href="/" className="flex items-center space-x-2" onClick={closeMenu}>
                <Shield className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                <span className="text-xl font-bold text-gray-900 dark:text-white">Sentinel AI</span>
              </Link>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <NavLink href="/dashboard" active={isActive('/dashboard')}>Dashboard</NavLink>
              <NavLink href="/analyze" active={isActive('/analyze')}>Analyze</NavLink>
              <NavLink href="/reports" active={isActive('/reports')}>Reports</NavLink>
              <NavLink href="/search" active={isActive('/search')}>Search</NavLink>
            </div>
          </div>
          <div className="hidden sm:flex items-center space-x-4">
            <ConnectionStatusIndicator />
            
            <button
              onClick={toggleTheme}
              className="p-2 rounded-md text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white focus:outline-none"
              aria-label="Toggle dark mode"
            >
              {theme === 'dark' ? <Sun /> : <Moon />}
            </button>

            {isAuthenticated ? (
              <DropdownMenu>
                <DropdownMenuTrigger className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800">
                  <User className="h-5 w-5 text-gray-600 dark:text-gray-300" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {session.user?.name || session.user?.email?.split('@')[0]}
                  </span>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>My Account</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link href="/settings/profile" className="cursor-pointer">
                      Profile Settings
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/settings/api-tokens" className="cursor-pointer">
                      API Tokens
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleSignOut} className="cursor-pointer text-red-600 dark:text-red-400">
                    <LogOut className="h-4 w-4 mr-2" />
                    Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Link 
                href="/login" 
                className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
              >
                Sign in
              </Link>
            )}
          </div>
          <div className="flex items-center sm:hidden">
            <button
              onClick={toggleMenu}
              className="p-2 rounded-md text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white focus:outline-none"
              aria-label="Toggle menu"
            >
              {isOpen ? <X /> : <Menu />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isOpen && (
        <div className="sm:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1">
            <MobileNavLink href="/dashboard" active={isActive('/dashboard')} onClick={closeMenu}>Dashboard</MobileNavLink>
            <MobileNavLink href="/analyze" active={isActive('/analyze')} onClick={closeMenu}>Analyze</MobileNavLink>
            <MobileNavLink href="/reports" active={isActive('/reports')} onClick={closeMenu}>Reports</MobileNavLink>
            <MobileNavLink href="/search" active={isActive('/search')} onClick={closeMenu}>Search</MobileNavLink>
            
            {isAuthenticated && (
              <>
                <MobileNavLink href="/settings/profile" active={isActive('/settings/profile')} onClick={closeMenu}>Profile Settings</MobileNavLink>
                <MobileNavLink href="/settings/api-tokens" active={isActive('/settings/api-tokens')} onClick={closeMenu}>API Tokens</MobileNavLink>
                <div 
                  className="block px-3 py-2 rounded-md text-base font-medium text-red-600 dark:text-red-400 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                  onClick={() => {
                    handleSignOut();
                    closeMenu();
                  }}
                >
                  Sign out
                </div>
              </>
            )}
            
            {!isAuthenticated && (
              <MobileNavLink href="/login" active={isActive('/login')} onClick={closeMenu}>Sign in</MobileNavLink>
            )}
            
            <div className="flex items-center justify-between pt-4 pb-2 px-3">
              <span className="text-gray-600 dark:text-gray-400">Dark Mode</span>
              <button
                onClick={toggleTheme}
                className="p-2 rounded-md text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white focus:outline-none"
                aria-label="Toggle dark mode"
              >
                {theme === 'dark' ? <Sun /> : <Moon />}
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}

function NavLink({ href, active, children }: { href: string; active: boolean; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
        active
          ? 'border-blue-600 dark:border-blue-400 text-gray-900 dark:text-white'
          : 'border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 hover:text-gray-700 dark:hover:text-gray-300'
      }`}
    >
      {children}
    </Link>
  );
}

function MobileNavLink({ href, active, onClick, children }: { 
  href: string; 
  active: boolean; 
  onClick: () => void;
  children: React.ReactNode 
}) {
  return (
    <Link
      href={href}
      className={`block px-3 py-2 rounded-md text-base font-medium ${
        active
          ? 'bg-blue-50 dark:bg-blue-900/30 border-l-4 border-blue-600 dark:border-blue-400 text-blue-700 dark:text-blue-400'
          : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'
      }`}
      onClick={onClick}
    >
      {children}
    </Link>
  );
}
