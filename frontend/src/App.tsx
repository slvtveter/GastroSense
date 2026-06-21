import { useState, useEffect, useRef } from 'react';
import ChatInterface from './components/ChatInterface';
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, ScatterChart, Scatter, ZAxis, ReferenceLine, ReferenceArea, Brush } from 'recharts';
import { Upload, TrendingUp, Pizza, Network, FileDown, Check, HelpCircle, BarChart3, Utensils, Sparkles, DollarSign, ShoppingBag, Receipt, Layers, ArrowUpRight, ArrowDownRight, Cpu } from 'lucide-react';
import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
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

// Accent ramp used across the charts so colours stay consistent with the CSS.
const C = {
    indigo: '#6e7bff',
    violet: '#a78bfa',
    cyan: '#22d3ee',
    emerald: '#34d399',
    rose: '#fb7185',
    slate: '#94a3b8',
    grid: 'rgba(255,255,255,0.06)',
    axis: '#64748b',
};

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

// Animated count-up for the KPI numbers. Eases from the previous value to the
// new one with requestAnimationFrame, so a preset switch animates instead of
// snapping. Purely presentational - takes a finished number + a formatter.
function AnimatedNumber({ value, format, duration = 950 }: { value: number; format: (n: number) => string; duration?: number }) {
    const [display, setDisplay] = useState(value);
    const fromRef = useRef(value);
    const rafRef = useRef<number | null>(null);

    useEffect(() => {
        const from = fromRef.current;
        const to = value;
        if (from === to) return;
        const start = performance.now();
        const tick = (now: number) => {
            const t = Math.min(1, (now - start) / duration);
            const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic
            setDisplay(from + (to - from) * eased);
            if (t < 1) {
                rafRef.current = requestAnimationFrame(tick);
            } else {
                fromRef.current = to;
            }
        };
        rafRef.current = requestAnimationFrame(tick);
        return () => {
            if (rafRef.current) cancelAnimationFrame(rafRef.current);
        };
    }, [value, duration]);

    return <>{format(display)}</>;
}

const CustomMenuTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="glass-card rounded-xl p-3 text-[var(--color-brand-text)] z-50">
          <p className="font-bold text-white mb-1">{data.item_name}</p>
          <p className="text-xs text-[var(--color-brand-muted)]">Cluster: <span className="font-semibold text-gradient-accent">{data.cluster_label}</span></p>
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
    if (data.revenue != null) rows.push({ label: 'Actual revenue', value: fmt(data.revenue)!, color: C.indigo });
    if (data.expected != null) rows.push({ label: 'AI forecast', value: fmt(data.expected)!, color: C.violet });

    return (
        <div className="glass-card rounded-xl p-3 text-[var(--color-brand-text)] text-xs space-y-1 max-w-[220px]">
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
    { label: 'Stars', emoji: '⭐', color: C.emerald, desc: 'High popularity & margin — promote heavily.' },
    { label: 'Workhorses', emoji: '💪', color: C.indigo, desc: 'Popular, lower margin — keep, optimize cost.' },
    { label: 'Puzzles', emoji: '🤔', color: C.slate, desc: 'High margin, low popularity — upsell, reposition.' },
    { label: 'Dogs', emoji: '🗑️', color: C.rose, desc: 'Low popularity & margin — consider removing.' },
];

// Hover help icon, matching the one on the Sales & Forecast chart. `position`
// places the popup relative to the icon (default: below-left); pass a different
// anchor (e.g. open upward for items near the bottom of the page).
const HelpTooltip = ({ title, children, position = 'left-0 top-6' }: { title: string; children: React.ReactNode; position?: string }) => (
    <span className="group relative inline-flex">
        <HelpCircle size={14} className="text-[var(--color-brand-muted)] cursor-help hover:text-white transition-colors" />
        <span className={`invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-opacity absolute ${position} z-30 w-72 glass-card rounded-xl p-3 shadow-2xl text-left font-normal normal-case tracking-normal block`}>
            <span className="text-xs font-bold text-white mb-1 block">{title}</span>
            <span className="text-[11px] text-[var(--color-brand-muted)] leading-relaxed block">{children}</span>
        </span>
    </span>
);

