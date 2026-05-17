import React, { useState } from "react";
import {
  ShieldCheck,
  Search,
  BookOpen,
  Brain,
  Database,
  Activity,
  Bell,
  Network,
  BarChart3,
  Cpu,
  ArrowRight,
  Home,
  Workflow,
  AlertTriangle,
} from "lucide-react";

const sidebarItems = [
  {
    title: "Overview",
    items: [
      {
        id: "intro",
        icon: <Home size={16} />,
        label: "Introduction",
      },
      {
        id: "architecture",
        icon: <Workflow size={16} />,
        label: "Architecture",
      },
      {
        id: "features",
        icon: <BookOpen size={16} />,
        label: "Features",
      },
      {
        id: "dataflow",
        icon: <Activity size={16} />,
        label: "Data Flow",
      },
    ],
  },
  {
    title: "Detection",
    items: [
      {
        id: "fraud",
        icon: <ShieldCheck size={16} />,
        label: "Fraud Methods",
      },
      {
        id: "risk",
        icon: <BarChart3 size={16} />,
        label: "Risk Factors",
      },
      {
        id: "ml",
        icon: <Brain size={16} />,
        label: "ML Models",
      },
      {
        id: "graph",
        icon: <Network size={16} />,
        label: "Graph Engine",
      },
    ],
  },
  {
    title: "Operations",
    items: [
      {
        id: "monitoring",
        icon: <Bell size={16} />,
        label: "Monitoring",
      },
      {
        id: "alerts",
        icon: <AlertTriangle size={16} />,
        label: "Alerts",
      },
      {
        id: "deployment",
        icon: <Database size={16} />,
        label: "Deployment",
      },
    ],
  },
];

const cards = [
  {
    title: "Fraud Detection",
    desc: "Advanced fraud prevention methods and layered detection logic.",
    icon: <ShieldCheck size={26} className="text-emerald-400" />,
  },
  {
    title: "Risk Scoring",
    desc: "AI-powered transaction risk assessment engine.",
    icon: <BarChart3 size={26} className="text-cyan-400" />,
  },
  {
    title: "ML Models",
    desc: "Machine learning pipelines for anomaly detection.",
    icon: <Brain size={26} className="text-pink-400" />,
  },
  {
    title: "Graph Analytics",
    desc: "Relationship mapping and fraud network discovery.",
    icon: <Network size={26} className="text-green-400" />,
  },
  {
    title: "Rule Engine",
    desc: "Custom fraud rules and real-time business logic.",
    icon: <Cpu size={26} className="text-teal-400" />,
  },
  {
    title: "Architecture",
    desc: "Microservices infrastructure and deployment overview.",
    icon: <Database size={26} className="text-sky-400" />,
  },
];

