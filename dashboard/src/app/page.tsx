"use client";
// v1.0.2 - Restored Local Pipeline & Realtime

import { useEffect, useState, useMemo, useRef, useCallback } from "react";
import { supabase, Shop, DialogScore, AppStatus } from "@/lib/supabase";
import { Badge } from "@/components/ui/badge";
import { 
  Coffee, ShieldCheck, Clock, Volume2, PlayCircle, PauseCircle, 
  CheckCircle2, ChevronLeft, ChevronDown, ChevronUp, AlertTriangle, 
  TrendingUp, Loader2, BarChart3, Star, Calendar, SkipForward, 
  SkipBack, Maximize2 
} from "lucide-react";
import { 
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  CartesianGrid 
} from 'recharts';
import { ThemeToggle } from "@/components/theme-toggle";
import { useTheme } from "next-themes";

// Global Styles for branding and scrollbars
const fontImport = `
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,900;1,900&display=swap');
`;

// Helper: returns YYYY-MM-DD in LOCAL timezone (not UTC)
function getLocalDateStr(d: Date = new Date()): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export default function Dashboard() {
  const { theme, systemTheme } = useTheme();
  const currentTheme = theme === 'system' ? systemTheme : theme;
  const isDark = currentTheme !== 'light';

  const [shops, setShops] = useState<Shop[]>([]);
  const [allDialogs, setAllDialogs] = useState<DialogScore[]>([]);
  const [selectedShopId, setSelectedShopId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedDialogId, setExpandedDialogId] = useState<number | null>(null); 
  const [appStatus, setAppStatus] = useState<AppStatus | null>(null);
  const [view, setView] = useState<string>("dashboard"); // 'dashboard', 'admin'
  const [telemetry, setTelemetry] = useState<any[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>(getLocalDateStr());
  const [activeDialog, setActiveDialog] = useState<DialogScore | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
    const [activePhraseIndex, setActivePhraseIndex] = useState<number | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  
  useEffect(() => {
    setIsMounted(true);
  }, []);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const transcriptRefs = useRef<(HTMLDivElement | null)[]>([]);

  // 1. Core Functions
  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) audioRef.current.pause();
      else audioRef.current.play().catch(() => {});
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current && activeDialog?.transcript) {
      const time = audioRef.current.currentTime;
      setCurrentTime(time);
      let index = -1;
      for (let i = 0; i < activeDialog.transcript.length; i++) {
        if (time >= activeDialog.transcript[i].start) {
          index = i;
        } else {
          break;
        }
      }
      if (index !== -1 && index !== activePhraseIndex) {
        setActivePhraseIndex(index);
      }
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) setDuration(audioRef.current.duration);
  };

  const playPhrase = (dialog: DialogScore, startTime: number) => {
    try {
      if (activeDialog?.id !== dialog.id) {
        setActiveDialog(dialog);
        setActivePhraseIndex(null);
        const timer = setTimeout(() => {
          if (audioRef.current) {
            audioRef.current.currentTime = startTime;
            audioRef.current.play().catch(() => {});
            setIsPlaying(true);
          }
        }, 300);
        return () => clearTimeout(timer);
      } else if (audioRef.current) {
        audioRef.current.currentTime = startTime;
        audioRef.current.play().catch(() => {});
        setIsPlaying(true);
      }
    } catch (e) {
      console.warn('playPhrase error:', e);
    }
  };

  useEffect(() => {
    if (activePhraseIndex !== null && transcriptRefs.current[activePhraseIndex]) {
      transcriptRefs.current[activePhraseIndex]?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [activePhraseIndex]);

  const formatTime = (time: number) => {
    const mins = Math.floor(time / 60);
    const secs = Math.floor(time % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const translateTag = (tag: string) => {
    const map: Record<string, string> = {
      'cross_sales_score': 'Кросс-селл',
      'upsell_score': 'Апселл',
      'christmas_tree_score': 'Помощь в выборе',
      'promo_score': 'Акция',
      'loyalty_score': 'Лояльность',
      'order_duplication_score': 'Дубл. заказа',
      'live_service_score': 'Живой сервис'
    };
    return map[tag.toLowerCase()] || tag;
  };

  const translateSpeaker = (speaker: string) => {
    if (!speaker) return "";
    return speaker
      .replace('Barista', 'Бариста')
      .replace('Customer', 'Клиент')
      .replace('(F)', '(Ж)')
      .replace('(M)', '(М)');
  };

  // 2. Data Fetching
  const loadData = useCallback(async (isSilent = false) => {
    try {
      if (!isSilent) setLoading(true);
      const startOfDay = selectedDate + 'T00:00:00.000Z';
      const endOfDay = selectedDate + 'T23:59:59.999Z';

      let query = supabase.from("dialogs").select("*");
      query = query.gte("created_at", startOfDay).lte("created_at", endOfDay);

      const { data: shopsData, error: shopsErr } = await supabase.from("shops").select("*").order("name");
      if (shopsErr) console.error("shops error:", shopsErr);
      
      const monthAgo = new Date();
      monthAgo.setDate(monthAgo.getDate() - 30);
      const { data: allMonthDialogs, error: dialogsErr } = await supabase.from("dialogs").select("*").gte("created_at", monthAgo.toISOString()).order("created_at", { ascending: false });
      if (dialogsErr) console.error("dialogs error:", dialogsErr);

      const { data: statusData, error: statusErr } = await supabase.from("app_status").select("*").eq("id", 1).single();
      if (statusErr && statusErr.code !== 'PGRST116') console.error("status error:", statusErr);
      
      const { data: telemetryData, error: telemetryErr } = await supabase.from("agent_telemetry").select("*").order("id");
      if (telemetryErr) console.error("telemetry error:", telemetryErr);
      
      if (shopsData) setShops(shopsData);
      if (allMonthDialogs) setAllDialogs(allMonthDialogs);
      if (statusData) setAppStatus(statusData);
      if (telemetryData) setTelemetry(telemetryData);
    } catch (err) {
      console.error("Unhandled error in loadData:", err);
    } finally {
      setLoading(false);
    }
  }, [selectedDate]);

  useEffect(() => {
    loadData();

    // 1. Realtime Telemetry
    const telemetryChannel = supabase
      .channel("agent_telemetry_changes")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "agent_telemetry" },
        (payload) => {
          setTelemetry((current) => 
            current.map(agent => agent.agent_name === (payload.new as any).agent_name ? payload.new : agent)
          );
        }
      )
      .subscribe();

    // 2. Realtime Dialogs (New analysis results)
    const dialogsChannel = supabase
      .channel("dialogs_changes")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "dialogs" },
        () => {
          console.log("New dialog detected, refreshing...");
          loadData(true); // Silent refresh
        }
      )
      .subscribe();

    // 3. Realtime App Status (Pipeline progress)
    const statusChannel = supabase
      .channel("status_changes")
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "app_status" },
        (payload) => {
          setAppStatus(payload.new as AppStatus);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(telemetryChannel);
      supabase.removeChannel(dialogsChannel);
      supabase.removeChannel(statusChannel);
    };
  }, [loadData]);

  // 3. Computed Analytics
  const getDialogPercent = (dialog: DialogScore) => {
    const details = (dialog.audit_details as any);
    if (!details) return 0;
    if (details.dialogue_type === 'dialog') return 0;
    if (details.is_conflict) return 0;

    const sum = (details.cross_sales_score || 0) + 
                (details.upsell_score || 0) + 
                (details.christmas_tree_score || 0) + 
                (details.promo_score || 0) + 
                (details.loyalty_score || 0) + 
                (details.order_duplication_score || 0);
    
    return Math.round((sum / 600) * 100);
  };

  const filteredDialogs = useMemo(() => {
    // Filter by selected date and sort chronologically
    return allDialogs
      .filter(d => d.created_at?.startsWith(selectedDate))
      .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
  }, [allDialogs, selectedDate]);

  const networkTrend = useMemo(() => {
    const dates: Record<string, { date: string, score: number, count: number }> = {};
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const s = getLocalDateStr(d);
      const label = d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
      dates[s] = { date: label, score: 0, count: 0 };
    }
    allDialogs.forEach(d => {
      const s = d.created_at.split('T')[0];
      if (dates[s]) {
        dates[s].score += getDialogPercent(d);
        dates[s].count += 1;
      }
    });
    return Object.values(dates).map(v => ({
      name: v.date,
      Оценка: v.count > 0 ? Math.round(v.score / v.count) : 0
    }));
  }, [allDialogs]);

  const networkPerformance = useMemo(() => {
    const stats: Record<string, { total: number, count: number }> = {
      'cross_sales_score': { total: 0, count: 0 },
      'upsell_score': { total: 0, count: 0 },
      'christmas_tree_score': { total: 0, count: 0 },
      'promo_score': { total: 0, count: 0 },
      'loyalty_score': { total: 0, count: 0 },
      'order_duplication_score': { total: 0, count: 0 }
    };
    filteredDialogs.forEach(d => {
      const details = (d as any).audit_details;
      if (details) {
        Object.entries(details).forEach(([key, val]) => {
          if (stats[key]) {
            stats[key].total += val as number;
            stats[key].count += 1;
          }
        });
      }
    });
    return Object.entries(stats).map(([key, val]) => ({
      key,
      name: translateTag(key),
      percent: val.count > 0 ? Math.round(val.total / val.count) : 0
    })).sort((a, b) => a.percent - b.percent);
  }, [filteredDialogs]);

  const shopSummaries = useMemo(() => {
    return shops
      .filter(shop => shop.name !== 'Офис работников' && shop.name !== 'Офис')
      .map(shop => {
        const shopDialogs = filteredDialogs.filter(d => d.shop_id === shop.id && (d.audit_details as any)?.dialogue_type !== 'dialog');
        const avgScorePercent = shopDialogs.length > 0
          ? Math.round(shopDialogs.reduce((acc, curr) => acc + getDialogPercent(curr), 0) / shopDialogs.length)
          : 0;

        // Weekly comparison for shop card chart
        const weekAgo = new Date(); weekAgo.setDate(weekAgo.getDate() - 7);
        const weeklyDialogs = allDialogs.filter(d => d.shop_id === shop.id && new Date(d.created_at) >= weekAgo && (d.audit_details as any)?.dialogue_type !== 'dialog');
        const weeklyAvgPercent = weeklyDialogs.length > 0
          ? Math.round(weeklyDialogs.reduce((acc, curr) => acc + getDialogPercent(curr), 0) / weeklyDialogs.length)
          : 0;

        const tagMap: Record<string, number> = {};
        shopDialogs.forEach(d => {
          const tags = Array.isArray(d.tags) ? d.tags : [];
          tags.forEach((tag: string) => {
            tagMap[tag] = (tagMap[tag] || 0) + 1;
          });
        });
        const topProblems = Object.entries(tagMap)
          .sort(([, a], [, b]) => b - a)
          .slice(0, 3)
          .map(([name]) => name);

        return {
          ...shop,
          count: shopDialogs.length,
          avgScorePercent,
          weeklyAvgPercent,
          topProblems
        };
      })
      .sort((a, b) => b.avgScorePercent - a.avgScorePercent);
  }, [shops, filteredDialogs, allDialogs]);

  const monthlyAnalytics = useMemo(() => {
    // allDialogs represents last 30 days
    const activeDialogs = allDialogs.filter(d => (d.audit_details as any)?.dialogue_type !== 'dialog');

    let missedUpsell = 0;
    let missedCrossSell = 0;
    let missedLoyalty = 0;
    
    activeDialogs.forEach(d => {
      const details = d.audit_details as any;
      if (details.upsell_score === 0) missedUpsell++;
      if (details.cross_sales_score === 0) missedCrossSell++;
      if (details.loyalty_score === 0) missedLoyalty++;
    });

    const lostRevenue = (missedUpsell * 80) + (missedCrossSell * 350) + (missedLoyalty * 600);

    const stats: Record<string, { total: number, count: number }> = {
      'cross_sales_score': { total: 0, count: 0 },
      'upsell_score': { total: 0, count: 0 },
      'christmas_tree_score': { total: 0, count: 0 },
      'promo_score': { total: 0, count: 0 },
      'loyalty_score': { total: 0, count: 0 },
      'order_duplication_score': { total: 0, count: 0 }
    };

    activeDialogs.forEach(d => {
      const details = d.audit_details as any;
      Object.entries(details).forEach(([key, val]) => {
        if (stats[key] !== undefined && typeof val === 'number') {
          stats[key].total += val;
          stats[key].count += 1;
        }
      });
    });
    
    let worstMetric = { key: '', name: '', percent: 100 };
    Object.entries(stats).forEach(([key, val]) => {
       const percent = val.count > 0 ? (val.total / val.count) : 0;
       if (percent < worstMetric.percent && val.count > 0) {
          worstMetric = { key, name: translateTag(key), percent: Math.round(percent) };
       }
    });

    const shiftStats: Record<string, { stars: number, totalRaw: number, count: number, name: string, date: string }> = {};
    activeDialogs.forEach(d => {
       const dateStr = d.created_at.split('T')[0];
       const shiftKey = `${d.shop_id}_${dateStr}`;
       if (!shiftStats[shiftKey]) {
          const shopName = shops.find(s => s.id === d.shop_id)?.name || 'Неизвестно';
          shiftStats[shiftKey] = { stars: 0, totalRaw: 0, count: 0, name: shopName, date: dateStr };
       }
       if ((d.audit_details as any)?.live_service_score >= 100) shiftStats[shiftKey].stars += 1;
       shiftStats[shiftKey].totalRaw += getDialogPercent(d);
       shiftStats[shiftKey].count += 1;
    });
    
    const rankedShifts = Object.values(shiftStats)
       .map(s => ({ ...s, percent: Math.round(s.totalRaw / s.count) }))
       .sort((a, b) => b.stars - a.stars || b.percent - a.percent)
       .slice(0, 3);

    let networkTotal = 0;
    activeDialogs.forEach(d => networkTotal += getDialogPercent(d));
    const networkAvgPercentMonth = activeDialogs.length > 0 ? Math.round(networkTotal / activeDialogs.length) : 0;

    return { missedUpsell, missedCrossSell, missedLoyalty, lostRevenue, worstMetric, rankedShifts, networkAvgPercentMonth, totalDialogs: activeDialogs.length };
  }, [allDialogs, shops]);

  const shopDetails = useMemo(() => {
    if (!selectedShopId) return [];
    return filteredDialogs.filter(d => d.shop_id === selectedShopId);
  }, [selectedShopId, filteredDialogs]);

  const shopPerformanceStats = useMemo(() => {
    if (!selectedShopId) return [];
    const stats: Record<string, { total: number, count: number, violations: number }> = {
      'cross_sales_score': { total: 0, count: 0, violations: 0 },
      'upsell_score': { total: 0, count: 0, violations: 0 },
      'christmas_tree_score': { total: 0, count: 0, violations: 0 },
      'promo_score': { total: 0, count: 0, violations: 0 },
      'loyalty_score': { total: 0, count: 0, violations: 0 },
      'order_duplication_score': { total: 0, count: 0, violations: 0 }
    };
    shopDetails.forEach(d => {
      const details = (d as any).audit_details;
      if (details) {
        Object.entries(details).forEach(([key, val]) => {
          if (stats[key]) {
            stats[key].total += val as number;
            stats[key].count += 1;
            if ((val as number) === 0) stats[key].violations += 1;
          }
        });
      }
    });
    return Object.entries(stats).map(([key, val]) => ({
      key,
      name: translateTag(key),
      percent: val.count > 0 ? Math.round(val.total / val.count) : 0,
      violations: val.violations
    }));
  }, [shopDetails, selectedShopId]);

  const selectedShopSummary = shopSummaries.find(s => s.id === selectedShopId);

  // 4. Render Logic
  if (!isMounted) return null;
  
  if (loading && shops.length === 0) {
    return (
      <main className="min-h-screen bg-black text-zinc-900 dark:text-white flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-zinc-900 border-t-white rounded-full animate-spin"></div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-zinc-50 dark:bg-[#050505] text-zinc-900 dark:text-zinc-900 dark:text-white pb-32 font-sans selection:bg-black/10 dark:selection:bg-white/20 antialiased overflow-x-hidden transition-colors duration-300">
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_top_right,_#101524_0%,_transparent_40%)] pointer-events-none opacity-20 dark:opacity-50"></div>
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_bottom_left,_#0a1510_0%,_transparent_40%)] pointer-events-none opacity-10 dark:opacity-30"></div>
      
      <div className="max-w-6xl mx-auto px-6 pt-12 relative z-10">
                    <header className="mb-12 flex items-center justify-between border-b border-black/5 dark:border-white/5 pb-10 relative">
               <div className="flex items-center gap-4 relative z-20">
                  <style dangerouslySetInnerHTML={{ __html: fontImport }} />
                  <div className="text-4xl tracking-tighter flex items-center gap-1 select-none" id="logo-dashboard-view">
                    <span className="font-sans font-medium text-zinc-500">talk:</span>
                    <span className="font-mono font-black text-zinc-900 dark:text-white tracking-[0.15em] bg-black/5 dark:bg-white/5 px-3 py-1 rounded-lg border border-black/10 dark:border-white/10 text-2xl shadow-[0_0_20px_rgba(255,255,255,0.05)]">core</span>
                  </div>
               </div>
               
               {/* Mobile Action Bar */}
               <div className="flex md:hidden items-center gap-2 relative z-20">
                  {selectedShopId && (
                    <button onClick={() => setSelectedShopId(null)} className="p-2 border border-black/5 dark:border-white/5 rounded-lg active:scale-95 transition-transform"><ChevronLeft size={20}/></button>
                  )}
                  {!selectedShopId && (
                    <>
                       {/* Compact Date Picker for Mobile */}
                       <div className="relative">
                          <button onClick={(e) => { const input = e.currentTarget.nextElementSibling as HTMLInputElement; input?.showPicker(); }} className="flex items-center justify-center bg-zinc-100 dark:bg-zinc-900 border border-black/5 dark:border-white/5 rounded-lg w-10 h-10">
                            <Calendar size={18} className="text-zinc-600 dark:text-zinc-400" />
                          </button>
                          <input 
                            type="date" 
                            value={selectedDate}
                            onChange={(e) => { setSelectedDate(e.target.value); setView('dashboard'); }}
                            className="absolute opacity-0 w-0 h-0"
                          />
                       </div>
                       
                       <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="flex items-center justify-center bg-zinc-100 dark:bg-zinc-900 border border-black/5 dark:border-white/5 rounded-lg w-10 h-10">
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-zinc-900 dark:text-white"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
                       </button>
                    </>
                  )}
               </div>

               {/* Desktop Nav */}
               <div className="hidden md:flex items-center gap-6">
                  <div className="flex items-center gap-6">
                     <div className="flex bg-zinc-100 dark:bg-[#0c0d12] p-1 rounded-xl border border-black/5 dark:border-white/5">
                        <button 
                          onClick={() => { setView('dashboard'); setSelectedShopId(null); }}
                          className={`px-5 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${(view === 'dashboard' && !selectedShopId) ? 'bg-white dark:bg-zinc-800 text-black dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'}`}
                        >
                          Дашборд
                        </button>
                        <button 
                          onClick={() => { setView('analytics'); setSelectedShopId(null); }}
                          className={`px-5 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${(view === 'analytics' && !selectedShopId) ? 'bg-white dark:bg-zinc-800 text-black dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'}`}
                        >
                          Отчет
                        </button>
                        <button 
                          onClick={() => { setView('admin'); setSelectedShopId(null); }}
                          className={`px-5 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${(view === 'admin' && !selectedShopId) ? 'bg-white dark:bg-zinc-800 text-black dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'}`}
                        >
                          Офис
                        </button>
                       </div>

                       <div className="w-px h-6 bg-black/5 dark:bg-white/5"></div>
                       <ThemeToggle />
                       <div className="w-px h-6 bg-black/5 dark:bg-white/5"></div>

                       <div className="flex items-center gap-2 text-[10px] font-bold text-zinc-600 uppercase tracking-widest whitespace-nowrap">
                          <Calendar size={12} /> Архив
                       </div>
                       <div className="relative flex items-center">
                          <input 
                            type="date" 
                            value={selectedDate}
                            onClick={(e) => (e.target as HTMLInputElement).showPicker()}
                            onChange={(e) => { setSelectedDate(e.target.value); setView('dashboard'); }}
                            className="bg-white dark:bg-[#0c0d12] border border-black/5 dark:border-white/5 rounded-xl px-4 py-2 flex items-center text-[11px] font-bold uppercase text-zinc-600 dark:text-zinc-400 focus:outline-none [color-scheme:light] dark:[color-scheme:dark] cursor-pointer"
                          />
                       </div>
                     </div>

                     {selectedShopId && (
                        <button 
                          onClick={() => setSelectedShopId(null)}
                          className="flex items-center gap-2 bg-zinc-100 dark:bg-zinc-900 hover:bg-zinc-200 dark:hover:bg-zinc-800 px-5 py-3 rounded-xl border border-black/5 dark:border-white/10 transition-all text-xs font-bold uppercase tracking-widest text-zinc-900 dark:text-white group shadow-sm"
                        >
                          <ChevronLeft size={16} className="group-hover:-translate-x-1 transition-transform" /> Назад
                        </button>
                     )}
               </div>
               
               {/* Dropdown Mobile Menu */}
               {isMobileMenuOpen && !selectedShopId && (
                  <div className="absolute top-full left-0 right-0 mt-4 bg-white dark:bg-zinc-900 border border-black/10 dark:border-white/10 rounded-2xl p-4 shadow-2xl z-50 flex flex-col md:hidden animate-in fade-in slide-in-from-top-4">
                     <div className="flex flex-col gap-2 mb-4">
                       <button onClick={() => {setView('dashboard'); setIsMobileMenuOpen(false);}} className={`text-left px-4 py-3 rounded-xl font-bold ${view === 'dashboard' ? 'bg-zinc-100 dark:bg-black/20 text-black dark:text-white' : 'text-zinc-600 dark:text-zinc-400'}`}>Дашборд</button>
                       <button onClick={() => {setView('analytics'); setIsMobileMenuOpen(false);}} className={`text-left px-4 py-3 rounded-xl font-bold ${view === 'analytics' ? 'bg-zinc-100 dark:bg-black/20 text-black dark:text-white' : 'text-zinc-600 dark:text-zinc-400'}`}>Отчет за месяц</button>
                       <button onClick={() => {setView('admin'); setIsMobileMenuOpen(false);}} className={`text-left px-4 py-3 rounded-xl font-bold ${view === 'admin' ? 'bg-zinc-100 dark:bg-black/20 text-black dark:text-white' : 'text-zinc-600 dark:text-zinc-400'}`}>Офис</button>
                     </div>
                     <div className="w-full h-px bg-black/5 dark:bg-white/5 my-2"></div>
                     <div className="flex items-center justify-between p-2">
                        <span className="font-bold text-sm text-zinc-600 dark:text-white">Смена темы</span>
                        <ThemeToggle />
                     </div>
                  </div>
               )}
            </header>

                        {view === 'admin' ? (
              <div className="space-y-12 animate-in fade-in slide-in-from-bottom-10 duration-700">
                <div className="flex items-center justify-between">
                   <h2 className="text-3xl font-black tracking-tighter flex items-center gap-3 text-zinc-900 dark:text-white">
                      <ShieldCheck className="text-indigo-500" /> Офис агентов (Служба оркестрации)
                   </h2>
                </div>
              
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                   {/* OFFICE ZONE */}
                   <div className="bg-[#2a2d34] dark:bg-[#1a1c23] border-4 border-zinc-700/50 rounded-3xl p-8 relative shadow-2xl flex flex-col">
                      <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/black-scales.png')] opacity-20 pointer-events-none"></div>
                      <h3 className="text-xl font-black uppercase tracking-[0.2em] text-white/50 mb-10 text-center relative z-10 border-b-2 border-white/10 pb-4">
                         🏢 Секретный Офис (Work Zone)
                      </h3>
                      
                      <div className="flex-1 grid grid-cols-2 gap-6 relative z-10">
                         {/* Supervisor Desk (Always occupied by Boss) */}
                         <div className="col-span-2 bg-gradient-to-b from-orange-500/20 to-black/40 border-2 border-orange-500/50 rounded-2xl p-6 flex items-center justify-between relative overflow-hidden shadow-[0_0_30px_rgb(249,115,22,0.1)]">
                            <div className="absolute -right-4 -top-4 w-24 h-24 bg-orange-500/20 rounded-full blur-2xl"></div>
                            <div>
                               <h4 className="text-orange-500 font-bold uppercase tracking-widest text-xs mb-1">Надзиратель</h4>
                               <div className="text-white font-black text-xl flex items-center gap-3">
                                  <span className="text-3xl">🐢</span> Микеланджело
                               </div>
                            </div>
                            <div className="bg-black/40 px-4 py-2 rounded-lg border border-white/10 text-xs font-mono text-emerald-400 animate-pulse">
                               СЛЕДИТ ЗА ПОРЯДКОМ
                            </div>
                         </div>

                         {/* 3 Computers */}
                         {[
                            { name: "Audio Diarization Agent", role: "Диаризатор", turtle: "Леонардо", color: "blue", emoji: "🐢", mask: "from-blue-500/20 to-black/40", border: "border-blue-500/50", glow: "bg-blue-500/20" },
                            { name: "Diarization Editor", role: "Редактор", turtle: "Донателло", color: "purple", emoji: "🐢", mask: "from-purple-500/20 to-black/40", border: "border-purple-500/50", glow: "bg-purple-500/20" },
                            { name: "QA Analyst", role: "QA Аналитик", turtle: "Рафаэль", color: "red", emoji: "🐢", mask: "from-red-500/20 to-black/40", border: "border-red-500/50", glow: "bg-red-500/20" }
                         ].map((desk, idx) => {
                            const agentIsBusy = telemetry.find(t => t.agent_name === desk.name && t.status === 'BUSY');
                            
                            return (
                               <div key={idx} className={`relative flex flex-col items-center justify-center p-6 border-2 rounded-2xl backdrop-blur-sm transition-all duration-500 ${agentIsBusy ? desk.mask + ' ' + desk.border + ' shadow-[0_0_20px_rgb(255,255,255,0.05)]' : 'bg-black/40 border-black/50 opacity-60 grayscale'}`}>
                                  {agentIsBusy && <div className={`absolute -inset-2 ${desk.glow} rounded-3xl blur-2xl -z-10`}></div>}
                                  
                                  <div className="text-zinc-600 mb-4">
                                     <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
                                  </div>
                                  
                                  {agentIsBusy ? (
                                     <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center animate-bounce">
                                        <span className="text-4xl filter drop-shadow-lg">{desk.emoji}</span>
                                        <span className={`text-xs font-black uppercase mt-2 px-2 py-1 bg-black/80 rounded border ${desk.border} text-white`}>{desk.turtle}</span>
                                     </div>
                                  ) : (
                                     <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">{desk.role}</span>
                                  )}

                                  {agentIsBusy && (
                                     <div className="absolute -top-4 bg-black/80 border border-white/20 text-white text-[9px] px-3 py-1 rounded-full whitespace-nowrap overflow-hidden max-w-[90%] text-ellipsis">
                                        {(agentIsBusy.active_task || "Обработка аудио...").substring(0, 20)}...
                                     </div>
                                  )}
                               </div>
                            )
                         })}
                      </div>
                   </div>
              
                   {/* CHILL ZONE */}
                   <div className="bg-[#1a1c23] dark:bg-[#111216] border-4 border-zinc-800/80 rounded-3xl p-8 relative shadow-inner overflow-hidden flex flex-col">
                      <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/brick-wall.png')] opacity-[0.03] pointer-events-none"></div>
                      <h3 className="text-xl font-black uppercase tracking-[0.2em] text-zinc-500 mb-10 text-center relative z-10 border-b-2 border-zinc-800 pb-4">
                         🍕 Чилл-Зона (Idle)
                      </h3>
                      
                      <div className="flex-1 flex flex-wrap content-start gap-4 relative z-10 p-6 bg-black/20 rounded-2xl border border-white/5">
                         {[
                            { name: "Audio Diarization Agent", turtle: "Леонардо", emoji: "🐢", colorText: "text-blue-500", bg: "bg-blue-500/10" },
                            { name: "Diarization Editor", turtle: "Донателло", emoji: "🐢", colorText: "text-purple-500", bg: "bg-purple-500/10" },
                            { name: "QA Analyst", turtle: "Рафаэль", emoji: "🐢", colorText: "text-red-500", bg: "bg-red-500/10" }
                         ].map((desk, idx) => {
                            const isChilling = !telemetry.find(t => t.agent_name === desk.name && t.status === 'BUSY');
                            if (!isChilling) return null;

                            return (
                               <div key={idx} className={`flex items-center gap-4 ${desk.bg} border-l-4 border-current ${desk.colorText} p-4 rounded-r-xl w-full hover:scale-[1.02] transition-transform cursor-default`}>
                                  <div className="text-3xl relative">
                                     {desk.emoji}
                                     <span className="absolute -top-1 -right-2 text-xl animate-pulse">🍕</span>
                                  </div>
                                  <div>
                                     <h4 className="font-black uppercase tracking-widest text-sm text-white">{desk.turtle}</h4>
                                     <p className="text-[10px] font-bold text-zinc-500 uppercase">Смотрит телик / Waiting</p>
                                  </div>
                               </div>
                            )
                         })}
                         
                         {telemetry.filter(t => t.status === 'BUSY').length === 3 && (
                            <div className="text-zinc-600 text-sm italic py-10 text-center w-full">Чилл-зона пуста. Все ебашат!</div>
                         )}
                      </div>
                   </div>
                </div>
              </div>
            ) : view === 'analytics' ? (
              /* VIEW 3: Analytics View */
              <div className="space-y-12 animate-in fade-in slide-in-from-bottom-10 duration-700">
                 <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Month Summary Card */}
                    <div className="bg-white dark:bg-[#0f1115]/80 border border-emerald-500/20 rounded-2xl p-10 flex flex-col justify-between shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-2xl relative overflow-hidden">
                       <div className="absolute -right-20 -bottom-20 w-64 h-64 bg-emerald-500/10 blur-[100px] rounded-full pointer-events-none"></div>
                       <div className="relative z-10">
                          <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-emerald-500 mb-8 flex items-center gap-2">
                            <TrendingUp size={14} /> Производительность сети
                          </h3>
                          <div className="text-7xl font-black italic tracking-tighter text-zinc-900 dark:text-white mb-2">
                             {monthlyAnalytics.networkAvgPercentMonth}%
                          </div>
                          <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest">за 30 дней ({monthlyAnalytics.totalDialogs} диалогов)</p>
                       </div>
                    </div>

                    {/* Lost Revenue Card */}
                    <div className="lg:col-span-2 bg-white dark:bg-[#0a0505]/80 border border-rose-500/20 rounded-2xl p-10 flex flex-col justify-between shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-2xl relative overflow-hidden">
                       <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-l from-rose-500/5 to-transparent pointer-events-none"></div>
                       <div className="relative z-10 flex flex-col lg:flex-row justify-between lg:items-end gap-10">
                          <div>
                             <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-rose-500 mb-8 flex items-center gap-2">
                               <AlertTriangle size={14} /> Упущенная выгода (LTV + Продажи)
                             </h3>
                             <div className="text-6xl font-black italic tracking-tighter text-rose-500 mb-3">
                               -{monthlyAnalytics.lostRevenue.toLocaleString('ru-RU')} ₽
                             </div>
                             
                          </div>
                          <div className="flex flex-col md:flex-row bg-rose-50/50 dark:bg-[#140b0b] rounded-xl border border-rose-500/10 p-5 gap-8">
                             <div className="flex flex-col gap-2">
                               <span className="text-[9px] font-bold text-rose-500/60 uppercase tracking-widest">Без доп. продажи</span>
                               <span className="text-xl font-bold text-rose-500">{monthlyAnalytics.missedUpsell}</span>
                             </div>
                             <div className="w-px bg-black/5 dark:bg-white/5"></div>
                             <div className="flex flex-col gap-2">
                               <span className="text-[9px] font-bold text-rose-500/60 uppercase tracking-widest">Без кросс-селла</span>
                               <span className="text-xl font-bold text-rose-500">{monthlyAnalytics.missedCrossSell}</span>
                             </div>
                          </div>
                       </div>
                    </div>
                 </div>

                 <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Weakest Point */}
                    <div className="bg-white dark:bg-[#0c0d12]/60 border border-black/5 dark:border-white/5 rounded-2xl p-10">
                       <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 mb-8 flex items-center gap-2">
                         ГЛАВНАЯ ТОЧКА РОСТА
                       </h3>
                       <div className="flex items-center justify-between mb-4">
                          <span className="text-3xl font-black tracking-tighter text-zinc-900 dark:text-white">{monthlyAnalytics.worstMetric.name || 'Нет данных'}</span>
                          <span className="text-2xl font-bold text-rose-500/80">{monthlyAnalytics.worstMetric.percent}%</span>
                       </div>
                       <div className="h-2 w-full bg-black/40 rounded-full overflow-hidden">
                          <div className="h-full bg-rose-500/50" style={{ width: `${monthlyAnalytics.worstMetric.percent}%` }}></div>
                       </div>
                       <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mt-6">
                         Требуется дополнительное обучение персонала по этому стандарту взаимодействия.
                       </p>
                    </div>

                    {/* Best Shifts */}
                    <div className="bg-white dark:bg-[#0c0d12]/60 border border-black/5 dark:border-white/5 rounded-2xl p-10">
                       <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 mb-8 flex items-center gap-2">
                         <Star size={14} className="text-amber-500" /> ЛУЧШИЕ СМЕНЫ МЕСЯЦА
                       </h3>
                       <div className="space-y-4">
                          {monthlyAnalytics.rankedShifts.map((shift, idx) => (
                             <div key={idx} className="flex items-center justify-between bg-white/[0.02] p-4 rounded-xl border border-black/5 dark:border-white/5">
                                <div className="flex items-center gap-4">
                                   <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-black ${idx === 0 ? 'bg-amber-500 text-black' : 'bg-zinc-200 dark:bg-zinc-800 text-zinc-900 dark:text-white'}`}>
                                      {idx + 1}
                                   </div>
                                   <div>
                                      <div className="text-sm font-bold">{shift.name}</div>
                                      <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">{new Date(shift.date).toLocaleDateString('ru-RU')} • {shift.count} диалогов</div>
                                   </div>
                                </div>
                                <span className="text-xl font-black italic text-emerald-500/80">{shift.percent}%</span>
                             </div>
                          ))}
                       </div>
                    </div>
                 </div>
              </div>
            ) : !selectedShopId ? (
              /* VIEW 1: Network View */
              <div className="space-y-12">
                 <div className="flex gap-4 overflow-x-auto py-6 -my-6 px-6 -mx-6 custom-scrollbar touch-pan-x snap-x snap-mandatory" onWheel={(e) => { e.currentTarget.scrollLeft += e.deltaY * 1.5;  }}>
                    {Array.from({length: 7}).map((_, i) => {
                       const d = new Date();
                       d.setDate(d.getDate() - i);
                       const dateStr = getLocalDateStr(d);
                       const displayDate = d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
                       
                       const dayDialogs = allDialogs.filter(dx => dx.created_at?.startsWith(dateStr) && (dx.audit_details as any)?.dialogue_type !== 'dialog');
                       let total = 0;
                       dayDialogs.forEach(dx => total += getDialogPercent(dx));
                       const avg = dayDialogs.length > 0 ? (total / dayDialogs.length).toFixed(1) : '--';

                       const isSelected = selectedDate === dateStr;

                       return (
                          <button 
                            key={dateStr}
                            onClick={() => { setSelectedDate(dateStr); setView('dashboard'); }}
                            className={`snap-center flex-shrink-0 flex flex-col justify-between p-4 rounded-3xl border transition-all h-24 w-40 text-left cursor-pointer
                              ${isSelected 
                                ? 'bg-zinc-900 dark:bg-white border-transparent shadow-xl' 
                                : 'bg-white dark:bg-[#0c0d12] hover:bg-zinc-100 dark:bg-zinc-900 border-black/5 dark:border-white/5'}`}
                          >
                             <span className={`text-[10px] font-bold ${isSelected ? 'text-white dark:text-black' : 'text-zinc-500'}`}>{displayDate}</span>
                             <div className="flex justify-between items-end mt-4">
                                <span className={`text-xl font-black tracking-tighter ${isSelected ? 'text-white dark:text-black' : 'text-zinc-900 dark:text-white'}`}>{avg}</span>
                                <span className={`text-[8px] font-bold uppercase tracking-widest ${isSelected ? 'text-white/60 dark:text-black/60' : 'text-zinc-500 dark:text-zinc-600'}`}>{dayDialogs.length} диалогов</span>
                             </div>
                          </button>
                       );
                    })}
                 </div>
                 <section className="bg-white dark:bg-[#0c0d12]/60 border border-black/5 dark:border-white/5 rounded-2xl overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-2xl backdrop-blur-xl">
                    <div className="p-10 border-b border-black/5 dark:border-white/5 bg-gradient-to-br from-black/[0.02] dark:from-white/[0.02] to-transparent">
                      <div className="flex items-center gap-3 mb-8">
                         <TrendingUp size={18} className="text-zinc-600" />
                         <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] text-zinc-600">Сетевая динамика</h3>
                      </div>
                      <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={networkTrend}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                            <XAxis 
                              dataKey="name" 
                              stroke="#3f3f46" fontSize={9} fontWeight="bold" 
                              tickLine={false} axisLine={false} dy={10}
                            />
                            <YAxis hide domain={[0, 100]} />
                            <Tooltip 
                              contentStyle={{ backgroundColor: isDark ? '#0c0d12' : '#ffffff', border: isDark ? '1px solid #ffffff10' : '1px solid #00000010', borderRadius: '12px', fontSize: '9px', color: isDark ? '#fff' : '#000' }}
                              itemStyle={{ color: isDark ? '#fff' : '#000', fontWeight: 'bold' }}
                            />
                            <Line 
                              type="monotone" dataKey="Оценка" stroke={isDark ? "#ffffff" : "#000000"} 
                              strokeWidth={2} dot={{ r: 3, fill: isDark ? '#fff' : '#000' }}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                   </div>
                   <div className="grid grid-cols-1 lg:grid-cols-2">
                      <div className="p-8 border-r border-black/5 dark:border-white/5">
                         <div className="flex items-center gap-3 mb-8">
                           <AlertTriangle size={18} className="text-zinc-900 dark:text-white" />
                           <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-900 dark:text-white">Краткая аналитика</h3>
                         </div>
                         <div className="space-y-5">
                           {networkPerformance.map((issue) => (
                             <div key={issue.key} className="space-y-2 group">
                               <div className="flex justify-between items-end">
                                 <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600 dark:text-zinc-400">
                                   {issue.name}
                                 </span>
                                 <span className={issue.percent < 50 ? "text-base font-bold text-rose-500" : "text-base font-bold text-emerald-500"}>
                                   {issue.percent}%
                                 </span>
                               </div>
                               <div className="h-1 w-full bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
                                 <div className="h-full bg-zinc-900 dark:bg-zinc-100" style={{ width: `${issue.percent}%` }}></div>
                               </div>
                             </div>
                           ))}
                         </div>
                      </div>
                      <div className="p-8">
                         <div className="flex items-center gap-3 mb-8">
                           <Star size={18} className="text-zinc-500" />
                           <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Рейтинг локаций</h3>
                         </div>
                         <div className="space-y-4">
                            {shopSummaries.map((shop, idx) => (
                              <div key={shop.id} className="flex items-center justify-between group cursor-pointer hover:bg-black/5 dark:hover:bg-white/5 p-2 rounded-xl transition-all" onClick={() => setSelectedShopId(shop.id)}>
                                 <div className="flex items-center gap-3">
                                    <span className="text-xs font-bold text-zinc-600">{idx + 1}.</span>
                                    <span className="text-sm font-bold text-zinc-700 dark:text-zinc-300">{shop.name}</span>
                                 </div>
                                 <span className="text-sm font-black text-emerald-500/80">{shop.avgScorePercent}%</span>
                              </div>
                            ))}
                         </div>
                      </div>
                   </div>
                </section>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {shopSummaries.map((shop) => (
                    <div 
                      key={shop.id}
                      className="bg-white dark:bg-[#0f1115]/60 border border-black/5 dark:border-white/5 rounded-2xl p-8 transition-all hover:bg-white dark:bg-[#0f1115]/80 shadow-xl flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex justify-between items-start mb-8">
                           <h2 className="text-2xl font-bold tracking-tighter text-zinc-900 dark:text-white">{shop.name}</h2>
                           <div className="text-xl font-black text-zinc-900 dark:text-white">{shop.avgScorePercent}%</div>
                        </div>
                        <div className="space-y-6">
                          <div className="flex items-center justify-between text-zinc-500 text-[10px] font-bold uppercase tracking-widest">
                            <div className="flex items-center gap-2"><Clock size={12} /> {shop.count} диалогов за день</div>
                          </div>
                          
                          <div className="space-y-3">
                            <div className="flex justify-between items-end text-xs font-bold text-zinc-600 dark:text-zinc-400">
                               <span>Сегодня</span>
                               <span className="text-zinc-900 dark:text-white">{shop.avgScorePercent}%</span>
                            </div>
                            <div className="h-1.5 w-full bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
                              <div className="h-full bg-zinc-900 dark:bg-zinc-100" style={{ width: `${shop.avgScorePercent}%` }}></div>
                            </div>
                            
                            <div className="flex justify-between items-end text-xs font-bold text-zinc-500 mt-2">
                               <span>За неделю</span>
                               <span className="text-zinc-900 dark:text-white/60">{shop.weeklyAvgPercent}%</span>
                            </div>
                            <div className="h-1.5 w-full bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
                              <div className="h-full bg-zinc-400 dark:bg-zinc-500" style={{ width: `${shop.weeklyAvgPercent}%` }}></div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <button 
                        onClick={() => setSelectedShopId(shop.id)}
                        className="mt-8 w-full py-3 border border-black/5 dark:border-white/5 rounded-xl font-bold uppercase tracking-widest text-[10px] text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:text-white hover:bg-black/5 dark:hover:bg-white/5 transition-all"
                      >
                         Подробнее
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              /* VIEW 2: Shop Details */
              <div className="space-y-10">
                <section className="grid md:grid-cols-12 gap-8 mb-4">
                   <div className="md:col-span-8 bg-white dark:bg-[#0c0d12]/60 border border-black/5 dark:border-white/5 rounded-2xl p-10">
                      <div className="flex flex-col xl:flex-row xl:items-end justify-between mb-8 gap-8">
                         <div>
                           <h2 className="text-3xl md:text-4xl font-bold tracking-tighter mb-4 text-zinc-900 dark:text-white break-words">{selectedShopSummary?.name}</h2>
                           <div className="flex flex-col sm:flex-row gap-4 sm:gap-8">
                              <div className="flex flex-col">
                                 <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Диалогов за период</span>
                                 <span className="text-2xl font-bold text-zinc-900 dark:text-white">{selectedShopSummary?.count}</span>
                              </div>
                              <div className="flex flex-col sm:border-l border-black/5 dark:border-white/5 sm:pl-8">
                                 <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Соблюдение скрипта</span>
                                 <span className="text-2xl font-bold text-zinc-900 dark:text-white">{selectedShopSummary?.avgScorePercent}%</span>
                              </div>
                           </div>
                         </div>
                         <div className="text-left xl:text-right">
                            <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-3">Статус обработки</div>
                            <div className="bg-zinc-100 dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 px-5 py-3 rounded-xl flex items-center gap-3 text-[10px] font-bold uppercase tracking-widest border border-black/5 dark:border-white/5">
                              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span> {appStatus?.status_message || "Системный онлайн"}
                            </div>
                         </div>
                      </div>
                   </div>

                   <div className="md:col-span-4 bg-white dark:bg-[#0c0d12]/60 border border-black/5 dark:border-white/5 rounded-2xl p-10">
                      <div className="flex items-center gap-3 mb-8 text-zinc-600">
                         <AlertTriangle size={18} />
                         <h3 className="text-[10px] font-bold uppercase tracking-widest">Аналитика по пунктам</h3>
                      </div>
                      <div className="space-y-5">
                         {shopPerformanceStats.map((stat) => (
                            <div key={stat.key} className="space-y-2">
                               <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                                  <span>{stat.name}</span>
                                  <span className="text-zinc-600 dark:text-zinc-400">{stat.percent}%</span>
                               </div>
                               <div className="h-1 bg-black/40 rounded-full overflow-hidden">
                                  <div className="h-full bg-emerald-500/40" style={{ width: `${stat.percent}%` }}></div>
                               </div>
                            </div>
                         ))}
                      </div>
                   </div>
                </section>

                <div className="space-y-4">
                  {shopDetails
                    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
                    .map((dialog, idx) => ({ dialog, originalIdx: idx + 1 }))
                    .reverse()
                    .map(({ dialog, originalIdx }) => (
                    <div 
                      key={dialog.id}
                      className={`bg-white dark:bg-[#0c0d12]/40 border ${expandedDialogId === dialog.id ? 'border-zinc-700' : 'border-black/5 dark:border-white/5'} rounded-2xl overflow-hidden`}
                    >
                      <div onClick={() => setExpandedDialogId(expandedDialogId === dialog.id ? null : dialog.id)} className="p-5 sm:p-8 flex flex-col md:flex-row items-start md:items-center justify-between cursor-pointer gap-4 md:gap-0">
                         <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 sm:gap-10">
                            <div className="flex flex-col">
                              <span className="text-xl font-bold tracking-tighter text-zinc-900 dark:text-white">Диалог #{originalIdx}</span>
                              {dialog.original_audio_file && (
                                <span className="text-xs text-zinc-400 font-mono mt-0.5">{dialog.original_audio_file}</span>
                              )}
                            </div>
                            <span className="text-[11px] font-bold text-zinc-500 uppercase">
                               {new Date(dialog.created_at).toLocaleTimeString('ru-RU', {hour: '2-digit', minute:'2-digit'})}
                            </span>
                            {(dialog.audit_details as any)?.dialogue_type === 'additional_order' ? (
                               <span className="bg-blue-500/10 text-blue-500 border border-blue-500/20 px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest">
                                 Дозаказ
                               </span>
                            ) : (dialog.audit_details as any)?.dialogue_type === 'dialog' ? (
                               <span className="bg-amber-500/10 text-amber-500 border border-amber-500/20 px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest">
                                 Разговор
                               </span>
                            ) : (
                               <span className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest">
                                 Заказ
                               </span>
                            )}
                            {(dialog.audit_details as any)?.is_conflict && (
                               <span className="bg-rose-500 text-white border border-rose-500/20 px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest animate-pulse shadow-[0_0_10px_rgba(244,63,94,0.5)]">
                                 Конфликт
                               </span>
                            )}
                         </div>
                         <div className={`text-4xl font-light tracking-tight ${(dialog.audit_details as any)?.dialogue_type === 'dialog' ? 'text-amber-500/50 text-3xl' : (getDialogPercent(dialog) >= 80 ? 'text-emerald-500' : 'text-rose-500')}`}>
                           {(dialog.audit_details as any)?.dialogue_type === 'dialog' ? 'Н/А' : `${getDialogPercent(dialog)}%`}
                         </div>
                      </div>

                      {expandedDialogId === dialog.id && (
                        <div className="px-10 pb-12 pt-6 border-t border-black/5 dark:border-white/5">
                           <div className="grid lg:grid-cols-12 gap-12">
                              <div className="lg:col-span-5 space-y-8">
                                 <button onClick={() => playPhrase(dialog, 0)} className="bg-white text-black px-8 py-4 rounded-xl font-bold uppercase text-xs">Прослушать целиком</button>
                                 <div className="bg-white dark:bg-[#0c0d12] p-8 rounded-2xl border border-black/5 dark:border-white/5 space-y-6">
                                    <div className="space-y-4 mb-6">
                                      <h4 className="text-[10px] font-bold text-zinc-500 uppercase">Оценки QA (Заказ)</h4>
                                      {[ 
                                        { key: 'cross_sales_score', label: 'Кросс-селл' },
                                        { key: 'upsell_score', label: 'Апселл' },
                                        { key: 'christmas_tree_score', label: 'Помощь в выборе' },
                                        { key: 'promo_score', label: 'Акция' },
                                        { key: 'loyalty_score', label: 'Лояльность' },
                                        { key: 'order_duplication_score', label: 'Дубл. заказа' }
                                      ].map((metric) => {
                                        const score = (dialog.audit_details as any)?.[metric.key] || 0;
                                        const isDialog = (dialog.audit_details as any)?.dialogue_type === 'dialog';
                                        const isExcluded = isDialog;
                                        const percent = isExcluded ? 0 : score;
                                        
                                        return (
                                          <div key={metric.key} className={`space-y-2 ${isExcluded ? 'opacity-30' : ''}`}>
                                            <div className="flex justify-between items-center text-[9px] font-bold uppercase tracking-widest text-zinc-600 dark:text-zinc-400">
                                              <span>{metric.label}</span>
                                              <span className={isExcluded ? "text-zinc-600" : (score >= 100 ? "text-emerald-500" : "text-rose-500")}>
                                                {isExcluded ? "Н/А" : `${Math.round(percent)}%`}
                                              </span>
                                            </div>
                                            <div className="h-1.5 bg-black/50 rounded-full overflow-hidden">
                                              <div className={`h-full ${isExcluded ? "bg-zinc-700" : (score >= 100 ? "bg-emerald-500/70" : "bg-rose-500/70")}`} style={{ width: isExcluded ? '100%' : `${percent}%` }}></div>
                                            </div>
                                          </div>
                                        );
                                      })}

                                      {/* LIVE SERVICE BADGE */}
                                      {!((dialog.audit_details as any)?.dialogue_type === 'dialog') && (
                                        <div className="mt-8 pt-6 border-t border-black/5 dark:border-white/5 space-y-4">
                                           <div className="flex items-center justify-between">
                                              <h4 className="text-[10px] font-bold text-amber-500 uppercase flex items-center gap-2">
                                                <Star size={12} /> Живой сервис
                                              </h4>
                                              <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${(dialog.audit_details as any)?.live_service_score >= 100 ? 'bg-amber-500 text-black shadow-lg shadow-amber-500/20' : 'bg-black/10 dark:bg-white/10 text-zinc-500'}`}>
                                                {(dialog.audit_details as any)?.live_service_score >= 110 ? '🌟 100%' : `${(dialog.audit_details as any)?.live_service_score || 0}%`}
                                              </span>
                                           </div>
                                        </div>
                                      )}
                                    </div>

                                    {/* EMOTION STATS UI */}
                                    {dialog.audit_details?.emotion_stats && (
                                      <div className="p-5 bg-black/[0.02] dark:bg-white/[0.02] border border-black/5 dark:border-white/5 rounded-2xl space-y-4">
                                         <div className="flex items-center justify-between">
                                            <h4 className="text-[10px] font-bold text-indigo-500 uppercase flex items-center gap-2">
                                              <Volume2 size={12} /> Акустический анализ эмоций (GigaAM-Emo)
                                            </h4>
                                            {dialog.audit_details?.is_conflict && (
                                              <span className="bg-rose-500 text-white px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest shadow-lg shadow-rose-500/30 animate-pulse">
                                                🚨 КОНФЛИКТ
                                              </span>
                                            )}
                                         </div>
                                         <div className="grid grid-cols-2 gap-4">
                                            {dialog.audit_details.emotion_stats.split(',').map((stat: string, i: number) => {
                                              const [name, valStr] = stat.trim().split('=');
                                              if (!name || !valStr) return null;
                                              const val = parseFloat(valStr) * 100;
                                              
                                              let color = "bg-zinc-500";
                                              let label = name;
                                              if (name.includes('angry')) { color = "bg-rose-500"; label = "Агрессия"; }
                                              else if (name.includes('positive')) { color = "bg-emerald-500"; label = "Позитив"; }
                                              else if (name.includes('sad')) { color = "bg-blue-500"; label = "Грусть"; }
                                              else if (name.includes('neutral')) { color = "bg-zinc-400 dark:bg-zinc-600"; label = "Нейтральность"; }

                                              return (
                                                <div key={i} className="space-y-1">
                                                  <div className="flex justify-between text-[9px] font-bold uppercase tracking-widest text-zinc-600 dark:text-zinc-400">
                                                    <span>{label}</span>
                                                    <span>{Math.round(val)}%</span>
                                                  </div>
                                                  <div className="h-1.5 w-full bg-black/10 dark:bg-white/10 rounded-full overflow-hidden">
                                                    <div className={`h-full ${color}`} style={{ width: `${val}%` }}></div>
                                                  </div>
                                                </div>
                                              );
                                            })}
                                         </div>
                                      </div>
                                    )}

                                    {dialog.audit_details?.critical_errors && dialog.audit_details.critical_errors !== "Не выявлено" && (
                                      <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl">
                                        <h4 className="text-[10px] font-bold text-rose-500 uppercase mb-2">Критические ошибки</h4>
                                        <p className="text-sm text-zinc-700 dark:text-zinc-300">{dialog.audit_details.critical_errors}</p>
                                      </div>
                                    )}
                                    {dialog.audit_details?.additional_service && !["null", "none", "не выявлено"].includes(String(dialog.audit_details.additional_service).toLowerCase()) && (
                                      <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                                        <h4 className="text-[10px] font-bold text-emerald-500 uppercase mb-2">Дополнительный сервис</h4>
                                        <p className="text-sm text-zinc-700 dark:text-zinc-300">{dialog.audit_details.additional_service}</p>
                                      </div>
                                    )}
                                    <div>
                                      <h4 className="text-[10px] font-bold text-zinc-500 uppercase mb-2">Рекомендация QA</h4>
                                      <p className="text-sm text-zinc-600 dark:text-zinc-400 italic">{dialog.text_analysis || "Анализ не доступен."}</p>
                                    </div>
                                 </div>
                              </div>
                              <div className="lg:col-span-7">
                                  <div className="bg-white dark:bg-black/20 p-6 md:p-10 rounded-3xl h-[500px] overflow-y-auto custom-scrollbar border border-black/5 dark:border-white/5 shadow-inner dark:shadow-none relative">
                                    {dialog.transcript?.map((line, idx) => (
                                      <div 
                                        key={idx} 
                                        onClick={() => playPhrase(dialog, line.start)} 
                                        ref={(el) => { if (idx === activePhraseIndex) transcriptRefs.current[idx] = el; }}
                                         className={`p-4 rounded-2xl cursor-pointer transition-all mb-2 border ${idx === activePhraseIndex ? 'bg-blue-50 dark:bg-white/10 border-blue-100 dark:border-white/10 shadow-sm dark:shadow-none text-blue-900 dark:text-white' : 'hover:bg-black/5 dark:hover:bg-white/5 border-transparent text-zinc-700 dark:text-zinc-300'}`}
                                      >
                                        <span className="text-[10px] text-emerald-500 font-bold block mb-1">{formatTime(line.start)} - {translateSpeaker(line.speaker)}</span>
                                        <p className="text-zinc-900 dark:text-white text-sm">{line.text}</p>
                                      </div>
                                    ))}
                                 </div>
                              </div>
                           </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
      </div>

      {activeDialog && (
        <div className="fixed bottom-0 left-0 right-0 z-50 animate-in slide-in-from-bottom duration-500 md:pb-8 pointer-events-none flex justify-center">
           <div className="w-full md:max-w-6xl md:px-6 pointer-events-auto">
              <div className="bg-white/95 dark:bg-zinc-900/95 backdrop-blur-3xl md:border border-black/10 dark:border-white/10 md:rounded-[2.5rem] rounded-t-[2rem] p-4 md:p-6 flex flex-col md:flex-row items-center gap-4 md:gap-10 shadow-[0_-10px_40px_rgb(0,0,0,0.1)] dark:shadow-2xl shadow-black/10 dark:shadow-black/50 border-t border-black/5 dark:border-white/10">
                 
                 <div className="flex items-center justify-between w-full md:w-auto md:min-w-[250px] shrink-0">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 md:w-16 md:h-16 bg-emerald-500 rounded-2xl flex items-center justify-center shrink-0 shadow-lg shadow-emerald-500/20">
                           <Volume2 size={24} className="text-black md:w-8 md:h-8" />
                        </div>
                        <div>
                           <h4 className="font-bold text-sm md:text-base tracking-tight mb-0.5 md:mb-1 text-zinc-900 dark:text-white line-clamp-1">Диалог #{activeDialog?.dialog_index}</h4>
                           <p className="text-[9px] md:text-[10px] font-bold text-zinc-500 uppercase line-clamp-1">{shops.find(s => s.id === activeDialog?.shop_id)?.name}</p>
                        </div>
                    </div>
                    {/* Mobile Close Button */}
                    <button onClick={() => { setActiveDialog(null); setIsPlaying(false); }} className="md:hidden w-10 h-10 flex items-center justify-center text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors bg-black/5 dark:bg-white/5 rounded-full">
                       <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                    </button>
                 </div>

                 <div className="flex-1 flex flex-col md:flex-col-reverse gap-3 md:gap-3 w-full">
                    {activeDialog.audio_url ? (
                       <>
                          {/* Progress Bar interactive */}
                          <div className="flex items-center gap-3">
                             <span className="text-[9px] md:text-[10px] font-bold text-zinc-400 min-w-[32px] md:min-w-[35px] font-mono text-right">{formatTime(currentTime)}</span>
                             <div className="flex-1 relative h-2 md:h-2 bg-black/5 dark:bg-white/5 rounded-full overflow-hidden flex items-center group">
                                <div className="absolute left-0 top-0 bottom-0 bg-emerald-500 pointer-events-none transition-all duration-75 group-hover:bg-emerald-400" style={{ width: `${(currentTime / duration) * 100}%` }} />
                                <input 
                                   type="range" 
                                   min="0" 
                                   max={duration || 100} 
                                   value={currentTime} 
                                   onChange={(e) => { 
                                     const time = Number(e.target.value); 
                                     if (audioRef.current) audioRef.current.currentTime = time; 
                                     setCurrentTime(time); 
                                   }} 
                                   className="absolute inset-0 w-full h-full opacity-0 cursor-pointer pointer-events-auto" 
                                />
                             </div>
                             <span className="text-[9px] md:text-[10px] font-bold text-zinc-400 min-w-[32px] md:min-w-[35px] font-mono">{formatTime(duration)}</span>
                          </div>

                          <div className="flex items-center justify-center gap-8 relative">
                             {/* Desktop Play Buttons */}
                             <button onClick={() => { if(audioRef.current) { audioRef.current.currentTime = Math.max(0, currentTime - 10); setCurrentTime(audioRef.current.currentTime); } }} className="text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors">
                                 <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 19 2 12 11 5 11 19"></polygon><polygon points="22 19 13 12 22 5 22 19"></polygon></svg>
                             </button>
                             <button onClick={togglePlay} className="w-12 h-12 md:w-14 md:h-14 bg-zinc-900 dark:bg-white text-white dark:text-black rounded-full flex items-center justify-center shadow-xl hover:scale-105 active:scale-95 transition-all">
                                {isPlaying ? <PauseCircle size={24} /> : <PlayCircle size={28} className="ml-1" />}
                             </button>
                             <button onClick={() => { if(audioRef.current) { audioRef.current.currentTime = Math.min(duration, currentTime + 10); setCurrentTime(audioRef.current.currentTime); } }} className="text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors">
                                 <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 19 22 12 13 5 13 19"></polygon><polygon points="2 19 11 12 2 5 2 19"></polygon></svg>
                             </button>
                          </div>
                       </>
                    ) : (
                       <div className="flex flex-col items-center justify-center text-center mt-2 md:mt-0 py-2 border border-dashed border-black/10 dark:border-white/10 rounded-2xl bg-black/[0.02] dark:bg-white/[0.02]">
                          <span className="text-xs font-bold text-zinc-500 dark:text-zinc-400">Аудиофайл не загружен на сервер</span>
                          <span className="text-[9px] text-zinc-400 dark:text-zinc-500 uppercase tracking-widest mt-1">OGG скрыт оркестратором</span>
                       </div>
                    )}
                 </div>

                 {/* Desktop Close Button */}
                 <button onClick={() => { setActiveDialog(null); setIsPlaying(false); }} className="hidden md:flex w-12 h-12 items-center justify-center text-zinc-400 hover:text-zinc-900 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 transition-colors rounded-full shrink-0">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                 </button>
                 
              </div>
           </div>
           <audio 
             ref={audioRef} 
             src={activeDialog.audio_url} 
             onTimeUpdate={handleTimeUpdate} 
             onLoadedMetadata={handleLoadedMetadata} 
             onPlay={() => setIsPlaying(true)} 
             onPause={() => setIsPlaying(false)} 
             onEnded={() => setIsPlaying(false)} 
           />
        </div>
      )}

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 5px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
      `}</style>
    </main>
  );
}
