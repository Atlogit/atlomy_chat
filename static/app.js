document.addEventListener('DOMContentLoaded', () => {
    // Navigation
    const navButtons = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('.mode-section');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            
            // Update active button
            navButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show active section
            sections.forEach(section => {
                section.classList.remove('active');
                if (section.id === `${mode}-section`) {
                    section.classList.add('active');
                }
            });
        });
    });

    // LLM Assistant
    const llmForm = document.querySelector('#llm-section');
    const llmResults = llmForm.querySelector('.results-content');

    llmForm.querySelector('#llm-submit').addEventListener('click', async () => {
        const query = llmForm.querySelector('#llm-query').value;
        try {
            const response = await fetch('/api/llm/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });
            const data = await response.json();
            llmResults.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            llmResults.textContent = `Error: ${error.message}`;
        }
    });

    // Lexical Values
    const lexicalSection = document.querySelector('#lexical-section');
    const actionButtons = lexicalSection.querySelectorAll('.action-btn');
    const actionForms = lexicalSection.querySelectorAll('.action-form');
    const lexicalResults = lexicalSection.querySelector('.results-content');

    actionButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const action = btn.dataset.action;
            actionForms.forEach(form => {
                form.classList.remove('active');
                if (form.id === `${action}-form`) {
                    form.classList.add('active');
                }
            });

            if (action === 'list') {
                listLexicalValues();
            }
        });
    });

    // Create lexical value
    document.querySelector('#create-form .submit-btn').addEventListener('click', async () => {
        const word = document.querySelector('#create-word').value;
        const searchLemma = document.querySelector('#create-lemma').checked;
        try {
            const response = await fetch('/api/lexical/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ word, searchLemma })
            });
            const data = await response.json();
            lexicalResults.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            lexicalResults.textContent = `Error: ${error.message}`;
        }
    });

    // Get lexical value
    document.querySelector('#get-form .submit-btn').addEventListener('click', async () => {
        const lemma = document.querySelector('#get-lemma').value;
        try {
            const response = await fetch(`/api/lexical/get/${encodeURIComponent(lemma)}`);
            const data = await response.json();
            lexicalResults.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            lexicalResults.textContent = `Error: ${error.message}`;
        }
    });

    // Update lexical value
    document.querySelector('#update-form .submit-btn').addEventListener('click', async () => {
        const lemma = document.querySelector('#update-lemma').value;
        const translation = document.querySelector('#update-translation').value;
        try {
            const response = await fetch('/api/lexical/update', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ lemma, translation })
            });
            const data = await response.json();
            lexicalResults.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            lexicalResults.textContent = `Error: ${error.message}`;
        }
    });

    // Delete lexical value
    document.querySelector('#delete-form .submit-btn').addEventListener('click', async () => {
        const lemma = document.querySelector('#delete-lemma').value;
        try {
            const response = await fetch(`/api/lexical/delete/${encodeURIComponent(lemma)}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            lexicalResults.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            lexicalResults.textContent = `Error: ${error.message}`;
        }
    });

    // List lexical values
    async function listLexicalValues() {
        try {
            const response = await fetch('/api/lexical/list');
            const data = await response.json();
            lexicalResults.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            lexicalResults.textContent = `Error: ${error.message}`;
        }
    }

    // Corpus Manager
    const corpusSection = document.querySelector('#corpus-section');
    const corpusResults = corpusSection.querySelector('.results-content');
    const searchForm = document.querySelector('#search-form');

    corpusSection.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const action = btn.dataset.action;
            
            // Show/hide search form based on action
            searchForm.style.display = action === 'search-texts' ? 'block' : 'none';

            // Handle immediate actions
            if (action === 'list-texts') {
                listTexts();
            } else if (action === 'get-all') {
                getAllTexts();
            }
        });
    });

    // Search texts
    searchForm.querySelector('.submit-btn').addEventListener('click', async () => {
        const query = document.querySelector('#search-query').value;
        const searchLemma = document.querySelector('#search-lemma').checked;
        try {
            const response = await fetch('/api/corpus/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query, searchLemma })
            });
            const data = await response.json();
            corpusResults.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            corpusResults.textContent = `Error: ${error.message}`;
        }
    });

    // List texts
    async function listTexts() {
        try {
            const response = await fetch('/api/corpus/list');
            const data = await response.json();
            corpusResults.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            corpusResults.textContent = `Error: ${error.message}`;
        }
    }

    // Get all texts
    async function getAllTexts() {
        try {
            const response = await fetch('/api/corpus/all');
            const data = await response.json();
            corpusResults.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
            corpusResults.textContent = `Error: ${error.message}`;
        }
    }
});
