import { useState, useEffect } from 'react';

interface Step {
  type: 'think' | 'act' | 'observe' | 'reflect' | 'output';
  title: string;
  detail: string;
}

interface QueryPreset {
  id: string;
  name: string;
  prompt: string;
  steps: Step[];
}

const PRESETS: QueryPreset[] = [
  {
    id: 'anomaly',
    name: 'Fraud & Anomaly Check',
    prompt: 'Flag anomaly and potential fraud for current month invoices',
    steps: [
      { type: 'think', title: '1. THINK', detail: 'Master orchestrator received request. Scanning active invoice registry for current billing cycle...' },
      { type: 'act', title: '2. ACT', detail: 'db_query_tool.run({ status: "all", limit: 100, month: "current" })' },
      { type: 'observe', title: '3. OBSERVE', detail: 'Found 47 invoices. Total volume $189,450. Loading anomalies detector sub-agent graph...' },
      { type: 'reflect', title: '4. REFLECT', detail: 'Identified potential duplicate billing risk and extreme statistical outlier. Compiling final insights report...' },
      { type: 'output', title: 'FINAL ANSWER', detail: 'Anomaly Report: 2 duplicate risks flagged (Acme Corp). 1 high outlier identified ($89,000). PDF report successfully generated.' }
    ]
  },
  {
    id: 'forecast',
    name: 'Revenue Forecasting',
    prompt: 'Compute revenue trend and forecast next month',
    steps: [
      { type: 'think', title: '1. THINK', detail: 'Master orchestrator received request. Loading historic ledger and forecasting models...' },
      { type: 'act', title: '2. ACT', detail: 'analytics_tools.get_revenue_trends({ range_months: 6 })' },
      { type: 'observe', title: '3. OBSERVE', detail: 'Ledger retrieved. Monthly average revenue: $42,500. Steady growth rate of +4.2% month-over-month.' },
      { type: 'reflect', title: '4. REFLECT', detail: 'Compiled trend matrices and projection tables. Generating narrative recommendations for cash-flow buffer...' },
      { type: 'output', title: 'FINAL ANSWER', detail: 'Insights Summary: Next month projected revenue is $48,200. Growth continues upward trend. Cash-flow health remains excellent.' }
    ]
  },
  {
    id: 'reminder',
    name: 'Automated Reminders',
    prompt: 'List top clients and run payment reminders',
    steps: [
      { type: 'think', title: '1. THINK', detail: 'Master orchestrator received request. Querying ledger database to pull client records and overdue balances...' },
      { type: 'act', title: '2. ACT', detail: 'action_tools.send_payment_reminder({ client: "Globex Corp", amount: 8500 })' },
      { type: 'observe', title: '3. OBSERVE', detail: 'Reminders successfully compiled and sent via SendGrid. Email delivery confirmation received.' },
      { type: 'reflect', title: '4. REFLECT', detail: 'Reminder dispatched and logged. Invoices database updated. Setting webhook to track payment notification...' },
      { type: 'output', title: 'FINAL ANSWER', detail: 'Action Completed: Payment reminder successfully delivered to Globex Corp ($8,500). Database status set to "reminded".' }
    ]
  }
];

