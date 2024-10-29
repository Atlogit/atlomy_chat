document.addEventListener('DOMContentLoaded', () => {
    // Navigation
    const navButtons = document.querySelectorAll('.tab');
    const sections = document.querySelectorAll('.mode-section');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            
            // Update active button
            navButtons.forEach(b => b.classList.remove('tab-active'));
            btn.classList.add('tab-active');
            
            // Show active section with animation
            sections.forEach(section => {
                if (section.id === `${mode}-section`) {
                    section.classList.remove('hidden');
                    section.classList.remove('animate-fade-in');
                    void section.offsetWidth; // Force reflow
                    section.classList.add('animate-fade-in');
                } else {
                    section.classList.add('hidden');
                }
            });
        });
    });

    // Helper function to handle loading states
    const withLoading = async (button, action) => {
        const spinner = button.querySelector('.loading');
        const text = button.querySelector('.button-text');
        const cancelBtn = button.parentElement?.querySelector('[data-cancel-for], .btn-error');
        const controller = new AbortController();
        const signal = controller.signal;
        
        if (spinner) spinner.classList.remove('hidden');
        if (text) text.classList.add('opacity-0');
        if (cancelBtn) {
            cancelBtn.classList.remove('hidden');
            cancelBtn.onclick = () => controller.abort();
        }
        button.disabled = true;
        
        try {
            await action(signal);
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Operation cancelled');
            } else {
                console.error('Operation failed:', error);
                throw error;
            }
        } finally {
            if (spinner) spinner.classList.add('hidden');
            if (text) text.classList.remove('opacity-0');
            if (cancelBtn) {
                cancelBtn.classList.add('hidden');
                cancelBtn.onclick = null;
            }
            button.disabled = false;
        }
    };

    // Helper function to update progress
    const updateProgress = (container, current, total) => {
        const progressContainer = container.querySelector('.progress-container');
        const progressBar = progressContainer?.querySelector('progress');
        const progressText = progressContainer?.querySelector('.progress-text');
        
        if (progressContainer && progressBar && progressText) {
            progressContainer.classList.remove('hidden');
            progressBar.value = (current / total) * 100;
            progressText.textContent = `${current}/${total}`;
        }
    };

    // Format citation with sentence context
    const formatCitation = (citation) => {
        const authorWork = `${citation.source.author}, ${citation.source.work}`;
        const location = [
            citation.location.volume && `Volume ${citation.location.volume}`,
            citation.location.chapter && `Chapter ${citation.location.chapter}`,
            citation.location.section && `Section ${citation.location.section}`
        ].filter(Boolean).join(', ');
        
        return `${authorWork} (${location})`;
    };

    // Create citation element with context preview
    const createCitationElement = (citation) => {
        const div = document.createElement('div');
        div.className = 'citation-entry card bg-base-200 p-4';
        
        const citationText = formatCitation(citation);
        const sentencePreview = citation.sentence.text.length > 100 
            ? citation.sentence.text.substring(0, 100) + '...'
            : citation.sentence.text;
            
        div.innerHTML = `
            <div class="flex justify-between items-start">
                <div class="citation-text font-medium">${citationText}</div>
                <button class="btn btn-sm btn-ghost show-context" data-citation-id="${citation.sentence.id}">
                    Show Context
                </button>
            </div>
            <div class="mt-2 text-sm">${sentencePreview}</div>
        `;
        
        // Add click handler for context preview
        const contextBtn = div.querySelector('.show-context');
        contextBtn.addEventListener('click', () => {
            showCitationContext(citation);
        });
        
        return div;
    };

    // Show citation context in modal
    const showCitationContext = (citation) => {
        const modal = document.getElementById('citation-preview-modal');
        const prevSentence = modal.querySelector('.prev-sentence');
        const currentSentence = modal.querySelector('.current-sentence');
        const nextSentence = modal.querySelector('.next-sentence');
        
        prevSentence.textContent = citation.sentence.prev_sentence || '';
        currentSentence.textContent = citation.sentence.text;
        nextSentence.textContent = citation.sentence.next_sentence || '';
        
        modal.showModal();
    };

    // Format lexical value display
    const formatLexicalValue = (data) => {
        const display = document.querySelector('.lexical-value-display');
        const rawDisplay = document.querySelector('.raw-results');
        
        if (!display || !rawDisplay) return;
        
        try {
            // Show structured display
            display.classList.remove('hidden');
            rawDisplay.classList.add('hidden');
            
            // Set basic information
            display.querySelector('.lemma-title').textContent = data.lemma;
            display.querySelector('.translation').textContent = data.translation;
            display.querySelector('.short-description').textContent = data.short_description;
            display.querySelector('.long-description').textContent = data.long_description;
            
            // Clear and populate citations
            const citationsList = display.querySelector('.citations-list');
            citationsList.innerHTML = '';
            if (data.citations_used) {
                data.citations_used.forEach(citation => {
                    citationsList.appendChild(createCitationElement(citation));
                });
            }
            
            // Add related terms
            const relatedTerms = display.querySelector('.related-terms');
            relatedTerms.innerHTML = '';
            if (data.related_terms) {
                data.related_terms.forEach(term => {
                    const badge = document.createElement('div');
                    badge.className = 'badge badge-primary';
                    badge.textContent = term;
                    relatedTerms.appendChild(badge);
                });
            }
            
            // Add version info
            const versionInfo = display.querySelector('.version-info');
            if (data.metadata) {
                versionInfo.innerHTML = `
                    <div>Created: ${new Date(data.metadata.created_at).toLocaleString()}</div>
                    <div>Updated: ${new Date(data.metadata.updated_at).toLocaleString()}</div>
                    <div>Version: ${data.metadata.version}</div>
                `;
            }
        } catch (error) {
            // Fallback to raw display
            console.error('Error formatting lexical value:', error);
            display.classList.add('hidden');
            rawDisplay.classList.remove('hidden');
            rawDisplay.textContent = JSON.stringify(data, null, 2);
        }
    };

    // Format JSON results
    const formatResults = (data, type = 'raw') => {
        try {
            if (type === 'lexical' && typeof data === 'object') {
                formatLexicalValue(data);
                return;
            }
            
            // Default to raw JSON display
            const display = document.querySelector('.lexical-value-display');
            const rawDisplay = document.querySelector('.raw-results');
            
            if (display) display.classList.add('hidden');
            if (rawDisplay) {
                rawDisplay.classList.remove('hidden');
                rawDisplay.textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
            }
        } catch (error) {
            console.error('Error formatting results:', error);
            return `Error formatting results: ${error.message}`;
        }
    };

    // LLM Assistant
    const llmForm = document.querySelector('#llm-section');
    if (llmForm) {
        const llmResults = llmForm.querySelector('.results-content');
        const llmSubmit = llmForm.querySelector('#llm-submit');

        if (llmSubmit) {
            llmSubmit.addEventListener('click', async () => {
                const query = llmForm.querySelector('#llm-query')?.value || '';
                
                try {
                    await withLoading(llmSubmit, async (signal) => {
                        const response = await fetch('/api/llm/query', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ query }),
                            signal
                        });
                        
                        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                        const data = await response.json();
                        if (llmResults) llmResults.textContent = formatResults(data);
                    });
                } catch (error) {
                    if (error.name !== 'AbortError' && llmResults) {
                        llmResults.textContent = `Error: ${error.message}`;
                    }
                }
            });
        }
    }

    // Lexical Values
    const lexicalSection = document.querySelector('#lexical-section');
    if (lexicalSection) {
        const actionButtons = lexicalSection.querySelectorAll('.join-item');
        const actionForms = lexicalSection.querySelectorAll('.action-form');
        const lexicalResults = lexicalSection.querySelector('.results-content');

        actionButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                
                // Update active button
                actionButtons.forEach(b => b.classList.remove('btn-active'));
                btn.classList.add('btn-active');
                
                // Show active form with animation
                actionForms.forEach(form => {
                    if (form.id === `${action}-form`) {
                        form.classList.remove('collapse');
                        form.classList.remove('animate-fade-in');
                        void form.offsetWidth; // Force reflow
                        form.classList.add('animate-fade-in');
                    } else {
                        form.classList.add('collapse');
                    }
                });

                if (action === 'list') {
                    listLexicalValues(btn, lexicalResults);
                }
            });
        });

        // Create lexical value
        const createForm = document.querySelector('#create-form');
        if (createForm) {
            const createButton = createForm.querySelector('.submit-btn');
            if (createButton) {
                createButton.addEventListener('click', async () => {
                    const word = document.querySelector('#create-word')?.value || '';
                    const searchLemma = document.querySelector('#create-lemma')?.checked || false;
                    
                    try {
                        await withLoading(createButton, async (signal) => {
                            const response = await fetch('/api/lexical/create', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ word, searchLemma }),
                                signal
                            });
                            
                            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                            const data = await response.json();
                            formatResults(data.entry, 'lexical');
                        });
                    } catch (error) {
                        if (error.name !== 'AbortError' && lexicalResults) {
                            formatResults(`Error: ${error.message}`);
                        }
                    }
                });
            }
        }

        // Batch Create lexical values
        const batchCreateForm = document.querySelector('#batch-create-form');
        if (batchCreateForm) {
            const batchCreateButton = batchCreateForm.querySelector('.submit-btn');
            if (batchCreateButton) {
                batchCreateButton.addEventListener('click', async () => {
                    const textarea = document.querySelector('#batch-create-words');
                    const words = textarea?.value.split('\n').filter(word => word.trim()) || [];
                    const searchLemma = document.querySelector('#batch-create-lemma')?.checked || false;
                    
                    if (words.length === 0) {
                        formatResults('Error: No words provided');
                        return;
                    }

                    try {
                        await withLoading(batchCreateButton, async (signal) => {
                            const response = await fetch('/api/lexical/batch-create', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ words, searchLemma }),
                                signal
                            });
                            
                            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                            const data = await response.json();
                            
                            // Update progress as results come in
                            const total = words.length;
                            const results = data.results || {};
                            updateProgress(batchCreateForm, Object.keys(results).length, total);
                            
                            formatResults(data);
                        });
                    } catch (error) {
                        if (error.name !== 'AbortError') {
                            formatResults(`Error: ${error.message}`);
                        }
                    }
                });
            }
        }

        // Get lexical value
        const getForm = document.querySelector('#get-form');
        if (getForm) {
            const getButton = getForm.querySelector('.submit-btn');
            if (getButton) {
                getButton.addEventListener('click', async () => {
                    const lemma = document.querySelector('#get-lemma')?.value || '';
                    
                    try {
                        await withLoading(getButton, async (signal) => {
                            const response = await fetch(`/api/lexical/get/${encodeURIComponent(lemma)}`, { signal });
                            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                            const data = await response.json();
                            formatResults(data, 'lexical');
                        });
                    } catch (error) {
                        if (error.name !== 'AbortError') {
                            formatResults(`Error: ${error.message}`);
                        }
                    }
                });
            }
        }

        // Update lexical value
        const updateForm = document.querySelector('#update-form');
        if (updateForm) {
            const updateButton = updateForm.querySelector('.submit-btn');
            if (updateButton) {
                updateButton.addEventListener('click', async () => {
                    const lemma = document.querySelector('#update-lemma')?.value || '';
                    const translation = document.querySelector('#update-translation')?.value || '';
                    
                    try {
                        await withLoading(updateButton, async (signal) => {
                            const response = await fetch('/api/lexical/update', {
                                method: 'PUT',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ lemma, translation }),
                                signal
                            });
                            
                            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                            const data = await response.json();
                            formatResults(data.entry, 'lexical');
                        });
                    } catch (error) {
                        if (error.name !== 'AbortError') {
                            formatResults(`Error: ${error.message}`);
                        }
                    }
                });
            }
        }

        // Batch Update lexical values
        const batchUpdateForm = document.querySelector('#batch-update-form');
        if (batchUpdateForm) {
            // Add Entry button handler
            const addEntryButton = batchUpdateForm.querySelector('#add-update-entry');
            const entriesContainer = batchUpdateForm.querySelector('#batch-update-entries');
            
            if (addEntryButton && entriesContainer) {
                addEntryButton.addEventListener('click', () => {
                    const newEntry = document.createElement('div');
                    newEntry.className = 'flex gap-2 batch-update-entry';
                    newEntry.innerHTML = `
                        <input type="text" placeholder="Enter lemma" class="input input-bordered flex-1 batch-update-lemma">
                        <input type="text" placeholder="Enter translation" class="input input-bordered flex-1 batch-update-translation">
                        <button class="btn btn-square btn-error remove-entry">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    `;
                    entriesContainer.appendChild(newEntry);
                });

                // Remove Entry button handler
                entriesContainer.addEventListener('click', (e) => {
                    if (e.target.closest('.remove-entry')) {
                        const entry = e.target.closest('.batch-update-entry');
                        if (entry && entriesContainer.children.length > 1) {
                            entry.remove();
                        }
                    }
                });

                // Submit handler
                const updateButton = batchUpdateForm.querySelector('.submit-btn');
                if (updateButton) {
                    updateButton.addEventListener('click', async () => {
                        const entries = Array.from(entriesContainer.querySelectorAll('.batch-update-entry'));
                        const updates = entries.map(entry => ({
                            lemma: entry.querySelector('.batch-update-lemma').value,
                            translation: entry.querySelector('.batch-update-translation').value
                        })).filter(update => update.lemma && update.translation);

                        if (updates.length === 0) {
                            formatResults('Error: No valid updates provided');
                            return;
                        }

                        try {
                            await withLoading(updateButton, async (signal) => {
                                const response = await fetch('/api/lexical/batch-update', {
                                    method: 'PUT',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ updates }),
                                    signal
                                });
                                
                                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                                const data = await response.json();
                                
                                // Update progress as results come in
                                const total = updates.length;
                                const results = data.results || {};
                                updateProgress(batchUpdateForm, Object.keys(results).length, total);
                                
                                formatResults(data);
                            });
                        } catch (error) {
                            if (error.name !== 'AbortError') {
                                formatResults(`Error: ${error.message}`);
                            }
                        }
                    });
                }
            }
        }

        // Delete lexical value
        const deleteForm = document.querySelector('#delete-form');
        if (deleteForm) {
            const deleteButton = deleteForm.querySelector('.submit-btn');
            if (deleteButton) {
                deleteButton.addEventListener('click', async () => {
                    const lemma = document.querySelector('#delete-lemma')?.value || '';
                    
                    try {
                        await withLoading(deleteButton, async (signal) => {
                            const response = await fetch(`/api/lexical/delete/${encodeURIComponent(lemma)}`, {
                                method: 'DELETE',
                                signal
                            });
                            
                            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                            const data = await response.json();
                            formatResults(data);
                        });
                    } catch (error) {
                        if (error.name !== 'AbortError') {
                            formatResults(`Error: ${error.message}`);
                        }
                    }
                });
            }
        }

        // Versions management
        const versionsForm = document.querySelector('#versions-form');
        if (versionsForm) {
            const versionsButton = versionsForm.querySelector('.submit-btn');
            const versionsList = versionsForm.querySelector('#versions-list');
            const versionsTable = versionsList?.querySelector('tbody');
            
            if (versionsButton && versionsList && versionsTable) {
                versionsButton.addEventListener('click', async () => {
                    const lemma = document.querySelector('#versions-lemma')?.value || '';
                    
                    try {
                        await withLoading(versionsButton, async (signal) => {
                            const response = await fetch(`/api/lexical/versions/${encodeURIComponent(lemma)}`, { signal });
                            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                            const data = await response.json();
                            
                            // Clear and populate versions table
                            versionsTable.innerHTML = '';
                            versionsList.classList.remove('hidden');
                            
                            data.versions.forEach(version => {
                                const row = document.createElement('tr');
                                row.innerHTML = `
                                    <td>${version.version}</td>
                                    <td>${new Date(version.date).toLocaleString()}</td>
                                    <td>
                                        <button class="btn btn-sm btn-primary view-version" data-version="${version.version}">
                                            View
                                        </button>
                                    </td>
                                `;
                                versionsTable.appendChild(row);
                            });
                            
                            // Add click handlers for version buttons
                            versionsTable.querySelectorAll('.view-version').forEach(btn => {
                                btn.addEventListener('click', async () => {
                                    const version = btn.dataset.version;
                                    try {
                                        const response = await fetch(`/api/lexical/get/${encodeURIComponent(lemma)}/${version}`);
                                        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                                        const data = await response.json();
                                        formatResults(data, 'lexical');
                                    } catch (error) {
                                        formatResults(`Error: ${error.message}`);
                                    }
                                });
                            });
                        });
                    } catch (error) {
                        if (error.name !== 'AbortError') {
                            formatResults(`Error: ${error.message}`);
                            versionsList.classList.add('hidden');
                        }
                    }
                });
            }
        }

        // List lexical values
        async function listLexicalValues(button, resultsElement) {
            try {
                await withLoading(button, async (signal) => {
                    const response = await fetch('/api/lexical/list', { signal });
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    const data = await response.json();
                    formatResults(data);
                });
            } catch (error) {
                if (error.name !== 'AbortError') {
                    formatResults(`Error: ${error.message}`);
                }
            }
        }
    }

    // Corpus Manager
    const corpusSection = document.querySelector('#corpus-section');
    if (corpusSection) {
        const corpusResults = corpusSection.querySelector('.results-content');
        const searchForm = document.querySelector('#search-form');

        corpusSection.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                
                // Show/hide search form with animation
                if (action === 'search-texts' && searchForm) {
                    searchForm.classList.remove('collapse');
                    searchForm.classList.remove('animate-fade-in');
                    void searchForm.offsetWidth; // Force reflow
                    searchForm.classList.add('animate-fade-in');
                } else if (searchForm) {
                    searchForm.classList.add('collapse');
                }

                // Handle immediate actions
                if (action === 'list-texts') {
                    listTexts(btn, corpusResults);
                } else if (action === 'get-all') {
                    getAllTexts(btn, corpusResults);
                }
            });
        });

        // Search texts
        if (searchForm) {
            const searchButton = searchForm.querySelector('.submit-btn');
            if (searchButton) {
                searchButton.addEventListener('click', async () => {
                    const query = document.querySelector('#search-query')?.value || '';
                    const searchLemma = document.querySelector('#search-lemma')?.checked || false;
                    
                    try {
                        await withLoading(searchButton, async (signal) => {
                            const response = await fetch('/api/corpus/search', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ query, searchLemma }),
                                signal
                            });
                            
                            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                            const data = await response.json();
                            formatResults(data);
                        });
                    } catch (error) {
                        if (error.name !== 'AbortError') {
                            formatResults(`Error: ${error.message}`);
                        }
                    }
                });
            }
        }

        // List texts
        async function listTexts(button, resultsElement) {
            try {
                await withLoading(button, async (signal) => {
                    const response = await fetch('/api/corpus/list', { signal });
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    const data = await response.json();
                    formatResults(data);
                });
            } catch (error) {
                if (error.name !== 'AbortError') {
                    formatResults(`Error: ${error.message}`);
                }
            }
        }

        // Get all texts
        async function getAllTexts(button, resultsElement) {
            try {
                await withLoading(button, async (signal) => {
                    const response = await fetch('/api/corpus/all', { signal });
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    const data = await response.json();
                    formatResults(data);
                });
            } catch (error) {
                if (error.name !== 'AbortError') {
                    formatResults(`Error: ${error.message}`);
                }
            }
        }
    }

    // Initialize first section
    document.querySelector('.tab-active')?.click();
});
