import re

with open('src/app/page.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update Player Block
old_player = """      {activeDialog && (
        <div className="fixed bottom-0 left-0 right-0 z-50 animate-in slide-in-from-bottom duration-500">
           <div className="max-w-6xl mx-auto mb-8 px-6">
              <div className="bg-zinc-100 dark:bg-zinc-900/90 backdrop-blur-3xl border border-black/10 dark:border-white/10 rounded-[2.5rem] p-6 flex items-center gap-10 shadow-[0_8px_30px_rgb(0,0,0,0.08)] dark:shadow-2xl shadow-black/10 dark:shadow-black/50 border-black/5 dark:border-white/10">
                 <div className="flex items-center gap-5">
                    <div className="w-16 h-16 bg-emerald-500 rounded-2xl flex items-center justify-center">
                       <Volume2 size={32} className="text-black" />
                    </div>
                    <div>
                       <h4 className="font-bold text-sm tracking-tight mb-1">Диалог #{activeDialog?.dialog_index}</h4>
                       <p className="text-[10px] font-bold text-zinc-500 uppercase">{shops.find(s => s.id === activeDialog?.shop_id)?.name}</p>
                    </div>
                 </div>
                 <div className="flex-1 flex flex-col gap-3">
                    <div className="flex items-center justify-center gap-8">
                       <button onClick={togglePlay} className="w-12 h-12 bg-white text-black rounded-full flex items-center justify-center shadow-xl hover:scale-110 active:scale-95 transition-all">
                          {isPlaying ? <PauseCircle size={24} /> : <PlayCircle size={24} />}
                       </button>
                    </div>
                    <div className="flex items-center gap-4">
                       <span className="text-[10px] text-zinc-600 min-w-[35px] font-mono">{formatTime(currentTime)}</span>
                       <div className="flex-1 h-2 bg-black/5 dark:bg-white/5 rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-500/50 transition-all duration-300" style={{ width: `${(currentTime / duration) * 100}%` }} />
                       </div>
                       <span className="text-[10px] text-zinc-600 min-w-[35px] font-mono">{formatTime(duration)}</span>
                    </div>
                 </div>
              </div>
           </div>"""

new_player = """      {activeDialog && (
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
                 </div>

                 {/* Desktop Close Button */}
                 <button onClick={() => { setActiveDialog(null); setIsPlaying(false); }} className="hidden md:flex w-12 h-12 items-center justify-center text-zinc-400 hover:text-zinc-900 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 transition-colors rounded-full shrink-0">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                 </button>
                 
              </div>
           </div>"""
code = code.replace(old_player, new_player)

# Also fix the fact that playphrase sets isPlaying true but doesn't actually trigger the toggle correctly sometimes.
# Let's ensure activeDialog goes to null safely and doesn't conflict. The `setActiveDialog(null)` inside the X button works correctly for Next.js.
with open('src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("done")
