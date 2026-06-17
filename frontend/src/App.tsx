import { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, ScatterChart, Scatter, ZAxis, ReferenceLine, ReferenceArea } from 'recharts';
import { Upload, TrendingUp, Pizza, Network, FileDown, Check, Sparkles } from 'lucide-react';
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
};

type ComboRecommendation = {
    name: string;
    prob: number;
};

const EMPTY_CROSS_SALES: CrossSalesMatrix = {
    index: [],
    columns: [],
    data: [],
};

// API Callers
const fetchStats = async () => (await axios.get('http://localhost:8000/api/v1/analytics/stats')).data;
const fetchForecast = async (): Promise<ForecastPoint[]> => {
    const hist = (await axios.get('http://localhost:8000/api/v1/analytics/history?days=14')).data;
    const fore = (await axios.get('http://localhost:8000/api/v1/analytics/forecast')).data;
    
    const merged: ForecastPoint[] = [];
    hist.forEach((h: any) => merged.push({ name: h.date, revenue: h.revenue != null ? Number(h.revenue) : null, expected: null }));
    fore.forEach((f: any) => merged.push({ name: f.date, revenue: null, expected: f.predicted_revenue != null ? Number(f.predicted_revenue) : null }));
    return merged;
};
const fetchMenu = async (): Promise<MenuItemPoint[]> => {
    const data = (await axios.get('http://localhost:8000/api/v1/analytics/menu')).data;

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
    const data = (await axios.get('http://localhost:8000/api/v1/analytics/associations')).data;

    return {
        index: Array.isArray(data?.index) ? data.index : [],
        columns: Array.isArray(data?.columns) ? data.columns : [],
        data: Array.isArray(data?.data)
            ? data.data.map((row: any) => (Array.isArray(row) ? row.map((value: any) => Number(value ?? 0)) : []))
            : [],
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

  // Queries
  const { data: stats, isLoading: statsLoading } = useQuery({ queryKey: ['stats'], queryFn: fetchStats });
  const { data: chartData = [], isLoading: chartLoading } = useQuery<ForecastPoint[]>({ queryKey: ['forecast'], queryFn: fetchForecast });
  const { data: menuData = [], isLoading: menuLoading } = useQuery<MenuItemPoint[]>({ queryKey: ['menu'], queryFn: fetchMenu });
  const { data: crossData = EMPTY_CROSS_SALES, isLoading: crossLoading } = useQuery<CrossSalesMatrix>({ queryKey: ['cross'], queryFn: fetchCrossSales });

  const getTopAssociations = (selectedItem: string): ComboRecommendation[] => {
    const itemIndex = crossData.index.indexOf(selectedItem);
    if (itemIndex === -1) {
        return [];
    }

    const row = crossData.data[itemIndex] ?? [];
    return crossData.columns
        .map((name, index) => ({
            name,
            prob: Number(row[index] ?? 0),
        }))
        .filter((assoc) => assoc.name !== selectedItem && Number.isFinite(assoc.prob) && assoc.prob > 0)
        .sort((a, b) => b.prob - a.prob)
        .slice(0, 3);
  };

  const topAssociations = selectedItemForCombo ? getTopAssociations(selectedItemForCombo) : [];

  const menuMeanX = menuData.length ? menuData.reduce((acc, d) => acc + d.popularity_sales, 0) / menuData.length : 0;
  const menuMeanY = menuData.length ? menuData.reduce((acc, d) => acc + d.avg_margin, 0) / menuData.length : 0;
  const menuMaxX = menuData.length ? Math.max(...menuData.map((d) => d.popularity_sales)) * 1.1 : 0;
  const menuMaxY = menuData.length ? Math.max(...menuData.map((d) => d.avg_margin)) * 1.1 : 0;


  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  // Mutations
  const seedMutation = useMutation({
      mutationFn: async (preset: string) => {
          await axios.post('http://localhost:8000/api/v1/upload/seed-demo', null, {
              params: { preset_name: preset }
          });
      },
      onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['stats'] });
          queryClient.invalidateQueries({ queryKey: ['forecast'] });
          queryClient.invalidateQueries({ queryKey: ['menu'] });
          queryClient.invalidateQueries({ queryKey: ['cross'] });
          setSelectedItemForCombo(null);
      }
  });

  const handlePresetChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      const preset = e.target.value;
      setActivePreset(preset);
      seedMutation.mutate(preset);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      setIsUploading(true);
      setUploadMessage("Uploading & Analyzing CSV...");
      
      const formData = new FormData();
      formData.append("file", file);

      try {
          await axios.post('http://localhost:8000/api/v1/upload/checks', formData, {
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
      window.open(`http://localhost:8000/api/v1/export/pdf?preset_name=${activePreset}`, '_blank');
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
            
            <section className="xl:col-span-2 flex flex-col gap-8">
                
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
                    <div className="bg-[var(--color-brand-card)] border border-rose-900/50 rounded-[16px] p-5 shadow-sm relative overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-br from-rose-500/10 to-transparent"></div>
                        <div className="text-[10px] font-bold text-rose-300 uppercase tracking-wider relative z-10">Avg Items/Order</div>
                        <div className="text-2xl font-extrabold text-white mt-1 relative z-10">
                            {statsLoading ? '...' : stats?.avg_items_per_check}
                        </div>
                    </div>
                </div>

                <div className="bg-[var(--color-brand-card)] border border-[var(--color-brand-border)] rounded-[20px] p-6 shadow-lg min-h-[500px] flex flex-col">
                    
                    {activeTab === 'forecast' && (
                        <>
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Revenue History & AI Forecast</h3>
                            </div>
                            <div className="flex-1 w-full pt-4">
                                {chartLoading ? (
                                    <div className="flex items-center justify-center h-full text-[var(--color-brand-muted)]">Loading metrics...</div>
                                ) : (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                        <defs>
                                            <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" vertical={false} />
                                        <XAxis dataKey="name" stroke="#94a3b8" tick={{fill: '#94a3b8', fontSize: 12}} tickLine={false} axisLine={false} />
                                        <YAxis stroke="#94a3b8" tick={{fill: '#94a3b8', fontSize: 12}} tickLine={false} axisLine={false} tickFormatter={(value) => `$${(value/1000).toFixed(0)}k`} />
                                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #2d3748', borderRadius: '8px', color: '#f1f5f9' }} itemStyle={{ color: '#e2e8f0' }} />
                                        <Area type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorRevenue)" name="Actual Revenue" />
                                        <Line type="monotone" dataKey="expected" stroke="#94a3b8" strokeWidth={2} strokeDasharray="5 5" dot={false} name="AI Forecast" />
                                        </AreaChart>
                                    </ResponsiveContainer>
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
                                                        stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} tickLine={false} axisLine={false}
                                                        label={{ value: 'Popularity (units sold)', position: 'insideBottom', offset: -20, fill: '#64748b', fontSize: 11 }}
                                                    />
                                                    <YAxis
                                                        type="number" dataKey="avg_margin" name="Margin"
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
                             <div className="flex justify-between items-center mb-6">
                                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Cross-Sales & Combos</h3>
                            </div>
                            <div className="flex-1 flex flex-col gap-6">
                                {crossLoading ? (
                                    <div className="flex items-center justify-center h-full text-[var(--color-brand-muted)]">Computing market basket analysis...</div>
                                ) : (
                                    <>
                                        <div className="bg-[#111827] border border-[var(--color-brand-border)] p-5 rounded-xl">
                                            <div className="flex items-center justify-between mb-4">
                                                <p className="text-sm text-[var(--color-brand-muted)]">Select a base item to view top associated products for combo deals:</p>
                                                {crossData?.index && crossData.index.length > 0 && (
                                                    <span className="text-[10px] font-bold text-[var(--color-brand-muted)] uppercase tracking-wider bg-[#0b0f19] border border-[var(--color-brand-border)] rounded-full px-2.5 py-1 flex-shrink-0">
                                                        {crossData.index.length} items
                                                    </span>
                                                )}
                                            </div>
                                            <div className="flex flex-wrap gap-2">
                                                {crossData?.index && crossData.index.length > 0 ? (
                                                    crossData.index.map((item: string) => {
                                                        const isSelected = selectedItemForCombo === item;
                                                        return (
                                                            <button
                                                                key={item}
                                                                onClick={() => setSelectedItemForCombo(item)}
                                                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${isSelected ? 'bg-[var(--color-brand-accent)] text-white border-[var(--color-brand-accent)] shadow-md' : 'bg-[var(--color-brand-card)] text-[var(--color-brand-muted)] border-[var(--color-brand-border)] hover:border-gray-500 hover:text-white'}`}
                                                            >
                                                                {isSelected && <Check size={12} />}
                                                                {item}
                                                            </button>
                                                        );
                                                    })
                                                ) : (
                                                    <p className="text-sm text-[var(--color-brand-muted)]">No items available for cross-sales analysis. Seed more data or check backend.</p>
                                                )}
                                            </div>
                                        </div>

                                        {selectedItemForCombo && (
                                            <div className="flex-1 bg-[var(--color-brand-card)] border border-indigo-900/50 p-6 rounded-xl relative overflow-hidden">
                                                 <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-transparent"></div>
                                                 <h4 className="text-lg font-bold text-white relative z-10 mb-1 flex items-center gap-2">
                                                     <Sparkles size={18} className="text-indigo-400" />
                                                     Combo Recommendations for: <span className="text-indigo-400">{selectedItemForCombo}</span>
                                                 </h4>
                                                 <p className="text-xs text-[var(--color-brand-muted)] relative z-10 mb-4">Customers who order this also order:</p>
                                                 {topAssociations.length > 0 ? (
                                                     <div className="grid grid-cols-1 md:grid-cols-3 gap-4 relative z-10">
                                                         {topAssociations.map((assoc, idx) => {
                                                             const pct = +(assoc.prob * 100).toFixed(1);
                                                             return (
                                                                 <div key={assoc.name} className="bg-[#0b0f19] border border-[var(--color-brand-border)] p-4 rounded-xl flex flex-col items-center text-center transition-transform hover:-translate-y-0.5 hover:border-indigo-700/50">
                                                                     <div className="text-2xl mb-2">{idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉'}</div>
                                                                     <p className="font-bold text-[var(--color-brand-text)] text-sm mb-2">{assoc.name}</p>
                                                                     <div className="w-full h-1.5 bg-[#1e293b] rounded-full overflow-hidden mb-1.5">
                                                                         <div className="h-full bg-emerald-400 rounded-full" style={{ width: `${Math.min(100, pct)}%` }}></div>
                                                                     </div>
                                                                     <p className="text-xs text-emerald-400 font-semibold">{pct}% co-occurrence</p>
                                                                 </div>
                                                             );
                                                         })}
                                                     </div>
                                                 ) : (
                                                     <div className="relative z-10 text-sm text-[var(--color-brand-muted)] flex items-center gap-2">
                                                         <Network size={16} /> No strong combo recommendations found for this item.
                                                     </div>
                                                 )}
                                            </div>
                                        )}
                                        {!selectedItemForCombo && (
                                            <div className="flex-1 flex flex-col items-center justify-center gap-3 text-[var(--color-brand-muted)] text-sm border-2 border-dashed border-[var(--color-brand-border)] rounded-xl">
                                                <Network size={28} className="opacity-40" />
                                                Select an item above to generate combo recommendations.
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>
                        </>
                    )}

                </div>
            </section>

            <section className="xl:col-span-1 flex flex-col h-[calc(100vh-140px)]">
                <ChatInterface />
            </section>

        </div>
      </main>
    </div>
  );
}

export default App;
