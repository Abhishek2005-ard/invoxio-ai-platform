import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../store/AuthContext';

export default function LoginPage() {
  const { login, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, loading, navigate]);
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Invalid email or password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row relative overflow-hidden font-sans">
      {/* Ambient Grid overlay */}
      <div className="absolute inset-0 bg-grid-pattern pointer-events-none opacity-40 z-0"></div>

      {/* Left Panel: Brand info (Visible on MD+) */}
      <div className="hidden md:flex md:w-1/2 bg-slate-950 text-white p-12 flex-col justify-between relative z-10 overflow-hidden border-r border-slate-900">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,#1e3a8a,transparent_60%)] opacity-35 z-0 animate-pulse-slow"></div>
        <div className="absolute -bottom-20 -left-20 w-80 h-80 bg-blue-600/10 rounded-full blur-[100px] pointer-events-none"></div>

        <div className="relative z-10">
          <Link to="/" className="flex items-center gap-2.5 font-bold text-lg text-white group">
            <svg 
              width="24" 
              height="24" 
              viewBox="0 0 24 24" 
              fill="none" 
              xmlns="http://www.w3.org/2000/svg" 
              className="group-hover:scale-105 group-hover:rotate-6 transition-transform duration-300 shrink-0"
            >
              <defs>
                <linearGradient id="logoGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="100%" stopColor="#6366f1" />
                </linearGradient>
              </defs>
              <path d="M12 2L2 7l10 5 10-5-10-5z" fill="url(#logoGrad2)" />
              <path d="M2 17l10 5 10-5" stroke="url(#logoGrad2)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M2 12l10 5 10-5" stroke="url(#logoGrad2)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.5" />
            </svg>
            <span>Invoxio</span>
          </Link>
        </div>

        <div className="relative z-10 max-w-md my-auto">
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-4 leading-tight">
            Autonomous Finance Operations at Your Fingertips.
          </h1>
          <p className="text-slate-400 text-sm md:text-base leading-relaxed mb-8">
            Sign in to access your secure Multi-Agent workspace. Orchestrate invoice extraction, audit ledger streams, and generate real-time predictive projections.
          </p>

          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2.5 text-xs font-semibold text-slate-300 bg-white/5 border border-white/10 px-4 py-2.5 rounded-xl w-fit">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              SOC-2 Type II Certified Workspace
            </div>
            <div className="flex items-center gap-2.5 text-xs font-semibold text-slate-300 bg-white/5 border border-white/10 px-4 py-2.5 rounded-xl w-fit">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="text-blue-400">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              Military-Grade AES-256 Encryption
            </div>
          </div>
        </div>

        <div className="relative z-10 text-xs text-slate-500 font-mono">
          © {new Date().getFullYear()} Invoxio AI, Inc.
        </div>
      </div>

      {/* Right Panel: Form */}
      <div className="flex-1 flex items-center justify-center p-8 md:p-12 relative z-10">
        <div className="w-full max-w-sm bg-white border border-slate-200/60 rounded-3xl p-8 shadow-xl shadow-slate-200/50 flex flex-col gap-6 animate-fade-in-up">
          <div className="text-center md:text-left">
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight mb-1">Welcome back</h2>
            <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Access your orchestrator console</p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-100 text-red-600 px-4 py-3 rounded-xl text-xs font-medium flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-red-500 rounded-full shrink-0"></span>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wide">Work Email</label>
              <input 
                type="email" 
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com" 
                className="bg-slate-50 border border-slate-200/80 text-slate-800 text-sm px-4 py-3 rounded-xl focus:outline-none focus:border-blue-500 focus:bg-white transition-all font-medium"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between items-center">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wide">Password</label>
                <a href="#" className="text-[11px] font-bold text-blue-600 hover:text-blue-700 transition-colors">Forgot?</a>
              </div>
              <input 
                type="password" 
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••" 
                className="bg-slate-50 border border-slate-200/80 text-slate-800 text-sm px-4 py-3 rounded-xl focus:outline-none focus:border-blue-500 focus:bg-white transition-all font-medium"
              />
            </div>

            <button 
              type="submit" 
              disabled={isLoading}
              className="bg-slate-900 hover:bg-slate-800 active:scale-95 text-white font-bold text-sm py-3.5 rounded-xl transition-all shadow-md shadow-slate-950/10 cursor-pointer flex items-center justify-center gap-2 mt-2"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Signing In...</span>
                </>
              ) : (
                <span>Sign In to Console</span>
              )}
            </button>
          </form>

          <div className="text-center text-xs text-slate-500 font-medium">
            Don't have enterprise access?{' '}
            <Link to="/register" className="font-bold text-blue-600 hover:text-blue-700 transition-colors">
              Request credentials
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
