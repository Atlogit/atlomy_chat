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

    // Format JSON results
    const formatResults = (data) => {
        try {
            return typeof data === 'string' ? data : JSON.stringify(data, null, 2);
        } catch (error) {
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
                            if (lexicalResults) lexicalResults.textContent = formatResults(data);
                        });
                    } catch (error) {
                        if (error.name !== 'AbortError' && lexicalResults) {
                            lexicalResults.textContent = `Error: ${error.message}`;
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
                        if (lexicalResults) lexicalResults.textContent = 'Error: No words provided';
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
                            
                            if (lexicalResults) lexicalResults.textContent = formatResults(data);
                        });
                    } catch (error) {
                        if (error.name !== 'AbortError' && lexicalResults) {
                            lexicalResults.textContent = `Error: ${error.message}`;
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
                            if (lexicalResults) lexicalResults.textContent = formatResults(data);
                        });
                    } catch (error) {
                        if (error.name !== 'AbortError' && lexicalResults) {
                            lexicalResults.textContent = `Error: ${error.message}`;
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
                            if (lexicalResults) lexicalResults.textContent = formatResults(data);
                        });
                    } catch (error) {
                        if (error.name !== 'AbortError' && lexicalResults) {
                            lexicalResults.textContent = `Error: ${error.message}`;
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
                            if (lexicalResults) lexicalResults.textContent = 'Error: No valid updates provided';
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
                                
                                if (lexicalResults) lexicalResults.textContent = formatResults(data);
                            });
                        } catch (error) {
                            if (error.name !== 'AbortError' && lexicalResults) {
                                lexicalResults.textContent = `Error: ${error.message}`;
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
                            if (lexicalResults) lexicalResults.textContent = formatResults(data);
                        });
                    } catch (error) {
                        if (error.name !== 'AbortError' && lexicalResults) {
                            lexicalResults.textContent = `Error: ${error.message}`;
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
                    if (resultsElement) resultsElement.textContent = formatResults(data);
                });
            } catch (error) {
                if (error.name !== 'AbortError' && resultsElement) {
                    resultsElement.textContent = `Error: ${error.message}`;
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
                            if (corpusResults) corpusResults.textContent = formatResults(data);
                        });
                    } catch (error) {
                        if (error.name !== 'AbortError' && corpusResults) {
                            corpusResults.textContent = `Error: ${error.message}`;
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
                    if (resultsElement) resultsElement.textContent = formatResults(data);
                });
            } catch (error) {
                if (error.name !== 'AbortError' && resultsElement) {
                    resultsElement.textContent = `Error: ${error.message}`;
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
                    if (resultsElement) resultsElement.textContent = formatResults(data);
                });
            } catch (error) {
                if (error.name !== 'AbortError' && resultsElement) {
                    resultsElement.textContent = `Error: ${error.message}`;
                }
            }
        }
    }

    // Initialize first section
    document.querySelector('.tab-active')?.click();
});
