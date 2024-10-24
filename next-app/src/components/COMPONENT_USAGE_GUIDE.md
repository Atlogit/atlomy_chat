# Component Usage Guide

This guide provides information on how to use the various components in the Ancient Medical Texts Analysis App. Each component is described with its purpose, import statement, props, and example usage.

## Table of Contents

1. [UI Components](#ui-components)
   - [Button](#button)
   - [ResultsDisplay](#resultsdisplay)
   - [ProgressDisplay](#progressdisplay)
2. [Layout Components](#layout-components)
   - [Header](#header)
   - [Navigation](#navigation)
3. [Section Components](#section-components)
   - [LLMSection](#llmsection)
   - [LexicalSection](#lexicalsection)
   - [CorpusSection](#corpussection)

## UI Components

### Button

A reusable button component with loading state support.

**Import:**
```javascript
import { Button } from '../components/ui/Button';
```

**Props:**
- `onClick`: Function to be called when the button is clicked
- `isLoading`: Boolean indicating if the button is in a loading state
- `disabled`: Boolean indicating if the button is disabled
- `children`: React node to be rendered inside the button
- `className`: Additional CSS classes to apply to the button

**Example Usage:**
```jsx
<Button
  onClick={handleSubmit}
  isLoading={isLoading}
  disabled={!formIsValid}
  className="mt-4"
>
  Submit
</Button>
```

### ResultsDisplay

A component to display API responses or errors.

**Import:**
```javascript
import { ResultsDisplay } from '../components/ui/ResultsDisplay';
```

**Props:**
- `title`: String for the title of the results
- `content`: String or null for the content to display
- `error`: String or null for any error message

**Example Usage:**
```jsx
<ResultsDisplay
  title="API Response"
  content={apiData ? JSON.stringify(apiData, null, 2) : null}
  error={apiError}
/>
```

### ProgressDisplay

A component to show progress for batch operations.

**Import:**
```javascript
import { ProgressDisplay } from '../components/ui/ResultsDisplay';
```

**Props:**
- `current`: Number representing the current progress
- `total`: Number representing the total items to process

**Example Usage:**
```jsx
<ProgressDisplay
  current={processedItems}
  total={totalItems}
/>
```

## Layout Components

### Header

The main header component for the application.

**Import:**
```javascript
import { Header } from '../components/layout/Header';
```

**Props:**
- `activeTab`: String representing the currently active tab
- `onTabChange`: Function to be called when a tab is changed

**Example Usage:**
```jsx
<Header
  activeTab={currentTab}
  onTabChange={handleTabChange}
/>
```

### Navigation

The navigation component for switching between different sections of the app.

**Import:**
```javascript
import { Navigation } from '../components/layout/Navigation';
```

**Props:**
- `activeTab`: String representing the currently active tab
- `onTabChange`: Function to be called when a tab is changed

**Example Usage:**
```jsx
<Navigation
  activeTab={currentTab}
  onTabChange={handleTabChange}
/>
```

## Section Components

### LLMSection

The main component for the LLM (Language Model) Assistant section.

**Import:**
```javascript
import { LLMSection } from '../components/sections/llm/LLMSection';
```

**Props:** None

**Example Usage:**
```jsx
<LLMSection />
```

### LexicalSection

The main component for managing lexical values.

**Import:**
```javascript
import { LexicalSection } from '../components/sections/lexical/LexicalSection';
```

**Props:** None

**Example Usage:**
```jsx
<LexicalSection />
```

### CorpusSection

The main component for corpus management.

**Import:**
```javascript
import { CorpusSection } from '../components/sections/corpus/CorpusSection';
```

**Props:** None

**Example Usage:**
```jsx
<CorpusSection />
```

This guide provides a basic overview of the main components in the application. For more detailed information about each component, including internal state management and specific behaviors, please refer to the individual component files and their associated tests.
