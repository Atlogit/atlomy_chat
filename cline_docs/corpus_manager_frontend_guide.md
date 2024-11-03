# Corpus Manager Frontend Guide

## Overview

The Corpus Manager frontend provides a user-friendly interface for interacting with the ancient medical texts corpus. It consists of three main views:
- List Texts: Display and manage the corpus texts
- Search: Search through the texts
- View Text: Detailed view of a specific text

## Components Structure

### CorpusSection
The main container component that manages:
- View state (list/search/view)
- Text data persistence
- Navigation between views

### ListTexts
Displays the corpus texts with features:
- Initial load button for corpus
- Loading progress animation with percentage
- Text count display
- Persistent text state across view changes
- Individual text cards with metadata

### SearchForm
Provides search functionality across the corpus.

### TextDisplay
Shows detailed view of a selected text.

## Features

### Text Loading and State Management

The corpus texts are loaded once and persist in memory:
- Initial state shows "Load Corpus" button
- Loading process shows:
  - Progress bar animation (0-100%)
  - Loading percentage
  - Text count as they're loaded
- Loaded texts remain in memory when switching views
- Returning to List Texts view shows previously loaded texts

### Text Display

Each text card shows:
- Work name
- Author
- Reference code
- Citation information
- Text preview
- Metadata badges
- Structure information
- Division counts

### Navigation

- Tabs for switching between views
- Breadcrumb navigation showing current location
- "View Text" button on each text card

## Usage Guide

### Loading Texts

1. Navigate to the Corpus Manager
2. If texts haven't been loaded:
   - Click "Load Corpus" button
   - Watch loading progress
   - See texts appear as they're loaded

### Viewing Texts

1. After texts are loaded, browse through the list
2. Each text shows:
   - Basic information (title, author)
   - Preview of content
   - Metadata and structure
3. Click "View Text" on any card to see full details

### Switching Views

1. Use the tabs to switch between:
   - List Texts
   - Search
   - View Text (when a text is selected)
2. Previously loaded texts remain available when returning to List Texts view

## State Persistence

The Corpus Manager maintains state across view changes:
- Texts remain loaded when switching views
- No need to reload when returning to List Texts
- Loading state persists if loading when switching views

## Error Handling

- Loading errors are displayed with clear messages
- Network issues show appropriate error states
- Failed loads can be retried

## Best Practices

1. Initial Load:
   - Load texts when needed
   - Wait for loading to complete before switching views

2. Navigation:
   - Use tabs for main view switching
   - Use breadcrumbs for navigation context
   - Return to list view using Home link

3. Text Management:
   - View text details through "View Text" button
   - Use search when looking for specific content
   - Monitor text count for corpus size

## Performance Considerations

- Texts are loaded once and cached in memory
- Loading state shows progress to indicate activity
- Large corpora show loading progress with text count
- State persistence prevents unnecessary reloading

## Integration with Backend

The frontend interfaces with the backend through:
- `/api/v1/corpus/list` for loading texts
- `/api/v1/corpus/text/{id}` for individual texts
- `/api/v1/corpus/search` for text search

## Future Improvements

Planned enhancements:
- Text filtering capabilities
- Advanced search options
- Bulk text operations
- Export functionality
