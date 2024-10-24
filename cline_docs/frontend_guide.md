# Frontend Development Guide

This guide documents the JavaScript patterns, API integration, and development workflow for the Ancient Medical Texts Analysis App.

## Table of Contents
1. [Development Setup](#development-setup)
2. [JavaScript Patterns](#javascript-patterns)
3. [API Integration](#api-integration)
4. [State Management](#state-management)
5. [Error Handling](#error-handling)
6. [Loading States](#loading-states)
7. [Event Handling](#event-handling)
8. [Build Process](#build-process)

## Development Setup

### Initial Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev  # Watches for CSS changes

# Build for production
npm run build
```

### Project Structure
```
/static/
  ├── app.js          # Main JavaScript
  ├── index.html      # HTML structure
  ├── input.css       # Source CSS
  └── styles.css      # Compiled CSS
```

## JavaScript Patterns

### Module Pattern
```javascript
document.addEventListener('DOMContentLoaded', () => {
    // Module-level variables
    const state = {
        currentSection: null,
        isLoading: false
    };

    // Initialize components
    initNavigation();
    initForms();
    initEventListeners();
});
```

### Loading State Handler
```javascript
const withLoading = async (button, action) => {
    const spinner = button.querySelector('.loading');
    const text = button.querySelector('.button-text');
    
    try {
        // Show loading state
        spinner.style.display = 'inline-block';
        text.style.opacity = '0';
        button.disabled = true;
        
        // Execute action
        await action();
        
    } catch (error) {
        console.error('Operation failed:', error);
        throw error;
    } finally {
        // Reset loading state
        spinner.style.display = 'none';
        text.style.opacity = '1';
        button.disabled = false;
    }
};
```

### Form Handling
```javascript
const handleFormSubmit = async (formElement, endpoint, method = 'POST') => {
    const formData = new FormData(formElement);
    const data = Object.fromEntries(formData.entries());
    
    try {
        const response = await fetch(endpoint, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Form submission failed:', error);
        throw error;
    }
};
```

## API Integration

### API Endpoints
```javascript
const API = {
    llm: {
        query: '/api/llm/query'
    },
    lexical: {
        create: '/api/lexical/create',
        get: (lemma) => `/api/lexical/get/${encodeURIComponent(lemma)}`,
        update: '/api/lexical/update',
        delete: (lemma) => `/api/lexical/delete/${encodeURIComponent(lemma)}`,
        list: '/api/lexical/list'
    },
    corpus: {
        list: '/api/corpus/list',
        search: '/api/corpus/search',
        all: '/api/corpus/all'
    }
};
```

### API Request Helper
```javascript
const apiRequest = async (endpoint, options = {}) => {
    const defaultOptions = {
        headers: { 'Content-Type': 'application/json' }
    };
    
    try {
        const response = await fetch(endpoint, { ...defaultOptions, ...options });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
};
```

## State Management

### Section Visibility
```javascript
const updateSectionVisibility = (targetSection) => {
    document.querySelectorAll('.mode-section').forEach(section => {
        if (section.id === targetSection) {
            section.classList.remove('hidden');
            section.classList.remove('animate-fade-in');
            void section.offsetWidth; // Force reflow
            section.classList.add('animate-fade-in');
        } else {
            section.classList.add('hidden');
        }
    });
};
```

### Form State
```javascript
const updateFormState = (formId, isVisible) => {
    const form = document.getElementById(formId);
    if (isVisible) {
        form.classList.remove('collapse');
        form.classList.remove('animate-fade-in');
        void form.offsetWidth; // Force reflow
        form.classList.add('animate-fade-in');
    } else {
        form.classList.add('collapse');
    }
};
```

## Error Handling

### Error Display
```javascript
const displayError = (container, error) => {
    container.textContent = `Error: ${error.message}`;
    container.classList.add('text-error');
    setTimeout(() => {
        container.classList.remove('text-error');
    }, 5000);
};
```

### Try-Catch Pattern
```javascript
const safeExecute = async (action, errorHandler) => {
    try {
        return await action();
    } catch (error) {
        console.error('Operation failed:', error);
        errorHandler(error);
        throw error;
    }
};
```

## Loading States

### Button Loading State
```javascript
const setButtonLoading = (button, isLoading) => {
    const spinner = button.querySelector('.loading');
    const text = button.querySelector('.button-text');
    
    spinner.style.display = isLoading ? 'inline-block' : 'none';
    text.style.opacity = isLoading ? '0' : '1';
    button.disabled = isLoading;
};
```

### Section Loading State
```javascript
const setSectionLoading = (section, isLoading) => {
    const content = section.querySelector('.content');
    const loader = section.querySelector('.section-loader');
    
    content.style.opacity = isLoading ? '0.5' : '1';
    loader.style.display = isLoading ? 'block' : 'none';
};
```

## Event Handling

### Event Delegation
```javascript
const delegateEvent = (container, selector, eventType, handler) => {
    container.addEventListener(eventType, (event) => {
        const target = event.target.closest(selector);
        if (target) {
            handler(event, target);
        }
    });
};
```

### Form Events
```javascript
const initFormEvents = (formId, submitHandler) => {
    const form = document.getElementById(formId);
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        await withLoading(
            form.querySelector('.submit-button'),
            () => submitHandler(form)
        );
    });
};
```

## Build Process

### Development
```bash
# Start development server with hot reload
npm run dev

# Watch for changes
npm run watch
```

### Production Build
```bash
# Create optimized production build
npm run build

# Test production build
npm run serve
```

### CSS Processing
```bash
# Build CSS
npm run build:css

# Watch CSS changes
npm run watch:css
```

## Best Practices

1. **Code Organization**
   - Use consistent module pattern
   - Keep functions small and focused
   - Maintain clear separation of concerns
   - Document complex logic

2. **Error Handling**
   - Always use try-catch blocks
   - Provide meaningful error messages
   - Log errors appropriately
   - Handle edge cases

3. **Performance**
   - Minimize DOM operations
   - Use event delegation
   - Optimize animations
   - Cache DOM queries

4. **Maintainability**
   - Follow consistent naming conventions
   - Comment complex logic
   - Use TypeScript for large features
   - Keep code modular

5. **Testing**
   - Write unit tests for utilities
   - Test error scenarios
   - Verify loading states
   - Check responsive behavior

This guide serves as a reference for frontend development patterns and best practices. Follow these guidelines when adding new features or modifying existing functionality to maintain code quality and consistency.
