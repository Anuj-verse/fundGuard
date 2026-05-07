import { Outlet, NavLink } from "react-router-dom";
import { Activity, ShieldAlert, GitGraph, Briefcase, FileText } from "lucide-react";

export default function MainLayout() {
  return (
    <div className="flex h-screen bg-dark-bg text-gray-200">
      {/* Sidebar */}
      <aside className="w-64 bg-dark-surface border-r border-gray-800 flex flex-col">
        <div className="p-6 font-bold text-2xl tracking-wider text-safe border-b border-gray-800">
          FundGuard
        </div>
        <nav className="flex-1 py-6 flex flex-col gap-2 px-4">
          <NavItem to="/dashboard" icon={<Activity />} label="Dashboard" />
          <NavItem to="/alerts" icon={<ShieldAlert />} label="Live Alerts" />
          <NavItem to="/graph/search" icon={<GitGraph />} label="Graph Intel" />
          <NavItem to="/cases" icon={<Briefcase />} label="Cases" />
          <NavItem to="/reports" icon={<FileText />} label="Reports" />
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        <header className="h-16 bg-dark-surface border-b border-gray-800 flex items-center px-8">
          <h1 className="text-xl font-semibold opacity-90">Investigation Hub</h1>
        </header>
        <div className="flex-1 overflow-y-auto p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

function NavItem({ to, icon, label }: { to: string; icon: React.ReactNode; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors font-medium ${
          isActive ? "bg-gray-800 text-safe" : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
        }`
      }
    >
      {icon}
      <span>{label}</span>
    </NavLink>
  );
}