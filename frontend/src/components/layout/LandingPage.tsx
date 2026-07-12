import { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../store/AuthContext';

// Watches elements with IntersectionObserver and adds 'revealed' class when they enter the viewport
function useScrollReveal() {
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
            observerRef.current?.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.05, rootMargin: '0px 0px 0px 0px' }
    );

    return () => observerRef.current?.disconnect();
  }, []);

  const reveal = useCallback((el: HTMLElement | null) => {
    if (el && observerRef.current) {
      observerRef.current.observe(el);
    }
  }, []);

  return reveal;
}

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

interface CarouselSlide {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  image: string;
  color: string;
  glowColor: string;
  bgGradient: string;
}

const CAROUSEL_SLIDES: CarouselSlide[] = [
  {
    id: 'extraction',
    title: 'Invoice Extraction',
    subtitle: 'OCR & Parsing',
    description: 'LLM-powered OCR that understands context, schemas, and complex line items with 99.9% accuracy. Extract vendor details, tax computations, and individual line items automatically.',
    image: '/invoice_extraction.png',
    color: 'blue',
    glowColor: 'rgba(59, 130, 246, 0.12)',
    bgGradient: 'from-blue-500 to-indigo-600'
  },
  {
    id: 'anomaly',
    title: 'Anomaly Detection',
    subtitle: 'Risk & Auditing',
    description: 'Instant fraud prevention, duplicate billing protection, and compliance auditing. Scans historical patterns to flag irregular pricing, outlier volumes, or unauthorized vendors.',
    image: '/anomaly_detection.png',
    color: 'red',
    glowColor: 'rgba(239, 68, 68, 0.12)',
    bgGradient: 'from-red-500 to-rose-600'
  },
  {
    id: 'forecasting',
    title: 'Predictive Forecasting',
    subtitle: 'Trends & Cash-Flow',
    description: 'Deep predictive intelligence for revenue, runway, and cash-flow health. Models historical invoicing ledger patterns to project future cash-inflows and optimize resource allocation.',
    image: '/predictive_forecasting.png',
    color: 'green',
    glowColor: 'rgba(16, 185, 129, 0.12)',
    bgGradient: 'from-emerald-500 to-teal-600'
  },
  {
    id: 'orchestrator',
    title: 'Master Orchestrator',
    subtitle: 'Autonomous Agent',
    description: 'A unified agent console that parses plain English queries, coordinates domain sub-agents, runs external tools, and delivers summarized executive reports in seconds.',
    image: '/master_orchestrator.png',
    color: 'purple',
    glowColor: 'rgba(139, 92, 246, 0.12)',
    bgGradient: 'from-purple-500 to-violet-600'
  }
];

const LOGOS = [
  {
    name: 'Modernity',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
      </svg>
    )
  },
  {
    name: 'Pintec',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <path d="M19 21V5a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v16"/>
      </svg>
    )
  },
  {
    name: 'Apex Finance',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <path d="M12 2L2 22h20L12 2z"/>
      </svg>
    )
  },
  {
    name: 'Globex',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <circle cx="12" cy="12" r="10"/>
        <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
      </svg>
    )
  },
  {
    name: 'Acme Corp',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
      </svg>
    )
  },
  {
    name: 'Nexus Tech',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z"/>
        <path d="M12 6v12M6 12h12"/>
      </svg>
    )
  },
  {
    name: 'Vertex',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <path d="M23 6l-9.5 9.5-5-5L1 18"/>
        <polyline points="17 6 23 6 23 12"/>
      </svg>
    )
  },
  {
    name: 'Invenio',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
    )
  }
];

