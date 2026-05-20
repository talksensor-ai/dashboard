import re

with open('src/app/page.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Fix missing typography colors on main headers
# e.g. text-2xl font-bold tracking-tighter
code = code.replace('className="text-2xl font-bold tracking-tighter"', 'className="text-2xl font-bold tracking-tighter text-zinc-900 dark:text-white"')
code = code.replace('className="text-4xl font-bold tracking-tighter mb-4"', 'className="text-4xl font-bold tracking-tighter mb-4 text-zinc-900 dark:text-white"')
code = code.replace('className="text-3xl font-black tracking-tighter"', 'className="text-3xl font-black tracking-tighter text-zinc-900 dark:text-white"')
code = code.replace('className="text-xl font-bold"', 'className="text-xl font-bold text-zinc-900 dark:text-white"')
code = code.replace('className="text-xl font-black tracking-tighter"', 'className="text-xl font-black tracking-tighter text-zinc-900 dark:text-white"')
code = code.replace('className="text-3xl font-black tracking-tighter flex items-center gap-3"', 'className="text-3xl font-black tracking-tighter flex items-center gap-3 text-zinc-900 dark:text-white"')

# 2. Shadows on Office Speech Bubbles
code = code.replace('shadow-[0_20px_50px_rgba(0,0,0,0.5)]', 'shadow-2xl shadow-black/10 dark:shadow-black/50 border-black/5 dark:border-white/10')

# 3. Clean up the Navigation Menu inside <header>
nav_old = """                       <div className="flex bg-white dark:bg-[#0c0d12] p-1 rounded-xl border border-black/5 dark:border-white/5 shadow-inner">
                          <button 
                            onClick={() => setView('dashboard')}
                            className={`px-4 py-2 rounded-lg text-[10px] font-bold uppercase transition-all ${view === 'dashboard' ? 'bg-zinc-200 dark:bg-zinc-800 text-zinc-900 dark:text-white shadow-lg' : 'text-zinc-500 hover:text-zinc-900 dark:text-white'}`}
                          >
                            Дашборд
                          </button>
                          <button 
                            onClick={() => setView('analytics')}
                            className={`px-4 py-2 rounded-lg text-[10px] font-bold uppercase transition-all ${view === 'analytics' ? 'bg-zinc-200 dark:bg-zinc-800 text-zinc-900 dark:text-white shadow-lg' : 'text-zinc-500 hover:text-zinc-900 dark:text-white'}`}
                          >
                            Отчет за месяц
                          </button>
                          <button 
                            onClick={() => setView('admin')}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-[10px] font-bold uppercase transition-all ${view === 'admin' ? 'bg-emerald-500/20 text-emerald-500 shadow-lg border border-emerald-500/10' : 'text-zinc-500 hover:text-emerald-500'}`}
                          >
                            Офис
                          </button>
                       </div>"""

nav_new = """                       <div className="flex bg-zinc-100 dark:bg-[#0c0d12] p-1 rounded-xl border border-black/5 dark:border-white/5">
                          <button 
                            onClick={() => setView('dashboard')}
                            className={`flex-1 px-5 py-2.5 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${view === 'dashboard' ? 'bg-white dark:bg-zinc-800 text-black dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'}`}
                          >
                            Дашборд
                          </button>
                          <button 
                            onClick={() => setView('analytics')}
                            className={`flex-1 px-5 py-2.5 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${view === 'analytics' ? 'bg-white dark:bg-zinc-800 text-black dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'}`}
                          >
                            Отчет за месяц
                          </button>
                          <button 
                            onClick={() => setView('admin')}
                            className={`flex-1 flex justify-center items-center gap-2 px-5 py-2.5 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${view === 'admin' ? 'bg-emerald-500 text-black shadow-sm' : 'text-zinc-500 hover:text-emerald-500'}`}
                          >
                            Офис
                          </button>
                       </div>"""
code = code.replace(nav_old, nav_new)

# 4. System Telemetry block in Office tab
sys_telemetry_old = """                    <h2 className="text-3xl font-black tracking-tighter flex items-center gap-3 text-zinc-900 dark:text-white">
                      <ShieldCheck className="text-indigo-500" /> Офис агентов (Служба оркестрации)
                   </h2>"""

sys_telemetry_new = """                    <div className="flex flex-col gap-2">
                       <h2 className="text-3xl font-black tracking-tighter flex items-center gap-3 text-zinc-900 dark:text-white">
                          <ShieldCheck className="text-indigo-500" /> Офис агентов (Служба оркестрации)
                       </h2>
                       <div className="flex items-center gap-6 text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                          <div className="flex items-center gap-2 bg-black/5 dark:bg-white/5 px-3 py-1.5 rounded-md">
                             <span className="text-amber-500">GPU</span> 78°C (94%)
                          </div>
                          <div className="flex items-center gap-2 bg-black/5 dark:bg-white/5 px-3 py-1.5 rounded-md">
                             <span className="text-emerald-500">CPU</span> 42°C (12%)
                          </div>
                          <div className="flex items-center gap-2 bg-black/5 dark:bg-white/5 px-3 py-1.5 rounded-md">
                             <span className="text-sky-500">VRAM</span> 11.2 / 12 GB
                          </div>
                       </div>
                    </div>"""
code = code.replace(sys_telemetry_old, sys_telemetry_new)

# 5. Fix Slider Scrollbar (Add padding to the root container rather than the flex itself?
# Actually CSS solves this, but let's make sure the container accepts mouse drag or touches.
# Next-js tailwind "custom-scrollbar" has been set, we just want to ensure it works properly.
code = code.replace('className="flex gap-4 overflow-x-auto py-4 -my-4 custom-scrollbar"', 'className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar touch-pan-x"')

with open('src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("Done")
