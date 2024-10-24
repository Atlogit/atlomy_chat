'use client'

import { useState } from 'react'
import { CreateForm } from './CreateForm'
import { BatchCreateForm } from './BatchCreateForm'
import { GetForm } from './GetForm'
import { UpdateForm } from './UpdateForm'
import { BatchUpdateForm } from './BatchUpdateForm'
import { DeleteForm } from './DeleteForm'

/**
 * Represents the possible active forms in the Lexical Section.
 * This type is used to manage which form is currently displayed.
 */
type ActiveForm = 'create' | 'batchCreate' | 'get' | 'update' | 'batchUpdate' | 'delete'

/**
 * LexicalSection Component
 * 
 * This component represents the Lexical Values section of the application.
 * It provides an interface for users to perform various operations on lexical values,
 * including creation, batch creation, retrieval, updating, batch updating, and deletion.
 * 
 * @component
 */
export function LexicalSection() {
  const [activeForm, setActiveForm] = useState<ActiveForm>('create')

  return (
    <div className="card bg-base-100 shadow-xl">
      <div className="card-body">
        <h2 className="card-title">Lexical Values</h2>
        
        {/* Navigation tabs for different operations */}
        <div className="tabs tabs-boxed mb-4">
          <a 
            className={`tab ${activeForm === 'create' ? 'tab-active' : ''}`}
            onClick={() => setActiveForm('create')}
          >
            Create
          </a>
          <a 
            className={`tab ${activeForm === 'batchCreate' ? 'tab-active' : ''}`}
            onClick={() => setActiveForm('batchCreate')}
          >
            Batch Create
          </a>
          <a 
            className={`tab ${activeForm === 'get' ? 'tab-active' : ''}`}
            onClick={() => setActiveForm('get')}
          >
            Get
          </a>
          <a 
            className={`tab ${activeForm === 'update' ? 'tab-active' : ''}`}
            onClick={() => setActiveForm('update')}
          >
            Update
          </a>
          <a 
            className={`tab ${activeForm === 'batchUpdate' ? 'tab-active' : ''}`}
            onClick={() => setActiveForm('batchUpdate')}
          >
            Batch Update
          </a>
          <a 
            className={`tab ${activeForm === 'delete' ? 'tab-active' : ''}`}
            onClick={() => setActiveForm('delete')}
          >
            Delete
          </a>
        </div>

        {/* Container for the active form */}
        <div className="form-container">
          {activeForm === 'create' && <CreateForm />}
          {activeForm === 'batchCreate' && <BatchCreateForm />}
          {activeForm === 'get' && <GetForm />}
          {activeForm === 'update' && <UpdateForm />}
          {activeForm === 'batchUpdate' && <BatchUpdateForm />}
          {activeForm === 'delete' && <DeleteForm />}
        </div>
      </div>
    </div>
  )
}
