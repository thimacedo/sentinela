'use client'

import { useEffect, useState } from 'react'
import { Sun, Moon } from 'lucide-react'

export default function ThemeToggle() {
  const [theme, setTheme] = useState('dark')

  useEffect(() => {
    // Recupera preferência salva ou usa dark como padrão
    const savedTheme = localStorage.getItem('sentinela-theme') || 'dark'
    setTheme(savedTheme)
    document.documentElement.setAttribute('data-theme', savedTheme)
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem('sentinela-theme', newTheme)
  }

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg bg-bg-card border border-border-main hover:border-brand-primary transition-all group"
      aria-label="Alternar Tema"
    >
      {theme === 'dark' ? (
        <Sun size={20} className="text-brand-primary group-hover:rotate-45 transition-transform" />
      ) : (
        <Moon size={20} className="text-slate-600 group-hover:-rotate-12 transition-transform" />
      )}
    </button>
  )
}
