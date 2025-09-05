// src/components/common/Layout.tsx - CORRIGÉ
import React, { ReactNode } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';

interface LayoutProps {
  showSidebar?: boolean;
  children?: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ showSidebar = true, children }) => {
  return (
    <div className="fixed w-full h-full bg-gradient-to-br from-black to-black dark:from-purple-600 dark:to-neutral-900">
      {showSidebar && <Sidebar />}
      <div className={`flex flex-col h-full transition-all duration-300 ${
        showSidebar ? 'ml-64' : ''
      }`} style={{
        // Ajustement dynamique basé sur la largeur de la sidebar
        marginLeft: showSidebar ? 'var(--sidebar-width, 256px)' : '0'
      }}>
        <Header showSidebar={showSidebar} />
        <main className="flex-1 overflow-hidden">
          {children || <Outlet />}
        </main>
      </div>
    </div>
  );
};

export default Layout;