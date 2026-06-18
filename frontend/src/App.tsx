import { useState, useEffect, useRef } from 'react';
import ChatInterface from './components/ChatInterface';
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, ScatterChart, Scatter, ZAxis, ReferenceLine, ReferenceArea } from 'recharts';
import { Upload, TrendingUp, Pizza, Network, FileDown, Check, HelpCircle } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const PRESETS = [
    "Casual Coffee Shop", "Fine Dining Restaurant", "Fast Food Chain", "Vegan Cafe", "Food Truck"
];

type ForecastPoint = {
    name: string;
    revenue: number | null;
    expected: number | null;
};

type MenuItemPoint = {
    item_name: string;
    category?: string | null;
    popularity_sales: number;
    avg_margin: number;
    total_revenue: number;
    cluster_label: string;
};

type CrossSalesMatrix = {
    index: string[];
    columns: string[];
    data: number[][];
    lift: number[][];
    support: number[][];
    total_orders: number;
};

type ForecastModelInfo = {
    model: string | null;
    description: string | null;
    validation_rmse: number | null;
    validated_on_days: number | null;
};

type SeedStatus = {
    in_progress: boolean;
    preset: string | null;
    days_seeded: number | null;
};

const EMPTY_CROSS_SALES: CrossSalesMatrix = {
    index: [],
    columns: [],
    data: [],
    lift: [],
    support: [],
    total_orders: 0,
};

// Pairs with fewer co-occurring orders than this are skipped in the combo
// leaderboards - with too few checks, lift/confidence is just sampling noise.
const MIN_COMBO_SUPPORT = 5;

// API Callers
const fetchStats = async () => (await axios.get('/api/v1/analytics/stats')).data;
const fetchForecastModelInfo = async (): Promise<ForecastModelInfo> =>
    (await axios.get('/api/v1/analytics/forecast-info')).data;
const fetchSeedStatus = async (): Promise<SeedStatus> =>
    (await axios.get('/api/v1/upload/seed-status')).data;
const HISTORY_RANGES = [
    { label: '7D', days: 7 },
    { label: '30D', days: 30 },
    { label: '90D', days: 90 },
    { label: '1Y', days: 365 },
];

const fetchForecast = async (historyDays: number): Promise<ForecastPoint[]> => {
    const hist = (await axios.get(`/api/v1/analytics/history?days=${historyDays}`)).data;
    const fore = (await axios.get('/api/v1/analytics/forecast')).data;

    const merged: ForecastPoint[] = [];
    hist.forEach((h: any, i: number) => {
        const isLastHistDay = i === hist.length - 1;
        const revenue = h.revenue != null ? Number(h.revenue) : null;
        merged.push({
            name: h.date,
            revenue,
            // Anchor the forecast line to the last actual point so it connects
            // visually instead of leaving a gap between history and forecast.
            expected: isLastHistDay ? revenue : null,
        });
    });
    fore.forEach((f: any) => {
        merged.push({
            name: f.date,
            revenue: null,
            expected: f.predicted_revenue != null ? Number(f.predicted_revenue) : null,
        });
    });
    return merged;
};
const fetchMenu = async (): Promise<MenuItemPoint[]> => {
    const data = (await axios.get('/api/v1/analytics/menu')).data;

    return (data ?? []).map((item: any) => ({
        item_name: item.item_name,
        category: item.category,
        popularity_sales: Number(item.popularity_sales ?? 0),
        avg_margin: Number(item.avg_margin ?? 0),
        total_revenue: Number(item.total_revenue ?? 0),
        cluster_label: item.cluster_label,
    }));
};
const fetchCrossSales = async (): Promise<CrossSalesMatrix> => {
    const data = (await axios.get('/api/v1/analytics/associations')).data;

    const toMatrix = (rows: any): number[][] =>
        Array.isArray(rows) ? rows.map((row: any) => (Array.isArray(row) ? row.map((value: any) => Number(value ?? 0)) : [])) : [];

    return {
        index: Array.isArray(data?.index) ? data.index : [],
        columns: Array.isArray(data?.columns) ? data.columns : [],
        data: toMatrix(data?.data),
        lift: toMatrix(data?.lift),
        support: toMatrix(data?.support),
        total_orders: Number(data?.total_orders ?? 0),
    };
};

const CustomMenuTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[#1e293b] border border-[var(--color-brand-border)] p-3 rounded-lg shadow-xl text-[var(--color-brand-text)] z-50">
          <p className="font-bold text-white mb-1">{data.item_name}</p>
          <p className="text-xs text-[var(--color-brand-muted)]">Cluster: <span className="font-semibold text-[var(--color-brand-accent)]">{data.cluster_label}</span></p>
          <p className="text-xs">Sales (Pop): {data.popularity_sales.toLocaleString()}</p>
          <p className="text-xs">Margin: ${parseFloat(data.avg_margin).toFixed(2)}</p>
        </div>
      );
    }
    return null;
};

const CustomForecastTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;
    const data = payload[0]?.payload;
    if (!data) return null;

    const fmt = (value: number | null | undefined) =>
        value == null ? null : `$${value.toFixed(2)}`;

    const rows: { label: string; value: string; color: string }[] = [];
    if (data.revenue != null) rows.push({ label: 'Actual revenue', value: fmt(data.revenue)!, color: '#3b82f6' });
    if (data.expected != null) rows.push({ label: 'AI forecast', value: fmt(data.expected)!, color: '#94a3b8' });

    return (
        <div className="bg-[#1e293b] border border-[var(--color-brand-border)] p-3 rounded-lg shadow-xl text-[var(--color-brand-text)] text-xs space-y-1 max-w-[220px]">
            <p className="font-bold text-white mb-1">{label}</p>
            {rows.map((row) => (
                <p key={row.label} className="flex justify-between gap-3">
                    <span style={{ color: row.color }}>{row.label}</span>
                    <span className="font-semibold">{row.value}</span>
                </p>
            ))}
        </div>
    );
};

const MENU_QUADRANTS = [
    { label: 'Stars', emoji: '⭐', color: '#34d399', desc: 'High popularity & margin — promote heavily.' },
    { label: 'Workhorses', emoji: '💪', color: '#3b82f6', desc: 'Popular, lower margin — keep, optimize cost.' },
    { label: 'Puzzles', emoji: '🤔', color: '#cbd5e1', desc: 'High margin, low popularity — upsell, reposition.' },
    { label: 'Dogs', emoji: '🗑️', color: '#f87171', desc: 'Low popularity & margin — consider removing.' },
];

