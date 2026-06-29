import { useAuth } from '../../store/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans relative">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 bg-grid-pattern pointer-events-none opacity-40 z-0"></div>

      {/* Top Navbar */}
      <header className="sticky top-0 bg-white/80 backdrop-blur-md border-b border-slate-100 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo Group */}
          <div className="flex items-center gap-2.5 font-bold text-slate-900 text-base">
            <svg 
              width="20" 
              height="20" 
              viewBox="0 0 24 24" 
              fill="none" 
              xmlns="http://www.w3.org/2000/svg"
              className="shrink-0"
            >
              <defs>
                <linearGradient id="logoGradDash" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="100%" stopColor="#6366f1" />
                </linearGradient>
              </defs>
              <path d="M12 2L2 7l10 5 10-5-10-5z" fill="url(#logoGradDash)" />
              <path d="M2 17l10 5 10-5" stroke="url(#logoGradDash)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>Invoxio Console</span>
            <span className="text-[9px] bg-slate-100 text-slate-500 font-mono px-1.5 py-0.5 rounded font-normal ml-1">v1.2.0-beta</span>
          </div>

          {/* User Profile + Logout */}
          <div className="flex items-center gap-4">
            <div className="flex flex-col text-right hidden sm:flex">
              <span className="text-xs font-bold text-slate-800">{user?.name}</span>
              <span className="text-[10px] text-slate-400 font-medium">{user?.email}</span>
            </div>
            
            <div className="w-8 h-8 rounded-full bg-blue-500/10 border border-blue-200 flex items-center justify-center text-xs font-bold text-blue-600 select-none">
              {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
            </div>

            <button 
              onClick={() => navigate('/')}
              className="text-xs font-bold text-slate-500 hover:text-slate-850 active:scale-95 transition-all cursor-pointer border border-slate-200 hover:border-slate-300 px-3 py-1.5 rounded-lg bg-white flex items-center gap-1.5"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="text-slate-400">
                <line x1="19" y1="12" x2="5" y2="12"></line>
                <polyline points="12 19 5 12 12 5"></polyline>
              </svg>
              <span>Back</span>
            </button>

            <button 
              onClick={handleLogout}
              className="text-xs font-bold text-slate-500 hover:text-red-600 transition-colors cursor-pointer border border-slate-200 hover:border-red-200 px-3 py-1.5 rounded-lg bg-white"
            >
              Log Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-10 relative z-10 flex flex-col gap-8">
        
        {/* Welcome Banner */}
        <div className="bg-white border border-slate-200/60 rounded-3xl p-8 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-48 h-48 bg-blue-500/5 rounded-full blur-3xl pointer-events-none"></div>
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight mb-1">
              Welcome back, {user?.name || 'Operator'}
            </h1>
            <p className="text-sm text-slate-500 max-w-xl leading-relaxed">
              Your autonomous multi-agent pipelines are running. The Master Orchestrator (ReAct Loop) is currently listening for triggers.
            </p>
          </div>
          <div className="flex items-center gap-2 bg-slate-50 border border-slate-200/50 px-3.5 py-2 rounded-xl shrink-0">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-xs font-bold text-slate-600 tracking-wide uppercase">All Agents Online</span>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="bg-white border border-slate-200/50 rounded-2xl p-6 shadow-sm flex flex-col gap-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Processed Invoices</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-extrabold text-slate-900">1,248</span>
              <span className="text-xs font-bold text-emerald-600">+14.2%</span>
            </div>
            <span className="text-[10px] text-slate-500 mt-2 font-medium">99.9% accuracy rate across uploads</span>
          </div>

          <div className="bg-white border border-slate-200/50 rounded-2xl p-6 shadow-sm flex flex-col gap-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Anomalies Audited</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-extrabold text-slate-900">47</span>
              <span className="text-xs font-bold text-slate-400">0 critical</span>
            </div>
            <span className="text-[10px] text-slate-500 mt-2 font-medium">3 potential duplicates auto-resolved</span>
          </div>

          <div className="bg-white border border-slate-200/50 rounded-2xl p-6 shadow-sm flex flex-col gap-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Projected Runway</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-extrabold text-slate-900">18.4 Months</span>
              <span className="text-xs font-bold text-emerald-600">+1.2m</span>
            </div>
            <span className="text-[10px] text-slate-500 mt-2 font-medium">Updated based on current billing cycle</span>
          </div>
        </div>

        {/* Core Capabilities Workspace */}
        <div className="flex flex-col gap-4">
          <h2 className="text-lg font-bold text-slate-800 tracking-tight">Orchestrated AI Pipelines</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Card 1 */}
            <div className="bg-white border border-slate-200/60 hover:border-blue-200 rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between gap-6 group">
              <div>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-purple-50 text-purple-600 border border-purple-100/50 mb-4">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                </div>
                <h3 className="text-base font-bold text-slate-900 mb-1.5 group-hover:text-blue-600 transition-colors">Invoice Extraction</h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Run context-aware LLM OCR instances to ingest purchase records, parse complex items, and update general ledger schemas.
                </p>
              </div>
              <button className="w-full bg-slate-50 border border-slate-200 hover:bg-slate-900 hover:text-white hover:border-slate-900 text-slate-800 text-xs font-bold py-2.5 rounded-xl transition-all cursor-pointer">
                Launch Extractor Console
              </button>
            </div>

            {/* Card 2 */}
            <div className="bg-white border border-slate-200/60 hover:border-blue-200 rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between gap-6 group">
              <div>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-red-50 text-red-500 border border-red-100/50 mb-4">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                  </svg>
                </div>
                <h3 className="text-base font-bold text-slate-900 mb-1.5 group-hover:text-blue-600 transition-colors">Anomaly Auditor</h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Trigger automated spend checks across active bank streams to locate duplicate ledger entries or identify unauthorized transactions.
                </p>
              </div>
              <button className="w-full bg-slate-50 border border-slate-200 hover:bg-slate-900 hover:text-white hover:border-slate-900 text-slate-800 text-xs font-bold py-2.5 rounded-xl transition-all cursor-pointer">
                Scan Active Streams
              </button>
            </div>

            {/* Card 3 */}
            <div className="bg-white border border-slate-200/60 hover:border-blue-200 rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between gap-6 group">
              <div>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-blue-50 text-blue-600 border border-blue-100/50 mb-4">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="18" y1="20" x2="18" y2="10" />
                    <line x1="12" y1="20" x2="12" y2="4" />
                    <line x1="6" y1="20" x2="6" y2="14" />
                  </svg>
                </div>
                <h3 className="text-base font-bold text-slate-900 mb-1.5 group-hover:text-blue-600 transition-colors">Predictive Ledger</h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Generate forecasting simulations based on macro variables, operational parameters, and previous seasonal performance metrics.
                </p>
              </div>
              <button className="w-full bg-slate-50 border border-slate-200 hover:bg-slate-900 hover:text-white hover:border-slate-900 text-slate-800 text-xs font-bold py-2.5 rounded-xl transition-all cursor-pointer">
                Compute Forecasts
              </button>
            </div>

            {/* Card 4 */}
            <div className="bg-white border border-slate-200/60 hover:border-blue-200 rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between gap-6 group">
              <div>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-indigo-50 text-indigo-600 border border-indigo-100/50 mb-4">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  </svg>
                </div>
                <h3 className="text-base font-bold text-slate-900 mb-1.5 group-hover:text-blue-600 transition-colors">Master Orchestrator</h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Communicate with the complete ReAct loop agent cluster via natural language queries. Plan complex database transformations dynamically.
                </p>
              </div>
              <button className="w-full bg-slate-50 border border-slate-200 hover:bg-slate-900 hover:text-white hover:border-slate-900 text-slate-800 text-xs font-bold py-2.5 rounded-xl transition-all cursor-pointer">
                Open ReAct Interface
              </button>
            </div>

          </div>
        </div>

      </main>
    </div>
  );
}
