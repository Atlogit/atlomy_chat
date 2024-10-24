'use client'

import { useState } from 'react'
import { Header } from '../components/layout/Header'
import { LLMSection } from '../components/sections/llm/LLMSection'
import { LexicalSection } from '../components/sections/lexical/LexicalSection'
import { CorpusSection } from '../components/sections/corpus/CorpusSection'
import ErrorBoundary from '../components/ErrorBoundary'

export default function Home() {
  const [activeTab, setActiveTab] = useState('llm')

  const ErrorFallback = () => (
    <div className="text-center py-10">
      <h2 className="text-2xl font-bold text-red-600 mb-4">Oops! Something went wrong.</h2>
      <p className="text-gray-600">We're sorry for the inconvenience. Please try refreshing the page or contact support if the problem persists.</p>
    </div>
  )

  return (
    <ErrorBoundary fallback={<ErrorFallback />}>
      <Header activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="container mx-auto py-6 px-4 space-y-6">
        {activeTab === 'llm' && <LLMSection />}
        {activeTab === 'lexical' && <LexicalSection />}
        {activeTab === 'corpus' && <CorpusSection />}
      </main>
    </ErrorBoundary>
  )
}
