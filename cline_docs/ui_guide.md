# UI Component Guide

This guide documents the HTML structure and CSS patterns used in the Ancient Medical Texts Analysis App.

## Table of Contents
1. [Layout Structure](#layout-structure)
2. [Components](#components)
3. [Utility Classes](#utility-classes)
4. [Animations](#animations)
5. [Responsive Design](#responsive-design)
6. [Theme System](#theme-system)

## Layout Structure

### Base Layout
```html
<div class="container mx-auto p-4">
    <header class="text-center mb-8">
        <!-- Header content -->
    </header>
    <main class="max-w-4xl mx-auto">
        <!-- Main content -->
    </main>
</div>
```

### Section Structure
```html
<section id="section-name" class="mode-section">
    <div class="card bg-base-100 card-container">
        <div class="card-body">
            <h2 class="section-title">Section Title</h2>
            <!-- Section content -->
        </div>
    </div>
</section>
```

## Components

```html
<div class="tabs tabs-boxed justify-center bg-base-100 p-2 rounded-lg shadow-md">
    <button class="tab tab-lg tab-active gap-2" data-mode="section-name">
        <svg class="h-5 w-5"><!-- Icon --></svg>
        Tab Text
    </button>
</div>
```

### Action Buttons
```html
<div class="action-buttons">
    <button class="action-button" data-action="action-name">
        <svg class="h-5 w-5"><!-- Icon --></svg>
        Button Text
    </button>
</div>
```

### Form Controls
```html
<div class="form-section">
    <div class="input-group">
        <input type="text" 
               class="input input-bordered w-full focus:input-primary transition-colors duration-200" 
               placeholder="Placeholder text">
        
        <label class="checkbox-group">
            <input type="checkbox" class="checkbox checkbox-primary">
            <span class="label-text">Checkbox Label</span>
        </label>
    </div>
    
    <button class="submit-button">
        <span class="loading loading-spinner" style="display: none;"></span>
        <span class="button-text">Submit</span>
    </button>
</div>
```

### Citation Components

#### Citation Display
```html
<div class="citation-container">
    <div class="citation-header flex justify-between items-center">
        <div class="citation-source">
            <span class="font-semibold">{{author}}</span>
            <span class="text-gray-600">{{work}}</span>
        </div>
        <div class="citation-location text-sm">
            {{location}}
        </div>
    </div>
    
    <div class="citation-content mt-2">
        <div class="prev-sentence text-gray-500 text-sm">{{prevSentence}}</div>
        <div class="main-sentence my-2">{{sentence}}</div>
        <div class="next-sentence text-gray-500 text-sm">{{nextSentence}}</div>
    </div>
    
    <div class="citation-metadata mt-2 text-sm text-gray-600">
        <div class="line-numbers">Lines: {{lineNumbers}}</div>
        <div class="categories">{{categories}}</div>
    </div>
</div>
```

#### Paginated Results
```html
<div class="paginated-results">
    <div class="results-header flex justify-between items-center mb-4">
        <h3 class="font-bold">Results</h3>
        <div class="results-count text-sm">
            Showing {{start}}-{{end}} of {{total}}
        </div>
    </div>
    
    <div class="results-content space-y-4">
        <!-- Citation components -->
    </div>
    
    <div class="pagination-controls mt-4 flex justify-center gap-2">
        <button class="btn btn-sm" disabled="{{isFirstPage}}">
            Previous
        </button>
        
        <div class="page-numbers flex gap-1">
            <!-- Page number buttons -->
        </div>
        
        <button class="btn btn-sm" disabled="{{isLastPage}}">
            Next
        </button>
    </div>
</div>
```

#### Search Results
```html
<div class="search-results">
    <div class="search-info mb-4">
        <div class="search-summary">
            Found {{totalResults}} results for "{{query}}"
        </div>
        <div class="search-filters flex gap-2 text-sm">
            <span class="filter-tag">
                {{filterName}}: {{filterValue}}
            </span>
        </div>
    </div>
    
    <!-- Paginated results component -->
</div>
```

### Results Display
```html
<div class="results-section">
    <h3 class="font-bold mb-2">Results</h3>
    <div class="results-content"></div>
</div>
```

## Utility Classes

### Layout Classes
- `container`: Main container with auto margins
- `max-w-4xl`: Maximum width constraint
- `mx-auto`: Center horizontally
- `p-4`: Padding
- `space-y-4`: Vertical spacing between children

### Flexbox Classes
- `flex`: Display flex
- `flex-col`: Column direction
- `gap-2`: Gap between items
- `justify-center`: Center horizontally
- `items-center`: Center vertically

### Typography Classes
- `text-4xl`: Large text size
- `font-bold`: Bold text
- `text-primary`: Primary text color
- `text-center`: Center text

### Spacing Classes
- `mt-4`: Margin top
- `mb-6`: Margin bottom
- `p-2`: Padding
- `gap-2`: Gap between items

## New Utility Classes

### Citation Classes
- `citation-container`: Base container for citations
- `citation-header`: Header with source and location
- `citation-content`: Main content area
- `citation-metadata`: Additional metadata display

### Pagination Classes
- `paginated-results`: Container for paginated content
- `pagination-controls`: Navigation controls
- `page-numbers`: Page number display
- `results-count`: Results counter display

## Animations

### Fade In Animation
```css
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
    animation: fadeIn 0.3s ease-out forwards;
}
```

### Transition Classes
- `transition-all`: All properties
- `duration-200`: 200ms duration
- `ease-in-out`: Smooth easing
- `hover:scale-105`: Scale up on hover

## Responsive Design

### Breakpoints
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
### Mobile Adjustments
```css
@media (max-width: 640px) {
    .citation-header {
        @apply flex-col items-start gap-1;
    }
    
    .pagination-controls {
        @apply flex-wrap justify-center;
    }
    
    .page-numbers {
        @apply order-3 w-full justify-center mt-2;
    }
}
```

## Theme System

### Theme Configuration
```html
<html lang="en" data-theme="light">
```

### Custom Theme Classes
```css
[data-theme="light"] {
    /* Custom theme variables */
}
```

### Component Variants
- `btn-primary`: Primary button
- `input-primary`: Primary input
- `checkbox-primary`: Primary checkbox

## Best Practices

1. **HTML Structure**
   - Use semantic HTML elements
   - Maintain consistent nesting
   - Include proper ARIA attributes
   - Keep markup clean and readable

2. **CSS Organization**
   - Use Tailwind's layer system
   - Group related utilities
   - Follow mobile-first approach
   - Maintain consistent spacing

3. **Component Design**
   - Keep components modular
   - Use consistent naming
   - Follow DaisyUI patterns
   - Consider accessibility

4. **Responsive Design**
   - Test all breakpoints
   - Use fluid typography
   - Ensure touch targets
   - Maintain readability

5. **Performance**
   - Minimize custom CSS
   - Use efficient selectors
   - Optimize animations
   - Leverage Tailwind's JIT
   
6. **Citation Display**
   - Show context when available
   - Clear source attribution
   - Consistent formatting
   - Accessible structure

7. **Pagination**
   - Clear navigation controls
   - Current position indicator
   - Responsive layout
   - Loading states

## Example Usage

### Complete Search Results Section
```html
<section class="search-section animate-fade-in">
    <div class="card bg-base-100 card-container">
        <div class="card-body">
            <h2 class="section-title">Search Results</h2>
            
            <div class="search-results">
                <div class="search-info mb-4">
                    <div class="search-summary">
                        Found 150 results for "example"
                    </div>
                    <div class="search-filters flex gap-2 text-sm">
                        <span class="filter-tag">
                            Category: Medical
                        </span>
                    </div>
                </div>
                
                <div class="paginated-results">
                    <div class="results-content space-y-4">
                        <div class="citation-container">
                            <div class="citation-header">
                                <div class="citation-source">
                                    <span class="font-semibold">Hippocrates</span>
                                    <span class="text-gray-600">De Medicina</span>
                                </div>
                                <div class="citation-location">
                                    Book 1, Chapter 2
                                </div>
                            </div>
                            
                            <div class="citation-content">
                                <div class="prev-sentence">Previous context...</div>
                                <div class="main-sentence">Main citation text...</div>
                                <div class="next-sentence">Following context...</div>
                            </div>
                        </div>
                        <!-- More citations -->
                    </div>
                    
                    <div class="pagination-controls">
                        <button class="btn btn-sm">Previous</button>
                        <div class="page-numbers">
                            <!-- Page numbers -->
                        </div>
                        <button class="btn btn-sm">Next</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>
```

This guide serves as a reference for maintaining consistent UI patterns across the application. Follow these patterns when adding new components or modifying existing ones to ensure a cohesive user experience.