function App() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState(() => {
      const h = typeof window !== 'undefined' ? window.location.hash.replace('#', '') : '';
      return ['forecast', 'menu', 'cross'].includes(h) ? h : 'forecast';
  });
  const [activePreset, setActivePreset] = useState(PRESETS[0]);
  const [selectedItemForCombo, setSelectedItemForCombo] = useState<string | null>(null);
  const [historyDays, setHistoryDays] = useState(30);

  // Keep the active module in the URL hash so views are shareable / deep-linkable.
  useEffect(() => {
      if (window.location.hash.replace('#', '') !== activeTab) {
          window.history.replaceState(null, '', `#${activeTab}`);
      }
  }, [activeTab]);

  // Queries. keepPreviousData stops the KPI cards from blanking to undefined
  // while a preset switch reseeds and refetches - they keep showing the last
  // good numbers until the new ones arrive.
  const { data: stats, isLoading: statsLoading } = useQuery({
      queryKey: ['stats'],
      queryFn: fetchStats,
      placeholderData: keepPreviousData,
      // While the DB is still empty (cold-started backend seeding itself), keep
      // polling so the dashboard fills in the moment data is ready.
      refetchInterval: (query) => {
          const d = query.state.data as any;
          return (!d || Number(d.total_orders) === 0) ? 4000 : false;
      },
  });
  // Only treat the KPIs as ready when every field is a real, finite number, so
  // a half-empty or failed response can never render "$NaN" / "$undefined".
  const kpiReady = !!stats
      && [stats.total_revenue, stats.total_orders, stats.avg_check, stats.avg_items_per_check]
          .every((v) => v != null && Number.isFinite(Number(v)));
  const { data: chartData = [], isLoading: chartLoading } = useQuery<ForecastPoint[]>({
      queryKey: ['forecast', historyDays],
      queryFn: () => fetchForecast(historyDays),
      // Poll while there's no history yet so the chart fills in once the
      // backend has seeded itself.
      refetchInterval: (query) => {
          const d = query.state.data as ForecastPoint[] | undefined;
          return (!d || d.length === 0) ? 4000 : false;
      },
  });
  const { data: modelInfo } = useQuery<ForecastModelInfo>({ queryKey: ['forecast-info'], queryFn: fetchForecastModelInfo });
  const { data: menuData = [], isLoading: menuLoading } = useQuery<MenuItemPoint[]>({
      queryKey: ['menu'],
      queryFn: fetchMenu,
      refetchInterval: (query) => {
          const d = query.state.data as MenuItemPoint[] | undefined;
          return (!d || d.length === 0) ? 4000 : false;
      },
  });
  const { data: crossData = EMPTY_CROSS_SALES, isLoading: crossLoading } = useQuery<CrossSalesMatrix>({
      queryKey: ['cross'],
      queryFn: fetchCrossSales,
      refetchInterval: (query) => {
          const d = query.state.data as CrossSalesMatrix | undefined;
          return (!d || d.index.length === 0) ? 4000 : false;
      },
  });

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
  const allComboRows = (selectedItemForCombo
    ? comboPairs
        .filter((p) => p.itemA === selectedItemForCombo || p.itemB === selectedItemForCombo)
        .map((p) => ({ label: p.itemA === selectedItemForCombo ? p.itemB : p.itemA, lift: p.lift, support: p.support }))
    : comboPairs.map((p) => ({ label: `${p.itemA} + ${p.itemB}`, lift: p.lift, support: p.support }))
  ).sort((a, b) => b.lift - a.lift);

  // Fits on one screen like the other tabs (no scrolling) - take the best
  // and worst few instead of an arbitrary prefix, so both green (real
  // synergy) and red (below random chance) rows stay visible at a glance.
  const COMBO_ROWS_PER_SIDE = 6;
  const comboRows = allComboRows.length > COMBO_ROWS_PER_SIDE * 2
    ? [...allComboRows.slice(0, COMBO_ROWS_PER_SIDE), ...allComboRows.slice(-COMBO_ROWS_PER_SIDE)]
    : allComboRows;

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

  // The dashboard renders instantly off the fast 30-day seed; this polls
  // whether the background seeding/training is still running, and refreshes all
  // the data once it flips back to done.
  const { data: seedStatus } = useQuery<SeedStatus>({
      queryKey: ['seed-status'],
      queryFn: fetchSeedStatus,
      refetchInterval: (query) => (query.state.data?.in_progress ? 3000 : false),
  });

  // Fallback auto-seed. The backend self-seeds on startup when its (ephemeral)
  // DB is empty, so normally this never fires. But if we ever observe an empty
  // DB that the backend is NOT already seeding, kick it off from here. Guarded
  // on seedStatus so we never race a seed that's already running.
  const autoSeedTriggeredRef = useRef(false);
  useEffect(() => {
      if (autoSeedTriggeredRef.current || statsLoading || !stats || !seedStatus) return;
      if (Number(stats.total_orders) > 0) {
          autoSeedTriggeredRef.current = true;
      } else if (!seedStatus.in_progress) {
          autoSeedTriggeredRef.current = true;
          seedMutation.mutate(activePreset);
      }
  }, [statsLoading, stats, seedStatus]);
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

  const TAB_META: Record<string, { title: string; subtitle: string }> = {
      forecast: { title: 'Sales Forecasting & Anomaly Detection', subtitle: 'Daily revenue history with a 7-day machine-learning forecast.' },
      menu: { title: 'Menu Engineering Matrix', subtitle: 'Every item clustered by popularity and margin (BCG-style).' },
      cross: { title: 'Cross-Sales & Combo Constructor', subtitle: 'Market-basket lift — which items truly sell better together.' },
  };

  const kpis = [
      { key: 'rev', label: 'Total Revenue', icon: DollarSign, accent: C.indigo, value: Number(stats?.total_revenue ?? 0), format: (n: number) => `$${(n / 1000).toFixed(1)}k`, sub: 'all-time' },
      { key: 'ord', label: 'Total Orders', icon: ShoppingBag, accent: C.violet, value: Number(stats?.total_orders ?? 0), format: (n: number) => Math.round(n).toLocaleString(), sub: 'all-time' },
      { key: 'chk', label: 'Avg Check', icon: Receipt, accent: C.cyan, value: Number(stats?.avg_check ?? 0), format: (n: number) => `$${n.toFixed(2)}`, sub: 'per order' },
      { key: 'itm', label: 'Avg Items / Order', icon: Layers, accent: C.emerald, value: Number(stats?.avg_items_per_check ?? 0), format: (n: number) => n.toFixed(1), sub: 'basket size' },
  ];

  return (
    <div className="relative min-h-screen font-sans text-[var(--color-brand-text)] flex overflow-hidden">
      <div className="app-grid" aria-hidden="true" />

      {/* Sidebar: Navigation & Controls */}
      <aside className="relative z-10 w-72 glass border-r border-[var(--border-soft)] flex-col justify-between hidden md:flex">
        <div>
            <div className="px-6 py-6 border-b border-[var(--border-soft)] flex items-center gap-3">
                <span className="w-10 h-10 rounded-2xl flex items-center justify-center btn-accent shadow-lg">
                    <Utensils size={20} className="text-white" />
                </span>
                <div className="leading-none">
                    <h1 className="text-lg font-extrabold font-display tracking-tight">Gastro<span className="text-gradient-accent">Sense</span></h1>
                    <p className="text-[10px] font-semibold text-[var(--color-brand-faint)] uppercase tracking-[0.2em] mt-1">AI Analytics</p>
                </div>
            </div>

            <div className="p-4 space-y-7">
                <div>
                    <h3 className="text-[10px] font-bold text-[var(--color-brand-muted)] uppercase tracking-[0.18em] mb-3 flex items-center gap-1.5">
                        Data Source
                        <HelpTooltip title="Uploading your own data" position="left-0 top-6">
                            Upload a CSV or Excel export of receipts from your POS (iiko, R-Keeper, etc.). It needs one row per item sold, with columns for check ID, date/time, item name, price, and quantity (category is optional). Column names are matched automatically in English or Russian. No data of your own? Pick a simulation preset below.
                        </HelpTooltip>
                    </h3>
                    <div className="space-y-2">
                        <label className="btn-outline-grad w-full flex items-center justify-between px-4 py-2.5 rounded-xl text-sm font-semibold cursor-pointer relative overflow-hidden">
                            <span className="flex items-center gap-2">
                                <Upload size={16} className="text-[var(--color-brand-accent)]"/>
                                {isUploading ? 'Uploading...' : 'Upload CSV'}
                            </span>
                            <input type="file" accept=".csv, .xlsx, .xls" className="hidden" onChange={handleFileUpload} disabled={isUploading || seedMutation.isPending} />
                        </label>
                        {uploadMessage && <p className="text-[10px] text-[var(--color-brand-emerald)] mt-1">{uploadMessage}</p>}

                        <div className="mt-4">
                            <label className="text-[11px] text-[var(--color-brand-muted)] mb-2 block">Or use a simulation preset:</label>
                            <select
                                value={activePreset}
                                onChange={handlePresetChange}
                                disabled={seedMutation.isPending}
                                className="w-full bg-[var(--color-brand-bg)] border border-[var(--border-soft)] rounded-xl px-3 py-2.5 text-sm text-[var(--color-brand-text)] outline-none focus:border-[var(--color-brand-accent)] transition-colors disabled:opacity-50 cursor-pointer"
                            >
                                {PRESETS.map(p => <option key={p} value={p}>{p}</option>)}
                            </select>
                            {seedMutation.isPending && <p className="text-xs text-[var(--color-brand-accent)] mt-2 animate-pulse">Generating realistic data…</p>}
                            {!seedMutation.isPending && seedStatus?.in_progress && (
                                <p className="text-xs text-[var(--color-brand-emerald)] mt-2 animate-pulse">Loading full year of history in background…</p>
                            )}
                        </div>
                    </div>
                </div>

                <div>
                    <h3 className="text-[10px] font-bold text-[var(--color-brand-muted)] uppercase tracking-[0.18em] mb-3">Modules</h3>
                    <nav className="space-y-1.5">
                        {[
                            { id: 'forecast', icon: TrendingUp, label: 'Sales & Forecast' },
                            { id: 'menu', icon: Pizza, label: 'Menu Engineering' },
                            { id: 'cross', icon: Network, label: 'Cross-Sales & Combos' },
                        ].map((m) => {
                            const active = activeTab === m.id;
                            return (
                                <button
                                    key={m.id}
                                    onClick={() => setActiveTab(m.id)}
                                    className={`group relative w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-sm font-semibold ${
                                        active
                                            ? 'btn-accent text-white'
                                            : 'text-[var(--color-brand-muted)] hover:text-white hover:bg-white/5'
                                    }`}
                                >
                                    {active && <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-1 rounded-r-full bg-white/80" />}
                                    <m.icon size={18} className={active ? 'text-white' : 'text-[var(--color-brand-muted)] group-hover:text-[var(--color-brand-accent)] transition-colors'} />
                                    {m.label}
                                </button>
                            );
                        })}
                    </nav>
                </div>
            </div>
        </div>

        <div className="p-4 border-t border-[var(--border-soft)] space-y-3">
            <div className="relative">
                <span className="absolute top-1.5 right-2 z-30">
                    <HelpTooltip title="What's in the report" position="bottom-7 right-0">
                        A one-page PDF summary of the currently selected venue: headline KPIs (revenue, orders, average check), the 7-day demand forecast, the menu engineering breakdown (Stars / Workhorses / Puzzles / Dogs), and the top cross-sell combos. Handy for sharing the snapshot without opening the dashboard.
                    </HelpTooltip>
                </span>
                <button onClick={handleDownloadPDF} className="btn-outline-grad w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-bold text-[var(--color-brand-muted)] hover:text-white whitespace-nowrap transition-colors">
                    <FileDown size={16} /> Generate PDF Report
                </button>
            </div>
            <div className="flex items-center justify-center gap-2 text-[10px] text-[var(--color-brand-faint)]">
                <span className="online-dot" /> Backend live · models trained
            </div>
        </div>
      </aside>

      <main className="relative z-10 flex-1 flex flex-col h-screen overflow-hidden">

        <header className="border-b border-[var(--border-soft)] flex items-center justify-between px-8 py-5 flex-shrink-0">
            <div className="min-w-0">
                <div className="flex items-center gap-2 mb-1.5">
                    <Sparkles size={12} className="text-[var(--color-brand-violet)]" />
                    <span className="text-[10px] font-bold uppercase tracking-[0.22em] text-gradient-accent">AI Analytics Platform</span>
                </div>
                <h2 className="text-2xl font-extrabold font-display text-white tracking-tight truncate">
                    {TAB_META[activeTab]?.title}
                </h2>
                <p className="text-xs text-[var(--color-brand-muted)] mt-1 truncate">{TAB_META[activeTab]?.subtitle}</p>
            </div>
            <div className="hidden lg:flex items-center gap-3 flex-shrink-0">
                {modelInfo?.model && (
                    <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-[11px] font-semibold text-[var(--color-brand-muted)]">
                        <Cpu size={13} className="text-[var(--color-brand-cyan)]" /> {modelInfo.model}
                    </span>
                )}
                <span className="flex items-center gap-2 px-3 py-1.5 rounded-full glass text-[11px] font-semibold text-[var(--color-brand-text)]">
                    <span className="online-dot" /> {activePreset}
                </span>
            </div>
        </header>

        <div className="flex-1 overflow-y-auto p-8 grid grid-cols-1 xl:grid-cols-3 gap-7">

            <section className="xl:col-span-2 flex flex-col gap-7 min-w-0">

                {/* KPI cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {kpis.map((kpi, i) => (
                        <div
                            key={kpi.key}
                            className="glass-card hoverable rounded-2xl p-5 overflow-hidden relative animate-fade-up"
                            style={{ animationDelay: `${i * 70}ms` }}
                        >
                            <span className="absolute top-0 left-5 right-5 h-px accent-rule opacity-70" />
                            <div className="flex items-center justify-between mb-3">
                                <span
                                    className="w-9 h-9 rounded-xl flex items-center justify-center"
                                    style={{ background: `${kpi.accent}1f`, color: kpi.accent, boxShadow: `0 0 18px -4px ${kpi.accent}66` }}
                                >
                                    <kpi.icon size={17} />
                                </span>
                                {kpi.key === 'rev' && forecastDays.length > 0 && (
                                    <span className={`flex items-center gap-0.5 text-[10px] font-bold px-1.5 py-0.5 rounded-md ${forecastTrendPct >= 0 ? 'text-[var(--color-brand-emerald)] bg-emerald-500/10' : 'text-[var(--color-brand-rose)] bg-rose-500/10'}`}>
                                        {forecastTrendPct >= 0 ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
                                        {Math.abs(forecastTrendPct).toFixed(0)}%
                                    </span>
                                )}
                            </div>
                            <div className="text-[10px] font-bold text-[var(--color-brand-muted)] uppercase tracking-[0.14em]">{kpi.label}</div>
                            <div className="text-[26px] leading-tight font-extrabold font-display text-white mt-1 tabular-nums">
                                {kpiReady ? <AnimatedNumber value={kpi.value} format={kpi.format} /> : <span className="skeleton inline-block w-20 h-7 align-middle" />}
                            </div>
                            <div className="text-[10px] text-[var(--color-brand-faint)] mt-1">{kpi.sub}</div>
                        </div>
                    ))}
                </div>

                <div className="glass-card rounded-3xl p-6 shadow-lg min-h-[500px] flex flex-col animate-fade-up" style={{ animationDelay: '120ms' }}>

                    {activeTab === 'forecast' && (
                        <>
                            <div className="mb-4 flex items-start justify-between gap-4 flex-wrap">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">Revenue History & AI Forecast</h3>
                                        {modelInfo?.model && (
                                            <div className="group relative inline-flex">
                                                <HelpCircle size={15} className="text-[var(--color-brand-muted)] cursor-help hover:text-white transition-colors" />
                                                <div className="invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-opacity absolute left-0 top-6 z-20 w-72 glass-card rounded-xl p-3 shadow-2xl text-left">
                                                    <p className="text-xs font-bold text-white mb-1">How we calculated this: {modelInfo.model}</p>
                                                    <p className="text-[11px] text-[var(--color-brand-muted)] leading-relaxed">{modelInfo.description}</p>
                                                    {modelInfo.validation_rmse != null && (
                                                        <p className="text-[11px] text-[var(--color-brand-emerald)] mt-2">
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
                                <div className="flex gap-1 glass rounded-xl p-1 flex-shrink-0">
                                    {HISTORY_RANGES.map((range) => (
                                        <button
                                            key={range.label}
                                            onClick={() => setHistoryDays(range.days)}
                                            className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                                                historyDays === range.days
                                                    ? 'btn-accent text-white'
                                                    : 'text-[var(--color-brand-muted)] hover:text-white'
                                            }`}
                                        >
                                            {range.label}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="flex-1 w-full flex flex-col gap-5 min-h-0">
                                {chartLoading || chartData.length === 0 ? (
                                    <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-brand-muted)] gap-3">
                                        <BarChart3 size={22} className="text-[var(--color-brand-accent)] animate-pulse" />
                                        <span className="text-sm">{seedStatus?.in_progress ? 'Preparing data & training models…' : 'Loading metrics…'}</span>
                                        <div className="w-full max-w-md space-y-2 mt-2">
                                            <div className="skeleton h-2.5 w-full" />
                                            <div className="skeleton h-2.5 w-4/5" />
                                            <div className="skeleton h-2.5 w-2/3" />
                                        </div>
                                    </div>
                                ) : (
                                    <>
                                        <div className="flex-1 min-h-[280px]">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <AreaChart data={chartData} margin={{ top: 10, right: 18, left: 0, bottom: 0 }}>
                                                <defs>
                                                    <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor={C.indigo} stopOpacity={0.55}/>
                                                    <stop offset="95%" stopColor={C.indigo} stopOpacity={0}/>
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
                                                <XAxis
                                                    dataKey="name"
                                                    stroke={C.axis}
                                                    tick={{fill: C.axis, fontSize: 12}}
                                                    tickLine={false}
                                                    axisLine={false}
                                                    minTickGap={40}
                                                    interval="preserveStartEnd"
                                                />
                                                <YAxis stroke={C.axis} tick={{fill: C.axis, fontSize: 12}} tickLine={false} axisLine={false} tickFormatter={(value) => `$${(value/1000).toFixed(0)}k`} />
                                                <Tooltip content={<CustomForecastTooltip />} cursor={{ stroke: C.indigo, strokeOpacity: 0.3 }} />

                                                <Area type="monotone" dataKey="revenue" stroke={C.indigo} strokeWidth={3} fillOpacity={1} fill="url(#colorRevenue)" name="Actual Revenue" style={{ filter: 'drop-shadow(0 3px 8px rgba(110,123,255,0.35))' }} activeDot={{ r: 5, fill: C.indigo, stroke: '#fff', strokeWidth: 1.5 }} />
                                                <Line type="monotone" dataKey="expected" stroke={C.violet} strokeWidth={2.2} strokeDasharray="5 5" dot={false} name="AI Forecast" />
                                                {/* Draggable range selector (like a trading chart) - drag the
                                                    handles to zoom into any window within the selected period. */}
                                                <Brush
                                                    dataKey="name"
                                                    height={22}
                                                    travellerWidth={9}
                                                    stroke={C.indigo}
                                                    fill="rgba(110,123,255,0.05)"
                                                    tickFormatter={() => ''}
                                                />
                                                </AreaChart>
                                            </ResponsiveContainer>
                                        </div>

                                        {/* Forecast insights. While the background job is still training,
                                            the forecast is empty - show a placeholder instead of a misleading
                                            $0.0k / -100%. */}
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 flex-shrink-0">
                                            <div className="glass rounded-2xl p-4">
                                                <p className="text-[10px] font-bold text-[var(--color-brand-muted)] uppercase tracking-wider mb-1">Next 7 days forecast</p>
                                                <p className="text-xl font-extrabold font-display text-white">{forecastDays.length > 0 ? `$${(next7Total / 1000).toFixed(1)}k` : '…'}</p>
                                            </div>
                                            <div className="glass rounded-2xl p-4">
                                                <p className="text-[10px] font-bold text-[var(--color-brand-muted)] uppercase tracking-wider mb-1">vs. last 7 days</p>
                                                <p className={`text-xl font-extrabold font-display flex items-center gap-1 ${forecastDays.length === 0 ? 'text-[var(--color-brand-muted)]' : forecastTrendPct >= 0 ? 'text-[var(--color-brand-emerald)]' : 'text-[var(--color-brand-rose)]'}`}>
                                                    {forecastDays.length > 0 && (forecastTrendPct >= 0 ? <ArrowUpRight size={18} /> : <ArrowDownRight size={18} />)}
                                                    {forecastDays.length > 0 ? `${forecastTrendPct >= 0 ? '+' : ''}${forecastTrendPct.toFixed(1)}%` : '…'}
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
                                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                                    Menu Engineering Matrix (BCG)
                                    <HelpTooltip title="How we calculated this: K-Means clustering">
                                        Each item is plotted by popularity (units sold) and average margin. We standardize both metrics so neither dominates, then run K-Means (K=4) to group items, and label the clusters against the median into Stars, Workhorses, Puzzles, and Dogs. Margins are estimated from category-based food-cost benchmarks.
                                    </HelpTooltip>
                                </h3>
                                <p className="text-xs text-[var(--color-brand-muted)] mt-1">Popularity (units sold) vs. average margin — each dot is one menu item.</p>
                            </div>
                            <div className="flex-1 w-full flex flex-col gap-5 min-h-0">
                                {menuLoading ? (
                                    <div className="flex-1 flex items-center justify-center text-[var(--color-brand-muted)] gap-2"><Pizza size={18} className="animate-pulse text-[var(--color-brand-accent)]" /> Analyzing menu clusters…</div>
                                ) : menuData.length === 0 ? (
                                    <div className="flex-1 flex items-center justify-center text-[var(--color-brand-muted)] text-sm text-center gap-2">
                                        {seedStatus?.in_progress ? (
                                            <><Pizza size={18} className="animate-pulse" /> Training the menu model…</>
                                        ) : 'No menu analysis data yet. Seed data or upload a CSV to generate the matrix.'}
                                    </div>
                                ) : (
                                    <>
                                        <div className="flex-1 min-h-[320px]">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <ScatterChart margin={{ top: 10, right: 20, bottom: 30, left: 10 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />

                                                    {/* Quadrant background tints */}
                                                    <ReferenceArea x1={0} x2={menuMeanX} y1={menuMeanY} y2={menuMaxY} fill={C.slate} fillOpacity={0.05} stroke="none" />
                                                    <ReferenceArea x1={menuMeanX} x2={menuMaxX} y1={menuMeanY} y2={menuMaxY} fill={C.emerald} fillOpacity={0.08} stroke="none" />
                                                    <ReferenceArea x1={0} x2={menuMeanX} y1={0} y2={menuMeanY} fill={C.rose} fillOpacity={0.07} stroke="none" />
                                                    <ReferenceArea x1={menuMeanX} x2={menuMaxX} y1={0} y2={menuMeanY} fill={C.indigo} fillOpacity={0.07} stroke="none" />

                                                    <XAxis
                                                        type="number" dataKey="popularity_sales" name="Popularity"
                                                        domain={[0, menuMaxX]}
                                                        stroke={C.axis} tick={{ fill: C.axis, fontSize: 12 }} tickLine={false} axisLine={false}
                                                        label={{ value: 'Popularity (units sold)', position: 'insideBottom', offset: -20, fill: C.axis, fontSize: 11 }}
                                                    />
                                                    <YAxis
                                                        type="number" dataKey="avg_margin" name="Margin"
                                                        domain={[0, menuMaxY]}
                                                        stroke={C.axis} tick={{ fill: C.axis, fontSize: 12 }} tickLine={false} axisLine={false}
                                                        tickFormatter={(value) => `$${value}`}
                                                        label={{ value: 'Avg margin ($)', angle: -90, position: 'insideLeft', fill: C.axis, fontSize: 11 }}
                                                    />
                                                    <ZAxis type="number" range={[120, 280]} />
                                                    <Tooltip content={<CustomMenuTooltip />} cursor={{ strokeDasharray: '3 3' }} />

                                                    <ReferenceLine x={menuMeanX} stroke="#475569" strokeDasharray="5 5" opacity={0.6} />
                                                    <ReferenceLine y={menuMeanY} stroke="#475569" strokeDasharray="5 5" opacity={0.6} />

                                                    <Scatter name="Stars" data={menuData.filter((d) => d.cluster_label === 'Stars')} fill={C.emerald} stroke="#070810" strokeWidth={1} />
                                                    <Scatter name="Workhorses" data={menuData.filter((d) => d.cluster_label === 'Workhorses')} fill={C.indigo} stroke="#070810" strokeWidth={1} />
                                                    <Scatter name="Puzzles" data={menuData.filter((d) => d.cluster_label === 'Puzzles')} fill={C.slate} stroke="#070810" strokeWidth={1} />
                                                    <Scatter name="Dogs" data={menuData.filter((d) => d.cluster_label === 'Dogs')} fill={C.rose} stroke="#070810" strokeWidth={1} />
                                                </ScatterChart>
                                            </ResponsiveContainer>
                                        </div>

                                        {/* Quadrant legend */}
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 flex-shrink-0">
                                            {MENU_QUADRANTS.map((q) => (
                                                <div key={q.label} className="glass rounded-2xl p-3 hoverable">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: q.color, boxShadow: `0 0 10px -1px ${q.color}` }}></span>
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
                                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                                    Cross-Sales & Combos
                                    <HelpTooltip title="How we calculated this: market basket lift">
                                        For every pair of items we compute lift = P(A and B) / (P(A) × P(B)) — how often they're actually bought together versus what pure chance would predict. Lift above 1 (green) is real synergy worth bundling; below 1 (red) means they're ordered together less than chance, so don't. Pairs with too few orders are filtered out as noise.
                                    </HelpTooltip>
                                </h3>
                                <p className="text-xs text-[var(--color-brand-muted)] mt-1">
                                    Ranked by lift: how many times more often items are bought together than random chance predicts. Green = real synergy, red = worse than chance — don't bundle.
                                </p>
                            </div>
                            {crossLoading ? (
                                <div className="flex-1 flex items-center justify-center text-[var(--color-brand-muted)] gap-2"><Network size={18} className="animate-pulse text-[var(--color-brand-accent)]" /> Computing market basket analysis…</div>
                            ) : crossData.index.length === 0 ? (
                                <div className="flex-1 flex items-center justify-center text-sm text-[var(--color-brand-muted)] gap-2">
                                    {seedStatus?.in_progress ? (
                                        <><Network size={18} className="animate-pulse" /> Computing combos from order history…</>
                                    ) : 'No items available for cross-sales analysis. Seed more data or check backend.'}
                                </div>
                            ) : (
                                <div className="flex-1 flex flex-col gap-4 min-h-0">
                                    <div className="flex flex-wrap gap-2 flex-shrink-0">
                                        <button
                                            onClick={() => setSelectedItemForCombo(null)}
                                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${!selectedItemForCombo ? 'btn-accent text-white border-transparent' : 'glass text-[var(--color-brand-muted)] border-[var(--border-soft)] hover:text-white'}`}
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
                                                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${isSelected ? 'btn-accent text-white border-transparent' : 'glass text-[var(--color-brand-muted)] border-[var(--border-soft)] hover:text-white'}`}
                                                >
                                                    {isSelected && <Check size={12} />}
                                                    {item}
                                                </button>
                                            );
                                        })}
                                    </div>

                                    <div className="rounded-2xl border border-[var(--border-soft)] glass divide-y divide-[var(--border-soft)] overflow-hidden">
                                        {comboRows.length === 0 ? (
                                            <div className="flex items-center justify-center text-sm text-[var(--color-brand-muted)] p-6 text-center">
                                                Not enough order history for a statistically meaningful combo {selectedItemForCombo ? `with ${selectedItemForCombo}` : ''}.
                                            </div>
                                        ) : (
                                            comboRows.map((row, idx) => {
                                                const isSecondHalf = allComboRows.length > COMBO_ROWS_PER_SIDE * 2 && idx >= COMBO_ROWS_PER_SIDE;
                                                const rank = isSecondHalf ? idx - COMBO_ROWS_PER_SIDE + 1 : idx + 1;
                                                const liftPct = Math.round((row.lift - 1) * 100);
                                                const positive = row.lift >= 1;
                                                const barWidth = Math.min(100, Math.abs(liftPct));
                                                return (
                                                    <div key={`${row.label}-${idx}`} className="flex items-center gap-4 px-4 py-2.5 hover:bg-white/[0.03] transition-colors">
                                                        <span className="text-[10px] font-bold text-[var(--color-brand-faint)] uppercase w-6 flex-shrink-0">{isSecondHalf ? '↓' : '#'}{rank}</span>
                                                        <span className="font-semibold text-sm text-[var(--color-brand-text)] flex-1 truncate">{row.label}</span>
                                                        <span className="text-[10px] text-[var(--color-brand-faint)] flex-shrink-0 hidden md:inline">{row.support} orders</span>
                                                        <div className="w-24 h-1.5 bg-white/5 rounded-full overflow-hidden flex-shrink-0 hidden sm:block">
                                                            <div className="h-full rounded-full" style={{ width: `${barWidth}%`, background: positive ? `linear-gradient(90deg, ${C.emerald}, #6ee7b7)` : `linear-gradient(90deg, ${C.rose}, #fda4af)` }}></div>
                                                        </div>
                                                        <span className={`text-xs font-bold w-16 text-right flex-shrink-0 ${positive ? 'text-[var(--color-brand-emerald)]' : 'text-[var(--color-brand-rose)]'}`}>
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

            <section className="xl:col-span-1 flex flex-col h-[calc(100vh-150px)] min-w-0 animate-fade-up" style={{ animationDelay: '180ms' }}>
                <ChatInterface />
            </section>

        </div>
      </main>
    </div>
  );
}

export default App;