function App() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('forecast');
  const [activePreset, setActivePreset] = useState(PRESETS[0]);
  const [selectedItemForCombo, setSelectedItemForCombo] = useState<string | null>(null);
  const [historyDays, setHistoryDays] = useState(30);

  // Queries
  const { data: stats, isLoading: statsLoading } = useQuery({ queryKey: ['stats'], queryFn: fetchStats });
  const { data: chartData = [], isLoading: chartLoading } = useQuery<ForecastPoint[]>({
      queryKey: ['forecast', historyDays],
      queryFn: () => fetchForecast(historyDays),
  });
  const { data: modelInfo } = useQuery<ForecastModelInfo>({ queryKey: ['forecast-info'], queryFn: fetchForecastModelInfo });
  const { data: menuData = [], isLoading: menuLoading } = useQuery<MenuItemPoint[]>({ queryKey: ['menu'], queryFn: fetchMenu });
  const { data: crossData = EMPTY_CROSS_SALES, isLoading: crossLoading } = useQuery<CrossSalesMatrix>({ queryKey: ['cross'], queryFn: fetchCrossSales });

  // Lift > 1 means the pair is bought together more often than random chance would
  // predict (real synergy); lift < 1 means less often than chance (not a real combo,
  // even if the items happen to co-occur sometimes). Pairs below MIN_COMBO_SUPPORT
  // orders are skipped entirely - too few checks for lift to mean anything.
  const comboPairs = (() => {
    const n = crossData.index.length;
    const pairs: { itemA: string; itemB: string; lift: number; support: number }[] = [];
    for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
            const support = Number(crossData.support[i]?.[j] ?? 0);
            if (support < MIN_COMBO_SUPPORT) continue;
            const lift = Number(crossData.lift[i]?.[j] ?? 0);
            const confAB = Number(crossData.data[i]?.[j] ?? 0);
            const confBA = Number(crossData.data[j]?.[i] ?? 0);
            const [itemA, itemB] = confAB >= confBA
                ? [crossData.index[i], crossData.columns[j]]
                : [crossData.index[j], crossData.columns[i]];
            pairs.push({ itemA, itemB, lift, support });
        }
    }
    return pairs;
  })();

  // Unified ranked combo list for the cross-sales screen - either every pair in the
  // menu (no item picked) or every pair involving the picked item, always sorted by
  // lift so the best synergies float to the top and the worst sink to the bottom.
  const comboRows = (selectedItemForCombo
    ? comboPairs
        .filter((p) => p.itemA === selectedItemForCombo || p.itemB === selectedItemForCombo)
        .map((p) => ({ label: p.itemA === selectedItemForCombo ? p.itemB : p.itemA, lift: p.lift, support: p.support }))
    : comboPairs.map((p) => ({ label: `${p.itemA} + ${p.itemB}`, lift: p.lift, support: p.support }))
  ).sort((a, b) => b.lift - a.lift);

  const forecastDays = chartData.filter((d) => d.revenue == null && d.expected != null);
  const historyPoints = chartData.filter((d) => d.revenue != null);
  const next7Total = forecastDays.reduce((acc, d) => acc + (d.expected ?? 0), 0);
  const last7Days = historyPoints.slice(-7);
  const last7Total = last7Days.reduce((acc, d) => acc + (d.revenue ?? 0), 0);
  const forecastTrendPct = last7Total > 0 ? ((next7Total - last7Total) / last7Total) * 100 : 0;

  const niceCeil = (value: number): number => {
      if (value <= 0) return 0;
      const magnitude = Math.pow(10, Math.floor(Math.log10(value)));
      return Math.ceil(value / magnitude) * magnitude;
  };

  const menuMeanX = menuData.length ? menuData.reduce((acc, d) => acc + d.popularity_sales, 0) / menuData.length : 0;
  const menuMeanY = menuData.length ? menuData.reduce((acc, d) => acc + d.avg_margin, 0) / menuData.length : 0;
  const menuMaxX = menuData.length ? niceCeil(Math.max(...menuData.map((d) => d.popularity_sales)) * 1.1) : 0;
  const menuMaxY = menuData.length ? niceCeil(Math.max(...menuData.map((d) => d.avg_margin)) * 1.1) : 0;


  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  // Mutations
  const seedMutation = useMutation({
      mutationFn: async (preset: string) => {
          await axios.post('/api/v1/upload/seed-demo', null, {
              params: { preset_name: preset }
          });
      },
      onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['stats'] });
          queryClient.invalidateQueries({ queryKey: ['forecast'] });
          queryClient.invalidateQueries({ queryKey: ['forecast-info'] });
          queryClient.invalidateQueries({ queryKey: ['menu'] });
          queryClient.invalidateQueries({ queryKey: ['cross'] });
          queryClient.invalidateQueries({ queryKey: ['seed-status'] });
          setSelectedItemForCombo(null);
      }
  });

  const handlePresetChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      const preset = e.target.value;
      setActivePreset(preset);
      seedMutation.mutate(preset);
  };

  // A freshly deployed instance has an empty database - without this, a first-
  // time visitor sees an all-zero dashboard and has to know to re-pick the
  // already-selected preset to trigger seeding. Auto-load the default preset
  // once stats have loaded and turn out to be empty.
  const autoSeedTriggeredRef = useRef(false);
  useEffect(() => {
      if (autoSeedTriggeredRef.current || statsLoading || !stats) return;
      if (stats.total_orders === 0) {
          autoSeedTriggeredRef.current = true;
          seedMutation.mutate(activePreset);
      } else {
          autoSeedTriggeredRef.current = true;
      }
  }, [statsLoading, stats]);

  // The dashboard renders instantly off the fast 30-day seed; this polls
  // whether the full-year background extension is still running, and
  // refreshes all the data once it flips back to done.
  const { data: seedStatus } = useQuery<SeedStatus>({
      queryKey: ['seed-status'],
      queryFn: fetchSeedStatus,
      refetchInterval: (query) => (query.state.data?.in_progress ? 3000 : false),
  });
  const wasSeedingRef = useRef(false);
  useEffect(() => {
      if (wasSeedingRef.current && seedStatus && !seedStatus.in_progress) {
          queryClient.invalidateQueries({ queryKey: ['stats'] });
          queryClient.invalidateQueries({ queryKey: ['forecast'] });
          queryClient.invalidateQueries({ queryKey: ['forecast-info'] });
          queryClient.invalidateQueries({ queryKey: ['menu'] });
          queryClient.invalidateQueries({ queryKey: ['cross'] });
      }
      wasSeedingRef.current = Boolean(seedStatus?.in_progress);
  }, [seedStatus, queryClient]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      setIsUploading(true);
      setUploadMessage("Uploading & Analyzing CSV...");
      
      const formData = new FormData();
      formData.append("file", file);

      try {
          await axios.post('/api/v1/upload/checks', formData, {
              headers: { 'Content-Type': 'multipart/form-data' }
          });
          setUploadMessage("Upload successful! Refreshing models...");
          
          // Re-fetch all data
          queryClient.invalidateQueries({ queryKey: ['stats'] });
          queryClient.invalidateQueries({ queryKey: ['forecast'] });
          queryClient.invalidateQueries({ queryKey: ['menu'] });
          queryClient.invalidateQueries({ queryKey: ['cross'] });
          setSelectedItemForCombo(null);
          setActivePreset("Custom CSV Data");
          
          setTimeout(() => setUploadMessage(null), 3000);
      } catch (error: any) {
          setUploadMessage(`Upload failed: ${error.response?.data?.detail || error.message}`);
          setTimeout(() => setUploadMessage(null), 5000);
      } finally {
          setIsUploading(false);
      }
  };

  const handleDownloadPDF = () => {
      window.open(`/api/v1/export/pdf?preset_name=${activePreset}`, '_blank');
  };

  return (
    <div className="min-h-screen bg-[var(--color-brand-bg)] font-sans text-[var(--color-brand-text)] flex overflow-hidden">
      
      {/* Sidebar: Navigation & Controls */}
      <aside className="w-64 bg-[#111827] border-r border-[var(--color-brand-border)] flex flex-col justify-between hidden md:flex">
        <div>
            <div className="p-6 border-b border-[var(--color-brand-border)] flex items-center gap-3">
                <span className="text-3xl">🍽️</span>
                <h1 className="text-xl font-extrabold tracking-tight">Gastro<span className="text-[var(--color-brand-accent)]">Sense</span></h1>
            </div>
            
            <div className="p-4 space-y-6">
                <div>
                    <h3 className="text-xs font-bold text-[var(--color-brand-muted)] uppercase tracking-wider mb-3">Data Source</h3>
                    <div className="space-y-2">
                        <label className="w-full flex items-center justify-between bg-[var(--color-brand-card)] border border-[var(--color-brand-border)] px-4 py-2.5 rounded-xl hover:border-[var(--color-brand-accent)] transition-colors text-sm font-semibold cursor-pointer relative overflow-hidden">
                            <span className="flex items-center gap-2">
                                <Upload size={16} className="text-[var(--color-brand-accent)]"/> 
                                {isUploading ? 'Uploading...' : 'Upload CSV'}
                            </span>
                            <input type="file" accept=".csv, .xlsx, .xls" className="hidden" onChange={handleFileUpload} disabled={isUploading || seedMutation.isPending} />
                        </label>
                        {uploadMessage && <p className="text-[10px] text-emerald-400 mt-1">{uploadMessage}</p>}
                        
                        <div className="mt-4">
                            <label className="text-xs text-[var(--color-brand-muted)] mb-2 block">Or use simulation preset:</label>
                            <select 
                                value={activePreset} 
                                onChange={handlePresetChange}
                                disabled={seedMutation.isPending}
                                className="w-full bg-[#0b0f19] border border-[var(--color-brand-border)] rounded-xl px-3 py-2 text-sm text-[var(--color-brand-text)] outline-none focus:border-[var(--color-brand-accent)] disabled:opacity-50"
                            >
                                {PRESETS.map(p => <option key={p} value={p}>{p}</option>)}
                            </select>
                            {seedMutation.isPending && <p className="text-xs text-[var(--color-brand-accent)] mt-2 animate-pulse">Generating realistic data...</p>}
                            {!seedMutation.isPending && seedStatus?.in_progress && (
                                <p className="text-xs text-emerald-400 mt-2 animate-pulse">Loading full year of history in background...</p>
                            )}
                        </div>
                    </div>
                </div>

                <div>
                    <h3 className="text-xs font-bold text-[var(--color-brand-muted)] uppercase tracking-wider mb-3">Modules</h3>
                    <nav className="space-y-1">
                        <button onClick={() => setActiveTab('forecast')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors text-sm font-semibold ${activeTab === 'forecast' ? 'bg-[var(--color-brand-accent)] text-white' : 'hover:bg-[#1e293b] text-[var(--color-brand-muted)] hover:text-white'}`}>
                            <TrendingUp size={18} /> Sales & Forecast
                        </button>
                        <button onClick={() => setActiveTab('menu')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors text-sm font-semibold ${activeTab === 'menu' ? 'bg-[var(--color-brand-accent)] text-white' : 'hover:bg-[#1e293b] text-[var(--color-brand-muted)] hover:text-white'}`}>
                            <Pizza size={18} /> Menu Engineering
                        </button>
                        <button onClick={() => setActiveTab('cross')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors text-sm font-semibold ${activeTab === 'cross' ? 'bg-[var(--color-brand-accent)] text-white' : 'hover:bg-[#1e293b] text-[var(--color-brand-muted)] hover:text-white'}`}>
                            <Network size={18} /> Cross-Sales & Combos
                        </button>
                    </nav>
                </div>
            </div>
        </div>

        <div className="p-4 border-t border-[var(--color-brand-border)]">
            <button onClick={handleDownloadPDF} className="w-full flex items-center justify-center gap-2 bg-[#1e293b] border border-[var(--color-brand-border)] px-4 py-3 rounded-xl hover:bg-[var(--color-brand-card)] transition-colors text-sm font-bold text-[var(--color-brand-muted)]">
                <FileDown size={16} /> Generate PDF Report
            </button>
        </div>
      </aside>

      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        
        <header className="h-20 border-b border-[var(--color-brand-border)] bg-[var(--color-brand-bg)] flex items-center justify-between px-8 flex-shrink-0">
            <div>
                <h2 className="text-xl font-bold text-white tracking-tight">
                    {activeTab === 'forecast' && 'Sales Forecasting & Anomaly Detection'}
                    {activeTab === 'menu' && 'Menu Engineering Matrix (BCG)'}
                    {activeTab === 'cross' && 'Cross-Sales & Combo Constructor'}
                </h2>
                <p className="text-xs text-[var(--color-brand-muted)] mt-1">Currently analyzing: <span className="font-semibold text-emerald-400">{activePreset}</span></p>
            </div>
        </header>

        <div className="flex-1 overflow-y-auto p-8 grid grid-cols-1 xl:grid-cols-3 gap-8">
            
            <section className="xl:col-span-2 flex flex-col gap-8 min-w-0">
                
                {/* Real KPI Data */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-[var(--color-brand-card)] border border-[var(--color-brand-border)] rounded-[16px] p-5 shadow-sm">
                        <div className="text-[10px] font-bold text-[var(--color-brand-muted)] uppercase tracking-wider">Total Revenue</div>
                        <div className="text-2xl font-extrabold text-white mt-1">
                            {statsLoading ? '...' : `$${(stats?.total_revenue / 1000).toFixed(1)}k`}
                        </div>
                    </div>
                    <div className="bg-[var(--color-brand-card)] border border-[var(--color-brand-border)] rounded-[16px] p-5 shadow-sm">
                        <div className="text-[10px] font-bold text-[var(--color-brand-muted)] uppercase tracking-wider">Total Orders</div>
                        <div className="text-2xl font-extrabold text-white mt-1">
                            {statsLoading ? '...' : stats?.total_orders.toLocaleString()}
                        </div>
                    </div>
                    <div className="bg-[var(--color-brand-card)] border border-[var(--color-brand-border)] rounded-[16px] p-5 shadow-sm">
                        <div className="text-[10px] font-bold text-[var(--color-brand-muted)] uppercase tracking-wider">Avg Check</div>
                        <div className="text-2xl font-extrabold text-white mt-1">
                            {statsLoading ? '...' : `$${stats?.avg_check}`}
                        </div>
                    </div>
                    <div className="bg-[var(--color-brand-card)] border border-[var(--color-brand-border)] rounded-[16px] p-5 shadow-sm">
                        <div className="text-[10px] font-bold text-[var(--color-brand-muted)] uppercase tracking-wider">Avg Items/Order</div>
                        <div className="text-2xl font-extrabold text-white mt-1">
                            {statsLoading ? '...' : stats?.avg_items_per_check}
                        </div>
                    </div>
                </div>

                <div className="bg-[var(--color-brand-card)] border border-[var(--color-brand-border)] rounded-[20px] p-6 shadow-lg min-h-[500px] flex flex-col">
                    
                    {activeTab === 'forecast' && (
                        <>
                            <div className="mb-4 flex items-start justify-between gap-4 flex-wrap">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">Revenue History & AI Forecast</h3>
                                        {modelInfo?.model && (
                                            <div className="group relative inline-flex">
                                                <HelpCircle size={15} className="text-[var(--color-brand-muted)] cursor-help hover:text-white transition-colors" />
                                                <div className="invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-opacity absolute left-0 top-6 z-20 w-72 bg-[#0b0f19] border border-[var(--color-brand-border)] rounded-xl p-3 shadow-2xl text-left">
                                                    <p className="text-xs font-bold text-white mb-1">How we calculated this: {modelInfo.model}</p>
                                                    <p className="text-[11px] text-[var(--color-brand-muted)] leading-relaxed">{modelInfo.description}</p>
                                                    {modelInfo.validation_rmse != null && (
                                                        <p className="text-[11px] text-emerald-400 mt-2">
                                                            Picked automatically: lowest validation error (${modelInfo.validation_rmse.toFixed(2)}) over the last {modelInfo.validated_on_days} days, vs. Ridge/Random Forest/XGBoost/LightGBM.
                                                        </p>
                                                    )}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                    <p className="text-xs text-[var(--color-brand-muted)] mt-1">
                                        Solid area = actual daily revenue. Dashed line = next 7 days predicted by the model.
                                    </p>
                                </div>
                                <div className="flex gap-1 bg-[#111827] border border-[var(--color-brand-border)] rounded-lg p-1 flex-shrink-0">
                                    {HISTORY_RANGES.map((range) => (
                                        <button
                                            key={range.label}
                                            onClick={() => setHistoryDays(range.days)}
                                            className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors ${
                                                historyDays === range.days
                                                    ? 'bg-[var(--color-brand-accent)] text-white'
                                                    : 'text-[var(--color-brand-muted)] hover:text-white'
                                            }`}
                                        >
                                            {range.label}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="flex-1 w-full flex flex-col gap-5 min-h-0">
                                {chartLoading ? (
                                    <div className="flex-1 flex items-center justify-center text-[var(--color-brand-muted)]">Loading metrics...</div>
                                ) : (
                                    <>
                                        <div className="flex-1 min-h-[280px]">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                                <defs>
                                                    <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" vertical={false} />
                                                <XAxis
                                                    dataKey="name"
                                                    stroke="#94a3b8"
                                                    tick={{fill: '#94a3b8', fontSize: 12}}
                                                    tickLine={false}
                                                    axisLine={false}
                                                    minTickGap={40}
                                                    interval="preserveStartEnd"
                                                />
                                                <YAxis stroke="#94a3b8" tick={{fill: '#94a3b8', fontSize: 12}} tickLine={false} axisLine={false} tickFormatter={(value) => `$${(value/1000).toFixed(0)}k`} />
                                                <Tooltip content={<CustomForecastTooltip />} />

                                                <Area type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorRevenue)" name="Actual Revenue" />
                                                <Line type="monotone" dataKey="expected" stroke="#94a3b8" strokeWidth={2} strokeDasharray="5 5" dot={false} name="AI Forecast" />
                                                </AreaChart>
                                            </ResponsiveContainer>
                                        </div>

                                        {/* Forecast insights */}
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 flex-shrink-0">
                                            <div className="bg-[#111827] border border-[var(--color-brand-border)] rounded-xl p-3">
                                                <p className="text-[10px] font-bold text-[var(--color-brand-muted)] uppercase tracking-wider mb-1">Next 7 days forecast</p>
                                                <p className="text-lg font-extrabold text-white">${(next7Total / 1000).toFixed(1)}k</p>
                                            </div>
                                            <div className="bg-[#111827] border border-[var(--color-brand-border)] rounded-xl p-3">
                                                <p className="text-[10px] font-bold text-[var(--color-brand-muted)] uppercase tracking-wider mb-1">vs. last 7 days</p>
                                                <p className={`text-lg font-extrabold ${forecastTrendPct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                                    {forecastTrendPct >= 0 ? '+' : ''}{forecastTrendPct.toFixed(1)}%
                                                </p>
                                            </div>
                                        </div>
                                    </>
                                )}
                            </div>
                        </>
                    )}

                    {activeTab === 'menu' && (
                        <>
                            <div className="mb-4">
                                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Menu Engineering Matrix (BCG)</h3>
                                <p className="text-xs text-[var(--color-brand-muted)] mt-1">Popularity (units sold) vs. average margin — each dot is one menu item.</p>
                            </div>
                            <div className="flex-1 w-full flex flex-col gap-5 min-h-0">
                                {menuLoading ? (
                                    <div className="flex-1 flex items-center justify-center text-[var(--color-brand-muted)]">Analyzing menu clusters...</div>
                                ) : menuData.length === 0 ? (
                                    <div className="flex-1 flex items-center justify-center text-[var(--color-brand-muted)] text-sm text-center">
                                        No menu analysis data yet. Seed data or upload a CSV to generate the matrix.
                                    </div>
                                ) : (
                                    <>
                                        <div className="flex-1 min-h-[320px]">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <ScatterChart margin={{ top: 10, right: 20, bottom: 30, left: 10 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />

                                                    {/* Quadrant background tints */}
                                                    <ReferenceArea x1={0} x2={menuMeanX} y1={menuMeanY} y2={menuMaxY} fill="#cbd5e1" fillOpacity={0.04} stroke="none" />
                                                    <ReferenceArea x1={menuMeanX} x2={menuMaxX} y1={menuMeanY} y2={menuMaxY} fill="#34d399" fillOpacity={0.07} stroke="none" />
                                                    <ReferenceArea x1={0} x2={menuMeanX} y1={0} y2={menuMeanY} fill="#f87171" fillOpacity={0.06} stroke="none" />
                                                    <ReferenceArea x1={menuMeanX} x2={menuMaxX} y1={0} y2={menuMeanY} fill="#3b82f6" fillOpacity={0.06} stroke="none" />

                                                    <XAxis
                                                        type="number" dataKey="popularity_sales" name="Popularity"
                                                        domain={[0, menuMaxX]}
                                                        stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} tickLine={false} axisLine={false}
                                                        label={{ value: 'Popularity (units sold)', position: 'insideBottom', offset: -20, fill: '#64748b', fontSize: 11 }}
                                                    />
                                                    <YAxis
                                                        type="number" dataKey="avg_margin" name="Margin"
                                                        domain={[0, menuMaxY]}
                                                        stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} tickLine={false} axisLine={false}
                                                        tickFormatter={(value) => `$${value}`}
                                                        label={{ value: 'Avg margin ($)', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }}
                                                    />
                                                    <ZAxis type="number" range={[120, 280]} />
                                                    <Tooltip content={<CustomMenuTooltip />} cursor={{ strokeDasharray: '3 3' }} />

                                                    <ReferenceLine x={menuMeanX} stroke="#475569" strokeDasharray="5 5" opacity={0.6} />
                                                    <ReferenceLine y={menuMeanY} stroke="#475569" strokeDasharray="5 5" opacity={0.6} />

                                                    <Scatter name="Stars" data={menuData.filter((d) => d.cluster_label === 'Stars')} fill="#34d399" stroke="#0b0f19" strokeWidth={1} />
                                                    <Scatter name="Workhorses" data={menuData.filter((d) => d.cluster_label === 'Workhorses')} fill="#3b82f6" stroke="#0b0f19" strokeWidth={1} />
                                                    <Scatter name="Puzzles" data={menuData.filter((d) => d.cluster_label === 'Puzzles')} fill="#cbd5e1" stroke="#0b0f19" strokeWidth={1} />
                                                    <Scatter name="Dogs" data={menuData.filter((d) => d.cluster_label === 'Dogs')} fill="#f87171" stroke="#0b0f19" strokeWidth={1} />
                                                </ScatterChart>
                                            </ResponsiveContainer>
                                        </div>

                                        {/* Quadrant legend */}
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 flex-shrink-0">
                                            {MENU_QUADRANTS.map((q) => (
                                                <div key={q.label} className="bg-[#111827] border border-[var(--color-brand-border)] rounded-xl p-3">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: q.color }}></span>
                                                        <span className="text-xs font-bold text-white">{q.emoji} {q.label}</span>
                                                    </div>
                                                    <p className="text-[11px] text-[var(--color-brand-muted)] leading-snug">{q.desc}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </>
                                )}
                            </div>
                        </>
                    )}

                    {activeTab === 'cross' && (
                        <>
                            <div className="mb-4">
                                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Cross-Sales & Combos</h3>
                                <p className="text-xs text-[var(--color-brand-muted)] mt-1">
                                    Ranked by lift: how many times more often items are bought together than random chance predicts. Green = real synergy, red = worse than chance - don't bundle.
                                </p>
                            </div>
                            {crossLoading ? (
                                <div className="flex-1 flex items-center justify-center text-[var(--color-brand-muted)]">Computing market basket analysis...</div>
                            ) : crossData.index.length === 0 ? (
                                <div className="flex-1 flex items-center justify-center text-sm text-[var(--color-brand-muted)]">No items available for cross-sales analysis. Seed more data or check backend.</div>
                            ) : (
                                <div className="flex-1 flex flex-col gap-4 min-h-0">
                                    <div className="flex flex-wrap gap-2 flex-shrink-0">
                                        <button
                                            onClick={() => setSelectedItemForCombo(null)}
                                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${!selectedItemForCombo ? 'bg-[var(--color-brand-accent)] text-white border-[var(--color-brand-accent)] shadow-md' : 'bg-[#111827] text-[var(--color-brand-muted)] border-[var(--color-brand-border)] hover:border-gray-500 hover:text-white'}`}
                                        >
                                            {!selectedItemForCombo && <Check size={12} />}
                                            All Pairs
                                        </button>
                                        {crossData.index.map((item: string) => {
                                            const isSelected = selectedItemForCombo === item;
                                            return (
                                                <button
                                                    key={item}
                                                    onClick={() => setSelectedItemForCombo(item)}
                                                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${isSelected ? 'bg-[var(--color-brand-accent)] text-white border-[var(--color-brand-accent)] shadow-md' : 'bg-[#111827] text-[var(--color-brand-muted)] border-[var(--color-brand-border)] hover:border-gray-500 hover:text-white'}`}
                                                >
                                                    {isSelected && <Check size={12} />}
                                                    {item}
                                                </button>
                                            );
                                        })}
                                    </div>

                                    <div className="flex-1 overflow-y-auto min-h-0 rounded-xl border border-[var(--color-brand-border)] bg-[#111827] divide-y divide-[var(--color-brand-border)]">
                                        {comboRows.length === 0 ? (
                                            <div className="h-full flex items-center justify-center text-sm text-[var(--color-brand-muted)] p-6 text-center">
                                                Not enough order history for a statistically meaningful combo {selectedItemForCombo ? `with ${selectedItemForCombo}` : ''}.
                                            </div>
                                        ) : (
                                            comboRows.map((row, idx) => {
                                                const liftPct = Math.round((row.lift - 1) * 100);
                                                const positive = row.lift >= 1;
                                                const barWidth = Math.min(100, Math.abs(liftPct));
                                                return (
                                                    <div key={`${row.label}-${idx}`} className="flex items-center gap-4 px-4 py-2.5">
                                                        <span className="text-[10px] font-bold text-[var(--color-brand-muted)] uppercase w-6 flex-shrink-0">#{idx + 1}</span>
                                                        <span className="font-semibold text-sm text-[var(--color-brand-text)] flex-1 truncate">{row.label}</span>
                                                        <span className="text-[10px] text-[var(--color-brand-muted)] flex-shrink-0 hidden md:inline">{row.support} orders</span>
                                                        <div className="w-24 h-1.5 bg-[#1e293b] rounded-full overflow-hidden flex-shrink-0 hidden sm:block">
                                                            <div className={`h-full rounded-full ${positive ? 'bg-emerald-400' : 'bg-rose-400'}`} style={{ width: `${barWidth}%` }}></div>
                                                        </div>
                                                        <span className={`text-xs font-bold w-16 text-right flex-shrink-0 ${positive ? 'text-emerald-400' : 'text-rose-400'}`}>
                                                            {liftPct > 0 ? '+' : ''}{liftPct}%
                                                        </span>
                                                    </div>
                                                );
                                            })
                                        )}
                                    </div>
                                </div>
                            )}
                        </>
                    )}

                </div>
            </section>

            <section className="xl:col-span-1 flex flex-col h-[calc(100vh-140px)] min-w-0">
                <ChatInterface />
            </section>

        </div>
      </main>
    </div>
  );
}

export default App;
