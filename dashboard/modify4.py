import re

with open('src/app/page.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. State for Mobile Menu
old_state = "const [activePhraseIndex, setActivePhraseIndex] = useState<number | null>(null);"
new_state = """  const [activePhraseIndex, setActivePhraseIndex] = useState<number | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);"""
if "isMobileMenuOpen" not in code:
    code = code.replace(old_state, new_state)

# 2. Header Reverting to a clean desktop look and hiding it behind md:flex, adding mobile menu
old_header_block = """            <header className="mb-12 flex flex-col xl:flex-row items-center xl:justify-between border-b border-black/5 dark:border-white/5 pb-10 gap-8 xl:gap-0">
               <div className="flex items-center gap-4">
                  <style dangerouslySetInnerHTML={{ __html: fontImport }} />
                  <div className="text-4xl tracking-tighter flex items-center gap-1 select-none" id="logo-dashboard-view">
                    <span className="font-sans font-medium text-zinc-500">talk:</span>
                    <span className="font-mono font-black text-zinc-900 dark:text-white tracking-[0.15em] bg-black/5 dark:bg-white/5 px-3 py-1 rounded-lg border border-black/10 dark:border-white/10 text-2xl shadow-[0_0_20px_rgba(255,255,255,0.05)]">core</span>
                  </div>
               </div>

               <div className="flex flex-col xl:flex-row items-center gap-6 w-full xl:w-auto">
                  {!selectedShopId && (
                    <div className="flex flex-col xl:flex-row items-center gap-6 w-full xl:w-auto">
                       <div className="flex w-full overflow-x-auto custom-scrollbar touch-pan-x bg-zinc-100 dark:bg-[#0c0d12] p-1 rounded-xl border border-black/5 dark:border-white/5 flex-nowrap">
                          <button 
                            onClick={() => setView('dashboard')}
                            className={`whitespace-nowrap flex-none px-5 py-2.5 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${view === 'dashboard' ? 'bg-white dark:bg-zinc-800 text-black dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'}`}
                          >
                            Дашборд
                          </button>
                          <button 
                            onClick={() => setView('analytics')}
                            className={`whitespace-nowrap flex-none px-5 py-2.5 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${view === 'analytics' ? 'bg-white dark:bg-zinc-800 text-black dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'}`}
                          >
                            Отчет за месяц
                          </button>
                          <button 
                            onClick={() => setView('admin')}
                            className={`whitespace-nowrap flex-none flex justify-center items-center gap-2 px-5 py-2.5 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${view === 'admin' ? 'bg-emerald-500 text-black shadow-sm' : 'text-zinc-500 hover:text-emerald-500'}`}
                          >
                            Офис
                          </button>
                       </div>

                       <div className="hidden xl:block w-px h-6 bg-black/5 dark:bg-white/5"></div>
                       <ThemeToggle />
                       <div className="hidden xl:block w-px h-6 bg-black/5 dark:bg-white/5"></div>

                       <div className="flex flex-wrap justify-center items-center gap-2 text-[9px] font-bold text-zinc-600 uppercase tracking-widest">
                          <Calendar size={12} /> Архив по дням
                       </div>
                       <div className="relative flex items-center">
                          <input 
                            type="date" 
                            value={selectedDate}
                            onClick={(e) => (e.target as HTMLInputElement).showPicker()}
                            onChange={(e) => { setSelectedDate(e.target.value); setView('dashboard'); }}
                            className="bg-white dark:bg-[#0c0d12] border border-black/5 dark:border-white/5 rounded-xl px-4 py-2 flex items-center text-[10px] font-bold uppercase text-zinc-600 dark:text-zinc-400 focus:outline-none [color-scheme:light] dark:[color-scheme:dark] cursor-pointer"
                          />
                       </div>
                    </div>
                  )}

                  {selectedShopId && (
                    <button 
                      onClick={() => setSelectedShopId(null)}
                      className="flex items-center gap-2 bg-zinc-100 dark:bg-zinc-900/50 hover:bg-zinc-200 dark:bg-zinc-800 px-5 py-3 rounded-xl border border-black/5 dark:border-white/5 transition-all text-xs font-bold uppercase tracking-widest group"
                    >
                      <ChevronLeft size={16} className="group-hover:-translate-x-1 transition-transform" /> Назад
                    </button>
                  )}
               </div>
            </header>"""

new_header_block = """            <header className="mb-12 flex items-center justify-between border-b border-black/5 dark:border-white/5 pb-10 relative">
               <div className="flex items-center gap-4 relative z-20 bg-zinc-50 dark:bg-[#050505]">
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
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
                       </button>
                    </>
                  )}
               </div>

               {/* Desktop Nav */}
               <div className="hidden md:flex items-center gap-6">
                  {!selectedShopId && (
                    <div className="flex items-center gap-6">
                       <div className="flex bg-zinc-100 dark:bg-[#0c0d12] p-1 rounded-xl border border-black/5 dark:border-white/5">
                          <button 
                            onClick={() => setView('dashboard')}
                            className={`px-5 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${view === 'dashboard' ? 'bg-white dark:bg-zinc-800 text-black dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'}`}
                          >
                            Дашборд
                          </button>
                          <button 
                            onClick={() => setView('analytics')}
                            className={`px-5 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${view === 'analytics' ? 'bg-white dark:bg-zinc-800 text-black dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'}`}
                          >
                            Отчет
                          </button>
                          <button 
                            onClick={() => setView('admin')}
                            className={`px-5 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${view === 'admin' ? 'bg-white dark:bg-zinc-800 text-black dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300'}`}
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
                  )}

                  {selectedShopId && (
                     <button 
                       onClick={() => setSelectedShopId(null)}
                       className="flex items-center gap-2 bg-zinc-100 dark:bg-zinc-900/50 hover:bg-zinc-200 dark:bg-zinc-800 px-5 py-3 rounded-xl border border-black/5 dark:border-white/5 transition-all text-xs font-bold uppercase tracking-widest group"
                     >
                       <ChevronLeft size={16} className="group-hover:-translate-x-1 transition-transform" /> Назад
                     </button>
                  )}
               </div>
               
               {/* Dropdown Mobile Menu */}
               {isMobileMenuOpen && !selectedShopId && (
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
               )}
            </header>"""
code = code.replace(old_header_block, new_header_block)

# 3. Horizontal Slider Mouse Wheel (Scroll Wheel translation)
old_slider = 'className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar touch-pan-x"'
new_slider = 'className="flex gap-4 overflow-x-auto pb-4 pt-1 px-1 -mx-1 custom-scrollbar touch-pan-x" onWheel={(e) => { e.currentTarget.scrollLeft += e.deltaY * 1.5; e.preventDefault(); }}'
code = code.replace(old_slider, new_slider)

# 4. Text contrast logic on slider dark mode
# "в слайдере что на скрине в темной теме цифры на белом фоне пропадают" 
# Right now the weekly slider cards look like this: 
# bg-white/60 dark:bg-[#0c0d12] ... 
# And selected: bg-white shadow-[... text-zinc-900.
# Actually I need to make sure text is readable.
code = code.replace('className={`p-4 rounded-xl border transition-all cursor-pointer select-none flex-shrink-0 w-[120px] ${selectedDate === d.dateString ? \'bg-white shadow-[0_10px_40px_rgba(0,0,0,0.1)] border-emerald-500/30\' : \'bg-white/60 dark:bg-[#0c0d12] border-black/5 dark:border-white/5 hover:border-emerald-500/20\'}`}', 'className={`p-4 rounded-xl border transition-all cursor-pointer select-none flex-shrink-0 w-[120px] ${selectedDate === d.dateString ? \'bg-white dark:bg-zinc-800 shadow-xl border-emerald-500/50\' : \'bg-white/60 dark:bg-[#0c0d12] border-black/5 dark:border-white/5 hover:border-emerald-500/20\'}`}')
code = code.replace('<div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">{d.label}</div>', '<div className="text-[10px] font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-widest">{d.label}</div>')
code = code.replace('<div className="text-3xl font-black mt-1 text-zinc-900 flex items-baseline gap-1">', '<div className="text-3xl font-black mt-1 text-zinc-900 dark:text-white flex items-baseline gap-1">')


# 5. Top Problems BW lines and colored numbers
# "где системные нарушения давай тоже сделаем линии чб , а цифры если меньше 50% то красные если больше то зеленые"
old_top_problems = """                                   <div className="flex justify-between items-end mb-2 text-xs font-bold text-zinc-600 dark:text-zinc-400">
                                      <span className="uppercase tracking-widest">{prob.name}</span>
                                      <span className="text-rose-500">{prob.percent}%</span>
                                   </div>
                                   <div className="h-2 w-full bg-black/5 dark:bg-white/5 rounded-full overflow-hidden">
                                     <div className="h-full bg-rose-500/50" style={{ width: `${prob.percent}%` }}></div>
                                   </div>"""

new_top_problems = """                                   <div className="flex justify-between items-end mb-2 text-xs font-bold text-zinc-600 dark:text-zinc-400">
                                      <span className="uppercase tracking-widest">{prob.name}</span>
                                      <span className={prob.percent < 50 ? "text-rose-500" : "text-emerald-500"}>{prob.percent}%</span>
                                   </div>
                                   <div className="h-2 w-full bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
                                     <div className="h-full bg-zinc-900 dark:bg-zinc-100" style={{ width: `${prob.percent}%` }}></div>
                                   </div>"""
code = code.replace(old_top_problems, new_top_problems)

with open('src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("done")
