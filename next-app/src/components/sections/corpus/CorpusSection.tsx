'use client'

import { useState } from 'react'
import { ListTexts } from './ListTexts'
import { SearchForm } from './SearchForm'
import { TextDisplay } from './TextDisplay'

type ActiveView = 'list' | 'search' | 'view'

export function CorpusSection() {
  const [activeView, setActiveView] = useState<ActiveView>('list')
  const [selectedText, setSelectedText] = useState<string | null>(null)

  return (
    <div className="card bg-base-100 shadow-xl">
      <div className="card-body">
        <h2 className="card-title">Corpus Manager</h2>
        
        <div className="tabs tabs-boxed mb-4">
          <a 
            className={`tab ${activeView === 'list' ? 'tab-active' : ''}`}
            onClick={() => {
              setActiveView('list')
              setSelectedText(null)
            }}
          >
            List Texts
          </a>
          <a 
            className={`tab ${activeView === 'search' ? 'tab-active' : ''}`}
            onClick={() => {
              setActiveView('search')
              setSelectedText(null)
            }}
          >
            Search
          </a>
          {selectedText && (
            <a 
              className={`tab ${activeView === 'view' ? 'tab-active' : ''}`}
              onClick={() => setActiveView('view')}
            >
              View Text
            </a>
          )}
        </div>

        <div className="view-container">
          {activeView === 'list' && (
            <ListTexts 
              onTextSelect={(text) => {
                setSelectedText(text)
                setActiveView('view')
              }}
            />
          )}
          {activeView === 'search' && (
            <SearchForm 
              onResultSelect={(text) => {
                setSelectedText(text)
                setActiveView('view')
              }}
            />
          )}
          {activeView === 'view' && selectedText && (
            <TextDisplay textId={selectedText} />
          )}
        </div>
      </div>
    </div>
  )
}
