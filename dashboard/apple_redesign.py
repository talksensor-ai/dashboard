import re

file_path = r"e:\talk\dashboard\src\app\page.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# ============================================================
# REPLACEMENTS — strictly className strings and text, NOT logic
# ============================================================

replacements = [
    # ---- Remove font import (already in globals.css) ----
    (
        """// Global Styles for branding and scrollbars
const fontImport = `
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
`;""",
        "// Font is imported in globals.css"
    ),
    
    # ---- Remove dangerouslySetInnerHTML for font import ----
    (
        '<style dangerouslySetInnerHTML={{ __html: fontImport }} />',
        ''
    ),

    # ---- Main container ----
    (
        'className="min-h-screen bg-zinc-50 dark:bg-[#050505] text-zinc-900 dark:text-white pb-32 font-sans selection:bg-black/10 dark:selection:bg-white/20 antialiased overflow-x-hidden transition-colors duration-300"',
        'className="min-h-screen bg-[#F5F5F7] dark:bg-black text-[#1D1D1F] dark:text-[#F5F5F7] pb-32 font-sans antialiased overflow-x-hidden transition-colors duration-300"'
    ),
    
    # ---- Remove radial gradient overlays ----
    (
        '<div className="fixed inset-0 bg-[radial-gradient(circle_at_top_right,_#101524_0%,_transparent_40%)] pointer-events-none opacity-20 dark:opacity-50"></div>',
        ''
    ),
    (
        '<div className="fixed inset-0 bg-[radial-gradient(circle_at_bottom_left,_#0a1510_0%,_transparent_40%)] pointer-events-none opacity-10 dark:opacity-30"></div>',
        ''
    ),

    # ---- Loading spinner ----
    (
        'className="min-h-screen bg-black text-zinc-900 dark:text-white flex items-center justify-center"',
        'className="min-h-screen bg-[#F5F5F7] dark:bg-black text-[#1D1D1F] dark:text-[#F5F5F7] flex items-center justify-center"'
    ),
    (
        'className="w-10 h-10 border-4 border-zinc-900 border-t-white rounded-full animate-spin"',
        'className="w-10 h-10 border-4 border-[#007AFF] border-t-transparent rounded-full animate-spin"'
    ),

    # ---- Header ----
    (
        'className="mb-12 flex items-center justify-between border-b border-black/5 dark:border-white/5 pb-10 relative"',
        'className="mb-10 flex items-center justify-between border-b border-black/[0.06] dark:border-white/[0.06] pb-8 relative"'
    ),
    
    # ---- Logo ----
    (
        """<div className="text-4xl tracking-tighter flex items-center gap-1 select-none" id="logo-dashboard-view">
                    <span className="font-sans font-medium text-zinc-500">talk:</span>
                    <span className="font-mono font-black text-zinc-900 dark:text-white tracking-[0.15em] bg-black/5 dark:bg-white/5 px-3 py-1 rounded-lg border border-black/10 dark:border-white/10 text-2xl shadow-[0_0_20px_rgba(255,255,255,0.05)]">core</span>
                  </div>""",
        """<div className="text-2xl flex items-center gap-1.5 select-none" id="logo-dashboard-view">
                    <span className="font-semibold text-[#86868B]">talk</span>
                    <span className="font-bold text-[#1D1D1F] dark:text-[#F5F5F7]">sensor</span>
                  </div>"""
    ),

    # ---- Desktop Tab Navigation (Segmented Control style) ----
    (
        'className="flex bg-zinc-100 dark:bg-[#0c0d12] p-1 rounded-xl border border-black/5 dark:border-white/5"',
        'className="flex bg-[#E5E5EA] dark:bg-[#38383A] p-1 rounded-xl"'
    ),
    # Active tab states
    (
        """className={`px-5 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${(view === 'dashboard' && !selectedShopId) ? 'bg-white dark:bg-zinc-800 text-black dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'}`}""",
        """className={`px-5 py-2 rounded-lg text-xs font-semibold transition-all ${(view === 'dashboard' && !selectedShopId) ? 'bg-white dark:bg-[#636366] text-[#1D1D1F] dark:text-white shadow-sm' : 'text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-white'}`}"""
    ),
    (
        """className={`px-5 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${(view === 'analytics' && !selectedShopId) ? 'bg-white dark:bg-zinc-800 text-black dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'}`}""",
        """className={`px-5 py-2 rounded-lg text-xs font-semibold transition-all ${(view === 'analytics' && !selectedShopId) ? 'bg-white dark:bg-[#636366] text-[#1D1D1F] dark:text-white shadow-sm' : 'text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-white'}`}"""
    ),
    (
        """className={`px-5 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${(view === 'admin' && !selectedShopId) ? 'bg-white dark:bg-zinc-800 text-black dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'}`}""",
        """className={`px-5 py-2 rounded-lg text-xs font-semibold transition-all ${(view === 'admin' && !selectedShopId) ? 'bg-white dark:bg-[#636366] text-[#1D1D1F] dark:text-white shadow-sm' : 'text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-white'}`}"""
    ),

    # ---- Dividers in header ----
    (
        'className="w-px h-6 bg-black/5 dark:bg-white/5"',
        'className="w-px h-5 bg-black/[0.08] dark:bg-white/[0.08]"'
    ),

    # ---- Archive label ----
    (
        'className="flex items-center gap-2 text-[10px] font-bold text-zinc-600 uppercase tracking-widest whitespace-nowrap"',
        'className="flex items-center gap-2 text-xs font-medium text-[#86868B] whitespace-nowrap"'
    ),

    # ---- Desktop date picker ----
    (
        'className="bg-white dark:bg-[#0c0d12] border border-black/5 dark:border-white/5 rounded-xl px-4 py-2 flex items-center text-[11px] font-bold uppercase text-zinc-600 dark:text-zinc-400 focus:outline-none [color-scheme:light] dark:[color-scheme:dark] cursor-pointer"',
        'className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-xl px-4 py-2 flex items-center text-sm font-medium text-[#1D1D1F] dark:text-[#F5F5F7] focus:outline-none [color-scheme:light] dark:[color-scheme:dark] cursor-pointer"'
    ),

    # ---- Back button (desktop) ----
    (
        'className="flex items-center gap-2 bg-zinc-100 dark:bg-zinc-900 hover:bg-zinc-200 dark:hover:bg-zinc-800 px-5 py-3 rounded-xl border border-black/5 dark:border-white/10 transition-all text-xs font-bold uppercase tracking-widest text-zinc-900 dark:text-white group shadow-sm"',
        'className="flex items-center gap-2 bg-white dark:bg-[#1C1C1E] hover:bg-[#E5E5EA] dark:hover:bg-[#38383A] px-5 py-3 rounded-xl border border-black/[0.06] dark:border-white/[0.08] transition-all text-sm font-semibold text-[#1D1D1F] dark:text-white group shadow-sm"'
    ),

    # ---- Mobile hamburger button ----
    (
        'className="flex items-center justify-center bg-zinc-100 dark:bg-zinc-900 border border-black/5 dark:border-white/5 rounded-lg w-10 h-10"',
        'className="flex items-center justify-center bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-xl w-10 h-10"'
    ),

    # ---- Mobile menu dropdown ----
    (
        'className="absolute top-full left-0 right-0 mt-4 bg-white dark:bg-zinc-900 border border-black/10 dark:border-white/10 rounded-2xl p-4 shadow-2xl z-50 flex flex-col md:hidden animate-in fade-in slide-in-from-top-4"',
        'className="absolute top-full left-0 right-0 mt-4 bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-4 shadow-lg z-50 flex flex-col md:hidden animate-in fade-in slide-in-from-top-4"'
    ),

    # ---- Mobile menu buttons ----
    (
        """`text-left px-4 py-3 rounded-xl font-bold ${view === 'dashboard' ? 'bg-zinc-100 dark:bg-black/20 text-black dark:text-white' : 'text-zinc-600 dark:text-zinc-400'}`""",
        """`text-left px-4 py-3 rounded-xl font-semibold ${view === 'dashboard' ? 'bg-[#007AFF]/10 text-[#007AFF]' : 'text-[#86868B]'}`"""
    ),
    (
        """`text-left px-4 py-3 rounded-xl font-bold ${view === 'analytics' ? 'bg-zinc-100 dark:bg-black/20 text-black dark:text-white' : 'text-zinc-600 dark:text-zinc-400'}`""",
        """`text-left px-4 py-3 rounded-xl font-semibold ${view === 'analytics' ? 'bg-[#007AFF]/10 text-[#007AFF]' : 'text-[#86868B]'}`"""
    ),
    (
        """`text-left px-4 py-3 rounded-xl font-bold ${view === 'admin' ? 'bg-zinc-100 dark:bg-black/20 text-black dark:text-white' : 'text-zinc-600 dark:text-zinc-400'}`""",
        """`text-left px-4 py-3 rounded-xl font-semibold ${view === 'admin' ? 'bg-[#007AFF]/10 text-[#007AFF]' : 'text-[#86868B]'}`"""
    ),

    # ---- Mobile menu divider ----
    (
        'className="w-full h-px bg-black/5 dark:bg-white/5 my-2"',
        'className="w-full h-px bg-black/[0.06] dark:bg-white/[0.06] my-2"'
    ),
    (
        'className="font-bold text-sm text-zinc-600 dark:text-white"',
        'className="font-medium text-sm text-[#86868B] dark:text-[#F5F5F7]"'
    ),

    # ============================================================
    # VIEW 1: NETWORK / DASHBOARD
    # ============================================================

    # ---- Date carousel card (selected) ----
    (
        """className={`snap-center flex-shrink-0 flex flex-col justify-between p-4 rounded-3xl border transition-all h-24 w-40 text-left cursor-pointer
                              ${isSelected 
                                ? 'bg-zinc-900 dark:bg-white border-transparent shadow-xl' 
                                : 'bg-white dark:bg-[#0c0d12] hover:bg-zinc-100 dark:bg-zinc-900 border-black/5 dark:border-white/5'}`}""",
        """className={`snap-center flex-shrink-0 flex flex-col justify-between p-4 rounded-2xl border transition-all h-24 w-40 text-left cursor-pointer
                              ${isSelected 
                                ? 'bg-[#007AFF] border-transparent shadow-lg shadow-[#007AFF]/20' 
                                : 'bg-white dark:bg-[#1C1C1E] hover:bg-white/80 dark:hover:bg-[#2C2C2E] border-black/[0.06] dark:border-white/[0.08]'}`}"""
    ),
    
    # Date carousel text
    (
        """className={`text-[10px] font-bold ${isSelected ? 'text-white dark:text-black' : 'text-zinc-500'}`}""",
        """className={`text-xs font-medium ${isSelected ? 'text-white' : 'text-[#86868B]'}`}"""
    ),
    (
        """className={`text-xl font-black tracking-tighter ${isSelected ? 'text-white dark:text-black' : 'text-zinc-900 dark:text-white'}`}""",
        """className={`text-xl font-bold ${isSelected ? 'text-white' : 'text-[#1D1D1F] dark:text-[#F5F5F7]'}`}"""
    ),
    (
        """className={`text-[8px] font-bold uppercase tracking-widest ${isSelected ? 'text-white/60 dark:text-black/60' : 'text-zinc-500 dark:text-zinc-600'}`}""",
        """className={`text-[10px] font-medium ${isSelected ? 'text-white/70' : 'text-[#86868B]'}`}"""
    ),

    # ---- Network chart section ----
    (
        'className="bg-white dark:bg-[#0c0d12]/60 border border-black/5 dark:border-white/5 rounded-2xl overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-2xl backdrop-blur-xl"',
        'className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl overflow-hidden shadow-sm"'
    ),
    (
        'className="p-10 border-b border-black/5 dark:border-white/5 bg-gradient-to-br from-black/[0.02] dark:from-white/[0.02] to-transparent"',
        'className="p-8 border-b border-black/[0.06] dark:border-white/[0.06]"'
    ),
    (
        """<TrendingUp size={18} className="text-zinc-600" />
                         <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] text-zinc-600">Сетевая динамика</h3>""",
        """<TrendingUp size={16} className="text-[#86868B]" />
                         <h3 className="text-xs font-semibold text-[#86868B]">Сетевая динамика</h3>"""
    ),
    
    # ---- Chart gradient colors: emerald -> Apple blue ----
    (
        '<stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>',
        '<stop offset="5%" stopColor="#007AFF" stopOpacity={0.2}/>'
    ),
    (
        '<stop offset="95%" stopColor="#10b981" stopOpacity={0}/>',
        '<stop offset="95%" stopColor="#007AFF" stopOpacity={0}/>'
    ),
    (
        'stroke="#10b981"',
        'stroke="#007AFF"'
    ),

    # ---- Analytics section inside network view ----
    (
        'className="p-8 border-r border-black/5 dark:border-white/5"',
        'className="p-8 border-r border-black/[0.06] dark:border-white/[0.06]"'
    ),
    (
        """<AlertTriangle size={18} className="text-zinc-900 dark:text-white" />
                           <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-900 dark:text-white">Краткая аналитика</h3>""",
        """<AlertTriangle size={16} className="text-[#1D1D1F] dark:text-[#F5F5F7]" />
                           <h3 className="text-xs font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]">Краткая аналитика</h3>"""
    ),
    
    # Analytics progress bar items
    (
        'className="text-[10px] font-bold uppercase tracking-widest text-zinc-600 dark:text-zinc-400"',
        'className="text-xs font-medium text-[#86868B]"'
    ),
    (
        'className="h-1 w-full bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden"',
        'className="h-1.5 w-full bg-[#E5E5EA] dark:bg-[#38383A] rounded-full overflow-hidden"'
    ),
    (
        'className="h-full bg-zinc-900 dark:bg-zinc-100"',
        'className="h-full bg-[#007AFF] rounded-full"'
    ),

    # ---- Rating section ----
    (
        """<Star size={18} className="text-zinc-500" />
                           <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Рейтинг локаций</h3>""",
        """<Star size={16} className="text-[#86868B]" />
                           <h3 className="text-xs font-semibold text-[#86868B]">Рейтинг локаций</h3>"""
    ),
    
    # Rating list items
    (
        'className="flex items-center justify-between group cursor-pointer hover:bg-black/5 dark:hover:bg-white/5 p-2 rounded-xl transition-all"',
        'className="flex items-center justify-between group cursor-pointer hover:bg-black/[0.03] dark:hover:bg-white/[0.05] p-3 rounded-xl transition-all"'
    ),
    (
        'className="text-xs font-bold text-zinc-600"',
        'className="text-xs font-medium text-[#86868B]"'
    ),
    (
        'className="text-sm font-bold text-zinc-700 dark:text-zinc-300"',
        'className="text-sm font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]"'
    ),
    (
        'className="text-sm font-black text-emerald-500/80"',
        'className="text-sm font-bold text-[#007AFF]"'
    ),

    # ---- Shop cards ----
    (
        'className="bg-white dark:bg-[#0f1115]/60 border border-black/5 dark:border-white/5 rounded-2xl p-8 transition-all hover:bg-white dark:bg-[#0f1115]/80 shadow-xl flex flex-col justify-between"',
        'className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-8 transition-all hover:shadow-md shadow-sm flex flex-col justify-between"'
    ),
    (
        'className="text-2xl font-bold tracking-tighter text-zinc-900 dark:text-white"',
        'className="text-xl font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]"'
    ),
    (
        'className="text-xl font-black text-zinc-900 dark:text-white"',
        'className="text-xl font-bold text-[#1D1D1F] dark:text-[#F5F5F7]"'
    ),
    
    # Shop card metrics label
    (
        'className="flex items-center justify-between text-zinc-500 text-[10px] font-bold uppercase tracking-widest"',
        'className="flex items-center justify-between text-[#86868B] text-xs font-medium"'
    ),
    
    # Shop card "Today" / "Weekly" labels
    (
        'className="flex justify-between items-end text-xs font-bold text-zinc-600 dark:text-zinc-400"',
        'className="flex justify-between items-end text-xs font-medium text-[#86868B]"'
    ),
    (
        """<span className="text-zinc-900 dark:text-white">{shop.avgScorePercent}%</span>""",
        """<span className="text-[#1D1D1F] dark:text-[#F5F5F7] font-semibold">{shop.avgScorePercent}%</span>"""
    ),
    
    # Shop card progress bars
    (
        'className="h-1.5 w-full bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden"',
        'className="h-1.5 w-full bg-[#E5E5EA] dark:bg-[#38383A] rounded-full overflow-hidden"'
    ),

    (
        'className="flex justify-between items-end text-xs font-bold text-zinc-500 mt-2"',
        'className="flex justify-between items-end text-xs font-medium text-[#86868B] mt-2"'
    ),
    (
        """<span className="text-zinc-900 dark:text-white/60">{shop.weeklyAvgPercent}%</span>""",
        """<span className="text-[#1D1D1F] dark:text-[#F5F5F7]/60 font-semibold">{shop.weeklyAvgPercent}%</span>"""
    ),
    (
        'className="h-full bg-zinc-400 dark:bg-zinc-500"',
        'className="h-full bg-[#86868B] rounded-full"'
    ),
    
    # Shop card "Подробнее" button
    (
        'className="mt-8 w-full py-3 border border-black/5 dark:border-white/5 rounded-xl font-bold uppercase tracking-widest text-[10px] text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:text-white hover:bg-black/5 dark:hover:bg-white/5 transition-all"',
        'className="mt-8 w-full py-3 rounded-xl font-semibold text-sm text-[#007AFF] hover:bg-[#007AFF]/5 transition-all"'
    ),

    # ============================================================
    # VIEW 2: SHOP DETAILS
    # ============================================================
    (
        'className="md:col-span-8 bg-white dark:bg-[#0c0d12]/60 border border-black/5 dark:border-white/5 rounded-2xl p-10"',
        'className="md:col-span-8 bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-8"'
    ),
    (
        'className="text-3xl md:text-4xl font-bold tracking-tighter mb-4 text-zinc-900 dark:text-white break-words"',
        'className="text-2xl md:text-3xl font-semibold mb-4 text-[#1D1D1F] dark:text-[#F5F5F7] break-words"'
    ),
    # Stats labels in shop details
    (
        'className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1"',
        'className="text-xs font-medium text-[#86868B] mb-1"'
    ),
    (
        'className="text-2xl font-bold text-zinc-900 dark:text-white"',
        'className="text-2xl font-bold text-[#1D1D1F] dark:text-[#F5F5F7]"'
    ),
    
    # Status pill
    (
        'className="bg-zinc-100 dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 px-5 py-3 rounded-xl flex items-center gap-3 text-[10px] font-bold uppercase tracking-widest border border-black/5 dark:border-white/5"',
        'className="bg-[#F2F2F7] dark:bg-[#2C2C2E] text-[#1D1D1F] dark:text-[#F5F5F7] px-4 py-2.5 rounded-xl flex items-center gap-3 text-xs font-medium border border-black/[0.06] dark:border-white/[0.08]"'
    ),
    (
        'className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"',
        'className="w-2 h-2 bg-[#34C759] rounded-full animate-pulse"'
    ),
    
    # Shop details right panel
    (
        'className="md:col-span-4 bg-white dark:bg-[#0c0d12]/60 border border-black/5 dark:border-white/5 rounded-2xl p-10"',
        'className="md:col-span-4 bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-8"'
    ),
    (
        'className="flex items-center gap-3 mb-8 text-zinc-600"',
        'className="flex items-center gap-3 mb-6 text-[#86868B]"'
    ),
    (
        """<h3 className="text-[10px] font-bold uppercase tracking-widest">Аналитика по пунктам</h3>""",
        """<h3 className="text-xs font-semibold">Аналитика по пунктам</h3>"""
    ),
    
    # Shop performance stats
    (
        'className="flex justify-between items-center text-[10px] font-bold uppercase tracking-widest text-zinc-500"',
        'className="flex justify-between items-center text-xs font-medium text-[#86868B]"'
    ),
    (
        'className="text-zinc-600 dark:text-zinc-400"',
        'className="text-[#1D1D1F] dark:text-[#F5F5F7]"'
    ),
    (
        'className="h-1 bg-black/40 rounded-full overflow-hidden"',
        'className="h-1.5 bg-[#E5E5EA] dark:bg-[#38383A] rounded-full overflow-hidden"'
    ),
    (
        'className="h-full bg-emerald-500/40"',
        'className="h-full bg-[#34C759] rounded-full"'
    ),
    
    # Dialog list items
    (
        """className={`bg-white dark:bg-[#0c0d12]/40 border ${expandedDialogId === dialog.id ? 'border-zinc-700' : 'border-black/5 dark:border-white/5'} rounded-2xl overflow-hidden`}""",
        """className={`bg-white dark:bg-[#1C1C1E] border ${expandedDialogId === dialog.id ? 'border-[#007AFF]/30' : 'border-black/[0.06] dark:border-white/[0.08]'} rounded-2xl overflow-hidden shadow-sm`}"""
    ),
    (
        'className="text-xl font-bold tracking-tighter text-zinc-900 dark:text-white"',
        'className="text-lg font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]"'
    ),
    (
        'className="text-xs text-zinc-400 font-mono mt-0.5"',
        'className="text-xs text-[#86868B] font-mono mt-0.5"'
    ),
    (
        'className="text-[11px] font-bold text-zinc-500 uppercase"',
        'className="text-xs font-medium text-[#86868B]"'
    ),
    
    # Dialog badges
    (
        'className="bg-zinc-500/10 text-zinc-500 border border-zinc-500/20 px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest"',
        'className="bg-[#E5E5EA] dark:bg-[#38383A] text-[#86868B] px-3 py-1 rounded-full text-[10px] font-semibold"'
    ),
    (
        'className="bg-blue-500/10 text-blue-500 border border-blue-500/20 px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest"',
        'className="bg-[#007AFF]/10 text-[#007AFF] px-3 py-1 rounded-full text-[10px] font-semibold"'
    ),
    (
        'className="bg-amber-500/10 text-amber-500 border border-amber-500/20 px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest"',
        'className="bg-[#FF9500]/10 text-[#FF9500] px-3 py-1 rounded-full text-[10px] font-semibold"'
    ),
    (
        'className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest"',
        'className="bg-[#34C759]/10 text-[#34C759] px-3 py-1 rounded-full text-[10px] font-semibold"'
    ),
    (
        'className="bg-rose-500 text-white border border-rose-500/20 px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest animate-pulse shadow-[0_0_10px_rgba(244,63,94,0.5)]"',
        'className="bg-[#FF3B30] text-white px-3 py-1 rounded-full text-[10px] font-semibold animate-pulse"'
    ),

    # Dialog score display
    (
        """className={`text-4xl font-light tracking-tight ${!dialog.audit_details ? 'text-zinc-500 text-3xl' : dialog.audit_details.dialogue_type === 'dialog' ? 'text-amber-500/50 text-3xl' : (getDialogPercent(dialog) >= 80 ? 'text-emerald-500' : 'text-rose-500')}`}""",
        """className={`text-3xl font-semibold ${!dialog.audit_details ? 'text-[#86868B]' : dialog.audit_details.dialogue_type === 'dialog' ? 'text-[#FF9500]/60' : (getDialogPercent(dialog) >= 80 ? 'text-[#34C759]' : 'text-[#FF3B30]')}`}"""
    ),

    # Expanded dialog section
    (
        'className="px-10 pb-12 pt-6 border-t border-black/5 dark:border-white/5"',
        'className="px-8 pb-10 pt-6 border-t border-black/[0.06] dark:border-white/[0.06]"'
    ),
    (
        'className="bg-white text-black px-8 py-4 rounded-xl font-bold uppercase text-xs"',
        'className="bg-[#007AFF] text-white px-6 py-3 rounded-xl font-semibold text-sm hover:bg-[#0066CC] transition-colors"'
    ),
    (
        'className="bg-white dark:bg-[#0c0d12] p-8 rounded-2xl border border-black/5 dark:border-white/5 space-y-6"',
        'className="bg-[#F2F2F7] dark:bg-[#2C2C2E] p-6 rounded-2xl space-y-6"'
    ),
    
    # QA scores header
    (
        """<h4 className="text-[10px] font-bold text-zinc-500 uppercase">Оценки QA (Заказ)</h4>""",
        """<h4 className="text-xs font-semibold text-[#86868B]">Оценки QA (Заказ)</h4>"""
    ),
    
    # QA score items
    (
        'className="flex justify-between items-center text-[9px] font-bold uppercase tracking-widest text-zinc-600 dark:text-zinc-400"',
        'className="flex justify-between items-center text-xs font-medium text-[#86868B]"'
    ),
    (
        'className="h-1.5 bg-black/50 rounded-full overflow-hidden"',
        'className="h-1.5 bg-[#E5E5EA] dark:bg-[#38383A] rounded-full overflow-hidden"'
    ),
    (
        '? "text-emerald-500" : "text-rose-500"',
        '? "text-[#34C759]" : "text-[#FF3B30]"'
    ),
    (
        '? "bg-emerald-500/70" : "bg-rose-500/70"',
        '? "bg-[#34C759]" : "bg-[#FF3B30]"'
    ),
    (
        '"bg-zinc-700"',
        '"bg-[#86868B]"'
    ),
    (
        '"text-zinc-600"',
        '"text-[#86868B]"'
    ),
    
    # Live service
    (
        """<h4 className="text-[10px] font-bold text-amber-500 uppercase flex items-center gap-2">""",
        """<h4 className="text-xs font-semibold text-[#FF9500] flex items-center gap-2">"""
    ),
    (
        """`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${(dialog.audit_details.live_service_score || 0) >= 75 ? 'bg-amber-500 text-black shadow-lg shadow-amber-500/20' : 'bg-black/10 dark:bg-white/10 text-zinc-500'}`""",
        """`px-3 py-1 rounded-full text-xs font-bold ${(dialog.audit_details.live_service_score || 0) >= 75 ? 'bg-[#FF9500] text-white' : 'bg-[#E5E5EA] dark:bg-[#38383A] text-[#86868B]'}`"""
    ),
    
    # Emotion stats
    (
        """<h4 className="text-[10px] font-bold text-indigo-500 uppercase flex items-center gap-2">""",
        """<h4 className="text-xs font-semibold text-[#5856D6] flex items-center gap-2">"""
    ),
    (
        'className="bg-rose-500 text-white px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest shadow-lg shadow-rose-500/30 animate-pulse"',
        'className="bg-[#FF3B30] text-white px-3 py-1 rounded-full text-[10px] font-semibold animate-pulse"'
    ),
    (
        'className="flex justify-between text-[9px] font-bold uppercase tracking-widest text-zinc-600 dark:text-zinc-400"',
        'className="flex justify-between text-xs font-medium text-[#86868B]"'
    ),
    (
        'className="h-1.5 w-full bg-black/10 dark:bg-white/10 rounded-full overflow-hidden"',
        'className="h-1.5 w-full bg-[#E5E5EA] dark:bg-[#38383A] rounded-full overflow-hidden"'
    ),
    
    # Critical errors + additional service
    (
        'className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl"',
        'className="p-4 bg-[#FF3B30]/10 border border-[#FF3B30]/20 rounded-xl"'
    ),
    (
        """<h4 className="text-[10px] font-bold text-rose-500 uppercase mb-2">Критические ошибки</h4>""",
        """<h4 className="text-xs font-semibold text-[#FF3B30] mb-2">Критические ошибки</h4>"""
    ),
    (
        'className="text-sm text-zinc-700 dark:text-zinc-300"',
        'className="text-sm text-[#1D1D1F] dark:text-[#F5F5F7]"'
    ),
    (
        'className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl"',
        'className="p-4 bg-[#34C759]/10 border border-[#34C759]/20 rounded-xl"'
    ),
    (
        """<h4 className="text-[10px] font-bold text-emerald-500 uppercase mb-2">Дополнительный сервис</h4>""",
        """<h4 className="text-xs font-semibold text-[#34C759] mb-2">Дополнительный сервис</h4>"""
    ),
    
    # QA recommendation
    (
        """<h4 className="text-[10px] font-bold text-zinc-500 uppercase mb-2">Рекомендация QA</h4>""",
        """<h4 className="text-xs font-semibold text-[#86868B] mb-2">Рекомендация QA</h4>"""
    ),
    (
        'className="text-sm text-zinc-600 dark:text-zinc-400 italic"',
        'className="text-sm text-[#86868B] italic"'
    ),

    # Transcript container
    (
        'className="bg-zinc-50 dark:bg-black/20 p-6 md:p-8 rounded-3xl h-[500px] overflow-y-auto custom-scrollbar border border-black/5 dark:border-white/5 shadow-inner dark:shadow-none relative flex flex-col gap-3"',
        'className="bg-[#F2F2F7] dark:bg-[#2C2C2E] p-6 md:p-8 rounded-2xl h-[500px] overflow-y-auto custom-scrollbar border border-black/[0.06] dark:border-white/[0.08] relative flex flex-col gap-3"'
    ),
    
    # Transcript speaker labels (emerald -> Apple green, indigo -> Apple blue)
    (
        """'text-emerald-500 dark:text-emerald-400'""",
        """'text-[#34C759]'"""
    ),
    (
        """'text-indigo-500 dark:text-indigo-400'""",
        """'text-[#007AFF]'"""
    ),
    
    # Transcript bubbles - barista active
    (
        "'bg-gradient-to-r from-emerald-500/10 to-emerald-500/5 border-l-4 border-l-emerald-500 border-y-emerald-500/10 border-r-emerald-500/10 dark:border-y-emerald-500/20 dark:border-r-emerald-500/20 shadow-[0_4px_20px_rgba(16,185,129,0.1)] text-emerald-950 dark:text-emerald-100'",
        "'bg-[#34C759]/10 border-l-4 border-l-[#34C759] border-y-transparent border-r-transparent text-[#1D1D1F] dark:text-[#F5F5F7]'"
    ),
    # Transcript bubbles - barista idle
    (
        "'bg-white dark:bg-zinc-900/40 border-l-4 border-l-emerald-500/50 border-y-transparent border-r-transparent hover:bg-zinc-100 dark:hover:bg-zinc-900/60 border-t-transparent border-b-transparent border-r-transparent text-zinc-700 dark:text-zinc-300'",
        "'bg-white dark:bg-[#1C1C1E] border-l-4 border-l-[#34C759]/40 border-y-transparent border-r-transparent hover:bg-[#E5E5EA] dark:hover:bg-[#38383A] text-[#1D1D1F] dark:text-[#F5F5F7]'"
    ),
    # Transcript bubbles - customer active
    (
        "'bg-gradient-to-r from-indigo-500/10 to-indigo-500/5 border-l-4 border-l-indigo-500 border-y-indigo-500/10 border-r-indigo-500/10 dark:border-y-indigo-500/20 dark:border-r-indigo-500/20 shadow-[0_4px_20px_rgba(99,102,241,0.1)] text-indigo-950 dark:text-indigo-100'",
        "'bg-[#007AFF]/10 border-l-4 border-l-[#007AFF] border-y-transparent border-r-transparent text-[#1D1D1F] dark:text-[#F5F5F7]'"
    ),
    # Transcript bubbles - customer idle
    (
        "'bg-white dark:bg-zinc-900/40 border-l-4 border-l-indigo-500/50 border-y-transparent border-r-transparent hover:bg-zinc-100 dark:hover:bg-zinc-900/60 border-t-transparent border-b-transparent border-r-transparent text-zinc-700 dark:text-zinc-300'",
        "'bg-white dark:bg-[#1C1C1E] border-l-4 border-l-[#007AFF]/40 border-y-transparent border-r-transparent hover:bg-[#E5E5EA] dark:hover:bg-[#38383A] text-[#1D1D1F] dark:text-[#F5F5F7]'"
    ),
    # Transcript text
    (
        'className="text-zinc-900 dark:text-white text-sm leading-relaxed"',
        'className="text-[#1D1D1F] dark:text-[#F5F5F7] text-sm leading-relaxed"'
    ),

    # ============================================================
    # VIEW 3: ANALYTICS
    # ============================================================
    (
        'className="bg-white dark:bg-[#0f1115]/80 border border-emerald-500/20 rounded-2xl p-10 flex flex-col justify-between shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-2xl relative overflow-hidden"',
        'className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-8 flex flex-col justify-between shadow-sm relative overflow-hidden"'
    ),
    (
        'className="absolute -right-20 -bottom-20 w-64 h-64 bg-emerald-500/10 blur-[100px] rounded-full pointer-events-none"',
        'className="absolute -right-20 -bottom-20 w-64 h-64 bg-[#34C759]/5 blur-[100px] rounded-full pointer-events-none"'
    ),
    (
        """<h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-emerald-500 mb-8 flex items-center gap-2">
                            <TrendingUp size={14} /> Производительность сети""",
        """<h3 className="text-xs font-semibold text-[#34C759] mb-6 flex items-center gap-2">
                            <TrendingUp size={14} /> Производительность сети"""
    ),
    (
        'className="text-7xl font-black italic tracking-tighter text-zinc-900 dark:text-white mb-2"',
        'className="text-5xl font-bold text-[#1D1D1F] dark:text-[#F5F5F7] mb-2"'
    ),
    (
        'className="text-xs font-bold text-zinc-500 uppercase tracking-widest"',
        'className="text-sm font-medium text-[#86868B]"'
    ),

    # Lost revenue card
    (
        'className="lg:col-span-2 bg-white dark:bg-[#0a0505]/80 border border-rose-500/20 rounded-2xl p-10 flex flex-col justify-between shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-2xl relative overflow-hidden"',
        'className="lg:col-span-2 bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-8 flex flex-col justify-between shadow-sm relative overflow-hidden"'
    ),
    (
        'className="absolute top-0 right-0 w-full h-full bg-gradient-to-l from-rose-500/5 to-transparent pointer-events-none"',
        'className="absolute top-0 right-0 w-full h-full bg-gradient-to-l from-[#FF3B30]/3 to-transparent pointer-events-none"'
    ),
    (
        """<h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-rose-500 mb-8 flex items-center gap-2">
                                <AlertTriangle size={14} /> Упущенная выгода (LTV + Продажи)""",
        """<h3 className="text-xs font-semibold text-[#FF3B30] mb-6 flex items-center gap-2">
                                <AlertTriangle size={14} /> Упущенная выгода (LTV + Продажи)"""
    ),
    (
        'className="text-6xl font-black italic tracking-tighter text-rose-500 mb-3"',
        'className="text-4xl font-bold text-[#FF3B30] mb-3"'
    ),
    (
        'className="flex flex-col md:flex-row bg-rose-50/50 dark:bg-[#140b0b] rounded-xl border border-rose-500/10 p-5 gap-8"',
        'className="flex flex-col md:flex-row bg-[#FF3B30]/5 dark:bg-[#FF3B30]/10 rounded-xl border border-[#FF3B30]/10 p-5 gap-8"'
    ),
    (
        'className="text-[9px] font-bold text-rose-500/60 uppercase tracking-widest"',
        'className="text-xs font-medium text-[#FF3B30]/70"'
    ),
    (
        'className="text-xl font-bold text-rose-500"',
        'className="text-xl font-bold text-[#FF3B30]"'
    ),
    
    # Weakest point card
    (
        'className="bg-white dark:bg-[#0c0d12]/60 border border-black/5 dark:border-white/5 rounded-2xl p-10"',
        'className="bg-white dark:bg-[#1C1C1E] border border-black/[0.06] dark:border-white/[0.08] rounded-2xl p-8"'
    ),
    (
        """<h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 mb-8 flex items-center gap-2">""",
        """<h3 className="text-xs font-semibold text-[#86868B] mb-6 flex items-center gap-2">"""
    ),
    (
        'className="text-3xl font-black tracking-tighter text-zinc-900 dark:text-white"',
        'className="text-2xl font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]"'
    ),
    (
        'className="text-2xl font-bold text-rose-500/80"',
        'className="text-2xl font-bold text-[#FF3B30]"'
    ),
    (
        'className="h-2 w-full bg-black/40 rounded-full overflow-hidden"',
        'className="h-2 w-full bg-[#E5E5EA] dark:bg-[#38383A] rounded-full overflow-hidden"'
    ),
    (
        'className="h-full bg-rose-500/50"',
        'className="h-full bg-[#FF3B30] rounded-full"'
    ),
    (
        """<p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mt-6">""",
        """<p className="text-xs font-medium text-[#86868B] mt-4">"""
    ),
    
    # Best shifts
    (
        'className="flex items-center justify-between bg-white/[0.02] p-4 rounded-xl border border-black/5 dark:border-white/5"',
        'className="flex items-center justify-between bg-[#F2F2F7] dark:bg-[#2C2C2E] p-4 rounded-xl"'
    ),
    (
        """`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-black ${idx === 0 ? 'bg-amber-500 text-black' : 'bg-zinc-200 dark:bg-zinc-800 text-zinc-900 dark:text-white'}`""",
        """`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${idx === 0 ? 'bg-[#FF9500] text-white' : 'bg-[#E5E5EA] dark:bg-[#38383A] text-[#1D1D1F] dark:text-[#F5F5F7]'}`"""
    ),
    (
        'className="text-sm font-bold"',
        'className="text-sm font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]"'
    ),
    (
        'className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest"',
        'className="text-xs font-medium text-[#86868B]"'
    ),
    (
        'className="text-xl font-black italic text-emerald-500/80"',
        'className="text-xl font-bold text-[#34C759]"'
    ),

    # ============================================================
    # VIEW 4: ADMIN
    # ============================================================
    (
        """<h2 className="text-3xl font-black tracking-tighter flex items-center gap-3 text-zinc-900 dark:text-white">
                      <ShieldCheck className="text-indigo-500 animate-pulse" /> Офис агентов (Служба оркестрации)""",
        """<h2 className="text-2xl font-semibold flex items-center gap-3 text-[#1D1D1F] dark:text-[#F5F5F7]">
                      <ShieldCheck className="text-[#5856D6]" /> Офис агентов"""
    ),
    
    # Office zone title
    (
        """<h3 className="text-xl font-black uppercase tracking-[0.2em] text-zinc-800 dark:text-white/70 mb-10 text-center relative z-10 border-b border-black/5 dark:border-white/10 pb-4">
                         🏢 Секретный Офис (Work Zone)""",
        """<h3 className="text-lg font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]/80 mb-8 text-center relative z-10 border-b border-black/[0.06] dark:border-white/[0.06] pb-4">
                         Рабочая зона"""
    ),
    
    # Chill zone title
    (
        """<h3 className="text-xl font-black uppercase tracking-[0.2em] text-zinc-800 dark:text-white/70 mb-10 text-center relative z-10 border-b border-black/5 dark:border-white/10 pb-4">
                         🍕 Чилл-Зона (Idle)""",
        """<h3 className="text-lg font-semibold text-[#1D1D1F] dark:text-[#F5F5F7]/80 mb-8 text-center relative z-10 border-b border-black/[0.06] dark:border-white/[0.06] pb-4">
                         Ожидание"""
    ),
    
    # Idle agent labels
    (
        """<h4 className="font-black uppercase tracking-widest text-xs text-zinc-900 dark:text-white">""",
        """<h4 className="font-semibold text-sm text-[#1D1D1F] dark:text-[#F5F5F7]">"""
    ),
    (
        """<p className="text-[10px] font-bold text-zinc-400 dark:text-zinc-500 uppercase mt-0.5">Ест пиццу / Ожидает задачи</p>""",
        """<p className="text-xs font-medium text-[#86868B] mt-0.5">Ожидает задачи</p>"""
    ),
    
    # Empty chill zone
    (
        """<div className="text-zinc-400 dark:text-zinc-500 text-sm italic py-10 text-center w-full">Чилл-зона пуста. Все ебашат!</div>""",
        """<div className="text-[#86868B] text-sm py-10 text-center w-full">Все агенты заняты</div>"""
    ),

    # ============================================================
    # AUDIO PLAYER (bottom bar)
    # ============================================================
    (
        'className="bg-zinc-900/90 dark:bg-black/80 backdrop-blur-2xl border border-white/10 rounded-3xl md:rounded-full p-4 md:p-5 flex flex-col md:flex-row items-center gap-4 md:gap-8 shadow-[0_20px_50px_rgba(0,0,0,0.5)]"',
        'className="bg-white/90 dark:bg-[#1C1C1E]/90 backdrop-blur-2xl border border-black/[0.08] dark:border-white/[0.08] rounded-2xl md:rounded-full p-4 md:p-5 flex flex-col md:flex-row items-center gap-4 md:gap-8 shadow-lg"'
    ),
    
    # Player gradient icon
    (
        'className="w-12 h-12 bg-gradient-to-tr from-emerald-500 to-indigo-600 rounded-2xl flex items-center justify-center shrink-0 shadow-lg shadow-emerald-500/10 relative overflow-hidden group"',
        'className="w-12 h-12 bg-gradient-to-tr from-[#007AFF] to-[#5856D6] rounded-2xl flex items-center justify-center shrink-0 shadow-md relative overflow-hidden group"'
    ),
    
    # Player dialog title
    (
        'className="font-bold text-sm tracking-tight text-white line-clamp-1"',
        'className="font-semibold text-sm text-[#1D1D1F] dark:text-[#F5F5F7] line-clamp-1"'
    ),
    (
        'className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider line-clamp-1"',
        'className="text-xs font-medium text-[#86868B] line-clamp-1"'
    ),
    
    # Player close button (mobile)
    (
        'className="md:hidden w-8 h-8 flex items-center justify-center text-zinc-400 hover:text-white transition-colors bg-white/5 rounded-full"',
        'className="md:hidden w-8 h-8 flex items-center justify-center text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-white transition-colors bg-black/5 dark:bg-white/5 rounded-full"'
    ),
    
    # Player controls
    (
        'className="text-zinc-400 hover:text-white transition-colors p-1"',
        'className="text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-white transition-colors p-1"'
    ),
    (
        'className="w-11 h-11 bg-white hover:bg-zinc-200 text-black rounded-full flex items-center justify-center shadow-xl hover:scale-105 active:scale-95 transition-all"',
        'className="w-11 h-11 bg-[#007AFF] hover:bg-[#0066CC] text-white rounded-full flex items-center justify-center shadow-md hover:scale-105 active:scale-95 transition-all"'
    ),
    (
        '<PauseCircle size={22} className="text-black" />',
        '<PauseCircle size={22} className="text-white" />'
    ),
    (
        '<PlayCircle size={24} className="ml-0.5 text-black" />',
        '<PlayCircle size={24} className="ml-0.5 text-white" />'
    ),
    
    # Player progress time labels
    (
        'className="text-[10px] font-bold text-zinc-400 min-w-[35px] font-mono text-right"',
        'className="text-[10px] font-medium text-[#86868B] min-w-[35px] font-mono text-right"'
    ),
    (
        'className="text-[10px] font-bold text-zinc-400 min-w-[35px] font-mono"',
        'className="text-[10px] font-medium text-[#86868B] min-w-[35px] font-mono"'
    ),
    
    # Player progress bar
    (
        'className="flex-1 relative h-2 bg-white/10 rounded-full overflow-hidden flex items-center group"',
        'className="flex-1 relative h-2 bg-[#E5E5EA] dark:bg-[#38383A] rounded-full overflow-hidden flex items-center group"'
    ),
    (
        'className="absolute left-0 top-0 bottom-0 bg-gradient-to-r from-emerald-500 via-emerald-400 to-indigo-500 pointer-events-none transition-all duration-75 group-hover:from-emerald-400 group-hover:to-indigo-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]"',
        'className="absolute left-0 top-0 bottom-0 bg-[#007AFF] pointer-events-none transition-all duration-75 rounded-full"'
    ),
    
    # No audio message
    (
        'className="text-xs font-bold text-zinc-300"',
        'className="text-xs font-medium text-[#86868B]"'
    ),
    (
        'className="text-[9px] text-zinc-500 uppercase tracking-widest mt-1"',
        'className="text-[10px] text-[#86868B] mt-1"'
    ),
    
    # Player close button (desktop)
    (
        'className="hidden md:flex w-10 h-10 items-center justify-center text-zinc-400 hover:text-white hover:bg-white/5 transition-colors rounded-full shrink-0"',
        'className="hidden md:flex w-10 h-10 items-center justify-center text-[#86868B] hover:text-[#1D1D1F] dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 transition-colors rounded-full shrink-0"'
    ),
]

# Apply all replacements
count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new, 1)
        count += 1

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Applied {count}/{len(replacements)} replacements successfully.")
