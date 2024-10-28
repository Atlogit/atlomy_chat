'use client'

import { QueryForm } from '../../../components/sections/corpus/QueryForm'

/**
 * CorpusQueryPage
 * 
 * This page provides an interface for users to query the corpus data using natural language.
 * The LLM will generate SQL queries based on the user's questions.
 */
export default function CorpusQueryPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Corpus Query Assistant</h1>
      <p className="mb-6 text-gray-600">
        Ask questions about the corpus data in natural language. The assistant will generate 
        SQL queries to help you find the information you need. For example:
      </p>
      <ul className="list-disc list-inside mb-8 text-gray-600">
        <li>Find all sentences containing words from the &apos;anatomy&apos; category that are also nouns</li>
        <li>Show me sentences where a word has both &apos;medical&apos; and &apos;technical&apos; categories</li>
        <li>List all sentences that mention body parts in chapters about diseases</li>
      </ul>
      <div className="bg-white shadow-md rounded-lg p-6">
        <QueryForm />
      </div>
    </div>
  )
}
