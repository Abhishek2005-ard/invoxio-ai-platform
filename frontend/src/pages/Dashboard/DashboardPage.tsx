import { useState, useRef, useCallback } from 'react';
import { useAuth } from '../../store/AuthContext';
import { useNavigate } from 'react-router-dom';

const AGENT_API = 'http://localhost:8000/api/agent/chat';

async function askAgent(message: string): Promise<string> {
  const res = await fetch(AGENT_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error(`Agent error ${res.status}`);
  const d = await res.json();
  return d.answer ?? JSON.stringify(d);
}

// ── Types ──────────────────────────────────────────────────────────────────
interface Invoice {
  id: string;
  vendor: string;
  amount: string;
  date: string;
  status: 'Paid' | 'Pending' | 'Overdue';
  po: string;
  tax: string;
}

// ── Mock extracted invoices ────────────────────────────────────────────────
const MOCK_INVOICES: Invoice[] = [
  { id: 'INV-1042', vendor: 'Globex Corp', amount: '$12,400', date: '2026-06-15', status: 'Paid',    po: 'PO-8821', tax: '$1,116' },
  { id: 'INV-1041', vendor: 'ACME Supplies', amount: '$3,250',  date: '2026-06-10', status: 'Pending', po: 'PO-8819', tax: '$292'  },
  { id: 'INV-1040', vendor: 'Initech Ltd',  amount: '$8,750',  date: '2026-05-28', status: 'Overdue', po: '—',      tax: '$787'  },
  { id: 'INV-1039', vendor: 'CloudNest',    amount: '$4,500',  date: '2026-05-20', status: 'Paid',    po: 'PO-8804', tax: '$405'  },
  { id: 'INV-1038', vendor: 'DataBridge',   amount: '$1,800',  date: '2026-05-12', status: 'Paid',    po: 'PO-8800', tax: '$162'  },
];

const INSIGHTS = [
  { icon: '📉', color: 'bg-red-50 border-red-200', badge: 'Anomaly', badgeColor: 'bg-red-100 text-red-700', title: 'Duplicate Invoice Detected', body: 'INV-1038 from DataBridge matches a previous entry ($1,800 on May 3). Review before approval.' },
  { icon: '⏰', color: 'bg-amber-50 border-amber-200', badge: 'Late Payment', badgeColor: 'bg-amber-100 text-amber-700', title: 'Initech Ltd — 18 days overdue', body: '$8,750 was due May 28. Automated reminder sent. Cash-flow risk: medium.' },
  { icon: '📈', color: 'bg-emerald-50 border-emerald-200', badge: 'Forecast', badgeColor: 'bg-emerald-100 text-emerald-700', title: 'Runway extended by 1.2 months', body: 'Based on Q2 growth (+20%) and current burn rate, projected runway is now 18.4 months.' },
  { icon: '💡', color: 'bg-blue-50 border-blue-200', badge: 'Trend', badgeColor: 'bg-blue-100 text-blue-700', title: 'Marketing spend up 34% vs last quarter', body: 'Vendor payments to Globex and ACME in the marketing category rose significantly. Review budget allocation.' },
];

const statusStyle: Record<string, string> = {
  Paid:    'bg-emerald-50 text-emerald-700 border-emerald-200',
  Pending: 'bg-amber-50 text-amber-700 border-amber-200',
  Overdue: 'bg-red-50 text-red-700 border-red-200',
};

// ══════════════════════════════════════════════════════════════════════════════
export default function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Upload
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>(MOCK_INVOICES);

  // NL Query
  const [query, setQuery] = useState('');
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryResult, setQueryResult] = useState<string | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);

  // ── File handler ───────────────────────────────────────────────────────
  const handleFiles = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    setUploading(true);
    setUploadResult(null);

    // Simulate reading file name and calling agent
    const fakeName = file.name.replace(/\.[^.]+$/, '');
    const prompt = `Extract invoice data from a document named "${file.name}". Return structured fields: Vendor Name, Invoice ID, Invoice Date, Total Amount, Tax Amount, PO Number, Line Items, and Payment Status.`;

    try {
      const result = await askAgent(prompt);
      setUploadResult(result);
      // Add mock entry to table
      const newInv: Invoice = {
        id: `INV-${1043 + invoices.length - MOCK_INVOICES.length}`,
        vendor: fakeName.split(/[-_]/)[0] ?? 'Unknown Vendor',
        amount: '$—',
        date: new Date().toISOString().split('T')[0],
        status: 'Pending',
        po: '—',
        tax: '$—',
      };
      setInvoices(prev => [newInv, ...prev]);
    } catch (e) {
      setUploadResult(`Error: ${String(e)}`);
    } finally {
      setUploading(false);
    }
  }, [invoices.length]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  // ── NL Query ───────────────────────────────────────────────────────────
  const handleQuery = async () => {
    if (!query.trim()) return;
    setQueryLoading(true);
    setQueryResult(null);
    setQueryError(null);
    try {
      const res = await askAgent(query);
      setQueryResult(res);
    } catch (e) {
      setQueryError(String(e));
    } finally {
      setQueryLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] font-sans flex flex-col">

      {/* ── Navbar ─────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 font-extrabold text-slate-900 text-base">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <defs>
                <linearGradient id="nv" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor="#3b82f6"/>
                  <stop offset="100%" stopColor="#6366f1"/>
                </linearGradient>
              </defs>
              <path d="M12 2L2 7l10 5 10-5-10-5z" fill="url(#nv)"/>
              <path d="M2 17l10 5 10-5" stroke="url(#nv)" strokeWidth="2.5" strokeLinecap="round"/>
            </svg>
            Invoxio
            <span className="text-[10px] font-mono bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded ml-1">v1.2</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-white text-xs font-bold select-none">
              {user?.name?.charAt(0).toUpperCase() ?? 'U'}
            </div>
            <div className="hidden sm:block text-right">
              <p className="text-xs font-bold text-slate-800">{user?.name}</p>
              <p className="text-[10px] text-slate-400">{user?.email}</p>
            </div>
            <button onClick={() => { logout(); navigate('/'); }}
              className="text-xs font-semibold text-slate-500 hover:text-red-600 border border-slate-200 hover:border-red-200 px-3 py-1.5 rounded-lg bg-white transition-colors cursor-pointer">
              Log Out
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 flex flex-col gap-8">

        {/* ── KPI Row ──────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Invoices', value: '1,248', sub: 'This quarter', up: true, delta: '+14%' },
            { label: 'Total Extracted', value: '$284,600', sub: 'Auto-parsed value', up: true, delta: '+9%' },
            { label: 'Overdue Invoices', value: '3', sub: '1 high risk', up: false, delta: 'Action needed' },
            { label: 'Projected Runway', value: '18.4 mo', sub: 'Based on cash flow', up: true, delta: '+1.2 mo' },
          ].map(k => (
            <div key={k.label} className="bg-white border border-slate-200/70 rounded-2xl p-5 shadow-sm flex flex-col gap-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{k.label}</span>
              <span className="text-2xl font-extrabold text-slate-900 mt-1">{k.value}</span>
              <div className="flex items-center gap-1.5 mt-1">
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${k.up ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-600'}`}>{k.delta}</span>
                <span className="text-[10px] text-slate-400">{k.sub}</span>
              </div>
            </div>
          ))}
        </div>

        {/* ── Upload + NL Query (side by side) ─────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Upload Zone */}
          <div className="bg-white border border-slate-200/70 rounded-2xl p-6 shadow-sm flex flex-col gap-4">
            <div>
              <h2 className="text-base font-bold text-slate-900">Upload Invoice</h2>
              <p className="text-xs text-slate-500 mt-0.5">PDF, scanned image, or email attachment — AI extracts everything automatically.</p>
            </div>

            <div
              onDragOver={e => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              onClick={() => fileRef.current?.click()}
              className={`flex flex-col items-center justify-center gap-3 border-2 border-dashed rounded-xl py-10 cursor-pointer transition-all
                ${dragOver ? 'border-blue-400 bg-blue-50' : 'border-slate-200 hover:border-blue-300 hover:bg-slate-50'}`}
            >
              <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
              </div>
              <div className="text-center">
                <p className="text-sm font-bold text-slate-700">{dragOver ? 'Drop to upload' : 'Drag & drop or click to browse'}</p>
                <p className="text-[11px] text-slate-400 mt-0.5">PDF · PNG · JPG · EML supported</p>
              </div>
            </div>
            <input ref={fileRef} type="file" accept=".pdf,.png,.jpg,.jpeg,.eml" className="hidden" onChange={e => handleFiles(e.target.files)} />

            {uploading && (
              <div className="flex items-center gap-2 text-xs text-blue-600 font-medium">
                <span className="w-3 h-3 rounded-full border-2 border-blue-500 border-t-transparent animate-spin"/>
                Extracting invoice data with AI…
              </div>
            )}

            {uploadResult && (
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-[11px] text-slate-700 font-mono whitespace-pre-wrap max-h-40 overflow-y-auto">
                {uploadResult}
              </div>
            )}
          </div>

          {/* NL Query */}
          <div className="bg-white border border-slate-200/70 rounded-2xl p-6 shadow-sm flex flex-col gap-4">
            <div>
              <h2 className="text-base font-bold text-slate-900">Ask Your Financials</h2>
              <p className="text-xs text-slate-500 mt-0.5">Query spending, revenue, or vendors in plain English.</p>
            </div>

            <div className="flex flex-col gap-2 flex-1">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleQuery()}
                  placeholder="What did we spend on marketing last quarter?"
                  className="flex-1 border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
                <button onClick={handleQuery} disabled={queryLoading}
                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-bold px-4 rounded-xl transition-colors cursor-pointer shrink-0">
                  {queryLoading ? '…' : 'Ask'}
                </button>
              </div>

              {/* Suggestion chips */}
              <div className="flex flex-wrap gap-1.5 mt-1">
                {[
                  'Who are our top vendors?',
                  'Show overdue invoices',
                  'Q2 revenue breakdown',
                  'Forecast next 6 months',
                ].map(q => (
                  <button key={q} onClick={() => { setQuery(q); }}
                    className="text-[11px] font-medium text-slate-600 bg-slate-100 hover:bg-blue-50 hover:text-blue-700 px-2.5 py-1 rounded-full border border-slate-200 hover:border-blue-200 transition-all cursor-pointer">
                    {q}
                  </button>
                ))}
              </div>
            </div>

            {queryLoading && (
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span className="w-3 h-3 rounded-full border-2 border-slate-400 border-t-transparent animate-spin"/>
                Agent is thinking…
              </div>
            )}
            {queryError && <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-xl p-3">{queryError}</p>}
            {queryResult && (
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-[11px] text-slate-700 font-mono whitespace-pre-wrap max-h-48 overflow-y-auto flex-1">
                {queryResult}
              </div>
            )}
          </div>
        </div>

        {/* ── Proactive Insights ────────────────────────────────────────── */}
        <div>
          <h2 className="text-base font-bold text-slate-900 mb-3">Proactive Insights</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            {INSIGHTS.map(ins => (
              <div key={ins.title} className={`border ${ins.color} rounded-2xl p-4 flex flex-col gap-2`}>
                <div className="flex items-center justify-between">
                  <span className="text-xl">{ins.icon}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${ins.badgeColor}`}>{ins.badge}</span>
                </div>
                <p className="text-xs font-bold text-slate-800 leading-snug">{ins.title}</p>
                <p className="text-[11px] text-slate-600 leading-relaxed">{ins.body}</p>
              </div>
            ))}
          </div>
        </div>

        {/* ── Invoice Table ─────────────────────────────────────────────── */}
        <div className="bg-white border border-slate-200/70 rounded-2xl shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
            <h2 className="text-base font-bold text-slate-900">Extracted Invoices</h2>
            <span className="text-xs text-slate-400">{invoices.length} records</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100 text-left">
                  {['Invoice ID', 'Vendor', 'Amount', 'Tax', 'PO Number', 'Date', 'Status'].map(h => (
                    <th key={h} className="px-5 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv, i) => (
                  <tr key={inv.id} className={`border-b border-slate-50 hover:bg-slate-50/60 transition-colors ${i % 2 === 0 ? '' : 'bg-slate-50/30'}`}>
                    <td className="px-5 py-3.5 font-mono font-bold text-slate-700">{inv.id}</td>
                    <td className="px-5 py-3.5 font-medium text-slate-800">{inv.vendor}</td>
                    <td className="px-5 py-3.5 font-bold text-slate-900">{inv.amount}</td>
                    <td className="px-5 py-3.5 text-slate-500">{inv.tax}</td>
                    <td className="px-5 py-3.5 font-mono text-slate-500">{inv.po}</td>
                    <td className="px-5 py-3.5 text-slate-500">{inv.date}</td>
                    <td className="px-5 py-3.5">
                      <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border ${statusStyle[inv.status]}`}>{inv.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </main>
    </div>
  );
}
