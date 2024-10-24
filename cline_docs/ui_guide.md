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

### Navigation Tabs
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
    .action-buttons {
        @apply grid grid-cols-2 gap-2;
    }
    
    .action-button {
        @apply w-full;
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

## Example Usage

### Complete Form Section
```html
<section class="mode-section animate-fade-in">
    <div class="card bg-base-100 card-container">
        <div class="card-body">
            <h2 class="section-title">Form Title</h2>
            
            <div class="form-section">
                <div class="input-group">
                    <input type="text" 
                           class="input input-bordered w-full focus:input-primary" 
                           placeholder="Enter text">
                           
                    <label class="checkbox-group">
                        <input type="checkbox" class="checkbox checkbox-primary">
                        <span class="label-text">Option</span>
                    </label>
                </div>
                
                <button class="submit-button">
                    <span class="loading loading-spinner" style="display: none;"></span>
                    <span class="button-text">Submit</span>
                </button>
            </div>
            
            <div class="results-section">
                <h3 class="font-bold mb-2">Results</h3>
                <div class="results-content"></div>
            </div>
        </div>
    </div>
</section>
```

This guide serves as a reference for maintaining consistent UI patterns across the application. Follow these patterns when adding new components or modifying existing ones to ensure a cohesive user experience.
