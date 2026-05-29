"use client";
// v1.0.2 - Restored Local Pipeline & Realtime

import { useEffect, useState, useMemo, useRef, useCallback } from "react";
import { supabase, Shop, DialogScore, AppStatus, AgentTelemetry } from "@/lib/supabase";
import { 
  Clock, Volume2, PlayCircle, PauseCircle, 
  ChevronLeft, AlertTriangle, TrendingUp, Star, Calendar,
  Cpu, Activity, HardDrive, Thermometer, ArrowRight
} from "lucide-react";
import { 
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  CartesianGrid 
} from 'recharts';
import { ThemeToggle } from "@/components/theme-toggle";
import { useTheme } from "next-themes";

// Font is imported in globals.css

// Helper: returns YYYY-MM-DD in LOCAL timezone (not UTC)
function getLocalDateStr(d: Date = new Date()): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function getDialogWord(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod100 >= 11 && mod100 <= 19) {
    return "диалогов";
  }
  if (mod10 === 1) {
    return "диалог";
  }
  if (mod10 >= 2 && mod10 <= 4) {
    return "диалога";
  }
  return "диалогов";
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
  const [telemetry, setTelemetry] = useState<AgentTelemetry[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>(getLocalDateStr());
  const [activeDialog, setActiveDialog] = useState<DialogScore | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [activePhraseIndex, setActivePhraseIndex] = useState<number | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const [analyticsPeriod, setAnalyticsPeriod] = useState<'week' | 'month'>('week');
  const [clockSkew, setClockSkew] = useState<number>(0);
  const [timerTick, setTimerTick] = useState<number>(0);
  
  const playTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingStartTimeRef = useRef<number | null>(null);
  const mobileDateInputRef = useRef<HTMLInputElement | null>(null);
  const dateInputRef = useRef<HTMLInputElement | null>(null);

  // Drag-to-scroll for date selector
  const dateScrollRef = useRef<HTMLDivElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const isDragActive = useRef(false);
  
  useEffect(() => {
    setIsMounted(true);
    
    // Fetch clock skew to handle client-to-server clock desynchronization
    fetch('/api/server-time')
      .then(res => res.json())
      .then(data => {
        const skew = data.serverTime - Date.now();
        setClockSkew(skew);
      })
      .catch(err => console.error("Error fetching server time:", err));

    return () => {
      if (playTimeoutRef.current) clearTimeout(playTimeoutRef.current);
    };
  }, []);


  const audioRef = useRef<HTMLAudioElement | null>(null);
  const transcriptRefs = useRef<Record<string, HTMLDivElement | null>>({});

  // Drag-to-scroll handlers
  const handleDateScrollMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!dateScrollRef.current) return;
    
    const slider = dateScrollRef.current;
    const startX = e.pageX - slider.offsetLeft;
    const scrollLeft = slider.scrollLeft;
    isDragActive.current = false;
    const startMouseX = e.clientX;
    const startMouseY = e.clientY;

    const handleMouseMove = (walkEvent: MouseEvent) => {
      if (!slider) return;
      const x = walkEvent.pageX - slider.offsetLeft;
      const moveX = Math.abs(walkEvent.clientX - startMouseX);
      const moveY = Math.abs(walkEvent.clientY - startMouseY);
      
      if (moveX > 5 || moveY > 5) {
        isDragActive.current = true;
        setIsDragging(true);
      }
      
      if (isDragActive.current) {
        walkEvent.preventDefault();
        const walk = (x - startX) * 1.5;
        slider.scrollLeft = scrollLeft - walk;
      }
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      setTimeout(() => {
        setIsDragging(false);
      }, 50);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const handleDateClick = (dateStr: string) => {
    if (isDragActive.current) return;
    setSelectedDate(dateStr);
    setView('dashboard');
  };

  // 1. Core Functions
  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        audioRef.current.play()
          .then(() => setIsPlaying(true))
          .catch((err) => {
            console.warn("Playback failed:", err);
            setIsPlaying(false);
          });
      }
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current && activeDialog?.transcript) {
      const time = audioRef.current.currentTime;
      setCurrentTime(time);
      
      const dur = audioRef.current.duration;
      const startOffset = activeDialog.transcript.length > 0 ? activeDialog.transcript[0].start : 0;
      const isUrlCropped = activeDialog?.audio_url?.includes('dialog_') || activeDialog?.audio_url?.includes('slice_') || activeDialog?.audio_url?.includes('_patched');
      const isCropped = isUrlCropped || (dur && !isNaN(dur) && dur < startOffset);
      const absoluteTime = isCropped ? time + startOffset : time;

      let index = -1;
      for (let i = 0; i < activeDialog.transcript.length; i++) {
        if (absoluteTime >= activeDialog.transcript[i].start) {
          index = i;
        } else {
          break;
        }
      }
      if (index !== activePhraseIndex) {
        setActivePhraseIndex(index === -1 ? null : index);
      }
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current && activeDialog) {
      const dur = audioRef.current.duration;
      setDuration(dur);
      if (pendingStartTimeRef.current !== null) {
        if (playTimeoutRef.current) clearTimeout(playTimeoutRef.current);
        
        const startOffset = activeDialog.transcript && activeDialog.transcript.length > 0 ? activeDialog.transcript[0].start : 0;
        const isUrlCropped = activeDialog?.audio_url?.includes('dialog_') || activeDialog?.audio_url?.includes('slice_') || activeDialog?.audio_url?.includes('_patched');
        const isCropped = isUrlCropped || (dur && !isNaN(dur) && dur < startOffset);
        const seekTime = isCropped ? (pendingStartTimeRef.current >= startOffset ? pendingStartTimeRef.current - startOffset : pendingStartTimeRef.current) : pendingStartTimeRef.current;

        audioRef.current.currentTime = seekTime;
        audioRef.current.play()
          .then(() => setIsPlaying(true))
          .catch((err) => {
            console.warn("Playback failed on load:", err);
            setIsPlaying(false);
          });
        pendingStartTimeRef.current = null;
      }
    }
  };

  const playPhrase = (dialog: DialogScore, startTime: number) => {
    try {
      if (playTimeoutRef.current) {
        clearTimeout(playTimeoutRef.current);
      }
      
      const startOffset = dialog.transcript && dialog.transcript.length > 0 ? dialog.transcript[0].start : 0;

      if (activeDialog?.id !== dialog.id) {
        setActiveDialog(dialog);
        setActivePhraseIndex(null);
        pendingStartTimeRef.current = startTime;
        // Fallback timeout in case onLoadedMetadata doesn't fire
        playTimeoutRef.current = setTimeout(() => {
          if (audioRef.current && dialog.audio_url && pendingStartTimeRef.current !== null) {
            const dur = audioRef.current.duration;
            const isUrlCropped = activeDialog?.audio_url?.includes('dialog_') || activeDialog?.audio_url?.includes('slice_') || activeDialog?.audio_url?.includes('_patched');
            const isCropped = isUrlCropped || (dur && !isNaN(dur) && dur < startOffset);
            const seekTime = isCropped ? (pendingStartTimeRef.current >= startOffset ? pendingStartTimeRef.current - startOffset : pendingStartTimeRef.current) : pendingStartTimeRef.current;

            audioRef.current.currentTime = seekTime;
            audioRef.current.play()
              .then(() => setIsPlaying(true))
              .catch((err) => {
                console.warn("Playback fallback failed:", err);
                setIsPlaying(false);
              });
            pendingStartTimeRef.current = null;
          }
        }, 800);
      } else if (audioRef.current && dialog.audio_url) {
        pendingStartTimeRef.current = null;
        const dur = audioRef.current.duration;
        const isUrlCropped = dialog?.audio_url?.includes('dialog_') || dialog?.audio_url?.includes('slice_') || dialog?.audio_url?.includes('_patched');
        const isCropped = isUrlCropped || (dur && !isNaN(dur) && dur < startOffset);
        const seekTime = isCropped ? (startTime >= startOffset ? startTime - startOffset : startTime) : startTime;

        audioRef.current.currentTime = seekTime;
        audioRef.current.play()
          .then(() => setIsPlaying(true))
          .catch((err) => {
            console.warn("Playback failed:", err);
            setIsPlaying(false);
          });
      }
    } catch (e) {
      console.warn('playPhrase error:', e);
    }
  };

  // Reset phrase index when changing active dialog
  useEffect(() => {
    setActivePhraseIndex(null);
  }, [activeDialog?.id]);

  // Handle active phrase auto-scroll
  useEffect(() => {
    if (activeDialog && activePhraseIndex !== null && transcriptRefs.current[`${activeDialog.id}-${activePhraseIndex}`]) {
      const el = transcriptRefs.current[`${activeDialog.id}-${activePhraseIndex}`];
      if (el) {
        const container = el.closest('.custom-scrollbar');
        if (container) {
          const c = container as HTMLElement;
          const relativeTop = el.getBoundingClientRect().top - container.getBoundingClientRect().top + c.scrollTop;
          c.scrollTo({
            top: relativeTop - c.clientHeight / 2 + el.clientHeight / 2,
            behavior: "smooth"
          });
        }
      }
    }
  }, [activeDialog, activePhraseIndex]);

  const formatAbsoluteTime = (time: number) => {
    if (typeof time !== 'number' || isNaN(time) || !isFinite(time)) return "00:00:00";
    const absoluteSeconds = time + 28800;
    const hours = Math.floor(absoluteSeconds / 3600);
    const mins = Math.floor((absoluteSeconds % 3600) / 60);
    const secs = Math.floor(absoluteSeconds % 60);
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const formatTime = (time: number) => {
    if (typeof time !== 'number' || isNaN(time) || !isFinite(time)) return "0:00";
    const mins = Math.floor(time / 60);
    const secs = Math.floor(Math.abs(time % 60));
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const translateTag = (tag: string) => {
    if (typeof tag !== 'string') return "";
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
    if (typeof speaker !== 'string') return "";
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

      const { data: shopsData, error: shopsErr } = await supabase.from("shops").select("*").order("name");
      if (shopsErr) console.error("shops error:", shopsErr);
      
      const monthAgo = new Date();
      monthAgo.setDate(monthAgo.getDate() - 30);
      const { data: allMonthDialogs, error: dialogsErr } = await supabase.from("dialogs").select("*").gte("created_at", monthAgo.toISOString()).order("created_at", { ascending: false });
      if (dialogsErr) console.error("dialogs error:", dialogsErr);

      const { data: statusData, error: statusErr } = await supabase.from("app_status").select("*").eq("id", 1).single();
      if (statusErr && statusErr.code !== 'PGRST116') console.error("status error:", statusErr);
      
      const { data: telemetryData, error: telemetryErr } = await supabase.from("agent_telemetry").select("*").order("id");
      if (telemetryErr) console.error("dialogs error:", telemetryErr);
      
      if (shopsData) setShops(shopsData);
      if (allMonthDialogs) setAllDialogs(allMonthDialogs);
      if (statusData) setAppStatus(statusData);
      if (telemetryData) setTelemetry(telemetryData);
    } catch (err) {
      console.error("Unhandled error in loadData:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();

    // 1. Realtime Telemetry
    const telemetryChannel = supabase
      .channel("agent_telemetry_changes")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "agent_telemetry" },
        (payload) => {
          if (payload.new && 'agent_name' in payload.new) {
            const newAgent = payload.new as AgentTelemetry;
            setTelemetry((current) => {
              const exists = current.some(agent => agent.agent_name === newAgent.agent_name);
              if (exists) {
                return current.map(agent => agent.agent_name === newAgent.agent_name ? newAgent : agent);
              } else {
                return [...current, newAgent];
              }
            });
          }
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
          if (payload.new) {
            setAppStatus(payload.new as AppStatus);
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(telemetryChannel);
      supabase.removeChannel(dialogsChannel);
      supabase.removeChannel(statusChannel);
    };
  }, [loadData]);

  // Periodically force recheck of online status
  useEffect(() => {
    const interval = setInterval(() => {
      setTimerTick(prev => prev + 1);
      loadData(true); // Poll database silently every 5 seconds as a fallback
    }, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  // 3. Computed Analytics
  const getDialogPercent = (dialog: DialogScore) => {
    const details = dialog.audit_details;
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
    const periodDays = analyticsPeriod === 'week' ? 7 : 30;
    const dates: Record<string, { date: string, score: number, count: number }> = {};
    for (let i = periodDays - 1; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const s = getLocalDateStr(d);
      const label = d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
      dates[s] = { date: label, score: 0, count: 0 };
    }
    allDialogs.forEach(d => {
      if (!d.created_at || !d.audit_details || d.audit_details.dialogue_type === 'dialog') return;
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
  }, [allDialogs, analyticsPeriod]);

  const dailyMetricsAverages = useMemo(() => {
    const dialogsForDate = filteredDialogs.filter(d => d.audit_details && d.audit_details.dialogue_type !== 'dialog');
    if (dialogsForDate.length === 0) {
      return {
        upsell: 0,
        crossSell: 0,
        christmasTree: 0,
        loyalty: 0,
        orderDuplication: 0,
      };
    }
    
    let sumUpsell = 0;
    let sumCross = 0;
    let sumChristmas = 0;
    let sumLoyalty = 0;
    let sumDuplication = 0;
    
    dialogsForDate.forEach(d => {
      const details = d.audit_details;
      if (details) {
        sumUpsell += details.upsell_score || 0;
        sumCross += details.cross_sales_score || 0;
        sumChristmas += details.christmas_tree_score || 0;
        sumLoyalty += details.loyalty_score || 0;
        sumDuplication += details.order_duplication_score || 0;
      }
    });
    
    const count = dialogsForDate.length;
    return {
      upsell: Math.round(sumUpsell / count),
      crossSell: Math.round(sumCross / count),
      christmasTree: Math.round(sumChristmas / count),
      loyalty: Math.round(sumLoyalty / count),
      orderDuplication: Math.round(sumDuplication / count),
    };
  }, [filteredDialogs]);

  const metricTrends = useMemo(() => {
    const currentDate = new Date(selectedDate);
    const prevDate = new Date(currentDate);
    prevDate.setDate(prevDate.getDate() - 1);
    const prevDateStr = getLocalDateStr(prevDate);

    const prevDialogs = allDialogs.filter(d => d.created_at?.startsWith(prevDateStr) && d.audit_details && d.audit_details.dialogue_type !== 'dialog');

    let prevUpsell = 0;
    let prevCross = 0;
    let prevChristmas = 0;
    let prevLoyalty = 0;
    let prevDuplication = 0;

    if (prevDialogs.length > 0) {
      let sumUpsell = 0;
      let sumCross = 0;
      let sumChristmas = 0;
      let sumLoyalty = 0;
      let sumDuplication = 0;
      prevDialogs.forEach(d => {
        const details = d.audit_details;
        if (details) {
          sumUpsell += details.upsell_score || 0;
          sumCross += details.cross_sales_score || 0;
          sumChristmas += details.christmas_tree_score || 0;
          sumLoyalty += details.loyalty_score || 0;
          sumDuplication += details.order_duplication_score || 0;
        }
      });
      const count = prevDialogs.length;
      prevUpsell = Math.round(sumUpsell / count);
      prevCross = Math.round(sumCross / count);
      prevChristmas = Math.round(sumChristmas / count);
      prevLoyalty = Math.round(sumLoyalty / count);
      prevDuplication = Math.round(sumDuplication / count);
    } else {
      const allAudited = allDialogs.filter(d => d.audit_details && d.audit_details.dialogue_type !== 'dialog');
      if (allAudited.length > 0) {
        let sumUpsell = 0;
        let sumCross = 0;
        let sumChristmas = 0;
        let sumLoyalty = 0;
        let sumDuplication = 0;
        allAudited.forEach(d => {
          const details = d.audit_details;
          if (details) {
            sumUpsell += details.upsell_score || 0;
            sumCross += details.cross_sales_score || 0;
            sumChristmas += details.christmas_tree_score || 0;
            sumLoyalty += details.loyalty_score || 0;
            sumDuplication += details.order_duplication_score || 0;
          }
        });
        const count = allAudited.length;
        prevUpsell = Math.round(sumUpsell / count);
        prevCross = Math.round(sumCross / count);
        prevChristmas = Math.round(sumChristmas / count);
        prevLoyalty = Math.round(sumLoyalty / count);
        prevDuplication = Math.round(sumDuplication / count);
      }
    }

    return {
      upsellUp: dailyMetricsAverages.upsell >= prevUpsell,
      crossSellUp: dailyMetricsAverages.crossSell >= prevCross,
      christmasTreeUp: dailyMetricsAverages.christmasTree >= prevChristmas,
      loyaltyUp: dailyMetricsAverages.loyalty >= prevLoyalty,
      orderDuplicationUp: dailyMetricsAverages.orderDuplication >= prevDuplication
    };
  }, [allDialogs, selectedDate, dailyMetricsAverages]);

  const sparklineTrends = useMemo(() => {
    const periodDays = analyticsPeriod === 'week' ? 7 : 30;
    const dates: Record<string, { upsellSum: number, crossSum: number, count: number }> = {};
    for (let i = periodDays - 1; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const s = getLocalDateStr(d);
      dates[s] = { upsellSum: 0, crossSum: 0, count: 0 };
    }
    allDialogs.forEach(d => {
      if (!d.created_at || !d.audit_details || d.audit_details.dialogue_type === 'dialog') return;
      const s = d.created_at.split('T')[0];
      if (dates[s]) {
        dates[s].upsellSum += d.audit_details.upsell_score || 0;
        dates[s].crossSum += d.audit_details.cross_sales_score || 0;
        dates[s].count += 1;
      }
    });
    return Object.entries(dates).map(([dateStr, v]) => ({
      date: dateStr,
      upsell: v.count > 0 ? Math.round(v.upsellSum / v.count) : 0,
      crosssell: v.count > 0 ? Math.round(v.crossSum / v.count) : 0
    })).sort((a, b) => a.date.localeCompare(b.date));
  }, [allDialogs, analyticsPeriod]);

  const shopSummaries = useMemo(() => {
    return shops
      .filter(shop => shop.name !== 'Офис работников' && shop.name !== 'Офис')
      .map(shop => {
        const shopDialogs = filteredDialogs.filter(d => d.audit_details && d.audit_details.dialogue_type !== 'dialog' && d.shop_id === shop.id);
        const avgScorePercent = shopDialogs.length > 0
          ? Math.round(shopDialogs.reduce((acc, curr) => acc + getDialogPercent(curr), 0) / shopDialogs.length)
          : 0;

        // Weekly comparison for shop card chart
        const weekAgo = new Date(); weekAgo.setDate(weekAgo.getDate() - 7);
        const weeklyDialogs = allDialogs.filter(d => d.audit_details && d.audit_details.dialogue_type !== 'dialog' && d.shop_id === shop.id && d.created_at && new Date(d.created_at) >= weekAgo);
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
    // allDialogs represents last 30 days, we only care about fully audited dialogs that are standard sales scripts
    const activeDialogs = allDialogs.filter(d => d.audit_details && d.audit_details.dialogue_type !== 'dialog');

    let missedUpsell = 0;
    let missedCrossSell = 0;
    let missedLoyalty = 0;
    
    activeDialogs.forEach(d => {
      const details = d.audit_details;
      if (details) {
        if (details.upsell_score === 0) missedUpsell++;
        if (details.cross_sales_score === 0) missedCrossSell++;
        if (details.loyalty_score === 0) missedLoyalty++;
      }
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
      const details = d.audit_details;
      if (details) {
        Object.entries(details).forEach(([key, val]) => {
          if (key in stats && typeof val === 'number') {
            stats[key].total += val;
            stats[key].count += 1;
          }
        });
      }
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
       if (!d.created_at) return;
       const dateStr = d.created_at.split('T')[0];
       const shiftKey = `${d.shop_id}_${dateStr}`;
       if (!shiftStats[shiftKey]) {
          const shopName = shops.find(s => s.id === d.shop_id)?.name || 'Неизвестно';
          shiftStats[shiftKey] = { stars: 0, totalRaw: 0, count: 0, name: shopName, date: dateStr };
       }
       if (d.audit_details?.live_service_score && d.audit_details.live_service_score >= 100) shiftStats[shiftKey].stars += 1;
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
      const details = d.audit_details;
      if (details) {
        Object.entries(details).forEach(([key, val]) => {
          if (key in stats && typeof val === 'number') {
            stats[key].total += val;
            stats[key].count += 1;
            if (val === 0) stats[key].violations += 1;
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

  // Determine active content view
  const activeView = selectedShopId ? 'shopDetail' : view;

  // Reset window scroll when active view changes (e.g. navigating to Shop Detail or different tabs)
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior });
    const handle = requestAnimationFrame(() => {
      window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior });
    });
    return () => cancelAnimationFrame(handle);
  }, [activeView]);

  // 4. Render Logic
  if (!isMounted) return null;
  
  if (loading && shops.length === 0) {
    return (
      <main className="min-h-screen bg-[#F5F5F7] dark:bg-black text-[#1D1D1F] dark:text-[#F5F5F7] flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-[#007AFF] border-t-transparent rounded-full animate-spin"></div>
      </main>
    );
  }

  // --- SVG Score Ring helper ---
  const ScoreRing = ({ percent, size = 80, strokeWidth = 6, color = "#007AFF" }: { percent: number; size?: number; strokeWidth?: number; color?: string }) => {
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percent / 100) * circumference;
    return (
      <svg width={size} height={size} className="transform -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)"} strokeWidth={strokeWidth} />
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={offset} className="transition-all duration-700 ease-out" />
      </svg>
    );
  };

  // Nav items config
  const navItems = [
    { id: 'dashboard', label: 'Дашборд', icon: <TrendingUp size={18} /> },
    { id: 'analytics', label: 'Аналитика', icon: <Star size={18} /> },
    { id: 'admin', label: 'Офис', icon: <Cpu size={18} /> },
  ];

  return (
    <main className="min-h-screen bg-[#F5F5F7] dark:bg-black text-[#1D1D1F] dark:text-[#F5F5F7] font-sans antialiased transition-colors duration-300">
      
      {/* ===================== MOBILE HEADER ===================== */}
      <header className="md:hidden fixed top-0 left-0 right-0 z-40 bg-white/80 dark:bg-[#1C1C1E]/80 backdrop-blur-xl border-b border-black/[0.06] dark:border-white/[0.08]">
        <div className="flex items-center justify-between px-4 h-14">
          <div className="flex items-center gap-3">
            {selectedShopId && (
              <button onClick={() => setSelectedShopId(null)} className="p-1.5 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors">
                <ChevronLeft size={20} />
              </button>
            )}
            <div className="text-lg flex items-center gap-1 select-none">
              <span className="font-semibold text-[#86868B]">talk</span>
              <span className="font-bold">sensor</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <button onClick={() => mobileDateInputRef.current?.showPicker()} className="flex items-center justify-center bg-white dark:bg-[#2C2C2E] border border-black/[0.06] dark:border-white/[0.08] rounded-xl w-9 h-9">
                <Calendar size={16} className="text-[#86868B]" />
              </button>
              <input 
                ref={mobileDateInputRef}
                type="date" 
                value={selectedDate}
                onChange={(e) => { setSelectedDate(e.target.value); setView('dashboard'); }}
                className="absolute opacity-0 w-0 h-0"
              />
            </div>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* ===================== MOBILE BOTTOM TAB BAR ===================== */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/80 dark:bg-[#1C1C1E]/80 backdrop-blur-xl border-t border-black/[0.06] dark:border-white/[0.08] safe-area-bottom">
        <div className="flex items-center justify-around h-16 px-2">
          {navItems.map(item => {
            const isActive = view === item.id && !selectedShopId;
            return (
              <button
                key={item.id}
                onClick={() => { setView(item.id); setSelectedShopId(null); }}
                className={`flex flex-col items-center justify-center gap-0.5 w-16 py-1 rounded-xl transition-colors ${
                  isActive 
                    ? 'text-[#007AFF]' 
                    : 'text-[#86868B] active:text-[#1D1D1F] dark:active:text-[#F5F5F7]'
                }`}
              >
                {item.icon}
                <span className="text-[10px] font-semibold">{item.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      <div className="min-h-screen">
        {/* ===================== DESKTOP SIDEBAR ===================== */}
        <aside className="hidden md:flex flex-col w-64 fixed left-0 top-0 bottom-0 bg-white dark:bg-[#1C1C1E] border-r border-black/[0.06] dark:border-white/[0.08] z-30">
          
          {/* Logo */}
          <div className="px-6 pt-8 pb-6">
            <div className="text-xl flex items-center gap-1 select-none">
              <span className="font-semibold text-[#86868B]">talk</span>
              <span className="font-bold text-[#1D1D1F] dark:text-[#F5F5F7]">sensor</span>
            </div>
            <p className="text-xs text-[#86868B] mt-1">Аудит качества сервиса</p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 space-y-1">
            {navItems.map(item => (
              <button
                key={item.id}
                onClick={() => { setView(item.id); setSelectedShopId(null); }}
                className={`flex items-center gap-3 w-full px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  (view === item.id && !selectedShopId)
                    ? 'bg-[#007AFF]/10 text-[#007AFF]'
                    : 'text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-[#F5F5F7] hover:bg-black/[0.03] dark:hover:bg-white/[0.03]'
                }`}
              >
                {item.icon}
                {item.label}
              </button>
            ))}

            {selectedShopId && (
              <button 
                onClick={() => setSelectedShopId(null)}
                className="flex items-center gap-3 w-full px-4 py-2.5 rounded-xl text-sm font-medium text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-[#F5F5F7] hover:bg-black/[0.03] dark:hover:bg-white/[0.03] transition-all"
              >
                <ChevronLeft size={18} />
                Назад к сети
              </button>
            )}
          </nav>

          {/* Sidebar bottom */}
          <div className="px-4 pb-6 space-y-4">
            {/* Theme toggle */}
            <div className="flex items-center justify-between px-2">
              <span className="text-xs font-medium text-[#86868B]">Тема</span>
              <ThemeToggle />
            </div>

            {/* Status bar */}
            <div className="bg-[#F5F5F7] dark:bg-[#2C2C2E] rounded-xl p-3 space-y-2">
              {(() => {
                const macMiniData = telemetry.find(t => t.agent_name === 'mac_mini_telemetry');
                const adjustedNow = Date.now() + clockSkew;
                const isServerOnline = (macMiniData && macMiniData.updated_at) 
                  ? (Math.abs(adjustedNow - new Date(macMiniData.updated_at).getTime()) < 35000) 
                  : false;

                if (!isServerOnline) {
                  return (
                    <>
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-[#FF3B30]"></span>
                        <span className="text-xs font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]">
                          Сервер оффлайн
                        </span>
                      </div>
                      <p className="text-[10px] text-[#86868B] leading-tight">
                        Хост Mac Mini не отвечает
                      </p>
                    </>
                  );
                }

                const busyAgent = telemetry.find(t => {
                  const isBusy = t.status?.trim().toUpperCase() === 'BUSY' && t.agent_name !== 'mac_mini_telemetry';
                  return isBusy;
                });
                
                const isAnalyzing = !!busyAgent || !!appStatus?.is_analyzing;
                
                let displayAgentName = busyAgent?.agent_name || '';
                if (displayAgentName.toLowerCase() === 'audio diarization agent') displayAgentName = 'Транскрибатор';
                else if (displayAgentName.toLowerCase() === 'diarization editor') displayAgentName = 'Аудитор';
                else if (displayAgentName.toLowerCase() === 'qa analyst') displayAgentName = 'QA аналитик';

                const statusMessage = busyAgent 
                  ? (busyAgent.active_task || `Агент: ${displayAgentName}`) 
                  : (appStatus?.status_message || 'Готов к работе');
                
                return (
                  <>
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${isAnalyzing ? 'bg-[#FF9500] animate-pulse' : 'bg-[#34C759]'}`}></span>
                      <span className="text-xs font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]">
                        {isAnalyzing ? 'Идёт анализ' : 'Система онлайн'}
                      </span>
                    </div>
                    <p className="text-[10px] text-[#86868B] leading-tight">
                      {statusMessage}
                    </p>
                  </>
                );
              })()}
            </div>
          </div>
        </aside>

        {/* ===================== CONTENT AREA ===================== */}
        <div className="md:ml-64 pt-16 md:pt-0 pb-28 md:pb-24 min-w-0">
          <div className="w-full px-3 sm:px-4 md:px-6 py-4 md:py-6">

            {/* ===================== VIEW: ADMIN ===================== */}
            {activeView === 'admin' && (() => {
              const macMiniData = telemetry.find(t => t.agent_name === 'mac_mini_telemetry');
              const adjustedNow = Date.now() + clockSkew;
              const isServerOnline = (macMiniData && macMiniData.updated_at) 
                ? (Math.abs(adjustedNow - new Date(macMiniData.updated_at).getTime()) < 35000) 
                : false;

              let realMetrics = {
                gpuLoad: 0,
                gpuTemp: 0,
                cpuLoad: 0,
                ramUsage: 0,
                latency: 0,
                uptime: "—",
                model: "M4"
              };

              if (isServerOnline && macMiniData?.active_task) {
                try {
                  realMetrics = JSON.parse(macMiniData.active_task);
                } catch (e) {
                  console.error("Error parsing mac mini telemetry:", e);
                }
              }

              return (
                <div className="space-y-8">
                  {/* Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <h1 className="text-2xl font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]">Офис (Mac Mini)</h1>
                      <p className="text-sm text-[#86868B] mt-1">Визуальный конвейер обработки диалогов и состояние хоста</p>
                    </div>
                    <div className="flex items-center gap-2.5 bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] px-4 py-2 rounded-xl">
                      <span className="relative flex h-2 w-2">
                        {isServerOnline && (
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#34C759] opacity-75"></span>
                        )}
                        <span className={`relative inline-flex rounded-full h-2 w-2 ${isServerOnline ? 'bg-[#34C759]' : 'bg-[#FF3B30]'}`}></span>
                      </span>
                      <span className="text-xs font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]">
                        {isServerOnline ? 'Сервер активен' : 'Сервер неактивен'}
                      </span>
                    </div>
                  </div>

                  {/* Pipeline Canvas */}
                  <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-6 relative overflow-hidden">
                    <div className="absolute -right-24 -top-24 w-64 h-64 bg-[#007AFF]/5 blur-[80px] rounded-full pointer-events-none"></div>
                    
                    <h3 className="text-sm font-semibold text-[#1D1D1F] dark:text-[#F5F5F7] mb-6 flex items-center gap-2">
                      <Activity size={16} className="text-[#007AFF]" />
                      Схема обработки диалогов
                    </h3>

                    <div className="flex flex-col lg:flex-row items-stretch justify-between gap-4 relative">
                      {[
                        { 
                          name: "Транскрибатор", 
                          step: "Шаг 1. Транскрибатор", 
                          desc: "Транскрибация аудио в текст (GigaAM)", 
                          color: "#007AFF" 
                        },
                        { 
                          name: "Аудитор", 
                          step: "Шаг 2. Аудитор", 
                          desc: "Проверка качества диалога, выявление ошибок", 
                          color: "#5856D6" 
                        },
                        { 
                          name: "QA аналитик", 
                          step: "Шаг 3. QA Аналитик", 
                          desc: "Интеллектуальная оценка и скоринг (DeepSeek)", 
                          color: "#FF9500" 
                        }
                      ].map((agent, idx) => {
                        const agentData = telemetry.find(t => {
                          const dbName = t.agent_name?.trim().toLowerCase();
                          if (idx === 0) return dbName === 'транскрибатор' || dbName === 'audio diarization agent';
                          if (idx === 1) return dbName === 'аудитор' || dbName === 'diarization editor';
                          if (idx === 2) return dbName === 'qa аналитик' || dbName === 'qa analyst';
                          return false;
                        });

                        const isBusy = isServerOnline && agentData?.status?.trim().toUpperCase() === 'BUSY';
                        const lastActivityStr = agentData?.updated_at 
                          ? new Date(agentData.updated_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) 
                          : '—';

                        const statusText = !isServerOnline ? 'Оффлайн' : isBusy ? 'В работе' : 'Ожидает';
                        const dotColor = !isServerOnline ? 'bg-neutral-500/40' : isBusy ? 'bg-[#34C759] animate-pulse' : 'bg-[#86868B]/40';

                        return (
                          <div key={idx} className="flex-1 flex flex-col lg:flex-row items-center gap-4">
                            {/* Card Block */}
                            <div className="w-full bg-[#F5F5F7] dark:bg-[#2C2C2E] rounded-xl p-5 border border-black/[0.04] dark:border-white/[0.04] flex flex-col justify-between min-h-[160px] relative z-10 transition-all hover:scale-[1.01]">
                              <div>
                                <div className="flex items-center justify-between mb-3">
                                  <span className="text-xs font-bold text-[#86868B]">{agent.step}</span>
                                  <div className="flex items-center gap-1.5">
                                    <span className={`w-2 h-2 rounded-full ${dotColor}`}></span>
                                    <span className={`text-[11px] font-semibold ${!isServerOnline ? 'text-[#86868B]/60' : isBusy ? 'text-[#34C759]' : 'text-[#86868B]'}`}>
                                      {statusText}
                                    </span>
                                  </div>
                                </div>
                                <h4 className="text-sm font-bold text-[#1D1D1F] dark:text-[#F5F5F7] mb-1">{agent.name}</h4>
                                <p className="text-xs text-[#86868B] leading-relaxed mb-4">{agent.desc}</p>
                              </div>

                              <div className="pt-3 border-t border-black/[0.06] dark:border-white/[0.06] flex items-center justify-between mt-auto">
                                <span className="text-[10px] text-[#86868B]">Последнее обновление:</span>
                                <span className="text-[10px] font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]">{lastActivityStr}</span>
                              </div>
                              
                              {isBusy && agentData?.active_task && (
                                <div className="absolute inset-x-0 -bottom-2 px-4 z-20">
                                  <div className="bg-[#007AFF] text-white text-[10px] py-1 px-3.5 rounded-full shadow-md text-center truncate max-w-full font-medium animate-bounce">
                                    Текущая задача: {agentData.active_task}
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* Connector Arrow */}
                            {idx < 2 && (
                              <div className="hidden lg:flex items-center justify-center shrink-0">
                                <div className="flex items-center gap-1">
                                  <span className={`h-1.5 w-1.5 rounded-full bg-[#007AFF] ${isBusy ? 'animate-ping' : ''}`} />
                                  <div className="h-[2px] w-6 bg-gradient-to-r from-[#007AFF] to-[#5856D6] rounded-full" />
                                  <ArrowRight size={14} className="text-[#5856D6]" />
                                </div>
                              </div>
                            )}
                            {idx < 2 && (
                              <div className="lg:hidden flex items-center justify-center py-2 shrink-0">
                                <div className="h-6 w-[2px] bg-gradient-to-b from-[#007AFF] to-[#5856D6] rounded-full" />
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Telemetry Dashboard Widgets */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    
                    {/* GPU Load */}
                    <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-5 flex flex-col justify-between">
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-xs font-semibold text-[#86868B]">Загрузка GPU (Mac Mini)</span>
                        <Cpu size={16} className={isServerOnline ? "text-[#007AFF]" : "text-[#86868B]/40"} />
                      </div>
                      <div>
                        <div className="flex items-baseline gap-1.5 mb-2">
                          <span className="text-3xl font-bold text-[#1D1D1F] dark:text-[#F5F5F7] font-mono">
                            {isServerOnline ? `${realMetrics.gpuLoad}%` : '—'}
                          </span>
                          <span className="text-xs text-[#34C759] font-semibold">{isServerOnline ? `${realMetrics.model || "M4"} Core` : '—'}</span>
                        </div>
                        <div className="h-2 bg-[#F5F5F7] dark:bg-[#2C2C2E] rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-[#007AFF] to-[#5856D6] rounded-full transition-all duration-1000" 
                            style={{ width: `${isServerOnline ? realMetrics.gpuLoad : 0}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* GPU Temp */}
                    <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-5 flex flex-col justify-between">
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-xs font-semibold text-[#86868B]">Температура GPU</span>
                        <Thermometer size={16} className={isServerOnline ? (realMetrics.gpuTemp > 75 ? 'text-[#FF3B30]' : realMetrics.gpuTemp > 65 ? 'text-[#FF9500]' : 'text-[#34C759]') : 'text-[#86868B]/40'} />
                      </div>
                      <div>
                        <div className="flex items-baseline justify-between mb-2">
                          <span className="text-3xl font-bold text-[#1D1D1F] dark:text-[#F5F5F7] font-mono">
                            {isServerOnline ? `${realMetrics.gpuTemp}°C` : '—'}
                          </span>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                            !isServerOnline
                              ? 'bg-neutral-500/10 text-neutral-500'
                              : realMetrics.gpuTemp > 75 
                                ? 'bg-[#FF3B30]/10 text-[#FF3B30]' 
                                : realMetrics.gpuTemp > 65 
                                  ? 'bg-[#FF9500]/10 text-[#FF9500]' 
                                  : 'bg-[#34C759]/10 text-[#34C759]'
                          }`}>
                            {!isServerOnline ? 'Выкл' : realMetrics.gpuTemp > 75 ? 'Горячо' : realMetrics.gpuTemp > 65 ? 'Норма' : 'Оптимально'}
                          </span>
                        </div>
                        <div className="text-[10px] text-[#86868B] flex justify-between">
                          <span>Порог: 95°C</span>
                          <span>Кулер: {isServerOnline ? 'Авто' : '—'}</span>
                        </div>
                      </div>
                    </div>

                    {/* CPU / RAM */}
                    <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-5 flex flex-col justify-between">
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-xs font-semibold text-[#86868B]">Загрузка CPU и ОЗУ</span>
                        <HardDrive size={16} className={isServerOnline ? "text-[#5856D6]" : "text-[#86868B]/40"} />
                      </div>
                      <div className="space-y-3">
                        <div>
                          <div className="flex justify-between text-[10px] font-semibold text-[#86868B] mb-1">
                            <span>CPU</span>
                            <span>{isServerOnline ? `${realMetrics.cpuLoad}%` : '—'}</span>
                          </div>
                          <div className="h-1.5 bg-[#F5F5F7] dark:bg-[#2C2C2E] rounded-full overflow-hidden">
                            <div className="h-full bg-[#5856D6] rounded-full transition-all duration-1000" style={{ width: `${isServerOnline ? realMetrics.cpuLoad : 0}%` }} />
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between text-[10px] font-semibold text-[#86868B] mb-1">
                            <span>ОЗУ (16 GB)</span>
                            <span>{isServerOnline ? `${realMetrics.ramUsage}%` : '—'}</span>
                          </div>
                          <div className="h-1.5 bg-[#F5F5F7] dark:bg-[#2C2C2E] rounded-full overflow-hidden">
                            <div className="h-full bg-[#AF52DE] rounded-full transition-all duration-1000" style={{ width: `${isServerOnline ? realMetrics.ramUsage : 0}%` }} />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Latency / Uptime */}
                    <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-5 flex flex-col justify-between">
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-xs font-semibold text-[#86868B]">Сеть и Время работы</span>
                        <Activity size={16} className={isServerOnline ? "text-[#34C759]" : "text-[#86868B]/40"} />
                      </div>
                      <div>
                        <div className="flex justify-between items-baseline mb-2">
                          <span className="text-2xl font-bold text-[#1D1D1F] dark:text-[#F5F5F7] font-mono">
                            {isServerOnline ? `${realMetrics.latency} ms` : '—'}
                          </span>
                          <span className="text-xs text-[#86868B]">Пинг к БД</span>
                        </div>
                        <div className="pt-2.5 border-t border-black/[0.06] dark:border-white/[0.06] flex items-center justify-between text-[10px] text-[#86868B]">
                          <span>Uptime:</span>
                          <span className="font-bold text-[#1D1D1F] dark:text-[#F5F5F7] font-mono">{isServerOnline ? realMetrics.uptime : '—'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* ===================== VIEW: ANALYTICS ===================== */}
            {activeView === 'analytics' && (
              <div className="space-y-8">
                <div>
                  <h1 className="text-2xl font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]">Аналитика за 30 дней</h1>
                  <p className="text-sm text-[#86868B] mt-1">{monthlyAnalytics.totalDialogs} диалогов проанализировано</p>
                </div>

                {/* Hero number */}
                <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-8 relative overflow-hidden">
                  <div className="absolute -right-16 -bottom-16 w-48 h-48 bg-[#34C759]/5 blur-[80px] rounded-full pointer-events-none"></div>
                  <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <TrendingUp size={16} className="text-[#34C759]" />
                        <span className="text-sm font-medium text-[#34C759]">Средний скрипт по сети</span>
                      </div>
                      <div className="text-6xl font-bold text-[#1D1D1F] dark:text-[#F5F5F7]">
                        {monthlyAnalytics.networkAvgPercentMonth}%
                      </div>
                    </div>
                    <div className="bg-[#FF3B30]/5 dark:bg-[#FF3B30]/10 rounded-xl border border-[#FF3B30]/10 p-5">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle size={14} className="text-[#FF3B30]" />
                        <span className="text-xs font-medium text-[#FF3B30]">Упущенная выгода</span>
                      </div>
                      <span className="text-3xl font-bold text-[#FF3B30]">-{monthlyAnalytics.lostRevenue.toLocaleString('ru-RU')} &#8381;</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Missed opportunities */}
                  <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-6">
                    <h3 className="text-sm font-semibold text-[#1D1D1F] dark:text-[#F5F5F7] mb-6">Упущенные продажи</h3>
                    <div className="space-y-4">
                      {[
                        { label: 'Без допродажи', value: monthlyAnalytics.missedUpsell, color: '#FF3B30' },
                        { label: 'Без кросс-продажи', value: monthlyAnalytics.missedCrossSell, color: '#FF9500' },
                        { label: 'Без лояльности', value: monthlyAnalytics.missedLoyalty, color: '#5856D6' },
                      ].map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }}></div>
                            <span className="text-sm text-[#86868B]">{item.label}</span>
                          </div>
                          <span className="text-lg font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]">{item.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Weakest point */}
                  <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-6">
                    <h3 className="text-sm font-semibold text-[#1D1D1F] dark:text-[#F5F5F7] mb-6">Главная точка роста</h3>
                    <div className="flex items-center gap-6">
                      <div className="relative flex items-center justify-center">
                        <ScoreRing percent={monthlyAnalytics.worstMetric.percent} size={90} strokeWidth={8} color="#FF3B30" />
                        <span className="absolute text-lg font-bold text-[#FF3B30]">{monthlyAnalytics.worstMetric.percent}%</span>
                      </div>
                      <div>
                        <p className="text-xl font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]">{monthlyAnalytics.worstMetric.name || 'Нет данных'}</p>
                        <p className="text-xs text-[#86868B] mt-2 leading-relaxed">Требуется дополнительное обучение по этому стандарту</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Best Shifts */}
                <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-6">
                  <h3 className="text-sm font-semibold text-[#1D1D1F] dark:text-[#F5F5F7] mb-4 flex items-center gap-2">
                    <Star size={16} className="text-[#FF9500]" />
                    Лучшие смены месяца
                  </h3>
                  <div className="space-y-3">
                    {monthlyAnalytics.rankedShifts.map((shift, idx) => (
                      <div key={idx} className="flex items-center justify-between bg-[#F5F5F7] dark:bg-[#2C2C2E] p-4 rounded-xl">
                        <div className="flex items-center gap-4">
                          <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${idx === 0 ? 'bg-[#FF9500] text-white' : 'bg-[#E5E5EA] dark:bg-[#38383A] text-[#1D1D1F] dark:text-[#F5F5F7]'}`}>
                            {idx + 1}
                          </div>
                          <div>
                            <span className="text-sm font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]">{shift.name}</span>
                            <span className="text-xs text-[#86868B] ml-3">{new Date(shift.date).toLocaleDateString('ru-RU')} &middot; {shift.count} диалогов</span>
                          </div>
                        </div>
                        <span className="text-lg font-bold text-[#34C759]">{shift.percent}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* ===================== VIEW: DASHBOARD (Network) ===================== */}
            {activeView === 'dashboard' && (
              <div className="space-y-4">

                {/* ===================== ROW 1: MAIN TREND (Full Width Hero) ===================== */}
                <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-4 md:p-5">
                  <div>
                    {/* Title + Toggle */}
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h2 className="text-sm font-semibold text-[#1D1D1F] dark:text-[#F5F5F7] uppercase tracking-wider">сетевая аналитика</h2>
                        <p className="text-[11px] text-[#86868B] mt-0.5">Средняя оценка по всем кофейням</p>
                      </div>
                      <div className="flex items-center bg-[#F5F5F7] dark:bg-[#2C2C2E] rounded-lg p-0.5">
                        <button
                          onClick={() => setAnalyticsPeriod('week')}
                          className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all duration-200 ${
                            analyticsPeriod === 'week'
                              ? 'bg-white dark:bg-[#3A3A3C] text-[#1D1D1F] dark:text-[#F5F5F7] shadow-sm'
                              : 'text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-[#F5F5F7]'
                          }`}
                        >
                          Неделя
                        </button>
                        <button
                          onClick={() => setAnalyticsPeriod('month')}
                          className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all duration-200 ${
                            analyticsPeriod === 'month'
                              ? 'bg-white dark:bg-[#3A3A3C] text-[#1D1D1F] dark:text-[#F5F5F7] shadow-sm'
                              : 'text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-[#F5F5F7]'
                          }`}
                        >
                          Месяц
                        </button>
                      </div>
                    </div>

                    {/* AreaChart */}
                    <div className="h-[120px] w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={networkTrend} margin={{ top: 10, right: 10, bottom: 0, left: -25 }}>
                          <defs>
                            <linearGradient id="colorOverallScore" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#007AFF" stopOpacity={0.15}/>
                              <stop offset="95%" stopColor="#007AFF" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.04)"} vertical={false} />
                          <XAxis 
                            dataKey="name" 
                            stroke="#86868B" 
                            fontSize={9} 
                            tickLine={false} 
                            axisLine={false} 
                            dy={6}
                          />
                          <YAxis 
                            stroke="#86868B"
                            fontSize={9}
                            tickLine={false}
                            axisLine={false}
                            domain={[0, 100]}
                            dx={-6}
                          />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: isDark ? 'rgba(28,28,30,0.95)' : 'rgba(255,255,255,0.95)',
                              border: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(0,0,0,0.06)',
                              borderRadius: '12px',
                              fontSize: '11px',
                              color: isDark ? '#F5F5F7' : '#1D1D1F',
                              backdropFilter: 'blur(8px)',
                              boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
                              padding: '6px 10px',
                            }}
                            // eslint-disable-next-line @typescript-eslint/no-explicit-any
                            formatter={(value: any) => [`${value}%`, "Общая оценка"]}
                            labelFormatter={(label) => `${label}`}
                          />
                          <Area 
                            type="monotone" 
                            dataKey="Оценка" 
                            stroke="#007AFF" 
                            strokeWidth={2.5} 
                            fillOpacity={1}
                            fill="url(#colorOverallScore)"
                            dot={{ r: 2.5, stroke: "#007AFF", strokeWidth: 1.5, fill: isDark ? "#1C1C1E" : "#ffffff" }}
                            activeDot={{ r: 4.5, stroke: "#007AFF", strokeWidth: 2, fill: "#007AFF" }}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                {/* ===================== ROW 2: GRID CONTENT (2/3 width Left + 1/3 width Right) ===================== */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                  {/* Left Section (2/3 width) - One Unified Card */}
                  <div className="lg:col-span-2 bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl overflow-hidden flex flex-col justify-between">
                    {/* Top part: Sparklines (2-column layout with vertical divider) */}
                    <div className="grid grid-cols-1 md:grid-cols-2">
                      {/* Апсейл Sparkline */}
                      <div className="p-4 md:p-5 flex flex-col justify-between h-[130px] relative overflow-hidden md:border-r border-black/[0.06] dark:border-white/[0.08] min-w-0">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold text-[#1D1D1F] dark:text-[#F5F5F7] uppercase tracking-wider">апсейл</span>
                          <span className="text-lg font-bold text-[#007AFF] flex items-center gap-1 select-none">
                            {dailyMetricsAverages.upsell}%
                            {metricTrends.upsellUp ? (
                              <span className="text-[10px] text-[#34C759] font-bold">▲</span>
                            ) : (
                              <span className="text-[10px] text-[#FF3B30] font-bold">▼</span>
                            )}
                          </span>
                        </div>
                        <div className="h-[65px] w-full">
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={sparklineTrends} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
                              <defs>
                                <linearGradient id="colorUpsell" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#007AFF" stopOpacity={0.15}/>
                                  <stop offset="95%" stopColor="#007AFF" stopOpacity={0}/>
                                </linearGradient>
                              </defs>
                              <Area 
                                type="monotone" 
                                dataKey="upsell" 
                                stroke="#007AFF" 
                                strokeWidth={2} 
                                fillOpacity={1}
                                fill="url(#colorUpsell)"
                                dot={false}
                              />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      </div>

                      {/* Кроссейл Sparkline */}
                      <div className="p-4 md:p-5 flex flex-col justify-between h-[130px] relative overflow-hidden min-w-0">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold text-[#1D1D1F] dark:text-[#F5F5F7] uppercase tracking-wider">кроссейл</span>
                          <span className="text-lg font-bold text-[#007AFF] flex items-center gap-1 select-none">
                            {dailyMetricsAverages.crossSell}%
                            {metricTrends.crossSellUp ? (
                              <span className="text-[10px] text-[#34C759] font-bold">▲</span>
                            ) : (
                              <span className="text-[10px] text-[#FF3B30] font-bold">▼</span>
                            )}
                          </span>
                        </div>
                        <div className="h-[65px] w-full">
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={sparklineTrends} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
                              <defs>
                                <linearGradient id="colorCrosssell" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#007AFF" stopOpacity={0.15}/>
                                  <stop offset="95%" stopColor="#007AFF" stopOpacity={0}/>
                                </linearGradient>
                              </defs>
                              <Area 
                                type="monotone" 
                                dataKey="crosssell" 
                                stroke="#007AFF" 
                                strokeWidth={2} 
                                fillOpacity={1}
                                fill="url(#colorCrosssell)"
                                dot={false}
                              />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    </div>

                    {/* Horizontal Divider Line */}
                    <div className="border-t border-black/[0.06] dark:border-white/[0.08]" />

                    {/* Bottom part: Segmented progress bars */}
                    <div className="p-4 md:p-5 flex flex-col justify-center space-y-3 bg-black/[0.01] dark:bg-white/[0.01]">
                      {[
                        { label: "Помощь В Выборе", percent: dailyMetricsAverages.christmasTree, up: metricTrends.christmasTreeUp },
                        { label: "Программа Лояльности", percent: dailyMetricsAverages.loyalty, up: metricTrends.loyaltyUp },
                        { label: "Дублирование Заказа", percent: dailyMetricsAverages.orderDuplication, up: metricTrends.orderDuplicationUp },
                      ].map((item, idx) => (
                        <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 py-2 border-b border-black/[0.03] dark:border-white/[0.03] last:border-0 font-medium">
                          <span className="text-sm text-[#1D1D1F] dark:text-[#F5F5F7]">{item.label}</span>
                          <div className="flex items-center gap-3">
                            <div className="flex gap-[3px]">
                              {Array.from({ length: 10 }).map((_, sIdx) => {
                                const isFilled = sIdx < Math.round((item.percent / 100) * 10);
                                return (
                                  <div
                                    key={sIdx}
                                    className={`w-4 h-5 sm:w-5 sm:h-6 rounded-[3px] transition-all duration-300 ${
                                      isFilled
                                        ? "bg-[#007AFF]/80 dark:bg-[#007AFF]/90"
                                        : "bg-black/[0.06] dark:bg-white/[0.06]"
                                    }`}
                                  />
                                );
                              })}
                            </div>
                            <span className="text-sm font-bold text-[#1D1D1F] dark:text-[#F5F5F7] min-w-[40px] text-right flex items-center justify-end gap-1 select-none">
                              {item.percent}%
                              {item.up ? (
                                <span className="text-[10px] text-[#34C759] font-bold">▲</span>
                              ) : (
                                <span className="text-[10px] text-[#FF3B30] font-bold">▼</span>
                              )}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Right Section (1/3 width): Location rating with stars */}
                  <div className="lg:col-span-1 bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-4 md:p-5 flex flex-col justify-between">
                    <div>
                      <h2 className="text-sm font-semibold text-[#1D1D1F] dark:text-[#F5F5F7] mb-0.5 uppercase tracking-wider">рейтинг локаций</h2>
                      <p className="text-[11px] text-[#86868B] mb-3">По уровню соблюдения скриптов</p>
                      
                      <div className="space-y-2 overflow-y-auto max-h-[200px] custom-scrollbar pr-1">
                        {shopSummaries.map((shop) => (
                          <div 
                            key={shop.id} 
                            className="flex items-center justify-between cursor-pointer hover:bg-black/[0.02] dark:hover:bg-white/[0.03] p-1.5 rounded-xl transition-colors" 
                            onClick={() => setSelectedShopId(shop.id)}
                          >
                            <span className="text-xs font-medium text-[#1D1D1F] dark:text-[#F5F5F7] truncate max-w-[140px]">{shop.name}</span>
                            <div className="flex items-center gap-0.5 text-[#FF9500] shrink-0">
                              {Array.from({ length: 5 }).map((_, sIdx) => {
                                const starVal = Math.round(shop.avgScorePercent / 20);
                                return (
                                  <Star 
                                    key={sIdx} 
                                    size={11} 
                                    className={sIdx < starVal ? "fill-[#FF9500] text-[#FF9500]" : "text-black/[0.1] dark:text-white/[0.1]"} 
                                  />
                                );
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* ===================== ROW 3: DATE SELECTOR (with datepicker) ===================== */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center px-1">
                    <span className="text-[11px] font-semibold text-[#86868B]">Выбор даты</span>
                    <div className="relative">
                      <button 
                        onClick={() => dateInputRef.current?.showPicker()} 
                        className="px-3 py-1.5 text-[11px] font-semibold bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] hover:bg-black/[0.02] dark:hover:bg-white/[0.02] active:scale-95 transition-all rounded-xl text-[#1D1D1F] dark:text-[#F5F5F7] flex items-center gap-1.5"
                      >
                        <Calendar size={12} className="text-[#86868B]" />
                        выбрать дату архива
                      </button>
                      <input 
                        ref={dateInputRef}
                        type="date" 
                        value={selectedDate}
                        onChange={(e) => { setSelectedDate(e.target.value); setView('dashboard'); }}
                        className="absolute opacity-0 w-0 h-0 pointer-events-none"
                      />
                    </div>
                  </div>

                  <div 
                    ref={dateScrollRef}
                    onMouseDown={handleDateScrollMouseDown}
                    onDragStart={(e) => e.preventDefault()}
                    onWheel={(e) => { e.currentTarget.scrollLeft += e.deltaY * 1.5; }}
                    className={`w-full overflow-x-auto custom-scrollbar touch-pan-x date-slider-container ${isDragging ? 'cursor-grabbing select-none' : 'cursor-grab snap-x snap-mandatory'}`}
                  >
                    <div className="flex gap-2 py-1 select-none">
                      {Array.from({length: 30}).map((_, i) => {
                        const d = new Date();
                        d.setDate(d.getDate() - i);
                        const dateStr = getLocalDateStr(d);
                        const displayDate = d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
                        const dayDialogs = allDialogs.filter(dx => dx.created_at?.startsWith(dateStr) && dx.audit_details?.dialogue_type !== 'dialog');
                        let total = 0;
                        dayDialogs.forEach(dx => total += getDialogPercent(dx));
                        const avg = dayDialogs.length > 0 ? (total / dayDialogs.length).toFixed(0) : '--';
                        const isSelected = selectedDate === dateStr;

                        return (
                          <button 
                            key={dateStr}
                            onClick={() => handleDateClick(dateStr)}
                            onDragStart={(e) => e.preventDefault()}
                            style={{ width: 'var(--card-width)', minWidth: 'var(--card-width)' }}
                            className={`flex-shrink-0 flex flex-col items-center justify-center gap-1 rounded-xl border transition-all duration-200 h-24 sm:h-28 py-3 px-2 cursor-pointer
                              ${isDragging ? '' : 'snap-center'}
                              ${isSelected 
                                ? 'bg-[#007AFF] border-transparent shadow-lg shadow-[#007AFF]/25 text-white' 
                                : 'bg-white dark:bg-[#1C1C1E] hover:bg-[#F5F5F7] dark:hover:bg-[#2C2C2E] border-black/[0.06] dark:border-white/[0.08]'}`}
                          >
                            <span className={`text-sm sm:text-base font-bold tracking-wide ${isSelected ? 'text-white' : 'text-[#1D1D1F] dark:text-[#F5F5F7]'}`}>{displayDate}</span>
                            <span className={`text-lg sm:text-xl font-extrabold ${isSelected ? 'text-white/90' : 'text-[#007AFF]'}`}>{avg}%</span>
                            <span className={`text-[10px] sm:text-[11px] font-medium ${isSelected ? 'text-white/60' : 'text-[#86868B]'}`}>{dayDialogs.length} {getDialogWord(dayDialogs.length)}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* ===================== ROW 4: BOTTOM SHOP CARDS ===================== */}
                <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                  {shopSummaries.map((shop) => {
                    const scoreColor = shop.avgScorePercent >= 70 ? '#34C759' : shop.avgScorePercent >= 40 ? '#FF9500' : '#FF3B30';
                    return (
                      <div 
                        key={shop.id}
                        onClick={() => setSelectedShopId(shop.id)}
                        className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-4 flex flex-col justify-between transition-all duration-200 hover:shadow-md cursor-pointer group relative overflow-hidden"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1 min-w-0 mr-3">
                            <h3 className="text-sm font-semibold text-[#1D1D1F] dark:text-[#F5F5F7] truncate group-hover:text-[#007AFF] transition-colors">{shop.name}</h3>
                            <p className="text-[11px] text-[#86868B] mt-1 font-medium">{shop.count} {getDialogWord(shop.count)}</p>
                          </div>
                          <div className="relative flex items-center justify-center shrink-0">
                            <ScoreRing percent={shop.avgScorePercent} size={46} strokeWidth={4} color={scoreColor} />
                            <span className="absolute text-[10px] font-bold" style={{ color: scoreColor }}>{shop.avgScorePercent}%</span>
                          </div>
                        </div>
                        
                        <div className="mt-2.5 w-full">
                          <button className="w-full py-1.5 px-3 text-[11px] font-semibold bg-[#F5F5F7] dark:bg-[#2C2C2E] hover:bg-[#007AFF]/10 hover:text-[#007AFF] dark:hover:bg-[#007AFF]/20 dark:hover:text-[#007AFF] text-[#1D1D1F] dark:text-[#F5F5F7] rounded-xl transition-all duration-200 text-center">
                            Перейти
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* ===================== VIEW: SHOP DETAIL ===================== */}
            {activeView === 'shopDetail' && (
              <div className="space-y-8">
                {/* Shop header */}
                <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-6">
                  <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
                    <div>
                      <h1 className="text-2xl font-semibold text-[#1D1D1F] dark:text-[#F5F5F7] mb-3">{selectedShopSummary?.name}</h1>
                      <div className="flex flex-wrap gap-6">
                        <div>
                          <span className="text-xs text-[#86868B]">Диалогов</span>
                          <p className="text-xl font-bold text-[#1D1D1F] dark:text-[#F5F5F7]">{selectedShopSummary?.count}</p>
                        </div>
                        <div>
                          <span className="text-xs text-[#86868B]">Скрипт</span>
                          <p className="text-xl font-bold text-[#1D1D1F] dark:text-[#F5F5F7]">{selectedShopSummary?.avgScorePercent}%</p>
                        </div>
                        <div>
                          <span className="text-xs text-[#86868B]">Статус</span>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="w-2 h-2 bg-[#34C759] rounded-full"></span>
                            <span className="text-sm font-medium text-[#1D1D1F] dark:text-[#F5F5F7]">{appStatus?.status_message || 'Онлайн'}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    {/* Shop score ring */}
                    <div className="relative flex items-center justify-center">
                      <ScoreRing percent={selectedShopSummary?.avgScorePercent || 0} size={100} strokeWidth={8} color={
                        (selectedShopSummary?.avgScorePercent || 0) >= 70 ? '#34C759' : (selectedShopSummary?.avgScorePercent || 0) >= 40 ? '#FF9500' : '#FF3B30'
                      } />
                      <span className="absolute text-xl font-bold text-[#1D1D1F] dark:text-[#F5F5F7]">{selectedShopSummary?.avgScorePercent || 0}%</span>
                    </div>
                  </div>
                </div>

                {/* Performance breakdown */}
                <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-6">
                  <h3 className="text-sm font-semibold text-[#1D1D1F] dark:text-[#F5F5F7] mb-5">Оценки по критериям</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {shopPerformanceStats.map((stat) => (
                      <div key={stat.key} className="bg-[#F5F5F7] dark:bg-[#2C2C2E] rounded-xl p-4">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-xs font-medium text-[#86868B]">{stat.name}</span>
                          <span className={`text-sm font-bold ${stat.percent >= 80 ? 'text-[#34C759]' : stat.percent >= 50 ? 'text-[#FF9500]' : 'text-[#FF3B30]'}`}>{stat.percent}%</span>
                        </div>
                        <div className="h-1.5 bg-[#E5E5EA] dark:bg-[#38383A] rounded-full overflow-hidden">
                          <div className={`h-full rounded-full transition-all duration-500 ${stat.percent >= 80 ? 'bg-[#34C759]' : stat.percent >= 50 ? 'bg-[#FF9500]' : 'bg-[#FF3B30]'}`} style={{ width: `${stat.percent}%` }}></div>
                        </div>
                        {stat.violations > 0 && <p className="text-[10px] text-[#FF3B30] mt-1.5">{stat.violations} нарушений</p>}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Dialog list - clean table-like rows */}
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-[#1D1D1F] dark:text-[#F5F5F7] mb-2">Список диалогов</h3>
                  {shopDetails
                    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
                    .map((dialog, idx) => ({ dialog, originalIdx: idx + 1 }))
                    .reverse()
                    .map(({ dialog, originalIdx }) => (
                    <div 
                      key={dialog.id}
                      className={`bg-white dark:bg-[#1C1C1E] border rounded-2xl overflow-hidden transition-all duration-200 ${expandedDialogId === dialog.id ? 'border-[#007AFF]/30 shadow-sm' : 'border-black/[0.06] dark:border-white/[0.08]'}`}
                    >
                      {/* Row header */}
                      <div onClick={() => setExpandedDialogId(expandedDialogId === dialog.id ? null : dialog.id)} className="px-5 py-4 flex items-center justify-between cursor-pointer hover:bg-black/[0.01] dark:hover:bg-white/[0.01] transition-colors">
                        <div className="flex items-center gap-4 min-w-0">
                          <div className="flex flex-col min-w-0">
                            <span className="text-sm font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]">Диалог #{originalIdx}</span>
                            {dialog.original_audio_file && (
                              <span className="text-[10px] text-[#86868B] font-mono truncate max-w-[200px]">{dialog.original_audio_file}</span>
                            )}
                          </div>
                          <span className="text-xs text-[#86868B] shrink-0">
                            {dialog.transcript?.[0]?.start !== undefined ? formatAbsoluteTime(dialog.transcript[0].start) : new Date(dialog.created_at).toLocaleTimeString('ru-RU', {hour: '2-digit', minute:'2-digit'})}
                          </span>
                          {!dialog.audit_details ? (
                            <span className="bg-[#E5E5EA] dark:bg-[#38383A] text-[#86868B] px-2.5 py-0.5 rounded-full text-[10px] font-medium shrink-0">Анализ...</span>
                          ) : dialog.audit_details.dialogue_type === 'additional_order' ? (
                            <span className="bg-[#007AFF]/10 text-[#007AFF] px-2.5 py-0.5 rounded-full text-[10px] font-medium shrink-0">Дозаказ</span>
                          ) : dialog.audit_details.dialogue_type === 'dialog' ? (
                            <span className="bg-[#FF9500]/10 text-[#FF9500] px-2.5 py-0.5 rounded-full text-[10px] font-medium shrink-0">Разговор</span>
                          ) : (
                            <span className="bg-[#34C759]/10 text-[#34C759] px-2.5 py-0.5 rounded-full text-[10px] font-medium shrink-0">Заказ</span>
                          )}
                          {dialog.audit_details?.is_conflict && (
                            <span className="bg-[#FF3B30] text-white px-2.5 py-0.5 rounded-full text-[10px] font-medium shrink-0">Конфликт</span>
                          )}
                        </div>
                        <span className={`text-2xl font-semibold shrink-0 ml-4 ${!dialog.audit_details ? 'text-[#86868B]' : dialog.audit_details.dialogue_type === 'dialog' ? 'text-[#FF9500]/50' : (getDialogPercent(dialog) >= 80 ? 'text-[#34C759]' : 'text-[#FF3B30]')}`}>
                          {!dialog.audit_details ? '—' : dialog.audit_details.dialogue_type === 'dialog' ? 'Н/А' : `${getDialogPercent(dialog)}%`}
                        </span>
                      </div>

                      {/* Expanded panel */}
                      {expandedDialogId === dialog.id && (
                        <div className="px-3 sm:px-5 pb-5 pt-4 border-t border-black/[0.06] dark:border-white/[0.06]">
                          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

                            {/* ═══ LEFT: Transcript + Play (6/12) ═══ */}
                            <div className="lg:col-span-6 flex flex-col gap-3">
                              <div className="bg-[#F5F5F7] dark:bg-[#2C2C2E] rounded-2xl border border-black/[0.06] dark:border-white/[0.08] overflow-hidden">
                                <div className="h-[460px] sm:h-[520px] overflow-y-auto custom-scrollbar p-4 sm:p-5 space-y-1.5">
                                  {dialog.transcript?.map((line, idx) => {
                                    const isBarista = line.speaker?.toLowerCase().includes('barista');
                                    const isActive = idx === activePhraseIndex && activeDialog?.id === dialog.id;
                                    
                                    return (
                                      <div 
                                        key={idx} 
                                        onClick={() => playPhrase(dialog, line.start)} 
                                        ref={(el) => { transcriptRefs.current[`${dialog.id}-${idx}`] = el; }}
                                        className={`flex flex-col ${isBarista ? 'items-start' : 'items-end'}`}
                                      >
                                        <div className={`w-full px-4 py-3 rounded-2xl cursor-pointer transition-all duration-200 ${
                                          isBarista 
                                            ? `rounded-bl-md ${
                                                isActive 
                                                  ? 'bg-[#34C759]/15 ring-2 ring-[#34C759]/30' 
                                                  : 'bg-white dark:bg-[#1C1C1E] hover:bg-[#E8E8ED] dark:hover:bg-[#38383A]'
                                              }`
                                            : `rounded-br-md ${
                                                isActive 
                                                  ? 'bg-[#007AFF] text-white shadow-md shadow-[#007AFF]/20' 
                                                  : 'bg-[#007AFF]/8 dark:bg-[#007AFF]/12 hover:bg-[#007AFF]/15 dark:hover:bg-[#007AFF]/20'
                                              }`
                                        }`}
                                        >
                                          <div className={`flex items-center gap-2 mb-1 ${isActive && !isBarista ? 'opacity-80' : ''}`}>
                                            <span className={`text-xs font-bold ${
                                              isActive && !isBarista ? 'text-white/70' : (isBarista ? 'text-[#34C759]' : 'text-[#007AFF]')
                                            }`}>
                                              {translateSpeaker(line.speaker)}
                                            </span>
                                            <span className={`text-[11px] font-mono ${
                                              isActive && !isBarista ? 'text-white/50' : 'text-[#86868B]'
                                            }`}>
                                              {formatAbsoluteTime(line.start)}
                                            </span>
                                          </div>
                                          <p className={`text-base leading-relaxed ${
                                            isActive && !isBarista ? 'text-white' : 'text-[#1D1D1F] dark:text-[#F5F5F7]'
                                          }`}>{line.text}</p>
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                              {dialog.audio_url ? (
                                <button onClick={() => playPhrase(dialog, dialog.transcript && dialog.transcript.length > 0 ? dialog.transcript[0].start : 0)} className="self-start bg-[#007AFF] text-white px-5 py-2.5 rounded-xl font-semibold text-sm hover:bg-[#0066CC] active:scale-95 transition-all flex items-center gap-2 shadow-sm">
                                  <PlayCircle size={16} /> Прослушать целиком
                                </button>
                              ) : (
                                <div className="self-start bg-[#F2F2F7] dark:bg-[#2C2C2E] text-[#86868B] px-5 py-2.5 rounded-xl font-semibold text-sm flex items-center gap-2 shadow-sm">
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                  Аудио загружается...
                                </div>
                              )}
                            </div>

                            {/* ═══ RIGHT: Analytics (6/12) ═══ */}
                            <div className="lg:col-span-6 space-y-3">

                              {/* QA Score Cards — 2x3 grid */}
                              <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-4">
                                <h4 className="text-xs font-bold text-[#86868B] uppercase tracking-wider mb-3">Оценка скрипта продаж</h4>
                                <div className="grid grid-cols-3 gap-2">
                                  {[ 
                                    { key: 'cross_sales_score', label: 'Кросс-селл' },
                                    { key: 'upsell_score', label: 'Апселл' },
                                    { key: 'christmas_tree_score', label: 'Выбор' },
                                    { key: 'promo_score', label: 'Акция' },
                                    { key: 'loyalty_score', label: 'Лояльность' },
                                    { key: 'order_duplication_score', label: 'Дубл. заказа' }
                                  ].map((metric) => {
                                    const details = dialog.audit_details;
                                    const score = details ? (details[metric.key as keyof typeof details] as number) || 0 : 0;
                                    const isDialog = details?.dialogue_type === 'dialog';
                                    const isExcluded = isDialog || !details;
                                    const color = isExcluded ? '#86868B' : score >= 100 ? '#34C759' : score > 0 ? '#FF9500' : '#FF3B30';
                                    return (
                                      <div key={metric.key} className="bg-[#F5F5F7] dark:bg-[#2C2C2E] rounded-xl p-2.5 text-center">
                                        <span className="text-xl font-bold block" style={{ color }}>
                                          {isExcluded ? '—' : `${Math.round(score)}%`}
                                        </span>
                                        <span className="text-xs font-medium text-[#86868B] block mt-0.5 leading-tight">{metric.label}</span>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>

                              {/* Emotions — grid cards like QA */}
                              {dialog.audit_details?.emotion_stats && (
                                <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-4">
                                  <div className="flex items-center justify-between mb-3">
                                    <h4 className="text-xs font-bold text-[#86868B] uppercase tracking-wider">Анализ эмоций</h4>
                                    {dialog.audit_details?.is_conflict && (
                                      <span className="bg-[#FF3B30] text-white px-2 py-0.5 rounded-full text-[9px] font-bold">КОНФЛИКТ</span>
                                    )}
                                  </div>
                                  <div className="grid grid-cols-4 gap-2">
                                    {dialog.audit_details.emotion_stats.split(',').map((stat: string, i: number) => {
                                      const [name, valStr] = stat.trim().split('=');
                                      if (!name || !valStr) return null;
                                      let val = parseFloat(valStr) * 100;
                                      if (isNaN(val)) val = 0;
                                      let color = '#86868B';
                                      let label = name;
                                      if (name.includes('angry')) { color = '#FF3B30'; label = 'Агрессия'; }
                                      else if (name.includes('positive')) { color = '#34C759'; label = 'Позитив'; }
                                      else if (name.includes('sad')) { color = '#007AFF'; label = 'Грусть'; }
                                      else if (name.includes('neutral')) { color = '#86868B'; label = 'Нейтральн.'; }
                                      return (
                                        <div key={i} className="bg-[#F5F5F7] dark:bg-[#2C2C2E] rounded-xl p-2.5 text-center">
                                          <span className="text-xl font-bold block" style={{ color }}>{Math.round(val)}%</span>
                                          <span className="text-xs font-medium text-[#86868B] block mt-0.5 leading-tight">{label}</span>
                                        </div>
                                      );
                                    })}
                                  </div>
                                </div>
                              )}

                              {/* Live service */}
                              {dialog.audit_details && dialog.audit_details.dialogue_type !== 'dialog' && (
                                <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl px-4 py-3">
                                  <div className="flex items-center justify-between">
                                    <span className="text-xs font-semibold text-[#FF9500] flex items-center gap-1.5">
                                      <Star size={12} /> Живой сервис
                                    </span>
                                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${(dialog.audit_details.live_service_score || 0) >= 75 ? 'bg-[#FF9500] text-white' : 'bg-[#E5E5EA] dark:bg-[#38383A] text-[#86868B]'}`}>
                                      {`${dialog.audit_details.live_service_score || 0}%`}
                                    </span>
                                  </div>
                                  <p className="text-[10px] text-[#86868B] mt-1.5 leading-relaxed">Оценка за персональное обращение, комплименты, эмпатию, запоминание предпочтений и инициативную помощь гостю.</p>
                                </div>
                              )}

                              {/* Critical errors */}
                              {dialog.audit_details?.critical_errors && dialog.audit_details.critical_errors !== "Не выявлено" && (
                                <div className="flex items-start gap-2 bg-[#FF3B30]/5 border border-[#FF3B30]/10 rounded-xl px-4 py-3">
                                  <AlertTriangle size={14} className="text-[#FF3B30] shrink-0 mt-0.5" />
                                  <p className="text-sm text-[#1D1D1F] dark:text-[#F5F5F7] leading-relaxed">{dialog.audit_details.critical_errors}</p>
                                </div>
                              )}

                              {/* Additional service */}
                              {dialog.audit_details?.additional_service && !["null", "none", "не выявлено"].includes(String(dialog.audit_details.additional_service).toLowerCase()) && (
                                <div className="flex items-start gap-2 bg-[#34C759]/5 border border-[#34C759]/10 rounded-xl px-4 py-3">
                                  <Star size={14} className="text-[#34C759] shrink-0 mt-0.5" />
                                  <p className="text-sm text-[#1D1D1F] dark:text-[#F5F5F7] leading-relaxed">{dialog.audit_details.additional_service}</p>
                                </div>
                              )}

                              {/* QA Recommendation */}
                              <div className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl px-4 py-3">
                                <h4 className="text-xs font-bold text-[#86868B] uppercase tracking-wider mb-1.5">Рекомендация</h4>
                                <p className="text-sm text-[#86868B] italic leading-relaxed">{dialog.text_analysis || "Анализ не доступен."}</p>
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
        </div>
      </div>

      {/* ===================== AUDIO PLAYER (floating) ===================== */}
      {activeDialog && (
        <div className="fixed bottom-16 md:bottom-0 left-0 right-0 z-50 pb-2 md:pb-6 pointer-events-none flex justify-center md:ml-64">
          <div className="w-full max-w-4xl px-4 pointer-events-auto">
            <div className="bg-white/90 dark:bg-[#1C1C1E]/90 backdrop-blur-2xl border border-black/[0.06] dark:border-white/[0.08] rounded-2xl md:rounded-full p-4 md:p-4 flex flex-col md:flex-row items-center gap-4 md:gap-6 shadow-xl">
              
              {/* Left: dialog info */}
              <div className="flex items-center justify-between w-full md:w-auto md:min-w-[200px] shrink-0 gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-tr from-[#007AFF] to-[#5856D6] rounded-xl flex items-center justify-center shrink-0 shadow-sm relative overflow-hidden">
                    {isPlaying ? (
                      <div className="flex items-end gap-0.5 h-4 w-4 shrink-0 justify-center">
                        <span className="w-0.5 bg-white rounded-full h-full animate-eq-1" />
                        <span className="w-0.5 bg-white rounded-full h-full animate-eq-2" />
                        <span className="w-0.5 bg-white rounded-full h-full animate-eq-3" />
                        <span className="w-0.5 bg-white rounded-full h-full animate-eq-4" />
                      </div>
                    ) : (
                      <Volume2 size={18} className="text-white" />
                    )}
                  </div>
                  <div className="min-w-0">
                    <h4 className="font-semibold text-sm text-[#1D1D1F] dark:text-[#F5F5F7] truncate">Диалог #{activeDialog?.dialog_index}</h4>
                    <p className="text-xs text-[#86868B] truncate">{shops.find(s => s.id === activeDialog?.shop_id)?.name}</p>
                  </div>
                </div>
                <button onClick={() => { setActiveDialog(null); setIsPlaying(false); }} className="md:hidden w-8 h-8 flex items-center justify-center text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-white transition-colors rounded-full hover:bg-black/5 dark:hover:bg-white/5">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                </button>
              </div>

              {/* Center: controls + seek */}
              <div className="flex-1 flex flex-col md:flex-row items-center gap-3 w-full">
                {activeDialog.audio_url ? (
                  <>
                    <div className="flex items-center gap-3 shrink-0">
                      <button onClick={() => { if(audioRef.current) { audioRef.current.currentTime = Math.max(0, currentTime - 10); setCurrentTime(audioRef.current.currentTime); } }} className="text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-white transition-colors p-1" title="-10 сек">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 19 2 12 11 5 11 19"></polygon><polygon points="22 19 13 12 22 5 22 19"></polygon></svg>
                      </button>
                      <button onClick={togglePlay} className="w-10 h-10 bg-[#007AFF] hover:bg-[#0066CC] text-white rounded-full flex items-center justify-center shadow-sm hover:scale-105 active:scale-95 transition-all">
                        {isPlaying ? <PauseCircle size={20} className="text-white" /> : <PlayCircle size={22} className="ml-0.5 text-white" />}
                      </button>
                      <button onClick={() => { if(audioRef.current) { audioRef.current.currentTime = Math.min(duration, currentTime + 10); setCurrentTime(audioRef.current.currentTime); } }} className="text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-white transition-colors p-1" title="+10 сек">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 19 22 12 13 5 13 19"></polygon><polygon points="2 19 11 12 2 5 2 19"></polygon></svg>
                      </button>
                    </div>
                    <div className="flex-1 flex items-center gap-2.5 w-full">
                      <span className="text-[10px] font-medium text-[#86868B] min-w-[32px] font-mono text-right">{formatTime(currentTime)}</span>
                      <div className="flex-1 relative h-1.5 bg-[#E5E5EA] dark:bg-[#38383A] rounded-full overflow-hidden flex items-center">
                        <div className="absolute left-0 top-0 bottom-0 bg-[#007AFF] pointer-events-none transition-all duration-75 rounded-full" style={{ width: `${duration && !isNaN(duration) && !isNaN(currentTime) ? (currentTime / duration) * 100 : 0}%` }} />
                        <input 
                          type="range" 
                          min="0" 
                          max={duration && !isNaN(duration) ? duration : 100} 
                          value={isNaN(currentTime) ? 0 : currentTime} 
                          onChange={(e) => { 
                            const time = Number(e.target.value); 
                            if (audioRef.current) audioRef.current.currentTime = time; 
                            setCurrentTime(time); 
                          }} 
                          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer pointer-events-auto" 
                        />
                      </div>
                      <span className="text-[10px] font-medium text-[#86868B] min-w-[32px] font-mono">{formatTime(duration)}</span>
                    </div>
                  </>
                ) : (
                  <div className="w-full flex items-center justify-center py-2">
                    <span className="text-xs text-[#86868B]">Аудиофайл не загружен</span>
                  </div>
                )}
              </div>

              {/* Desktop close */}
              <button onClick={() => { setActiveDialog(null); setIsPlaying(false); }} className="hidden md:flex w-8 h-8 items-center justify-center text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 transition-colors rounded-full shrink-0">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>
          </div>
          <audio 
            ref={audioRef} 
            src={activeDialog.audio_url} 
            preload="auto"
            onTimeUpdate={handleTimeUpdate} 
            onLoadedMetadata={handleLoadedMetadata} 
            onPlay={() => setIsPlaying(true)} 
            onPause={() => setIsPlaying(false)} 
            onEnded={() => setIsPlaying(false)} 
            onError={(e) => {
              const audio = e.currentTarget;
              const err = audio.error;
              console.error("Audio error:", err?.code, err?.message, "src:", audio.src);
            }}
          />
        </div>
      )}

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 5px; height: 5px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(128,128,128,0.2); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .date-slider-container {
          --card-width: calc((100% - 1rem) / 3);
        }
        @media (min-width: 640px) {
          .date-slider-container {
            --card-width: calc((100% - 2rem) / 4.5);
          }
        }
        @media (min-width: 768px) {
          .date-slider-container {
            --card-width: calc((100% - 3rem) / 6.5);
          }
        }
        .safe-area-bottom {
          padding-bottom: env(safe-area-inset-bottom, 0px);
        }
      `}</style>
    </main>
  );
}
