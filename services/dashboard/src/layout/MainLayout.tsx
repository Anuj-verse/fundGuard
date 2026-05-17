import { createContext, useContext, useEffect, useState } from "react";
import { Outlet, NavLink, Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Activity,
  ShieldAlert,
  GitGraph,
  Briefcase,
  FileText,
  Menu,
  X,
  Search,
  MapPin,
  ShieldCheck,
  Moon,
  Sun,
} from "lucide-react";

type DashboardAnchorContextType = {
  registerDashboardAnchor: (node: HTMLDivElement | null) => void;
  requestDashboardScroll: () => void;
};

type ThemeContextType = {
  isDarkMode: boolean;
};

const DashboardAnchorContext = createContext<DashboardAnchorContextType | null>(null);
const ThemeContext = createContext<ThemeContextType | null>(null);

export function useDashboardAnchor() {
  const context = useContext(DashboardAnchorContext);
  if (!context) {
    throw new Error("useDashboardAnchor must be used within MainLayout");
  }
  return context;
}

export function useThemeMode() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useThemeMode must be used within MainLayout");
  }
  return context;
}

export default function MainLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [dashboardAnchor, setDashboardAnchor] = useState<HTMLDivElement | null>(null);
  const [pendingDashboardScroll, setPendingDashboardScroll] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (pendingDashboardScroll && dashboardAnchor) {
      dashboardAnchor.scrollIntoView({ behavior: "smooth", block: "start" });
      setPendingDashboardScroll(false);
    }
  }, [pendingDashboardScroll, dashboardAnchor]);

  useEffect(() => {
    document.body.style.overflow = isSidebarOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [isSidebarOpen]);

  const requestDashboardScroll = () => {
    setPendingDashboardScroll(true);
    navigate("/dashboard");
    setIsSidebarOpen(false);
  };

  const rootThemeClasses = isDarkMode
    ? "bg-[#0B111E] text-slate-100"
    : "bg-[#F4F6F9] text-slate-950";

  const headerSurface = isDarkMode
    ? "bg-[#0F172A]/80 border-slate-800 text-slate-100"
    : "bg-white/90 border-slate-200 text-slate-950";

  const surfacePanel = isDarkMode
    ? "bg-[#1E293B] border-slate-700 text-slate-100"
    : "bg-white border-slate-200 text-slate-950";

  const profilePopupSurface = isDarkMode
    ? "bg-slate-800 border border-slate-700 text-slate-100"
    : "bg-white border border-gray-200 text-gray-900 shadow-2xl shadow-gray-400/30";

  const profileAccentButton = isDarkMode
    ? "bg-emerald-500 text-slate-950 hover:bg-emerald-400"
    : "bg-emerald-700 text-white hover:bg-emerald-600";

  return (
    <DashboardAnchorContext.Provider
      value={{ registerDashboardAnchor: setDashboardAnchor, requestDashboardScroll }}
    >
      <ThemeContext.Provider value={{ isDarkMode }}>
        <div className={`flex min-h-screen flex-col font-sans ${rootThemeClasses} transition-colors duration-300 overflow-hidden`}>
          <header className={`sticky top-0 z-50 h-[72px] border-b ${headerSurface} backdrop-blur-xl bg-opacity-85`}> 
            <div className="mx-auto  flex items-center justify-between gap-3 px-6 max-w-[1600px] h-[72px]">
              <div className="flex items-center gap-4">
                <Link to="/dashboard" className="inline-flex items-center gap-3 rounded-2xl border border-white/5 bg-transparent px-3 py-2 transition transform hover:opacity-90 hover:scale-105">
                  <ShieldCheck size={28} className="text-emerald-400" />
                  <div className="leading-none">
                    <p className="text-[28px] font-black tracking-tight leading-none text-white">FundGuard</p>
                    <p className="text-[10px] mt-3 uppercase tracking-[0.35em] font-bold text-emerald-400">BANK FRAUD DETECTION PLATFORM</p>
                  </div>
                </Link>
                <div className="inline-flex items-center gap-2 rounded-full border border-slate-300/30 bg-slate-950/95 px-4 py-2 text-sm font-semibold text-slate-100 shadow-sm shadow-black/10">
                  <MapPin size={20} className="text-emerald-300" />
                  <span>System Scope: India Operations</span>
                </div>
              </div>

              <div className="relative flex-1 max-w-[480px]">
                <Search size={18} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="search"
                  placeholder="Search transactions, accounts, or alert IDs..."
                  className="w-full h-11 rounded-full border border-white/5 bg-[#0B1220] pl-10 pr-4 text-sm placeholder:text-slate-500 text-slate-200 outline-none transition focus:border-emerald-400/80 focus:ring-2 focus:ring-emerald-400/10"
                />
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setIsSidebarOpen(true)}
                  className="inline-flex items-center gap-2 rounded-full bg-[#111827] border border-white/5 px-5 py-2.5 text-sm font-bold text-slate-100 transition-all duration-200 hover:bg-[#1E293B]"
                >
                  <Menu size={18} />
                  <span>Features</span>
                </button>
                <motion.button
                  type="button"
                  onClick={() => setIsDarkMode((current) => !current)}
                  whileTap={{ scale: 0.95 }}
                  animate={{ rotate: isDarkMode ? 360 : 0 }}
                  transition={{ duration: 0.35, ease: "easeInOut" }}
                  className="grid h-10 w-10 place-items-center rounded-full border border-white/5 bg-[#0f1724] text-slate-100 transition hover:bg-[#111827]"
                  aria-label="Toggle dark mode"
                >
                  {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
                </motion.button>
                <div className="relative">
                  <button
                    onClick={() => setIsProfileOpen((open) => !open)}
                    className="flex h-10 w-10 items-center justify-center rounded-full border border-white/5 bg-[#0f1724] text-sm font-bold text-white shadow-sm shadow-black/20 transition hover:border-emerald-400"
                    aria-label="Open profile menu"
                  >
                    R
                  </button>
                  {isProfileOpen && (
                    <div className={`absolute right-0 top-full mt-2 w-64 rounded-2xl p-3 ${profilePopupSurface}`}>
                      <div className="space-y-4">
                        <div>
                          <p className="text-[11px] uppercase tracking-widest font-bold text-gray-400">USER ACCOUNT</p>
                          <p className="mt-1 text-base font-bold font-sans">Yjsjs</p>
                          <p className="text-sm font-mono text-gray-500">FG-98765-IN</p>
                        </div>
                        <button
                          onClick={() => {
                            navigate("/profile");
                            setIsProfileOpen(false);
                          }}
                          className={`w-full rounded-2xl px-4 py-2 text-sm font-bold transition ${profileAccentButton}`}
                        >
                          Manage Your Account 
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </header>

          <motion.div
            className={`fixed inset-0 z-40 bg-black/50 backdrop-blur-sm transition-opacity duration-300 ${
              isSidebarOpen ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"
            }`}
            onClick={() => setIsSidebarOpen(false)}
            initial={false}
            animate={{ opacity: isSidebarOpen ? 1 : 0 }}
          />

          <motion.aside
            initial={false}
            animate={{ x: isSidebarOpen ? "0%" : "100%" }}
            transition={{ type: "spring", stiffness: 260, damping: 30 }}
            className="fixed inset-y-0 right-0 z-50 w-[340px] border-l border-slate-700 bg-[#090a0f] px-6 py-6 shadow-2xl shadow-slate-950/40 overflow-y-auto h-screen"
          >
            <div className="flex items-center justify-between pb-4">
              <div className="mt-5">
                <p className="text-xs uppercase tracking-[0.3em] text-emerald-400/80">Feature Center</p>
                <h2 className="text-2xl font-semibold text-white">FundGuard Workspace</h2>
              </div>
              <button
                onClick={() => setIsSidebarOpen(false)}
                className="rounded-full border border-slate-700 p-2 text-slate-300 transition hover:bg-slate-900"
                aria-label="Close features drawer"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <nav className="mt-3 flex flex-col gap-3">
              <SidebarLink icon={<Activity size={18} />} label="Dashboard" onClick={() => { requestDashboardScroll(); setIsSidebarOpen(false); }} />
              <SidebarLink icon={<ShieldAlert size={18} />} label="Live Alerts" to="/alerts" onClick={() => setIsSidebarOpen(false)} />
              <SidebarLink icon={<GitGraph size={18} />} label="Graph Intel" to="/graph/FG-98765-IN" onClick={() => setIsSidebarOpen(false)} />
              <SidebarLink icon={<Briefcase size={18} />} label="Cases" to="/cases" onClick={() => setIsSidebarOpen(false)} />
              <SidebarLink icon={<FileText size={18} />} label="Reports" to="/reports" onClick={() => setIsSidebarOpen(false)} />
              <SidebarLink icon={<FileText size={18} />} label="Documentation" to="/docs" onClick={() => setIsSidebarOpen(false)} />
            </nav>
          </motion.aside>

          <main className="flex-1 w-full max-w-[1600px] mx-auto px-6 lg:px-8 pt-4 pb-6 pt-8">
            <Outlet />
          </main>
        </div>
      </ThemeContext.Provider>
    </DashboardAnchorContext.Provider>
  );
}

function SidebarLink({
  icon,
  label,
  to,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  to?: string;
  onClick: () => void;
}) {
  if (to) {
    return (
      <NavLink
        to={to}
        onClick={onClick}
        className={({ isActive }) =>
          `flex items-center gap-3 rounded-2xl border border-slate-700 px-4 py-3 text-sm font-medium transition ${
            isActive ? "bg-emerald-500/10 text-emerald-300" : "text-slate-300 hover:bg-white/5"
          }`
        }
      >
        {icon}
        <span>{label}</span>
      </NavLink>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-full items-center gap-3 rounded-2xl border border-slate-700 bg-[#0f1219] px-4 py-3 text-left text-sm font-medium text-slate-300 transition hover:bg-white/5"
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}
