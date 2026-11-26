import React from 'react';
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Camera,
  Layers,
  LayoutDashboard,
  RefreshCw,
  TrendingUp,
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  activeAlertCount: number;
  isBackendHealthy: boolean;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  activeAlertCount,
  isBackendHealthy,
  onRefresh,
  isRefreshing,
}) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'inventory', label: 'Inventory & Shelf Fusion', icon: Layers },
    { id: 'vision', label: 'AI Vision & CCTV', icon: Camera },
    { id: 'forecast', label: 'Demand & Reorder', icon: TrendingUp },
    { id: 'sales', label: 'POS Sales', icon: BarChart3 },
    {
      id: 'alerts',
      label: 'Alerts',
      icon: AlertTriangle,
      badge: activeAlertCount > 0 ? activeAlertCount : undefined,
    },
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 bg-slate-950/85 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Status */}
          <div className="flex items-center space-x-3">
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 via-teal-500 to-cyan-400 shadow-lg shadow-emerald-500/25">
              <Activity className="w-5 h-5 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
                  RetailMind
                </span>
                <span className="text-xs px-1.5 py-0.5 font-bold uppercase rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  AI
                </span>
              </div>
              <div className="flex items-center space-x-1.5 text-xs text-slate-400">
                <span
                  className={`w-2 h-2 rounded-full ${
                    isBackendHealthy ? 'bg-emerald-400 animate-ping' : 'bg-rose-500'
                  }`}
                />
                <span className="text-[11px] font-medium text-slate-300">
                  {isBackendHealthy ? 'Engine Connected' : 'Engine Offline'}
                </span>
                <span className="text-slate-600">•</span>
                <span className="text-[11px] text-slate-400">Store #01 (Indiranagar)</span>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  id={`nav-tab-${item.id}`}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all duration-200 ${
                    isActive
                      ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm shadow-emerald-500/10'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                  {item.badge !== undefined && (
                    <span className="ml-1.5 px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-rose-500 text-white animate-pulse">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right Controls */}
          <div className="flex items-center space-x-3">
            <button
              id="global-refresh-btn"
              onClick={onRefresh}
              disabled={isRefreshing}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 transition shadow-sm active:scale-95 disabled:opacity-50"
              title="Refresh Store Ledger & AI Insights"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
              <span className="hidden sm:inline">Sync Data</span>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation bar */}
      <div className="md:hidden flex items-center justify-around border-t border-slate-800/80 bg-slate-950 px-2 py-1.5 overflow-x-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex flex-col items-center p-1.5 rounded text-[10px] font-medium ${
                isActive ? 'text-emerald-400' : 'text-slate-400'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="mt-0.5">{item.label.split(' ')[0]}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
};
