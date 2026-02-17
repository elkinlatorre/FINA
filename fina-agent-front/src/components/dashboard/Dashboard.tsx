"use client";

import React, { useState } from 'react';
import {
  LayoutDashboard,
  MessageSquare,
  FileUp,
  Settings,
  LogOut,
  User,
  Search,
  PanelRightClose
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import ChatInterface from './ChatInterface';
import IngestionPanel from './IngestionPanel';
import HITLPanel from './HITLPanel';
import PortfolioOverview from './PortfolioOverview';

export default function Dashboard() {
  const { user, signOut } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const userName = user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'Member';

  return (
    <div className="dashboard-container">
      {/* Sidebar Navigation */}
      <aside className={`sidebar glass-panel ${isSidebarOpen ? 'w-64' : 'w-20'}`}>
        <div className="sidebar-header flex-center">
          <div className="logo-icon gradient-bg">F</div>
          {isSidebarOpen && <span className="logo-text ml-3">FINA</span>}
        </div>

        <nav className="sidebar-nav">
          <NavItem
            icon={<MessageSquare size={20} />}
            label="Chat & Agent"
            active={activeTab === 'chat'}
            collapsed={!isSidebarOpen}
            onClick={() => setActiveTab('chat')}
          />
          <NavItem
            icon={<FileUp size={20} />}
            label="Documents"
            active={activeTab === 'docs'}
            collapsed={!isSidebarOpen}
            onClick={() => setActiveTab('docs')}
          />
          <NavItem
            icon={<LayoutDashboard size={20} />}
            label="Portfolio"
            active={activeTab === 'portfolio'}
            collapsed={!isSidebarOpen}
            onClick={() => setActiveTab('portfolio')}
          />
        </nav>

        <div className="sidebar-footer">
          <NavItem
            icon={<Settings size={20} />}
            label="Settings"
            collapsed={!isSidebarOpen}
          />
          <div className="user-profile glass-card">
            <User size={20} className="text-primary" />
            {isSidebarOpen && (
              <div className="user-info">
                <p className="user-name">{userName}</p>
                <p className="user-status">Verified Account</p>
              </div>
            )}
          </div>
          <button onClick={signOut} className="logout-btn flex-center">
            <LogOut size={18} className="mr-2" /> {isSidebarOpen && 'Logout'}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <header className="content-header">
          <div className="search-bar glass-card">
            <Search size={18} className="text-muted" />
            <input type="text" placeholder="Search across your financial history..." />
          </div>
          <div className="header-actions">
            <button className="icon-btn glass-card"><PanelRightClose size={20} /></button>
          </div>
        </header>

        <section className="content-body">
          {activeTab === 'chat' && <ChatInterface />}
          {activeTab === 'docs' && <IngestionPanel />}
          {activeTab === 'portfolio' && <PortfolioOverview />}
        </section>
      </main>

      {/* HITL Right Panel (Simulation) */}
      <HITLPanel />

      <style jsx>{`
        .dashboard-container {
          display: flex;
          height: 100vh;
          background: #05070a;
          overflow: hidden;
        }

        .sidebar {
          display: flex;
          flex-direction: column;
          padding: 1.5rem 1rem;
          height: 100%;
          border-radius: 0 24px 24px 0;
          transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          z-index: 10;
        }

        .w-64 { width: 16rem; }
        .w-20 { width: 5rem; }

        .sidebar-header {
          margin-bottom: 3rem;
          justify-content: flex-start;
          padding-left: 0.5rem;
        }

        .logo-icon {
          width: 40px;
          height: 40px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 700;
          font-family: 'Outfit', sans-serif;
        }

        .sidebar-nav {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .sidebar-footer {
          margin-top: 2rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .user-profile {
          padding: 0.75rem;
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .user-name {
          font-size: 0.85rem;
          font-weight: 600;
        }

        .user-status {
          font-size: 0.7rem;
          color: var(--secondary);
        }

        .logout-btn {
          width: 100%;
          padding: 0.75rem;
          color: #ef4444;
          background: rgba(239, 68, 68, 0.05);
          border: 1px solid rgba(239, 68, 68, 0.1);
          border-radius: 12px;
          cursor: pointer;
          font-weight: 600;
          transition: var(--transition);
        }

        .logout-btn:hover {
          background: rgba(239, 68, 68, 0.1);
        }

        .main-content {
          flex: 1;
          display: flex;
          flex-direction: column;
          padding: 1.5rem 2rem;
          overflow: hidden;
        }

        .content-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 2rem;
        }

        .search-bar {
          width: 400px;
          padding: 0.6rem 1rem;
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .search-bar input {
          background: none;
          border: none;
          color: white;
          width: 100%;
          font-size: 0.9rem;
        }

        .search-bar input:focus { outline: none; }

        .content-body {
          flex: 1;
          overflow: hidden;
          background: rgba(255, 255, 255, 0.01);
          border-radius: 20px;
        }

        .icon-btn {
          padding: 0.6rem;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }
      `}</style>
    </div>
  );
}

function NavItem({ icon, label, active = false, collapsed = false, onClick }: any) {
  return (
    <button
      onClick={onClick}
      className={`nav-item ${active ? 'active' : ''} ${collapsed ? 'collapsed' : ''}`}
    >
      <span className="icon">{icon}</span>
      {!collapsed && <span className="label">{label}</span>}
      <style jsx>{`
        .nav-item {
          display: flex;
          align-items: center;
          padding: 0.75rem 1rem;
          border-radius: 12px;
          color: var(--text-muted);
          background: transparent;
          border: none;
          cursor: pointer;
          transition: var(--transition);
          width: 100%;
          gap: 1rem;
        }

        .nav-item.collapsed {
          justify-content: center;
          padding: 0.75rem;
        }

        .nav-item:hover {
          background: rgba(255, 255, 255, 0.05);
          color: white;
        }

        .nav-item.active {
          background: rgba(59, 130, 246, 0.1);
          color: var(--primary);
          border: 1px solid rgba(59, 130, 246, 0.2);
        }

        .label {
          font-weight: 500;
          font-size: 0.95rem;
        }
      `}</style>
    </button>
  );
}