const LogoIcon = () => (
  <svg 
    width="22" 
    height="22" 
    viewBox="0 0 24 24" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg" 
    className="group-hover:scale-105 group-hover:rotate-6 transition-transform duration-300 shrink-0"
  >
    <defs>
      <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#2563eb" />
        <stop offset="100%" stopColor="#4f46e5" />
      </linearGradient>
    </defs>
    <path 
      d="M12 2L2 7l10 5 10-5-10-5z" 
      fill="url(#logoGrad)" 
    />
    <path 
      d="M2 17l10 5 10-5" 
      stroke="url(#logoGrad)" 
      strokeWidth="2.5" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
    />
    <path 
      d="M2 12l10 5 10-5" 
      stroke="url(#logoGrad)" 
      strokeWidth="2.5" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      opacity="0.5"
    />
  </svg>
);

export default function LandingPage() {
  const { isAuthenticated } = useAuth();
  const [activePreset, setActivePreset] = useState<QueryPreset>(PRESETS[0]);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [latency, setLatency] = useState<number>(24);

  // Carousel state
  const [activeSlide, setActiveSlide] = useState<number>(0);
  const [carouselIsPlaying, setCarouselIsPlaying] = useState<boolean>(true);
  const [progress, setProgress] = useState<number>(0);

  // Mobile nav toggle
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Scroll-reveal hook
  const reveal = useScrollReveal();

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

  // Randomly flicker the RTT display to simulate live system activity
  useEffect(() => {
    const metricTimer = setInterval(() => {
      setLatency(Math.floor(20 + Math.random() * 8));
    }, 4000);
    return () => clearInterval(metricTimer);
  }, []);

  // Advance carousel slide automatically every 5 seconds
  useEffect(() => {
    if (!carouselIsPlaying) return;

    const intervalTime = 50;
    const totalDuration = 5000;
    const increment = (intervalTime / totalDuration) * 100;

    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          setActiveSlide((prevSlide) => (prevSlide + 1) % CAROUSEL_SLIDES.length);
          return 0;
        }
        return prev + increment;
      });
    }, intervalTime);

    return () => clearInterval(timer);
  }, [carouselIsPlaying]);

  const handleTabClick = (index: number) => {
    setActiveSlide(index);
    setProgress(0);
  };

  const handleNext = () => {
    setActiveSlide((prev) => (prev + 1) % CAROUSEL_SLIDES.length);
    setProgress(0);
  };

  const handlePrev = () => {
    setActiveSlide((prev) => (prev - 1 + CAROUSEL_SLIDES.length) % CAROUSEL_SLIDES.length);
    setProgress(0);
  };

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


  return (
    <div className="relative min-h-screen bg-slate-50 overflow-x-hidden text-slate-900 font-sans antialiased selection:bg-blue-100 selection:text-blue-800">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 bg-grid-pattern pointer-events-none opacity-100 z-0"></div>

      {/* Top nav — sticky with blur backdrop */}
      <header className="sticky top-0 bg-white/80 backdrop-blur-md border-b border-slate-100 z-50 animate-fade-in-down">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <a href="#" className="flex items-center gap-2.5 font-bold text-lg text-slate-900 group">
            <LogoIcon />
            <span>Invoxio</span>
            <span className="text-[10px] bg-slate-100 text-slate-500 font-mono px-2 py-0.5 rounded-md font-normal ml-1">v1.2.0-beta</span>
          </a>

          {/* Desktop nav links */}
          <nav className="hidden md:flex items-center gap-8">
            <a href="#" className="text-xs font-semibold text-slate-500 hover:text-slate-950 transition-colors uppercase tracking-wider">Platform</a>
            <button
              onClick={() => document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })}
              className="text-xs font-semibold text-slate-500 hover:text-slate-950 transition-colors uppercase tracking-wider cursor-pointer"
            >
              ReAct Engine
            </button>
            <a href="#" className="text-xs font-semibold text-slate-500 hover:text-slate-950 transition-colors uppercase tracking-wider">Security</a>
            <a href="#" className="text-xs font-semibold text-slate-500 hover:text-slate-950 transition-colors uppercase tracking-wider">Enterprise</a>
          </nav>

          {/* CTA buttons + mobile hamburger */}
          <div className="flex items-center gap-3 sm:gap-6">
            {isAuthenticated ? (
              <Link to="/dashboard" className="bg-slate-900 hover:bg-slate-800 active:scale-95 text-white font-semibold text-xs px-4 sm:px-5 py-2.5 rounded-full transition-all shadow-sm cursor-pointer uppercase tracking-wider">
                Dashboard
              </Link>
            ) : (
              <>
                <Link to="/login" className="hidden sm:inline-block text-xs font-semibold text-slate-500 hover:text-slate-950 transition-colors uppercase tracking-wider">Sign In</Link>
                <Link to="/register" className="bg-slate-900 hover:bg-slate-800 active:scale-95 text-white font-semibold text-xs px-4 sm:px-5 py-2.5 rounded-full transition-all shadow-sm cursor-pointer uppercase tracking-wider">
                  Get Started
                </Link>
              </>
            )}
            {/* Hamburger — only shown on mobile */}
            <button
              className="md:hidden p-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                {mobileMenuOpen
                  ? <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </>
                  : <><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></>
                }
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile dropdown menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-slate-100 bg-white px-4 py-4 flex flex-col gap-3">
            <a href="#" className="text-sm font-semibold text-slate-600 hover:text-slate-900 py-2" onClick={() => setMobileMenuOpen(false)}>Platform</a>
            <button
              onClick={() => { document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' }); setMobileMenuOpen(false); }}
              className="text-sm font-semibold text-slate-600 hover:text-slate-900 py-2 text-left cursor-pointer"
            >
              ReAct Engine
            </button>
            <a href="#" className="text-sm font-semibold text-slate-600 hover:text-slate-900 py-2" onClick={() => setMobileMenuOpen(false)}>Security</a>
            <a href="#" className="text-sm font-semibold text-slate-600 hover:text-slate-900 py-2" onClick={() => setMobileMenuOpen(false)}>Enterprise</a>
            {!isAuthenticated && (
              <Link to="/login" className="text-sm font-semibold text-blue-600 py-2" onClick={() => setMobileMenuOpen(false)}>Sign In</Link>
            )}
          </div>
        )}
      </header>

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 pt-16 sm:pt-24 pb-12 sm:pb-16 text-center relative z-10">
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.15] mb-6 animate-fade-in-up delay-100">
          Autonomous Financial Operations<br />Powered by Multi-Agent AI.
        </h1>
        <p className="text-base md:text-lg text-slate-500 max-w-3xl mx-auto leading-relaxed mb-8 animate-fade-in-up delay-200">
          Invoxio orchestrates specialized AI agents to automate document parsing, audit ledger transactions, flag anomalies, and generate predictive BI reports—securely at enterprise scale.
        </p>
        <div className="flex flex-col sm:flex-row justify-center items-center gap-4 mb-12 animate-fade-in-up delay-300">
          {isAuthenticated ? (
            <Link 
              to="/dashboard" 
              className="w-full sm:w-auto bg-slate-900 hover:bg-slate-800 active:scale-[0.98] text-white font-bold text-sm px-8 py-4 rounded-xl shadow-lg shadow-slate-950/10 hover:shadow-slate-950/20 transition-all cursor-pointer text-center"
            >
              Enter Dashboard Console
            </Link>
          ) : (
            <>
              <Link 
                to="/register" 
                className="w-full sm:w-auto bg-slate-900 hover:bg-slate-800 active:scale-[0.98] text-white font-bold text-sm px-8 py-4 rounded-xl shadow-lg shadow-slate-950/10 hover:shadow-slate-950/20 transition-all cursor-pointer text-center"
              >
                Request Enterprise Access
              </Link>
              <button 
                onClick={() => document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })}
                className="w-full sm:w-auto bg-white border border-slate-200 hover:border-slate-300 hover:bg-slate-50 active:scale-[0.98] text-slate-700 font-bold text-sm px-8 py-4 rounded-xl shadow-sm transition-all inline-flex items-center justify-center gap-2 cursor-pointer"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-slate-400">
                  <path d="M23 7H1a1 1 0 0 0-1 1v13a1 1 0 0 0 1 1h22a1 1 0 0 0 1-1V8a1 1 0 0 0-1-1zM10 12.5l5 3-5 3v-6z" />
                </svg>
                Book Technical Demo
              </button>
            </>
          )}
        </div>

        {/* Security & Compliance Trust Badges */}
        <div className="flex flex-wrap justify-center items-center gap-x-8 gap-y-3 mb-16 animate-fade-in-up delay-400 opacity-80">
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 tracking-wider uppercase bg-slate-100/60 px-3 py-1 rounded-full border border-slate-200/50">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            SOC-2 Type II Certified
          </div>
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 tracking-wider uppercase bg-slate-100/60 px-3 py-1 rounded-full border border-slate-200/50">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="text-slate-400">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            AES-256 Encryption
          </div>
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 tracking-wider uppercase bg-slate-100/60 px-3 py-1 rounded-full border border-slate-200/50">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="text-slate-400">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            99.99% Uptime SLA
          </div>
        </div>

        {/* Workflow Showcase Image Carousel */}
        <div 
          onMouseEnter={() => setCarouselIsPlaying(false)}
          onMouseLeave={() => setCarouselIsPlaying(true)}
          className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center mt-12 max-w-5xl mx-auto text-left relative animate-fade-in-up delay-500"
        >
          {/* Ambient Glow Background Effect */}
          <div 
            className="absolute -inset-10 bg-radial blur-[80px] opacity-15 rounded-full transition-all duration-1000 ease-in-out pointer-events-none z-0 animate-glow-pulse"
            style={{
              background: `radial-gradient(circle, ${CAROUSEL_SLIDES[activeSlide].glowColor} 0%, rgba(255,255,255,0) 70%)`
            }}
          />

          {/* Left Side: Interactive Accordion Tabs */}
          <div className="lg:col-span-5 flex flex-col gap-4 z-10 relative">
            {CAROUSEL_SLIDES.map((slide, index) => {
              const isActive = activeSlide === index;
              return (
                <div
                  key={slide.id}
                  onClick={() => handleTabClick(index)}
                  className={`group cursor-pointer p-5 rounded-2xl border transition-all duration-300 relative overflow-hidden ${
                    isActive 
                      ? 'bg-white border-slate-200/80 shadow-md shadow-slate-100/50' 
                      : 'bg-transparent border-transparent hover:bg-slate-100/50'
                  }`}
                >
                  {/* Progress Indicator Bar */}
                  {isActive && (
                    <div className="absolute bottom-0 left-0 h-1 bg-slate-100 w-full">
                      <div 
                        className={`h-full bg-gradient-to-r ${slide.bgGradient} transition-all duration-75`}
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  )}
                  
                  <div className="flex gap-4 items-start">
                    {/* Index Badge */}
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 transition-all ${
                      isActive 
                        ? `bg-gradient-to-br ${slide.bgGradient} text-white shadow-sm scale-105` 
                        : 'bg-slate-100 text-slate-400 group-hover:bg-slate-200 group-hover:text-slate-600'
                    }`}>
                      0{index + 1}
                    </div>
                    
                    <div className="flex-grow">
                      <h3 className={`font-bold text-sm transition-colors ${
                        isActive ? 'text-slate-900' : 'text-slate-500 group-hover:text-slate-800'
                      }`}>
                        {slide.title}
                      </h3>
                      <p className={`text-[10px] font-bold tracking-wider uppercase mt-0.5 transition-colors ${
                        isActive ? 'text-blue-600' : 'text-slate-400'
                      }`}>
                        {slide.subtitle}
                      </p>
                      
                      {/* Description Panel */}
                      <div className={`transition-all duration-300 overflow-hidden ${
                        isActive ? 'max-h-40 opacity-100 mt-2.5' : 'max-h-0 opacity-0 pointer-events-none'
                      }`}>
                        <p className="text-xs text-slate-500 leading-relaxed">
                          {slide.description}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right side — mock browser showing workflow screenshots */}
          <div className="lg:col-span-7 relative z-10">
            {/* Prev arrow — hidden on mobile since the browser bar handles it */}
            <button
              onClick={handlePrev}
              className="absolute left-[-20px] top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white border border-slate-100 shadow-lg flex items-center justify-center text-slate-400 hover:text-slate-700 hover:scale-105 active:scale-95 transition-all z-20 cursor-pointer hidden md:flex"
              title="Previous workflow"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M15 18l-6-6 6-6" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>

            {/* Next arrow */}
            <button 
              onClick={handleNext}
              className="absolute right-[-20px] top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white border border-slate-100 shadow-lg flex items-center justify-center text-slate-400 hover:text-slate-700 hover:scale-105 active:scale-95 transition-all z-20 cursor-pointer hidden md:flex"
              title="Next workflow"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M9 18l6-6-6-6" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>

            {/* Browser chrome frame */}
            <div className="relative rounded-2xl border border-slate-200/80 bg-white p-2.5 shadow-2xl transition-all duration-500 w-full overflow-hidden aspect-[16/10]">
              {/* Fake address bar / traffic lights */}
              <div className="flex items-center justify-between px-3 pb-2.5 border-b border-slate-100 select-none">
                <div className="flex gap-1.5 items-center">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-400"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-yellow-400"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-green-400"></div>
                </div>
                <div className="bg-slate-50 text-slate-400 px-4 py-1 rounded-md text-[9px] font-mono border border-slate-100/60 w-3/5 text-center truncate">
                  invoxio.ai/workflows/{CAROUSEL_SLIDES[activeSlide].id}
                </div>
                <div className="flex gap-2 text-slate-300">
                  <button 
                    onClick={handlePrev}
                    className="hover:text-slate-600 transition-colors cursor-pointer"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <path d="M15 18l-6-6 6-6" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </button>
                  <button 
                    onClick={handleNext}
                    className="hover:text-slate-600 transition-colors cursor-pointer"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <path d="M9 18l6-6-6-6" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </button>
                </div>
              </div>
              {/* Slide images with crossfade transition */}
              <div className="relative w-full h-full bg-slate-950 rounded-lg overflow-hidden mt-2.5">
                {CAROUSEL_SLIDES.map((slide, index) => {
                  const isActive = activeSlide === index;
                  return (
                    <img
                      key={slide.id}
                      src={slide.image}
                      alt={slide.title}
                      className={`absolute inset-0 w-full h-full object-cover transition-all duration-700 ease-in-out ${
                        isActive 
                          ? 'opacity-100 scale-100 pointer-events-auto' 
                          : 'opacity-0 scale-95 pointer-events-none'
                      }`}
                    />
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Logo marquee strip */}
      <section ref={reveal} className="border-y border-slate-100 bg-white py-10 relative z-10 overflow-hidden scroll-reveal">
        <div className="max-w-5xl mx-auto px-6 mb-6 text-center">
          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
            Trusted by modern, forward-thinking teams worldwide
          </div>
        </div>
        
        {/* Marquee with left/right fade masks */}
        <div className="relative flex overflow-x-hidden w-full before:absolute before:left-0 before:top-0 before:z-10 before:h-full before:w-24 before:bg-gradient-to-r before:from-white before:to-transparent after:absolute after:right-0 after:top-0 after:z-10 after:h-full after:w-24 after:bg-gradient-to-l after:from-white after:to-transparent">
          <div className="flex gap-20 animate-marquee whitespace-nowrap py-2 select-none">
            {/* First copy of logos */}
            {LOGOS.map((logo, index) => (
              <div key={`logo-1-${index}`} className="flex items-center gap-2.5 text-slate-400 hover:text-slate-700 transition-colors duration-300 font-bold text-sm tracking-widest uppercase cursor-default">
                {logo.icon}
                <span>{logo.name}</span>
              </div>
            ))}
            {/* Duplicate set so the marquee loops seamlessly */}
            {LOGOS.map((logo, index) => (
              <div key={`logo-2-${index}`} className="flex items-center gap-2.5 text-slate-400 hover:text-slate-700 transition-colors duration-300 font-bold text-sm tracking-widest uppercase cursor-default">
                {logo.icon}
                <span>{logo.name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Core feature cards */}
      <section ref={reveal} className="max-w-4xl mx-auto px-4 sm:px-6 py-16 sm:py-24 relative z-10 scroll-reveal">
        <div className="text-center mb-16">
          <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight mb-4">Intelligent Core Capabilities</h2>
        </div>

        <div className="flex flex-col gap-6">
          {/* Card 1 */}
          <div ref={reveal} className="bg-white border border-slate-100 rounded-2xl p-8 shadow-sm flex flex-col md:flex-row gap-6 items-start hover:border-blue-200 hover:-translate-y-1 hover:shadow-md hover:shadow-blue-500/5 transition-all duration-300 group relative scroll-reveal sr-delay-1">
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
          <div ref={reveal} className="bg-white border border-slate-100 rounded-2xl p-8 shadow-sm flex flex-col md:flex-row gap-6 items-start hover:border-blue-200 hover:-translate-y-1 hover:shadow-md hover:shadow-blue-500/5 transition-all duration-300 group relative scroll-reveal sr-delay-2">
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
          <div ref={reveal} className="bg-white border border-slate-100 rounded-2xl p-8 shadow-sm flex flex-col md:flex-row gap-6 items-start hover:border-blue-200 hover:-translate-y-1 hover:shadow-md hover:shadow-blue-500/5 transition-all duration-300 group relative scroll-reveal sr-delay-3">
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
          <div ref={reveal} className="bg-white border border-slate-100 rounded-2xl p-8 shadow-sm flex flex-col md:flex-row gap-6 items-start hover:border-blue-200 hover:-translate-y-1 hover:shadow-md hover:shadow-blue-500/5 transition-all duration-300 group relative scroll-reveal sr-delay-4">
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

      {/* Interactive ReAct agent simulator */}
      <section id="demo" className="bg-slate-100/40 border-y border-slate-200/50 py-16 sm:py-24 relative z-10">
        <div ref={reveal} className="max-w-4xl mx-auto px-4 sm:px-6 scroll-reveal">
          <div className="text-center mb-16">
            <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight mb-4">The ReAct Loop</h2>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-5 gap-10 items-stretch">
            {/* Step list on the left */}
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

              {/* Scenario picker */}
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

            {/* Fake terminal showing agent reasoning steps */}
            <div className="lg:col-span-3 bg-[#0d1117] border border-slate-900 rounded-2xl flex flex-col h-[380px] sm:h-[400px] shadow-xl overflow-hidden relative">
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

      {/* Bottom CTA — no scroll-reveal here; it sits at the very bottom and can miss the observer on mobile */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 py-14 sm:py-20 relative z-10">
        <div className="bg-gradient-to-r from-slate-900 to-slate-950 rounded-3xl p-8 sm:p-12 text-center text-white shadow-xl shadow-slate-950/10 relative overflow-hidden border border-slate-800">
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl pointer-events-none animate-glow-pulse"></div>
          <h2 className="text-2xl md:text-3xl font-extrabold mb-4 tracking-tight">Ready to orchestrate your financial operations?</h2>
          <p className="text-slate-400 max-w-xl mx-auto mb-8 text-sm md:text-base leading-relaxed">
            Join leading enterprise finance teams implementing autonomous multi-agent pipelines with Invoxio.
          </p>
          <Link 
            to="/register" 
            className="bg-white hover:bg-slate-50 active:scale-[0.98] text-slate-950 font-bold px-8 py-3.5 rounded-xl shadow-md transition-all cursor-pointer text-center inline-block"
          >
            Request Enterprise Access
          </Link>
        </div>
      </section>

      {/* Footer — always visible, no scroll animation */}
      <footer className="border-t border-slate-100 bg-white py-12 sm:py-16 relative z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-12 gap-6 sm:gap-8 md:gap-10 mb-10 sm:mb-16">
            {/* Brand column */}
            <div className="md:col-span-4 flex flex-col gap-4">
              <a href="#" className="flex items-center gap-2.5 font-bold text-slate-900 text-lg group">
                <LogoIcon />
                <span>Invoxio</span>
              </a>
              <p className="text-slate-500 text-xs leading-relaxed max-w-xs">
                Autonomous finance operations and multi-agent orchestration for the global enterprise.
              </p>
              {/* Status Indicator */}
              <div className="flex items-center gap-2 mt-2 w-max bg-slate-50 border border-slate-200/50 px-3 py-1.5 rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="text-[10px] font-bold text-slate-500 tracking-wider uppercase">System Status: Operational</span>
              </div>
            </div>

            {/* Platform links */}
            <div className="md:col-span-2 flex flex-col gap-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Platform</span>
              <ul className="flex flex-col gap-2.5 text-xs font-semibold text-slate-500">
                <li><a href="#" className="hover:text-blue-600 transition-colors">Invoice Parser</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Anomaly Auditor</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Predictive Ledger</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">BI & Insights</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Developer APIs</a></li>
              </ul>
            </div>

            {/* Legal / trust links */}
            <div className="md:col-span-2 flex flex-col gap-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Trust & Legal</span>
              <ul className="flex flex-col gap-2.5 text-xs font-semibold text-slate-500">
                <li><a href="#" className="hover:text-blue-600 transition-colors">Compliance Center</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Trust & Safety</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Security Controls</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-blue-600 transition-colors">Terms of Service</a></li>
              </ul>
            </div>

            {/* Newsletter signup */}
            <div className="md:col-span-4 flex flex-col gap-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Enterprise Updates</span>
              <p className="text-slate-500 text-xs leading-relaxed">
                Subscribe to receive technical insights on agentic finance workflows.
              </p>
              <form onSubmit={(e) => e.preventDefault()} className="flex items-center gap-2 mt-1">
                <input 
                  type="email" 
                  placeholder="name@company.com" 
                  className="bg-slate-50 border border-slate-200 text-slate-800 text-xs px-3.5 py-2.5 rounded-lg focus:outline-none focus:border-blue-500 focus:bg-white transition-all w-full font-medium"
                />
                <button type="submit" className="bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs px-4 py-2.5 rounded-lg transition-all active:scale-95 shrink-0">
                  Subscribe
                </button>
              </form>
            </div>

          </div>

          {/* Copyright + social links */}
          <div className="border-t border-slate-100 pt-8 flex flex-col sm:flex-row justify-between items-center gap-4 text-[11px] text-slate-400">
            <div className="flex flex-col gap-1 text-center sm:text-left">
              <span>© {new Date().getFullYear()} Invoxio AI, Inc. All rights reserved.</span>
              <span className="opacity-75">Enterprise Cloud hosted in AWS us-east-1 (SOC-2 compliant data center).</span>
            </div>
            <div className="flex gap-4">
              <a href="#" className="text-slate-400 hover:text-slate-600 transition-colors" aria-label="LinkedIn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6zM2 9h4v12H2z" />
                  <circle cx="4" cy="4" r="2" />
                </svg>
              </a>
              <a href="#" className="text-slate-400 hover:text-slate-600 transition-colors" aria-label="Twitter">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z" />
                </svg>
              </a>
              <a href="#" className="text-slate-400 hover:text-slate-600 transition-colors" aria-label="GitHub">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
                </svg>
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
