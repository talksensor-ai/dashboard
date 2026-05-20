import re

with open('src/app/page.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Fix crash from e.preventDefault() in onWheel
code = code.replace(
    'e.preventDefault();',
    ''
)

# 2. Fix Header Logo background overlapping
code = code.replace(
    '<div className="flex items-center gap-4 relative z-20 bg-zinc-50 dark:bg-[#050505]">',
    '<div className="flex items-center gap-4 relative z-20">'
)

# 3. Slider Shadow Cropping
old_slider = 'className="flex gap-4 overflow-x-auto pb-4 pt-1 px-1 -mx-1 custom-scrollbar touch-pan-x"'
new_slider = 'className="flex gap-4 overflow-x-auto py-8 -my-8 px-4 -mx-4 custom-scrollbar touch-pan-x"'
code = code.replace(old_slider, new_slider)

# 4. Hamburger Icon Color
old_svg = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">'
new_svg = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-zinc-900 dark:text-white">'
code = code.replace(old_svg, new_svg)

# 5. Shop Details Mobile layout fix
old_details_header = """                      <div className="flex items-end justify-between mb-8">
                         <div>
                           <h2 className="text-4xl font-bold tracking-tighter mb-4 text-zinc-900 dark:text-white">{selectedShopSummary?.name}</h2>
                           <div className="flex gap-8">
                              <div className="flex flex-col">
                                 <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-1">Диалогов за период</span>
                                 <span className="text-2xl font-bold">{selectedShopSummary?.count}</span>
                              </div>
                              <div className="flex flex-col border-l border-black/5 dark:border-white/5 pl-8">
                                 <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-1">Соблюдение скрипта</span>
                                 <span className="text-2xl font-bold text-emerald-400/80">{selectedShopSummary?.avgScorePercent}%</span>
                              </div>
                           </div>
                         </div>
                         <div className="text-right">
                            <div className="text-[10px] font-bold text-zinc-700 uppercase tracking-widest mb-3">Статус обработки</div>
                            <div className="bg-emerald-500/5 text-emerald-500/80 px-5 py-3 rounded-xl flex items-center gap-3 text-[10px] font-bold uppercase tracking-widest border border-emerald-500/10">
                              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span> {appStatus?.status_message || "Системный онлайн"}
                            </div>
                         </div>
                      </div>"""

new_details_header = """                      <div className="flex flex-col xl:flex-row xl:items-end justify-between mb-8 gap-8">
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
                      </div>"""
code = code.replace(old_details_header, new_details_header)

# 6. Top Problems / Analytics By Points Progress lines - making them monochrome
old_analytics_points = """                                <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                                  <span>{stat.name}</span>
                                  <span className="text-zinc-600 dark:text-zinc-400">{stat.percent}%</span>
                               </div>
                               <div className="h-1 bg-black/40 rounded-full overflow-hidden">
                                  <div className="h-full bg-emerald-500/40" style={{ width: `${stat.percent}%` }}></div>
                               </div>"""

new_analytics_points = """                                <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                                  <span>{stat.name}</span>
                                  <span className={stat.percent < 50 ? "text-rose-500" : "text-emerald-500"}>{stat.percent}%</span>
                               </div>
                               <div className="h-1 bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
                                  <div className="h-full bg-zinc-900 dark:bg-zinc-100" style={{ width: `${stat.percent}%` }}></div>
                               </div>"""
code = code.replace(old_analytics_points, new_analytics_points)


# 7. Dialog mobile adaptation
old_dialog_header = """                      <div onClick={() => setExpandedDialogId(expandedDialogId === dialog.id ? null : dialog.id)} className="p-8 flex items-center justify-between cursor-pointer">
                         <div className="flex items-center gap-10">
                            <span className="text-xl font-bold tracking-tighter">Диалог #{dialog.dialog_index}</span>
                            <span className="text-[11px] font-bold text-zinc-600 dark:text-zinc-400 uppercase">
                               {new Date(dialog.created_at).toLocaleTimeString('ru-RU', {hour: '2-digit', minute:'2-digit'})}
                            </span>"""

new_dialog_header = """                      <div onClick={() => setExpandedDialogId(expandedDialogId === dialog.id ? null : dialog.id)} className="p-5 sm:p-8 flex flex-col md:flex-row items-start md:items-center justify-between cursor-pointer gap-4 md:gap-0">
                         <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 sm:gap-10">
                            <span className="text-xl font-bold tracking-tighter text-zinc-900 dark:text-white">Диалог #{dialog.dialog_index}</span>
                            <span className="text-[11px] font-bold text-zinc-500 uppercase">
                               {new Date(dialog.created_at).toLocaleTimeString('ru-RU', {hour: '2-digit', minute:'2-digit'})}
                            </span>"""
code = code.replace(old_dialog_header, new_dialog_header)


# 8. Dark text issue in slider
# Currently it is: <div className="text-3xl font-black mt-1 text-zinc-900 dark:text-white flex items-baseline gap-1">
# But when bg-white dark:bg-zinc-800 applies, it works fine! Why wouldn't it? 
# Maybe previous string replacement didn't catch it!
code = code.replace('<div className="text-3xl font-black mt-1 text-zinc-900 flex items-baseline gap-1">', '<div className="text-3xl font-black mt-1 text-zinc-900 dark:text-white flex items-baseline gap-1">')
code = code.replace('<span className="text-sm font-bold text-zinc-500">диалогов</span>', '<span className="text-sm font-bold text-zinc-500 dark:text-zinc-400">диалогов</span>')

with open('src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("done")
