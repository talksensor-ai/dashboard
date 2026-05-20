import re

with open('src/app/page.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Slider Text Visibility in Dark Mode
old_slider = """                       return (
                          <button 
                            key={dateStr}
                            onClick={() => { setSelectedDate(dateStr); setView('dashboard'); }}
                            className={`flex-shrink-0 flex flex-col justify-between p-4 rounded-3xl border transition-all h-24 w-40 text-left cursor-pointer
                              ${isSelected 
                                ? 'bg-white text-black border-white shadow-xl' 
                                : 'bg-white dark:bg-[#0c0d12] hover:bg-zinc-100 dark:bg-zinc-900 border-black/5 dark:border-white/5 text-zinc-900 dark:text-white'}`}
                          >
                             <span className={`text-[10px] font-bold ${isSelected ? 'text-black' : 'text-zinc-500'}`}>{displayDate}</span>
                             <div className="flex justify-between items-end mt-4">
                                <span className="text-xl font-black tracking-tighter text-zinc-900 dark:text-white">{avg}</span>
                                <span className={`text-[8px] font-bold uppercase tracking-widest ${isSelected ? 'text-zinc-500' : 'text-zinc-600'}`}>{dayDialogs.length} диалогов</span>
                             </div>
                          </button>
                       );"""

new_slider = """                       return (
                          <button 
                            key={dateStr}
                            onClick={() => { setSelectedDate(dateStr); setView('dashboard'); }}
                            className={`flex-shrink-0 flex flex-col justify-between p-4 rounded-3xl border transition-all h-24 w-40 text-left cursor-pointer
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
                       );"""
code = code.replace(old_slider, new_slider)


# 2. Краткая аналитика
old_analytics = """                         <div className="flex items-center gap-3 mb-8">
                           <AlertTriangle size={18} className="text-rose-500/60" />
                           <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500">Системные нарушения</h3>
                         </div>
                         <div className="space-y-5">
                           {networkPerformance.map((issue) => (
                             <div key={issue.key} className="space-y-2 group">
                               <div className="flex justify-between items-end">
                                 <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">
                                   {issue.name}
                                 </span>
                                 <span className={`text-base font-bold ${issue.percent >= 80 ? 'text-emerald-500/80' : 'text-rose-500/80'}`}>
                                   {issue.percent}%
                                 </span>
                               </div>
                               <div className="h-1 w-full bg-black/40 rounded-full overflow-hidden">
                                 <div className="h-full bg-emerald-500/60" style={{ width: `${issue.percent}%` }}></div>
                               </div>
                             </div>
                           ))}
                         </div>"""

new_analytics = """                         <div className="flex items-center gap-3 mb-8">
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
                         </div>"""
code = code.replace(old_analytics, new_analytics)


# 2b. Second "Краткая аналитика" inside Shop Details -> Ensure it's BW too!
old_shop_analytics = """                       <div className="flex items-center gap-3 mb-8 text-zinc-600">
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
                      </div>"""

new_shop_analytics = """                       <div className="flex items-center gap-3 mb-8 text-zinc-900 dark:text-white">
                         <AlertTriangle size={18} />
                         <h3 className="text-[10px] font-bold uppercase tracking-widest">Краткая аналитика</h3>
                      </div>
                      <div className="space-y-5">
                         {shopPerformanceStats.map((stat) => (
                            <div key={stat.key} className="space-y-2">
                               <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-widest text-zinc-600 dark:text-zinc-400">
                                  <span>{stat.name}</span>
                                  <span className={stat.percent < 50 ? "text-rose-500" : "text-emerald-500"}>{stat.percent}%</span>
                               </div>
                               <div className="h-1 bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
                                  <div className="h-full bg-zinc-900 dark:bg-zinc-100" style={{ width: `${stat.percent}%` }}></div>
                               </div>
                            </div>
                         ))}
                      </div>"""
code = code.replace(old_shop_analytics, new_shop_analytics)


# 3. Report Tab text removal
code = code.replace(
    '<p className="text-[10px] font-bold text-zinc-600 dark:text-zinc-400 uppercase tracking-widest max-w-sm leading-relaxed">\n                               Расчет основан на пропущенных доп. продажах (-400₽), забытых приветствиях (потеря LTV -3000₽) и упущенной лояльности (-200₽).\n                             </p>',
    ''
)


# 4. Mobile Menu dark mode fix
old_mobile_menu = """               {isMobileMenuOpen && !selectedShopId && (
                  <div className="absolute top-full left-0 right-0 mt-4 bg-white dark:bg-[#101012] border border-black/10 dark:border-white/10 rounded-2xl p-4 shadow-2xl z-50 flex flex-col md:hidden animate-in fade-in slide-in-from-top-4">
                     <div className="flex flex-col gap-2 mb-4">
                       <button onClick={() => {setView('dashboard'); setIsMobileMenuOpen(false);}} className={`text-left px-4 py-3 rounded-xl font-bold ${view === 'dashboard' ? 'bg-zinc-100 dark:bg-zinc-800 text-black dark:text-white' : 'text-zinc-600 dark:text-zinc-400'}`}>Дашборд</button>
                       <button onClick={() => {setView('analytics'); setIsMobileMenuOpen(false);}} className={`text-left px-4 py-3 rounded-xl font-bold ${view === 'analytics' ? 'bg-zinc-100 dark:bg-zinc-800 text-black dark:text-white' : 'text-zinc-600 dark:text-zinc-400'}`}>Отчет за месяц</button>
                       <button onClick={() => {setView('admin'); setIsMobileMenuOpen(false);}} className={`text-left px-4 py-3 rounded-xl font-bold ${view === 'admin' ? 'bg-zinc-100 dark:bg-zinc-800 text-black dark:text-white' : 'text-zinc-600 dark:text-zinc-400'}`}>Офис</button>
                     </div>
                     <div className="w-full h-px bg-black/5 dark:bg-white/5 my-2"></div>
                     <div className="flex items-center justify-between p-2">
                        <span className="font-bold text-sm text-zinc-600 dark:text-zinc-400">Смена темы</span>
                        <ThemeToggle />
                     </div>
                  </div>
               )}"""

new_mobile_menu = """               {isMobileMenuOpen && !selectedShopId && (
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
               )}"""
code = code.replace(old_mobile_menu, new_mobile_menu)


# 5. Ninja Turtles Office Redesign
tmnt_office = """                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
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
                                        {agentIsBusy.active_task.substring(0, 20)}...
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
                </div>"""

# Replace lines 567 to 608 with tmnt office!
old_office_chunk = """                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                   {/* OFFICE ZONE */}
                   <div className="bg-white dark:bg-[#0c0d12]/80 border border-black/5 dark:border-emerald-500/20 rounded-3xl p-8 relative overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-2xl">
                      <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-5 pointer-events-none"></div>
                      <h3 className="text-lg font-black uppercase tracking-widest text-emerald-500 mb-12 flex items-center gap-2">
                         🖥️ Рабочая зона (Busy)
                      </h3>
                      <div className="grid grid-cols-1 gap-12 relative z-10">
                         {telemetry.filter(t => t.status === 'BUSY').map(agent => (
                            <div key={agent.agent_name} className="bg-zinc-50 dark:bg-zinc-900 border border-emerald-500/30 rounded-2xl p-6 relative shadow-lg">
                               <div className="absolute -top-6 -right-4 bg-white dark:bg-[#0c0d12] border border-black/10 dark:border-white/10 rounded-2xl p-4 text-xs font-bold shadow-2xl shadow-black/10 dark:shadow-black/50 border-black/5 dark:border-white/10 max-w-[200px] text-zinc-600 dark:text-zinc-300 animate-bounce">
                                  💬 {agent.active_task || "Обработка..."}
                               </div>
                               <h4 className="text-xl font-bold text-zinc-900 dark:text-white">{agent.agent_name}</h4>
                               <p className="text-xs text-emerald-500 mt-2 font-mono">{agent.status}</p>
                               <div className="mt-4 w-full bg-black/5 dark:bg-white/5 h-2 rounded-full overflow-hidden">
                                  <div className="bg-emerald-500 h-full w-full animate-pulse"></div>
                               </div>
                            </div>
                         ))}
                         {telemetry.filter(t => t.status === 'BUSY').length === 0 && (
                           <div className="text-zinc-500 dark:text-zinc-500 text-sm italic py-10 text-center">Офис пуст. Агенты ушли на пляж.</div>
                         )}
                      </div>
                   </div>
              
                   {/* BEACH ZONE */}
                   <div className="bg-sky-50 dark:bg-sky-950/20 border border-black/5 dark:border-sky-500/20 rounded-3xl p-8 relative overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-2xl">
                      <h3 className="text-lg font-black uppercase tracking-widest text-sky-500 mb-8 flex items-center gap-2">
                         🌴 Пляж (Idle / Offline)
                      </h3>
                      <div className="grid grid-cols-2 gap-6 relative z-10">
                         {telemetry.filter(t => t.status !== 'BUSY').map(agent => (
                            <div key={agent.agent_name} className="bg-white/50 dark:bg-black/20 border border-black/5 dark:border-sky-500/10 rounded-2xl p-6 flex flex-col items-center justify-center text-center hover:scale-105 transition-all cursor-default relative group shadow-sm dark:shadow-none">
                               <div className="text-4xl mb-4 group-hover:animate-bounce">🍹</div>
                               <h4 className="text-sm font-bold text-sky-900 dark:text-sky-100">{agent.agent_name}</h4>
                               <p className={`text-[10px] font-bold uppercase tracking-widest mt-2 ${agent.status === 'IDLE' ? 'text-sky-500' : 'text-rose-500'}`}>{agent.status}</p>
                            </div>
                         ))}
                      </div>
                   </div>
                </div>"""

code = code.replace(old_office_chunk, tmnt_office)

with open('src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("done")
