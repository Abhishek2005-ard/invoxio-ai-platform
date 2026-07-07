import { useState, useRef, useCallback, useEffect } from 'react';
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

// Types
interface Invoice {
  id: string;
  dbId?: string;
  vendor: string;
  amount: string;
  date: string;
  status: 'Paid' | 'Pending' | 'Overdue' | 'Rejected';
  po: string;
  tax: string;
}



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
  Rejected: 'bg-rose-50 text-rose-700 border-rose-200',
};

export default function DashboardPage() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();

  // Upload
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);

  // Camera Scanner
  const videoRef = useRef<HTMLVideoElement>(null);
  const [showScanner, setShowScanner] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);

  // NL Query
  const [query, setQuery] = useState('');
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryResult, setQueryResult] = useState<string | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);

  // Stats
  const [stats, setStats] = useState({
    totalInvoices: 0,
    totalExtracted: '$0',
    overdueInvoices: 0,
    projectedRunway: '18.4 mo',
  });

  // Fetch invoices and calculate stats dynamically
  const fetchInvoices = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch('http://localhost:5000/api/invoices', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (!res.ok) throw new Error('Failed to fetch invoices');
      const data = await res.json();
      if (data.success && data.data) {
        const rawInvoices = data.data;

        // Map invoices
        const mapped: Invoice[] = rawInvoices.map((inv: any) => ({
          id: inv.runId || inv._id || `INV-${Date.now()}`,
          dbId: inv._id,
          vendor: inv.extractedData?.vendor || 'Unknown Vendor',
          amount: inv.extractedData?.amount ? `$${Number(inv.extractedData.amount).toLocaleString()}` : (inv.amount ? `$${Number(inv.amount).toLocaleString()}` : '$—'),
          date: inv.extractedData?.date || (inv.createdAt ? new Date(inv.createdAt).toISOString().split('T')[0] : '—'),
          status: inv.status === 'completed' ? 'Paid' : (inv.status === 'awaiting_approval' ? 'Pending' : (inv.status === 'rejected' ? 'Rejected' : 'Overdue')),
          po: inv.extractedData?.po_number || '—',
          tax: inv.extractedData?.tax ? `$${Number(inv.extractedData.tax).toLocaleString()}` : '$—',
        }));
        setInvoices(mapped);

        // Compute metrics dynamically
        const totalInvoices = rawInvoices.length;

        const totalExtractedSum = rawInvoices.reduce((sum: number, inv: any) => {
          const amt = inv.extractedData?.amount || inv.amount || 0;
          return sum + Number(amt);
        }, 0);

        const overdueCount = rawInvoices.filter((inv: any) => 
          inv.status !== 'completed' && inv.status !== 'awaiting_approval' && inv.status !== 'rejected'
        ).length;

        // Projected runway calculation: assume starting balance of $150,000
        const monthlyBurn = rawInvoices
          .filter((inv: any) => inv.status === 'completed' || inv.status === 'awaiting_approval')
          .reduce((sum: number, inv: any) => sum + Number(inv.extractedData?.amount || inv.amount || 0), 0);

        // If monthlyBurn is extremely small or zero, we default to 18.4 months baseline, otherwise dynamically calculate
        const runwayMonths = monthlyBurn > 0 ? Math.max(1, Math.min(60, 150000 / monthlyBurn)) : 18.4;
        const projectedRunway = `${runwayMonths.toFixed(1)} mo`;

        setStats({
          totalInvoices,
          totalExtracted: `$${totalExtractedSum.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
          overdueInvoices: overdueCount,
          projectedRunway,
        });
      }
    } catch (e) {
      console.error('Error fetching invoices:', e);
    }
  }, [token]);

  // Fetch invoices on component mount
  useEffect(() => {
    fetchInvoices();
  }, [fetchInvoices]);

  // ── File handler ───────────────────────────────────────────────────────
  const handleFiles = useCallback(async (files: FileList | File[] | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    setUploading(true);
    setUploadResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://localhost:5000/api/invoices/process', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || `Upload failed with status ${res.status}`);
      }
      const data = await res.json();
      
      if (data.success && data.data) {
        const inv = data.data;
        setUploadResult(JSON.stringify(inv, null, 2));
        fetchInvoices();
      } else {
        throw new Error(data.message || 'Processing failed');
      }
    } catch (e) {
      setUploadResult(`Error: ${String(e)}`);
    } finally {
      setUploading(false);
    }
  }, [token, fetchInvoices]);

  const startCamera = async () => {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      });
      setCameraStream(stream);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err: any) {
      console.error('Camera access error:', err);
      setCameraError(err.message || 'Could not access the camera. Make sure you have granted permission.');
    }
  };

  const stopCamera = useCallback(() => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
      setCameraStream(null);
    }
  }, [cameraStream]);

  const capturePhoto = useCallback(() => {
    if (!videoRef.current) return;
    
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], `scanned-invoice-${Date.now()}.jpg`, { type: 'image/jpeg' });
          handleFiles([file]);
        }
        stopCamera();
        setShowScanner(false);
      }, 'image/jpeg', 0.95);
    }
  }, [handleFiles, stopCamera]);

  const handleApprove = useCallback(async (invoiceId: string, decision: 'approved' | 'rejected') => {
    if (!token) return;
    try {
      const res = await fetch('http://localhost:5000/api/invoices/approve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          invoiceId,
          decision,
        }),
      });
      if (!res.ok) {
        throw new Error('Approval request failed');
      }
      const data = await res.json();
      if (data.success) {
        fetchInvoices();
      }
    } catch (e) {
      console.error('Error in handleApprove:', e);
    }
  }, [token, fetchInvoices]);

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
            <button onClick={() => navigate('/')}
              className="text-xs font-semibold text-slate-500 hover:text-blue-600 border border-slate-200 hover:border-blue-200 px-3 py-1.5 rounded-lg bg-white transition-colors cursor-pointer flex items-center gap-1">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="19" y1="12" x2="5" y2="12"/>
                <polyline points="12 19 5 12 12 5"/>
              </svg>
              Back to Home
            </button>
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
            { label: 'Total Invoices', value: stats.totalInvoices.toString(), sub: 'Active database count', up: true, delta: 'Live' },
            { label: 'Total Extracted', value: stats.totalExtracted, sub: 'Auto-parsed sum', up: true, delta: 'Live' },
            { label: 'Overdue Invoices', value: stats.overdueInvoices.toString(), sub: 'Needs immediate review', up: stats.overdueInvoices === 0, delta: stats.overdueInvoices === 0 ? 'Clear' : 'Pending' },
            { label: 'Projected Runway', value: stats.projectedRunway, sub: 'Dynamic cash estimate', up: true, delta: 'Forecast' },
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
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-slate-900">Upload Invoice</h2>
                <p className="text-xs text-slate-500 mt-0.5">PDF, scanned image, or email attachment — AI extracts everything automatically.</p>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); setShowScanner(true); startCamera(); }}
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 border border-blue-200 hover:border-blue-300 px-3 py-1.5 rounded-lg bg-blue-50/50 hover:bg-blue-50 transition-colors cursor-pointer flex items-center gap-1.5 shrink-0"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                  <circle cx="12" cy="13" r="4"/>
                </svg>
                Scan Invoice
              </button>
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
                  {['Invoice ID', 'Vendor', 'Amount', 'Tax', 'PO Number', 'Date', 'Status', 'Actions'].map(h => (
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
                    <td className="px-5 py-3.5">
                      {inv.status === 'Pending' && inv.dbId ? (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleApprove(inv.dbId!, 'approved')}
                            className="bg-emerald-500 hover:bg-emerald-600 text-white text-[10px] font-extrabold px-2 py-1 rounded transition-colors cursor-pointer"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleApprove(inv.dbId!, 'rejected')}
                            className="bg-rose-500 hover:bg-rose-600 text-white text-[10px] font-extrabold px-2 py-1 rounded transition-colors cursor-pointer"
                          >
                            Reject
                          </button>
                        </div>
                      ) : (
                        <span className="text-[10px] text-slate-350">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </main>

      {/* ── Camera Scanner Modal ────────────────────────────────────────── */}
      {showScanner && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 shadow-2xl rounded-3xl w-full max-w-lg overflow-hidden flex flex-col gap-4 p-6 relative">
            
            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                  <svg className="text-blue-500 animate-pulse" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <circle cx="12" cy="12" r="10"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                  Scan Invoice Document
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5">Align the invoice within the scanner frame.</p>
              </div>
              <button
                onClick={() => { stopCamera(); setShowScanner(false); }}
                className="w-8 h-8 rounded-full border border-slate-200 hover:border-red-200 hover:bg-red-50 text-slate-400 hover:text-red-600 flex items-center justify-center transition-colors cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Camera View Area */}
            <div className="relative rounded-2xl bg-slate-950 border border-slate-800 overflow-hidden aspect-[4/3] flex items-center justify-center">
              {cameraError ? (
                <div className="p-6 text-center flex flex-col items-center gap-3">
                  <span className="text-3xl">⚠️</span>
                  <p className="text-xs font-semibold text-slate-400 leading-relaxed">{cameraError}</p>
                  <button onClick={startCamera} className="text-xs font-bold text-blue-500 hover:underline">Retry Camera Connection</button>
                </div>
              ) : (
                <>
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    className="w-full h-full object-cover transform scale-x-[-1]"
                  />
                  {/* Scanner overlay alignment box */}
                  <div className="absolute inset-6 border-2 border-dashed border-blue-400/60 rounded-xl pointer-events-none flex items-center justify-center">
                    <div className="absolute inset-0 bg-blue-500/5 animate-pulse rounded-xl" />
                    <span className="text-[10px] font-bold text-blue-400 uppercase tracking-widest bg-slate-900/80 px-2.5 py-1 rounded-full backdrop-blur-sm">
                      Align Document
                    </span>
                  </div>
                </>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => { stopCamera(); setShowScanner(false); }}
                className="flex-1 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-600 hover:text-slate-800 rounded-xl text-xs font-bold transition-all cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={capturePhoto}
                disabled={!!cameraError || !cameraStream}
                className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center justify-center gap-1.5 shadow-lg shadow-blue-500/20"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
                Capture Photo
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