export default function LandingPage() {
  const [activePreset, setActivePreset] = useState<QueryPreset>(PRESETS[0]);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [latency, setLatency] = useState<number>(24);

  useEffect(() => {
    if (!isPlaying) return;

    const timer = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < activePreset.steps.length - 1) {
          return prev + 1;
        } else {
          return 0;
        }
      });
    }, 3000);

    return () => clearInterval(timer);
  }, [activePreset, isPlaying]);

  // Simulate subtle system metrics updates
  useEffect(() => {
    const metricTimer = setInterval(() => {
      setLatency(Math.floor(20 + Math.random() * 8));
    }, 4000);
    return () => clearInterval(metricTimer);
  }, []);

  const selectPreset = (preset: QueryPreset) => {
    setActivePreset(preset);
    setCurrentStep(0);
    setIsPlaying(true);
  };

  const handleNodeClick = (stepIndex: number) => {
    setIsPlaying(false);
    setCurrentStep(stepIndex);
  };

  const getActiveType = (): string => {
    if (currentStep < activePreset.steps.length) {
      return activePreset.steps[currentStep].type;
    }
    return '';
  };

  const activeType = getActiveType();

  // Calculate dynamic dashoffset for the flowing connection line in the SVG
  // 12 o'clock (Think) -> 3 o'clock (Act) -> 6 o'clock (Observe) -> 9 o'clock (Reflect)
  const getDashOffset = () => {
    switch (activeType) {
      case 'think': return 0;
      case 'act': return -62.8; // 1/4 of circumference
      case 'observe': return -125.6; // 1/2 of circumference
      case 'reflect':
      case 'output':
        return -188.4; // 3/4 of circumference
      default: return 0;
    }
  };

  return (
    <div className="relative min-h-screen bg-slate-50 overflow-x-hidden text-slate-900 font-sans antialiased selection:bg-blue-100 selection:text-blue-800">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 bg-grid-pattern pointer-events-none opacity-100 z-0"></div>

      {/* Header Nav */}
      <header className="sticky top-0 bg-white/80 backdrop-blur-md border-b border-slate-100 z-50">
        <div className="max-w-6xl mx-auto px-6 h-18 flex items-center justify-between">
          <a href="#" className="flex items-center gap-2 font-bold text-lg text-slate-900 group">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-blue-600 group-hover:rotate-45 transition-transform duration-300">
              <path d="M12 2v20M2 12h20M5.636 5.636l12.728 12.728M5.636 18.364L18.364 5.636" strokeLinecap="round"/>
            </svg>
            <span>Invoxio</span>
            <span className="text-[10px] bg-slate-100 text-slate-500 font-mono px-2 py-0.5 rounded-md font-normal ml-1">v1.2.0-beta</span>
          </a>
          <div className="flex items-center gap-6">
            <button className="bg-blue-600 hover:bg-blue-700 active:scale-95 text-white font-semibold text-xs px-5 py-2.5 rounded-full transition-all shadow-sm shadow-blue-500/10 cursor-pointer uppercase tracking-wider">
              Book Demo
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-4xl mx-auto px-6 pt-20 pb-16 text-center relative z-10">
        <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-100/60 px-4 py-1.5 rounded-full text-[10px] font-bold text-blue-600 tracking-wider uppercase mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
          🤖 ALIGNING WORKFLOWS
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.15] mb-6">
          Autonomous AI for the<br />Modern Finance Team.
        </h1>
        <p className="text-base md:text-lg text-slate-500 max-w-2xl mx-auto leading-relaxed mb-8">
          Invoxio automates invoice processing, detects anomalies in real-time, and generates deep financial insights.
        </p>
        <div className="flex flex-col sm:flex-row justify-center items-center gap-4 mb-16">
          <button className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm px-8 py-3.5 rounded-xl shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 transition-all cursor-pointer">
            Start Free Trial
          </button>
          <button 
            onClick={() => document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })}
            className="w-full sm:w-auto bg-white border border-slate-200 hover:border-slate-300 text-slate-700 font-bold text-sm px-6 py-3.5 rounded-xl shadow-sm transition-all inline-flex items-center justify-center gap-2 cursor-pointer"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-slate-400">
              <path d="M23 7H1a1 1 0 0 0-1 1v13a1 1 0 0 0 1 1h22a1 1 0 0 0 1-1V8a1 1 0 0 0-1-1zM10 12.5l5 3-5 3v-6z" />
            </svg>
            Watch the Agent
          </button>
        </div>

        {/* Circular Agent Orbit Loop Widget */}
        <div className="bg-white border border-slate-100 rounded-3xl p-10 max-w-md mx-auto shadow-sm flex items-center justify-center relative min-h-[300px]">
          {/* Dash connection line SVG */}
          <svg className="absolute w-52 h-52 pointer-events-none -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" stroke="#f1f5f9" strokeWidth="1.5" fill="none" strokeDasharray="3 3" />
            <circle 
              cx="50" 
              cy="50" 
              r="40" 
              stroke="#2563eb" 
              strokeWidth="2" 
              fill="none" 
              strokeDasharray="62.8 188.4" 
              strokeDashoffset={getDashOffset()} 
              strokeLinecap="round"
              className="transition-all duration-500 ease-in-out" 
            />
          </svg>

          {/* Core loop icons positioned absolutely */}
          {/* 12 o'clock - THINK */}
          <div 
            onClick={() => handleNodeClick(0)}
            className={`absolute top-8 flex flex-col items-center gap-1.5 transition-all duration-300 cursor-pointer ${activeType === 'think' ? 'scale-110' : 'opacity-70 hover:opacity-90'}`}
          >
            <div className={`w-11 h-11 rounded-full flex items-center justify-center bg-white shadow-md border ${activeType === 'think' ? 'border-blue-500 text-blue-600 ring-4 ring-blue-50' : 'border-slate-100 text-slate-500'}`}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 select-none">Think</span>
          </div>

          {/* 3 o'clock - ACT */}
          <div 
            onClick={() => handleNodeClick(1)}
            className={`absolute right-8 flex flex-col items-center gap-1.5 transition-all duration-300 cursor-pointer ${activeType === 'act' ? 'scale-110' : 'opacity-70 hover:opacity-90'}`}
          >
            <div className={`w-11 h-11 rounded-full flex items-center justify-center bg-white shadow-md border ${activeType === 'act' ? 'border-blue-500 text-blue-600 ring-4 ring-blue-50' : 'border-slate-100 text-slate-500'}`}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 select-none">Act</span>
          </div>

          {/* 6 o'clock - OBSERVE */}
          <div 
            onClick={() => handleNodeClick(2)}
            className={`absolute bottom-8 flex flex-col items-center gap-1.5 transition-all duration-300 cursor-pointer ${activeType === 'observe' ? 'scale-110' : 'opacity-70 hover:opacity-90'}`}
          >
            <div className={`w-11 h-11 rounded-full flex items-center justify-center bg-white shadow-md border ${activeType === 'observe' ? 'border-blue-500 text-blue-600 ring-4 ring-blue-50' : 'border-slate-100 text-slate-500'}`}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 select-none">Observe</span>
          </div>

          {/* 9 o'clock - REFLECT */}
          <div 
            onClick={() => handleNodeClick(3)}
            className={`absolute left-8 flex flex-col items-center gap-1.5 transition-all duration-300 cursor-pointer ${activeType === 'reflect' || activeType === 'output' ? 'scale-110' : 'opacity-70 hover:opacity-90'}`}
          >
            <div className={`w-11 h-11 rounded-full flex items-center justify-center bg-white shadow-md border ${activeType === 'reflect' || activeType === 'output' ? 'border-blue-500 text-blue-600 ring-4 ring-blue-50' : 'border-slate-100 text-slate-500'}`}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
              </svg>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 select-none">Reflect</span>
          </div>

          {/* Center visual log details */}
          <div className="z-10 text-center select-none bg-slate-50/80 backdrop-blur-sm p-3 rounded-full border border-slate-100/50 shadow-inner">
            <span className="text-[9px] font-bold tracking-widest text-blue-600 uppercase block mb-0.5">State Log</span>
            <span className="text-xs font-bold text-slate-800 tracking-tight capitalize block">{activeType || 'idle'}</span>
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="border-y border-slate-100 bg-white py-12 text-center relative z-10">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 mb-8">Trusted by modern, forward-thinking teams</div>
          <div className="flex flex-wrap justify-center items-center gap-x-20 gap-y-6 opacity-60">
            <div className="flex items-center gap-2 font-bold text-slate-600 text-sm tracking-widest uppercase">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-slate-400">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              </svg>
              MODERNITY
            </div>
            <div className="flex items-center gap-2 font-bold text-slate-600 text-sm tracking-widest uppercase">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-slate-400">
                <path d="M19 21V5a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v16"/>
              </svg>
              PINTEC
            </div>
          </div>
        </div>
      </section>

      {/* Intelligent Core Capabilities */}
      <section className="max-w-4xl mx-auto px-6 py-24 relative z-10">
        <div className="text-center mb-16">
          <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight mb-4">Intelligent Core Capabilities</h2>
        </div>

        <div className="flex flex-col gap-6">
          {/* Card 1 */}
          <div className="bg-white border border-slate-100 rounded-2xl p-8 shadow-sm flex flex-col md:flex-row gap-6 items-start hover:border-blue-200 hover:-translate-y-1 hover:shadow-md hover:shadow-blue-500/5 transition-all duration-300 group relative">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-purple-50 text-purple-600 shrink-0 border border-purple-100/50">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <div className="flex-grow">
              <h3 className="text-base font-bold text-slate-900 mb-1.5">Invoice Extraction</h3>
              <p className="text-sm text-slate-500 leading-relaxed max-w-2xl">
                LLM-powered OCR that understands context, not just text. Parses complex line items with 99.9% accuracy.
              </p>
            </div>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="absolute top-6 right-6 text-slate-300 group-hover:text-blue-500 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all duration-300">
              <path d="M7 17L17 7M17 7H7M17 7V17" />
            </svg>
          </div>

          {/* Card 2 */}
          <div className="bg-white border border-slate-100 rounded-2xl p-8 shadow-sm flex flex-col md:flex-row gap-6 items-start hover:border-blue-200 hover:-translate-y-1 hover:shadow-md hover:shadow-blue-500/5 transition-all duration-300 group relative">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-red-50 text-red-500 shrink-0 border border-red-100/50">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              </svg>
            </div>
            <div className="flex-grow">
              <h3 className="text-base font-bold text-slate-900 mb-1.5">Anomaly Detection</h3>
              <p className="text-sm text-slate-500 leading-relaxed max-w-2xl">
                Instant fraud alerts and duplicate-spend prevention using behavioral pattern matching.
              </p>
            </div>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="absolute top-6 right-6 text-slate-300 group-hover:text-blue-500 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all duration-300">
              <path d="M7 17L17 7M17 7H7M17 7V17" />
            </svg>
          </div>

          {/* Card 3 */}
          <div className="bg-white border border-slate-100 rounded-2xl p-8 shadow-sm flex flex-col md:flex-row gap-6 items-start hover:border-blue-200 hover:-translate-y-1 hover:shadow-md hover:shadow-blue-500/5 transition-all duration-300 group relative">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-blue-50 text-blue-600 shrink-0 border border-blue-100/50">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="20" x2="18" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
            </div>
            <div className="flex-grow">
              <h3 className="text-base font-bold text-slate-900 mb-1.5">Predictive Forecasting</h3>
              <p className="text-sm text-slate-500 leading-relaxed max-w-2xl">
                Deep revenue and cash flow projections based on historical data and market trends.
              </p>
            </div>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="absolute top-6 right-6 text-slate-300 group-hover:text-blue-500 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all duration-300">
              <path d="M7 17L17 7M17 7H7M17 7V17" />
            </svg>
          </div>

          {/* Card 4 */}
          <div className="bg-white border border-slate-100 rounded-2xl p-8 shadow-sm flex flex-col md:flex-row gap-6 items-start hover:border-blue-200 hover:-translate-y-1 hover:shadow-md hover:shadow-blue-500/5 transition-all duration-300 group relative">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-indigo-50 text-indigo-600 shrink-0 border border-indigo-100/50">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <div className="flex-grow">
              <h3 className="text-base font-bold text-slate-900 mb-1.5">Master Orchestrator</h3>
              <p className="text-sm text-slate-500 leading-relaxed max-w-2xl mb-4">
                Ask complex questions in plain English: "Show me all SaaS subscriptions over $500 that haven't been used in 30 days."
              </p>
              <div className="bg-slate-50 border border-slate-100 rounded-xl p-4 font-mono text-[11px] text-slate-500 select-none relative overflow-hidden">
                <span className="text-blue-600">$ run</span> Querying system logs, databases...<span className="animate-pulse ml-0.5">_</span><br />
                <span className="text-slate-400">invoices...</span> found 12 anomalies.
              </div>
            </div>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="absolute top-6 right-6 text-slate-300 group-hover:text-blue-500 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all duration-300">
              <path d="M7 17L17 7M17 7H7M17 7V17" />
            </svg>
          </div>
        </div>
      </section>

      {/* Simulator / ReAct Loop Section */}
      <section id="demo" className="bg-slate-100/40 border-y border-slate-200/50 py-24 relative z-10">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight mb-4">The ReAct Loop</h2>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-5 gap-10 items-stretch">
            {/* Steps & Controls */}
            <div className="lg:col-span-2 flex flex-col justify-center gap-6">
              <div className="flex flex-col gap-6">
                <div 
                  onClick={() => handleNodeClick(0)}
                  className={`flex gap-4 cursor-pointer p-2 rounded-xl transition-all duration-300 ${activeType === 'think' ? 'bg-white shadow-sm ring-1 ring-slate-100' : 'hover:bg-slate-50/50'}`}
                >
                  <div className={`w-8 h-8 rounded-full border flex items-center justify-center font-bold text-xs shrink-0 transition-all ${activeType === 'think' ? 'bg-blue-600 border-blue-600 text-white shadow-md' : 'bg-white border-slate-200 text-slate-500'}`}>
                    1
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-800 mb-0.5">Think</h4>
                    <p className="text-xs text-slate-500 leading-relaxed">Agent analyzes the objective and creates a step-by-step reasoning chain.</p>
                  </div>
                </div>

                <div 
                  onClick={() => handleNodeClick(1)}
                  className={`flex gap-4 cursor-pointer p-2 rounded-xl transition-all duration-300 ${activeType === 'act' ? 'bg-white shadow-sm ring-1 ring-slate-100' : 'hover:bg-slate-50/50'}`}
                >
                  <div className={`w-8 h-8 rounded-full border flex items-center justify-center font-bold text-xs shrink-0 transition-all ${activeType === 'act' ? 'bg-blue-600 border-blue-600 text-white shadow-md' : 'bg-white border-slate-200 text-slate-500'}`}>
                    2
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-800 mb-0.5">Act</h4>
                    <p className="text-xs text-slate-500 leading-relaxed">Executes actions via API: fetching invoices, verifying signatures, or moving funds.</p>
                  </div>
                </div>

                <div 
                  onClick={() => handleNodeClick(2)}
                  className={`flex gap-4 cursor-pointer p-2 rounded-xl transition-all duration-300 ${activeType === 'observe' ? 'bg-white shadow-sm ring-1 ring-slate-100' : 'hover:bg-slate-50/50'}`}
                >
                  <div className={`w-8 h-8 rounded-full border flex items-center justify-center font-bold text-xs shrink-0 transition-all ${activeType === 'observe' ? 'bg-blue-600 border-blue-600 text-white shadow-md' : 'bg-white border-slate-200 text-slate-500'}`}>
                    3
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-800 mb-0.5">Observe</h4>
                    <p className="text-xs text-slate-500 leading-relaxed">Receives environment feedback and validates the outcome of the action.</p>
                  </div>
                </div>

                <div 
                  onClick={() => handleNodeClick(3)}
                  className={`flex gap-4 cursor-pointer p-2 rounded-xl transition-all duration-300 ${activeType === 'reflect' || activeType === 'output' ? 'bg-white shadow-sm ring-1 ring-slate-100' : 'hover:bg-slate-50/50'}`}
                >
                  <div className={`w-8 h-8 rounded-full border flex items-center justify-center font-bold text-xs shrink-0 transition-all ${activeType === 'reflect' || activeType === 'output' ? 'bg-blue-600 border-blue-600 text-white shadow-md' : 'bg-white border-slate-200 text-slate-500'}`}>
                    4
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-800 mb-0.5">Reflect</h4>
                    <p className="text-xs text-slate-500 leading-relaxed">Synthesizes findings and updates the internal state for the next iteration.</p>
                  </div>
                </div>
              </div>

              {/* Preset Selector buttons */}
              <div className="mt-8 border-t border-slate-200/60 pt-6">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-3">Choose a scenario:</span>
                <div className="flex flex-wrap gap-2">
                  {PRESETS.map((preset) => (
                    <button
                      key={preset.id}
                      onClick={() => selectPreset(preset)}
                      className={`text-xs font-bold px-4 py-2 rounded-lg border transition-all cursor-pointer ${
                        activePreset.id === preset.id
                          ? 'border-blue-600 bg-blue-50 text-blue-600'
                          : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
                      }`}
                    >
                      {preset.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Terminal Panel */}
            <div className="lg:col-span-3 bg-[#0d1117] border border-slate-900 rounded-2xl flex flex-col h-[400px] shadow-xl overflow-hidden relative">
              <div className="h-10 bg-[#161b22] border-b border-slate-900/50 flex items-center justify-between px-4 select-none">
                <div className="flex gap-1.5">
                  <div 
                    onClick={() => setIsPlaying(!isPlaying)}
                    className={`w-2.5 h-2.5 rounded-full cursor-pointer hover:scale-110 transition-transform ${isPlaying ? 'bg-green-500' : 'bg-yellow-500'}`}
                    title={isPlaying ? "Pause Simulation" : "Play Simulation"}
                  ></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-slate-600"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-slate-600"></div>
                </div>
                <div className="text-[10px] font-mono text-slate-500 flex items-center gap-1.5">
                  <span>invoxio-master-orchestrator</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                </div>
                <div className="text-[9px] font-mono text-slate-500">RTT: {latency}ms</div>
              </div>

              <div className="p-6 flex-grow overflow-y-auto font-mono text-[11px] leading-relaxed text-left">
                <div className="text-blue-400 mb-6 font-semibold select-none flex items-center gap-1">
                  <span>$ invoxio-agent --query "{activePreset.prompt}"</span>
                  {isPlaying && <span className="animate-pulse block w-1.5 h-3.5 bg-blue-400"></span>}
                </div>

                <div className="flex flex-col gap-4">
                  {activePreset.steps.slice(0, currentStep + 1).map((step, index) => (
                    <div
                      key={index}
                      className={`pl-3 border-l-2 transition-all duration-300 ${
                        step.type === 'output' ? 'border-green-500' : 'border-slate-700'
                      }`}
                    >
                      <div
                        className={`font-bold text-[9px] tracking-wide mb-1 uppercase ${
                          step.type === 'think' ? 'text-yellow-400' :
                          step.type === 'act' ? 'text-blue-400' :
                          step.type === 'observe' ? 'text-green-400' :
                          step.type === 'reflect' ? 'text-purple-400' :
                          'text-green-400'
                        }`}
                      >
                        {step.title}
                      </div>
                      <div className="text-slate-300 text-xs">{step.detail}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Box */}
      <section className="max-w-4xl mx-auto px-6 py-20 relative z-10">
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-3xl p-12 text-center text-white shadow-xl shadow-blue-500/10 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-3xl pointer-events-none"></div>
          <h2 className="text-2xl md:text-3xl font-extrabold mb-4 tracking-tight">Ready to put your financial operations on autopilot?</h2>
          <p className="text-blue-100 max-w-xl mx-auto mb-8 text-sm md:text-base leading-relaxed">
            Join 200+ enterprises optimizing their back-office with Invoxio.ai.
          </p>
          <button className="bg-white hover:bg-slate-50 text-blue-600 font-bold px-8 py-3.5 rounded-xl shadow-md transition-all hover:scale-[1.02] cursor-pointer">
            Get Started Free
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-100 bg-white py-16 relative z-10">
        <div className="max-w-4xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10 mb-12">
            <div>
              <div className="flex items-center gap-2 font-bold text-slate-900 mb-4 text-base">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-blue-600">
                  <path d="M12 2v20M2 12h20M5.636 5.636l12.728 12.728M5.636 18.364L18.364 5.636" strokeLinecap="round"/>
                </svg>
                <span>Invoxio</span>
              </div>
              <p className="text-slate-400 text-xs leading-relaxed max-w-xs">
                Autonomous Finance Orchestration for the global enterprise.
              </p>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-4">Platform</span>
              <ul className="flex flex-col gap-2.5 text-xs font-semibold text-slate-500">
                <li><a href="#" className="hover:text-blue-600 transition-colors">Pricing</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Integrations</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Network</a></li>
              </ul>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-4">Company</span>
              <ul className="flex flex-col gap-2.5 text-xs font-semibold text-slate-500">
                <li><a href="#" className="hover:text-blue-600 transition-colors">About</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Security</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Legal</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-100 pt-8 flex flex-col sm:flex-row justify-between items-center gap-4 text-[11px] text-slate-400">
            <span>© {new Date().getFullYear()} Invoxio AI. Autonomous Finance Orchestration.</span>
            <div className="flex gap-4">
              <a href="#" className="hover:text-slate-600 transition-colors">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z" />
                </svg>
              </a>
              <a href="#" className="hover:text-slate-600 transition-colors">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
                  <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
                  <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
                </svg>
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