const Documentation = () => {
  const [activeDoc, setActiveDoc] = useState("intro");

  return (
    <div className="h-screen bg-[#020817] text-white flex overflow-hidden">
      {/* Sidebar */}
      <aside className="hidden lg:flex w-[260px] h-screen sticky top-0 bg-[#050d1d] border-r border-white/5 flex-col px-5 py-6 overflow-y-auto scrollbar-thin scrollbar-thumb-emerald-500/20 scrollbar-track-transparent">
        {/* Logo */}
        <div className="mb-10">
          <h1 className="text-2xl font-bold tracking-tight">
            FundGuard{" "}
            <span className="text-emerald-400">
              Docs
            </span>
          </h1>

          <p className="text-[11px] tracking-[0.2em] mt-2 text-emerald-400/70 uppercase">
            Fraud Detection Platform
          </p>
        </div>

        {/* Navigation */}
        <div className="space-y-8">
          {sidebarItems.map((section, i) => (
            <div key={i}>
              <h3 className="text-[11px] uppercase tracking-widest text-gray-500 mb-3">
                {section.title}
              </h3>

              <div className="space-y-1.5">
                {section.items.map((item, idx) => {
                  const isActive =
                    activeDoc === item.id;

                  return (
                    <button
                      key={idx}
                      onClick={() =>
                        setActiveDoc(item.id)
                      }
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                        isActive
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-[0_0_20px_rgba(16,185,129,0.15)]"
                          : "text-gray-400 hover:bg-white/[0.03]"
                      }`}
                    >
                      {item.icon}

                      <span className="text-sm">
                        {item.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Help Box */}
        <div className="mt-auto rounded-2xl border border-white/5 bg-[#071224] p-5">
          <h2 className="font-semibold mb-2">
            Need Help?
          </h2>

          <p className="text-sm text-gray-400 leading-6 mb-5">
            View troubleshooting guides and
            deployment docs.
          </p>

          <button className="w-full rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-medium py-3 transition-all">
            Open Docs
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 h-screen overflow-y-auto scrollbar-thin scrollbar-thumb-emerald-500/20 scrollbar-track-transparent">
        {/* Topbar */}
        <header className="border-b border-white/5 px-6 lg:px-10 py-5 bg-[#020817]">
          <div className="flex items-center bg-[#071224] border border-white/5 rounded-full px-5 py-3 w-full max-w-[520px]">
            <Search
              size={18}
              className="text-gray-500"
            />

            <input
              type="text"
              placeholder="Search documentation..."
              className="bg-transparent outline-none ml-3 text-sm flex-1 placeholder:text-gray-500 text-white"
            />
          </div>
        </header>

        {/* Hero */}
        <section className="px-6 lg:px-10 pt-8">
          <div className="relative overflow-hidden rounded-3xl border border-white/5 bg-gradient-to-br from-[#071224] via-[#03111f] to-[#04172a] p-8 lg:p-10">
            <div className="absolute top-0 right-0 w-[350px] h-[350px] bg-emerald-500/10 blur-[120px]" />

            <div className="relative z-10 flex flex-col lg:flex-row items-center justify-between gap-10">
              <div className="max-w-2xl">
                <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-6">
                  <BookOpen
                    size={30}
                    className="text-emerald-400"
                  />
                </div>

                <h1 className="text-4xl lg:text-5xl font-bold leading-tight mb-4">
                  FundGuard Documentation
                </h1>

                <h2 className="text-emerald-400 text-xl font-semibold mb-5">
                  AI Powered Fraud Detection
                </h2>

                <p className="text-gray-400 leading-8 max-w-xl">
                  Comprehensive guides for
                  understanding, deploying, and
                  scaling intelligent banking fraud
                  prevention infrastructure.
                </p>
              </div>

              <div className="hidden lg:flex items-center justify-center">
                <div className="w-[240px] h-[240px] rounded-full border border-emerald-500/20 bg-emerald-500/5 flex items-center justify-center">
                  <ShieldCheck
                    size={90}
                    className="text-emerald-400"
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Overview Cards */}
        <section className="px-6 lg:px-10 pt-10">
          <div className="mb-8">
            <h2 className="text-3xl font-bold">
              Documentation Overview
            </h2>

            <p className="text-gray-400 mt-2">
              Explore fraud detection modules,
              machine learning pipelines, and
              architecture.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {cards.map((card, index) => (
              <div
                key={index}
                className="group rounded-3xl border border-white/5 bg-[#071224] hover:border-emerald-500/20 hover:bg-[#091427] transition-all p-6"
              >
                <div className="mb-5">
                  {card.icon}
                </div>

                <h3 className="text-xl font-semibold mb-3">
                  {card.title}
                </h3>

                <p className="text-gray-400 text-sm leading-7">
                  {card.desc}
                </p>

                <div className="mt-6">
                  <ArrowRight className="text-emerald-400 group-hover:translate-x-1 transition-all" />
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Pipeline */}
        <section className="px-6 lg:px-10 py-10">
          <div className="rounded-3xl border border-white/5 bg-[#071224] p-8 lg:p-10">
            <h2 className="text-3xl font-bold mb-2">
              Fraud Detection Pipeline
            </h2>

            <p className="text-gray-400 mb-10">
              End-to-end workflow for identifying
              suspicious banking activities.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-8">
              {[
                "Data Ingestion",
                "Risk Analysis",
                "Decision Engine",
                "Alert Review",
                "Final Outcome",
              ].map((step, index) => (
                <div
                  key={index}
                  className="text-center"
                >
                  <div className="w-20 h-20 mx-auto rounded-full border border-emerald-500/20 bg-[#020817] flex items-center justify-center text-emerald-400 text-2xl font-bold">
                    {index + 1}
                  </div>

                  <h3 className="mt-5 text-lg font-semibold">
                    {step}
                  </h3>

                  <p className="text-sm text-gray-400 mt-3 leading-6">
                    Real-time fraud monitoring and
                    intelligent analysis pipeline.
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Documentation;