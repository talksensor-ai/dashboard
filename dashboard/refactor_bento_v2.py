import re
import os

file_path = r"e:\talk\dashboard\src\app\page.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Imports
if "import { BentoGrid" not in content:
    content = content.replace(
        'import { ThemeToggle }', 
        'import { BentoGrid, BentoGridItem } from "@/components/ui/bento-grid";\nimport { Button } from "@pikoloo/darwin-ui";\nimport { ThemeToggle }'
    )
    
lucide_old = '''  ShieldCheck, Clock, Volume2, PlayCircle, PauseCircle, 
  ChevronLeft, AlertTriangle, TrendingUp, Star, Calendar 
} from "lucide-react";'''
lucide_new = '''  ShieldCheck, Clock, Volume2, PlayCircle, PauseCircle, Play, Pause,
  ChevronLeft, AlertTriangle, TrendingUp, Star, Calendar, Activity, Briefcase, Menu, X
} from "lucide-react";'''
content = content.replace(lucide_old, lucide_new)

# 2. Remove fontImport and <style dangerouslySetInnerHTML={{ __html: fontImport }} />
content = re.sub(r'const fontImport = `\n.*?`;\n', '', content, flags=re.DOTALL)
content = content.replace('<style dangerouslySetInnerHTML={{ __html: fontImport }} />', '')

# 3. Refactor main layout (after loading)
start_layout_str = '  return (\n    <main className="min-h-screen'
# Find where the main component ends. The main component ends with:
#       )}
#     </main>
#   );
# }

new_layout = '''  return (
    <div className="flex min-h-screen bg-background text-foreground font-sans antialiased">
      {/* Sidebar - Frosted Glass */}
      <aside className="w-64 glass-sidebar border-r border-border h-screen sticky top-0 hidden md:flex flex-col z-30">
        <div className="p-6 pb-4">
          <div className="text-3xl tracking-tighter flex items-center gap-1 select-none">
            <span className="font-sans font-medium text-muted-foreground">talk:</span>
            <span className="font-mono font-black text-foreground tracking-[0.15em] bg-black/5 dark:bg-white/5 px-2 py-1 rounded-lg border border-border text-xl shadow-sm">core</span>
          </div>
        </div>
        
        <nav className="flex-1 px-4 py-6 space-y-2">
          <Button 
            variant={view === 'dashboard' ? 'default' : 'secondary'} 
            className="w-full justify-start font-bold"
            onClick={() => setView('dashboard')}
          >
            <Activity className="mr-2 h-4 w-4" />
            Дашборд
          </Button>
          <Button 
            variant={view === 'analytics' ? 'default' : 'secondary'} 
            className="w-full justify-start font-bold"
            onClick={() => setView('analytics')}
          >
            <TrendingUp className="mr-2 h-4 w-4" />
            Отчет за месяц
          </Button>
          <Button 
            variant={view === 'admin' ? 'default' : 'secondary'} 
            className="w-full justify-start font-bold"
            onClick={() => setView('admin')}
          >
            <Briefcase className="mr-2 h-4 w-4" />
            Офис
          </Button>
        </nav>

        <div className="p-4 border-t border-border mt-auto">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Смена темы</span>
            <ThemeToggle />
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-h-screen overflow-x-hidden relative">
        {/* Mobile Header */}
        <header className="md:hidden flex items-center justify-between p-4 border-b border-border glass-sidebar sticky top-0 z-40">
           <div className="text-xl tracking-tighter flex items-center gap-1 select-none">
            <span className="font-sans font-medium text-muted-foreground">talk:</span>
            <span className="font-mono font-black text-foreground tracking-[0.15em] bg-black/5 dark:bg-white/5 px-2 py-0.5 rounded-lg border border-border text-sm shadow-sm">core</span>
          </div>
          <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="p-2 border border-border rounded-lg bg-background">
            {isMobileMenuOpen ? <X size={20}/> : <Menu size={20}/>}
          </button>
        </header>

        {isMobileMenuOpen && (
           <div className="md:hidden fixed inset-0 z-30 pt-16 bg-background/80 backdrop-blur-xl">
              <div className="p-4 flex flex-col gap-2">
                <Button variant={view === 'dashboard' ? 'default' : 'secondary'} onClick={() => {setView('dashboard'); setIsMobileMenuOpen(false);}}>Дашборд</Button>
                <Button variant={view === 'analytics' ? 'default' : 'secondary'} onClick={() => {setView('analytics'); setIsMobileMenuOpen(false);}}>Отчет за месяц</Button>
                <Button variant={view === 'admin' ? 'default' : 'secondary'} onClick={() => {setView('admin'); setIsMobileMenuOpen(false);}}>Офис</Button>
              </div>
           </div>
        )}

        <div className="flex-1 p-4 md:p-8">
          {view === 'dashboard' && renderDashboard()}
          {view === 'analytics' && renderAnalytics()}
          {view === 'admin' && renderAdmin()}
        </div>
      </main>

      {/* Floating Audio Player */}
      {activeDialog && (
        <div className="fixed bottom-0 left-0 right-0 z-50 animate-in slide-in-from-bottom duration-500 pb-4 md:pb-8 pointer-events-none flex justify-center">
           <div className="w-full max-w-5xl px-4 md:px-6 pointer-events-auto">
              <div className="glass-sidebar border border-border shadow-2xl rounded-[2rem] p-3 md:p-4 flex flex-col md:flex-row items-center gap-4 transition-all duration-300">
                 <button onClick={() => setIsPlaying(!isPlaying)} className="w-12 h-12 flex items-center justify-center bg-primary text-primary-foreground rounded-full shrink-0 shadow-lg hover:scale-105 active:scale-95 transition-all">
                    {isPlaying ? <Pause fill="currentColor" size={20} /> : <Play fill="currentColor" size={20} className="ml-1" />}
                 </button>
                 <div className="flex-1 flex flex-col justify-center min-w-0 w-full px-2">
                    <div className="flex items-center justify-between mb-1.5">
                       <span className="text-xs font-bold text-foreground truncate">{activeDialog.agent} • {activeDialog.shop_id}</span>
                       <span className="text-[10px] font-bold text-muted-foreground ml-2 shrink-0">{formatDuration(audioDuration)}</span>
                    </div>
                    <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden cursor-pointer relative" onClick={handleSeek}>
                       <div className="absolute top-0 left-0 h-full bg-primary rounded-full" style={{ width: `${(audioProgress / audioDuration) * 100}%` }}></div>
                    </div>
                 </div>
                 <button onClick={() => { setActiveDialog(null); setIsPlaying(false); }} className="hidden md:flex w-10 h-10 items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted transition-colors rounded-full shrink-0">
                    <X size={20}/>
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
    </div>
  );
}'''

