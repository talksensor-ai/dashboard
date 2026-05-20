import re

with open('src/app/page.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Colors of the progress lines in Shop Card
old_card_progress_1 = """                            <div className="flex justify-between items-end text-xs font-bold text-zinc-600 dark:text-zinc-400">
                               <span>Сегодня</span>
                               <span className={shop.avgScorePercent >= 80 ? 'text-emerald-500/60' : 'text-amber-500/60'}>{shop.avgScorePercent}%</span>
                            </div>
                            <div className="h-1.5 w-full bg-black/40 rounded-full overflow-hidden">
                              <div className={`h-full ${shop.avgScorePercent >= 80 ? 'bg-emerald-500/50' : 'bg-amber-500/50'}`} style={{ width: `${shop.avgScorePercent}%` }}></div>
                            </div>
                            
                            <div className="flex justify-between items-end text-xs font-bold text-zinc-500 mt-2">
                               <span>За неделю</span>
                               <span className={shop.weeklyAvgPercent >= 80 ? 'text-emerald-500/40' : 'text-amber-500/40'}>{shop.weeklyAvgPercent}%</span>
                            </div>
                            <div className="h-1.5 w-full bg-black/40 rounded-full overflow-hidden">
                              <div className={`h-full ${shop.weeklyAvgPercent >= 80 ? 'bg-emerald-500/30' : 'bg-amber-500/30'}`} style={{ width: `${shop.weeklyAvgPercent}%` }}></div>
                            </div>"""

new_card_progress_1 = """                            <div className="flex justify-between items-end text-xs font-bold text-zinc-600 dark:text-zinc-400">
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
                            </div>"""
code = code.replace(old_card_progress_1, new_card_progress_1)

# Fix the big percentage on the top of the card
code = code.replace('<div className="text-xl font-black text-emerald-500/80">{shop.avgScorePercent}%</div>', '<div className="text-xl font-black text-zinc-900 dark:text-white">{shop.avgScorePercent}%</div>')

# 2. Black block in Analytics Tab
code = code.replace('className="flex bg-[#140b0b] rounded-xl border border-rose-500/10 p-5 gap-8"', 'className="flex flex-col md:flex-row bg-rose-50/50 dark:bg-[#140b0b] rounded-xl border border-rose-500/10 p-5 gap-8"')
code = code.replace('className="text-2xl font-black italic tracking-tighter text-rose-500/80"', 'className="text-2xl font-black italic tracking-tighter text-rose-500"')

# 3. Mobile responsiveness for Header
old_header_1 = '<header className="mb-12 flex items-center justify-between border-b border-black/5 dark:border-white/5 pb-10">'
new_header_1 = '<header className="mb-12 flex flex-col xl:flex-row items-center xl:justify-between border-b border-black/5 dark:border-white/5 pb-10 gap-8 xl:gap-0">'
code = code.replace(old_header_1, new_header_1)

old_header_2 = '<div className="flex items-center gap-6">'
new_header_2 = '<div className="flex flex-col xl:flex-row items-center gap-6 w-full xl:w-auto">'
code = code.replace(old_header_2, new_header_2)

old_header_3 = '<div className="w-px h-6 bg-black/5 dark:bg-white/5"></div>'
new_header_3 = '<div className="hidden xl:block w-px h-6 bg-black/5 dark:bg-white/5"></div>'
code = code.replace(old_header_3, new_header_3)

# The Nav buttons wrapper
old_nav_wrap = '<div className="flex bg-zinc-100 dark:bg-[#0c0d12] p-1 rounded-xl border border-black/5 dark:border-white/5">'
new_nav_wrap = '<div className="flex w-full overflow-x-auto custom-scrollbar touch-pan-x bg-zinc-100 dark:bg-[#0c0d12] p-1 rounded-xl border border-black/5 dark:border-white/5 flex-nowrap">'
code = code.replace(old_nav_wrap, new_nav_wrap)

# Inside the nav buttons, replace flex-1 with flex-none whitespace-nowrap
code = code.replace('className={`flex-1 px-5 py-2.5', 'className={`whitespace-nowrap flex-none px-5 py-2.5')
code = code.replace('className={`flex-1 flex justify-center', 'className={`whitespace-nowrap flex-none flex justify-center')

# Wrap the date block on mobile
# find the block with calendar icon
old_dateblock = '<div className="flex items-center gap-2 text-[9px] font-bold text-zinc-600 uppercase tracking-widest">'
new_dateblock = '<div className="flex flex-wrap justify-center items-center gap-2 text-[9px] font-bold text-zinc-600 uppercase tracking-widest">'
code = code.replace(old_dateblock, new_dateblock)

# 4. Office Zone responsiveness
# <div className="grid grid-cols-1 gap-12 relative z-10"> -> gap-8 to ensure it fits better? 
# The UI fits reasonably well on mobiles already thanks to grid-cols-1 lg:grid-cols-2

with open('src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("page.tsx updated")
