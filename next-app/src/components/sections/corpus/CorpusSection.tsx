'use client'

import { useState } from 'react'
import { ListTexts } from './ListTexts'
import { SearchForm } from './SearchForm'
import { TextDisplay } from './TextDisplay'
import { ResultsDisplay } from '../../../components/ui/ResultsDisplay'

type ActiveView = 'list' | 'search' | 'view'

interface ViewError {
  message: string
  code?: string
  details?: string
}

export function CorpusSection() {
  const [activeView, setActiveView] = useState<ActiveView>('list')
  const [selectedText, setSelectedText] = useState<string | null>(null)
  const [error, setError] = useState<ViewError | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleError = (err: Error | ViewError) => {
    console.error('Corpus section error:', err)
    const errorMessage = 'code' in err 
      ? `${err.message}${err.details ? ` - ${err.details}` : ''}`
      : err.message
    setError({ message: errorMessage })
  }

  const handleTextSelect = async (textId: string) => {
    try {
      setIsLoading(true)
      setSelectedText(textId)
      setActiveView('view')
      setError(null)
    } catch (err) {
      handleError(err as Error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleViewChange = (view: ActiveView) => {
    try {
      setActiveView(view)
      if (view !== 'view') {
        setSelectedText(null)
      }
      setError(null)
    } catch (err) {
      handleError(err as Error)
    }
  }

  const renderBreadcrumbs = () => {
    const crumbs = []
    
    // Always show Home
    crumbs.push(
      <button 
        key="home"
        className="text-sm hover:underline"
        onClick={() => handleViewChange('list')}
      >
        Home
      </button>
    )

    // Add current view
    if (activeView === 'search') {
      crumbs.push(
        <span key="search" className="text-sm text-base-content/70">
          / Search
        </span>
      )
    } else if (activeView === 'view' && selectedText) {
      crumbs.push(
        <span key="view" className="text-sm text-base-content/70">
          / Viewing Text {selectedText}
        </span>
      )
    }

    return (
      <div className="text-sm breadcrumbs">
        <ul>
          {crumbs.map((crumb, index) => (
            <li key={index}>{crumb}</li>
          ))}
        </ul>
      </div>
    )
  }

  return (
    <div className="card bg-base-100 shadow-xl">
      <div className="card-body">
        <div className="space-y-4">
          {/* Header Section */}
          <div className="flex justify-between items-center">
            <h2 className="card-title text-2xl">Corpus Manager</h2>
            <div className="tabs tabs-boxed">
              <a 
                className={`tab ${activeView === 'list' ? 'tab-active' : ''}`}
                onClick={() => handleViewChange('list')}
              >
                List Texts
              </a>
              <a 
                className={`tab ${activeView === 'search' ? 'tab-active' : ''}`}
                onClick={() => handleViewChange('search')}
              >
                Search
              </a>
              {selectedText && (
                <a 
                  className={`tab ${activeView === 'view' ? 'tab-active' : ''}`}
                  onClick={() => handleViewChange('view')}
                >
                  View Text
                </a>
              )}
            </div>
          </div>

          {/* Breadcrumb Navigation */}
          {renderBreadcrumbs()}

          {/* Main Content */}
          {error ? (
            <ResultsDisplay 
              error={error.message}
              content={null}
            />
          ) : isLoading ? (
            <div className="flex justify-center p-8">
              <span className="loading loading-spinner loading-lg"></span>
            </div>
          ) : (
            <div className="view-container">
              {activeView === 'list' && (
                <ListTexts onTextSelect={handleTextSelect} />
              )}
              {activeView === 'search' && (
                <SearchForm onResultSelect={handleTextSelect} />
              )}
              {activeView === 'view' && selectedText && (
                <TextDisplay textId={selectedText} />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