# Extract from start of return to the end of the file
layout_start_idx = content.find(start_layout_str)
if layout_start_idx != -1:
    content = content[:layout_start_idx] + new_layout

# Fix loading screen background
loading_str = '''  if (loading && shops.length === 0) {
    return (
      <main className="min-h-screen bg-black text-white flex items-center justify-center">'''
loading_new = '''  if (loading && shops.length === 0) {
    return (
      <main className="min-h-screen bg-background text-foreground flex items-center justify-center">'''
content = content.replace(loading_str, loading_new)


# 4. Refactor renderDashboard
start_rd = "const renderDashboard = () => {"
end_rd = "  // ---- 3. Render Analytics (month) ----"
start_idx = content.find(start_rd)
end_idx = content.find(end_rd)

new_rd = '''const renderDashboard = () => {
    if (selectedShopId) return renderDialogs();
    
    return (
      <div className="space-y-6">
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Сводка за {selectedDate}</h1>
            <p className="text-muted-foreground text-sm mt-1">Оценка работы сети по всем локациям</p>
          </div>
          <div className="relative">
            <Button onClick={() => mobileDateInputRef.current?.showPicker()} variant="secondary" className="flex items-center gap-2">
              <Calendar size={16} />
              {displayDate}
            </Button>
            <input 
              ref={mobileDateInputRef}
              type="date" 
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="absolute opacity-0 w-0 h-0"
            />
          </div>
        </header>

        {/* Top metrics summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bento-card p-4">
            <div className="text-muted-foreground text-xs uppercase font-bold tracking-wider mb-2">Всего диалогов</div>
            <div className="text-3xl font-black">{dayDialogs.length}</div>
          </div>
          <div className="bento-card p-4">
            <div className="text-muted-foreground text-xs uppercase font-bold tracking-wider mb-2">Средняя оценка</div>
            <div className="text-3xl font-black">{overallAverageScore.toFixed(1)} <span className="text-sm font-normal text-muted-foreground">/ 10</span></div>
          </div>
          <div className="bento-card p-4">
            <div className="text-muted-foreground text-xs uppercase font-bold tracking-wider mb-2">Целевые</div>
            <div className="text-3xl font-black">{dayDialogs.filter(d => d.role_system_score && d.role_system_score >= 8).length}</div>
          </div>
          <div className="bento-card p-4">
            <div className="text-muted-foreground text-xs uppercase font-bold tracking-wider mb-2">Критичные</div>
            <div className="text-3xl font-black text-destructive">{dayDialogs.filter(d => d.role_system_score && d.role_system_score < 4).length}</div>
          </div>
        </div>

        <BentoGrid className="max-w-none md:auto-rows-[22rem]">
          {/* Main Chart */}
          <BentoGridItem
            title="Сетевая динамика"
            description="Изменение средней оценки по сети за последние 7 дней"
            header={
              <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#007AFF" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#007AFF" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="currentColor" strokeOpacity={0.1} vertical={false} />
                    <XAxis dataKey="date" stroke="currentColor" strokeOpacity={0.5} fontSize={10} tickMargin={10} axisLine={false} tickLine={false}/>
                    <YAxis domain={[0, 10]} stroke="currentColor" strokeOpacity={0.5} fontSize={10} axisLine={false} tickLine={false}/>
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'var(--color-card)', borderColor: 'var(--color-border)', borderRadius: '12px', fontSize: '12px', fontWeight: 'bold' }}
                      itemStyle={{ color: 'var(--color-foreground)' }}
                    />
                    <Area type="monotone" dataKey="score" stroke="#007AFF" strokeWidth={3} fillOpacity={1} fill="url(#colorScore)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            }
            className="md:col-span-2"
          />

          {/* Rating Locations */}
          <BentoGridItem
            title="Рейтинг локаций"
            description="Топ кофеен по среднему баллу за день"
            header={
              <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-3 mt-2">
                {shopSummaries.length === 0 ? (
                  <div className="text-muted-foreground text-sm italic text-center py-4">Нет данных для рейтинга</div>
                ) : (
                  shopSummaries.slice(0, 5).map((shop, idx) => (
                    <div key={shop.id} className="flex items-center justify-between p-2 hover:bg-muted/50 rounded-xl transition-colors cursor-pointer" onClick={() => setSelectedShopId(shop.id)}>
                      <div className="flex items-center gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${idx === 0 ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-500' : 'bg-muted text-muted-foreground'}`}>
                          {idx + 1}
                        </div>
                        <span className="text-sm font-medium">{shop.name}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold">{shop.avgScore}</div>
                        <div className="text-[10px] text-muted-foreground">{shop.dialogCount} д.</div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            }
            className="md:col-span-1"
          />

          {/* Quick Analytics */}
          <BentoGridItem
            title="Краткая аналитика"
            description="Частые проблемы и инсайты за день"
            header={
              <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 mt-2 space-y-3">
                {dailyIssues.length === 0 ? (
                  <div className="text-muted-foreground text-sm italic text-center py-4">Нет критических проблем</div>
                ) : (
                  dailyIssues.map((issue, idx) => (
                    <div key={idx} className="bg-muted/50 p-3 rounded-xl border border-border/50">
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-xs font-bold text-destructive">{issue.type}</span>
                        <span className="text-[10px] font-bold text-muted-foreground">{issue.count} инц.</span>
                      </div>
                      <div className="h-1.5 w-full bg-border rounded-full overflow-hidden">
                        <div className="h-full bg-destructive" style={{ width: `${issue.percent}%` }}></div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            }
            className="md:col-span-1"
          />

          {/* Active Employees */}
          <BentoGridItem
            title="Активность на точках"
            description="Сотрудники, участвовавшие в диалогах сегодня"
            className="md:col-span-2"
            header={
              <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 mt-2 grid grid-cols-1 sm:grid-cols-2 gap-3">
                 {/* Aggregate agents from all dialogs today */}
                 {Array.from(new Set(dayDialogs.map(d => d.agent).filter(Boolean))).slice(0,6).map((agent, i) => {
                    const agentDialogs = dayDialogs.filter(d => d.agent === agent);
                    const avg = agentDialogs.reduce((sum, d) => sum + (d.role_system_score || 0), 0) / agentDialogs.length;
                    return (
                      <div key={i} className="flex items-center gap-3 p-2 bg-muted/30 rounded-xl border border-border/50">
                        <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs uppercase">
                          {agent.slice(0, 2)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium truncate">{agent}</div>
                          <div className="text-[10px] text-muted-foreground">{agentDialogs.length} диалогов</div>
                        </div>
                        <div className={`text-xs font-bold px-2 py-1 rounded-lg ${avg >= 7 ? 'bg-green-100 text-green-700 dark:bg-green-900/30' : avg < 5 ? 'bg-red-100 text-red-700 dark:bg-red-900/30' : 'bg-muted text-muted-foreground'}`}>
                          {avg.toFixed(1)}
                        </div>
                      </div>
                    )
                 })}
              </div>
            }
          />

        </BentoGrid>
      </div>
    );
  };
'''

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_rd + content[end_idx:]

# Ensure all cyberpunk zinc-X classes are stripped out of renderAnalytics, renderAdmin, renderDialogs
content = re.sub(r'bg-zinc-100 dark:bg-zinc-900', 'bg-muted', content)
content = re.sub(r'bg-zinc-200 dark:bg-zinc-800', 'bg-muted hover:bg-muted/80', content)
content = re.sub(r'bg-white dark:bg-zinc-950/40', 'bg-card', content)
content = re.sub(r'bg-white dark:bg-[#0c0d12]', 'bg-card', content)
content = re.sub(r'bg-zinc-50 dark:bg-white/5', 'bg-muted', content)
content = re.sub(r'border-black/5 dark:border-white/5', 'border-border', content)
content = re.sub(r'text-zinc-500 dark:text-zinc-400', 'text-muted-foreground', content)
content = re.sub(r'text-zinc-600 dark:text-zinc-400', 'text-muted-foreground', content)
content = re.sub(r'text-zinc-900 dark:text-white', 'text-foreground', content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("page.tsx refactored with BentoGrid and Sidebar successfully.")
