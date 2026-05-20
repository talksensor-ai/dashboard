"use client"

import * as React from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <button
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
      className="relative inline-flex items-center justify-center p-2 rounded-xl bg-[#0c0d12] border border-white/5 hover:bg-zinc-800 text-zinc-400 hover:text-white transition-all overflow-hidden"
      aria-label="Toggle theme"
    >
      <div className="relative w-4 h-4">
          <Sun className="absolute inset-0 w-4 h-4 transition-transform duration-500 rotate-0 scale-100 dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute inset-0 w-4 h-4 transition-transform duration-500 rotate-90 scale-0 dark:rotate-0 dark:scale-100" />
      </div>
    </button>
  )
}
