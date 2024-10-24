'use client'

import { Navigation } from './Navigation'

interface HeaderProps {
  activeTab: string
  onTabChange: (tabId: string) => void
}

export function Header({ activeTab, onTabChange }: HeaderProps) {
  return (
    <header className="text-center mb-8 animate-fade-in">
      <h1 className="text-4xl font-bold mb-6 text-primary">
        Ancient Medical Texts Analysis
      </h1>
      <Navigation activeTab={activeTab} onTabChange={onTabChange} />
    </header>
  )
}
