import sys

with open('src/app/page.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

gamification_ui = """            {view === 'admin' ? (
              <div className="space-y-12 animate-in fade-in slide-in-from-bottom-10 duration-700">
                <div className="flex items-center justify-between">
                   <h2 className="text-3xl font-black tracking-tighter flex items-center gap-3">
                      <ShieldCheck className="text-indigo-500" /> Офис агентов (Служба оркестрации)
                   </h2>
                </div>
              
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                   {/* OFFICE ZONE */}
                   <div className="bg-white dark:bg-[#0c0d12]/80 border border-black/5 dark:border-emerald-500/20 rounded-3xl p-8 relative overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-2xl">
                      <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-5 pointer-events-none"></div>
                      <h3 className="text-lg font-black uppercase tracking-widest text-emerald-500 mb-12 flex items-center gap-2">
                         🖥️ Рабочая зона (Busy)
                      </h3>
                      <div className="grid grid-cols-1 gap-12 relative z-10">
                         {telemetry.filter(t => t.status === 'BUSY').map(agent => (
                            <div key={agent.agent_name} className="bg-zinc-50 dark:bg-zinc-900 border border-emerald-500/30 rounded-2xl p-6 relative shadow-lg">
                               <div className="absolute -top-6 -right-4 bg-white dark:bg-[#0c0d12] border border-black/10 dark:border-white/10 rounded-2xl p-4 text-xs font-bold shadow-[0_20px_50px_rgba(0,0,0,0.5)] max-w-[200px] text-zinc-600 dark:text-zinc-300 animate-bounce">
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
                </div>
              </div>
            ) : view === 'analytics' ? ("""

start_idx = code.find("{view === 'admin' ? (")
if start_idx == -1:
    print('Cannot find start snippet')
    sys.exit(1)
    
end_idx = code.find("            <header", start_idx)
if end_idx == -1:
    print('Cannot find header')
    sys.exit(1)
    
header_str = "            <header"

# Strip out the top level wrapper entirely
code = code[:start_idx] + header_str + code[end_idx + len(header_str):]

# Now inject Gamification UI
analytics_start = "{view === 'analytics' ? ("
if analytics_start in code:
    code = code.replace(analytics_start, gamification_ui)
    
# Clean up closing wrappers
code = code.replace("          </>\n        )}\\n      </div>\n    </main>", "        )}\n      </div>\n    </main>")
# Actually just replace <> and </> wrappers
code = code.replace("        ) : (\n          <>\n            <header", "          <header")
code = code.replace("          </>\n        )}\n      </div>\n    </main>", "        )}\n      </div>\n    </main>")

with open('src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(code)

print('Success')
