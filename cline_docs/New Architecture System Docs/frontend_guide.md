This guide documents the Next.js patterns, TypeScript integration, and development workflow for the Ancient Medical Texts Analysis App.

## Table of Contents
1. [Environment Setup](#environment-setup)
2. [Project Structure](#project-structure)
3. [Component Architecture](#component-architecture)
4. [Next.js Configuration](#nextjs-configuration)
5. [API Integration](#api-integration)
6. [State Management](#state-management)
7. [Error Handling](#error-handling)
8. [Testing](#testing)
9. [Performance Optimization](#performance-optimization)
10. [Accessibility](#accessibility)

## Environment Setup

### Conda Environment
```bash
# Activate the environment
conda activate atlomy_chat

# If not created, run setup script
bash setup_conda_env.sh
```

### Node.js Setup
- Node.js LTS (v20) is installed within the conda environment
- Verify installation:
```bash
node --version
```

## Project Structure

```
next-app/
├── src/
│   ├── app/
│   │   ├── layout.tsx      # Root layout
│   │   ├── page.tsx        # Home page with tab management
│   │   └── globals.css     # Global styles
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   └── Navigation.tsx
│   │   ├── sections/
│   │   │   ├── llm/
│   │   │   │   └── LLMSection.tsx
│   │   │   ├── lexical/
│   │   │   │   ├── LexicalSection.tsx
│   │   │   │   ├── CreateForm.tsx
│   │   │   │   ├── BatchCreateForm.tsx
│   │   │   │   ├── GetForm.tsx
│   │   │   │   ├── UpdateForm.tsx
│   │   │   │   ├── BatchUpdateForm.tsx
│   │   │   │   └── DeleteForm.tsx
│   │   │   └── corpus/
│   │   │       ├── CorpusSection.tsx
│   │   │       ├── ListTexts.tsx
│   │   │       ├── SearchForm.tsx
│   │   │       └── TextDisplay.tsx
│   │   └── ui/
│   │       ├── Button.tsx
│   │       ├── ResultsDisplay.tsx
│   │       └── ProgressDisplay.tsx
│   ├── hooks/
│   │   ├── useApi.ts
│   │   ├── useLoading.ts
│   │   └── useLoadingWithProgress.ts
│   └── utils/
│       └── api/
│           ├── endpoints.ts
│           ├── fetch.ts
│           └── types/
```

## Component Architecture

### Core Components

#### Button Component
```typescript
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  isLoading?: boolean
  variant?: 'primary' | 'error' | 'outline'
  className?: string
}

export function Button({
  children,
  isLoading = false,
  variant = 'primary',
  className = '',
  ...props
}: ButtonProps) {
  const baseClasses = 'btn'
  const variantClasses = {
    primary: 'btn-primary',
    error: 'btn-error',
    outline: 'btn-outline',
  }

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      disabled={isLoading || props.disabled}
      {...props}
    >
      {isLoading && (
        <span className="loading loading-spinner loading-xs" role="status" aria-label="Loading"></span>
      )}
      <span className={`button-text ${isLoading ? 'opacity-0' : 'opacity-100'}`}>
        {children}
      </span>
    </button>
  )
}
```

#### ResultsDisplay Component
```typescript
interface ResultsDisplayProps {
  title?: string
  content: string | null | LexicalValue
  error?: string | null
  className?: string
  isHtml?: boolean
  onShowCitation?: (citation: Citation) => void
}

export function ResultsDisplay({
  title = 'Results',
  content,
  error,
  className = '',
  isHtml = false,
  onShowCitation,
}: ResultsDisplayProps) {
  // Implementation details
}
```

### Section Components

#### LLM Section
```typescript
export function LLMSection() {
  const [term, setTerm] = useState('')
  const [contexts, setContexts] = useState<Context[]>([])
  const [response, setResponse] = useState('')
  const [tokenCount, setTokenCount] = useState<TokenCountResponse | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const { data, error, isLoading, execute } = useApi<AnalysisResponse>()

  // Implementation details
}
```

## Next.js Configuration

### API Proxying
```javascript
// next.config.js
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
}
```

### Error Boundary Implementation
```typescript
class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_: Error): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}
```

## API Integration

### useApi Hook Implementation
```typescript
const DEFAULT_TIMEOUT = 300000; // 5 minutes
const MAX_RETRIES = 0;
const INITIAL_BACKOFF = 1000; // 1 second

export function useApi<T>(): ApiHookResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [progress, setProgress] = useState<{ current: number; total: number }>({ current: 0, total: 0 });

  const execute = useCallback(async (
    endpoint: string, 
    options?: RequestInit, 
    timeout: number = DEFAULT_TIMEOUT
  ): Promise<T | null> => {
    setIsLoading(true);
    setError(null);
    setData(null); // Clear previous data when starting new request
    setProgress({ current: 0, total: 0 });

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const result = await fetchApi<T>(endpoint, {
        ...options,
        signal: controller.signal
      }, (stage: string) => {
        // Parse progress from stage string if available
        const match = stage.match(/(\d+)\/(\d+)/);
        if (match) {
          setProgress({ current: parseInt(match[1]), total: parseInt(match[2]) });
        }
      });

      if (result !== null) {
        setData(result);
      }
      
      return result;
    } catch (err) {
      handleApiError(err);
      return null;
    } finally {
      clearTimeout(timeoutId);
      setIsLoading(false);
    }
  }, []);

  return { data, error, isLoading, progress, execute };
}
```

### Hook Usage Patterns

#### Basic Usage
```typescript
function MyComponent() {
  const { data, error, isLoading, execute } = useApi<MyDataType>();

  useEffect(() => {
    execute('/api/endpoint');
  }, [execute]);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay error={error} />;
  if (!data) return null;

  return <div>{/* Render data */}</div>;
}
```

#### With Progress Tracking
```typescript
function BatchOperation() {
  const { execute, progress, isLoading } = useApi<BatchResult>();

  const handleBatch = async () => {
    await execute('/api/batch', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  };

  return (
    <div>
      <Button onClick={handleBatch} isLoading={isLoading}>
        Process Batch
      </Button>
      {isLoading && (
        <ProgressDisplay 
          current={progress.current} 
          total={progress.total} 
        />
      )}
    </div>
  );
}
```

#### With Custom Timeout
```typescript
function LongRunningOperation() {
  const { execute } = useApi<Result>();

  const handleOperation = async () => {
    // Set 10-minute timeout
    await execute('/api/long-operation', {}, 600000);
  };

  return <Button onClick={handleOperation}>Start Operation</Button>;
}
```

### Error Handling

#### Error Types
```typescript
interface ApiError {
  message: string;
  status?: number;
  detail?: string;
}

// Error handling in components
function ErrorAwareComponent() {
  const { error, execute } = useApi<Data>();

  const handleError = useCallback(() => {
    if (error?.status === 404) {
      // Handle not found
    } else if (error?.status === 403) {
      // Handle forbidden
    } else {
      // Handle general error
    }
  }, [error]);

  useEffect(() => {
    if (error) handleError();
  }, [error, handleError]);

  return <div>{/* Component content */}</div>;
}
```

### Progress Tracking

#### Progress State Management
```typescript
interface ProgressState {
  current: number;
  total: number;
}

// In components
function ProgressAwareComponent() {
  const { progress, isLoading } = useApi<Data>();

  return (
    <div>
      {isLoading && progress.total > 0 && (
        <div>
          <ProgressBar 
            value={(progress.current / progress.total) * 100} 
          />
          <div>
            Processing {progress.current} of {progress.total}
          </div>
        </div>
      )}
    </div>
  );
}
```

## Testing

### Jest Configuration
```javascript
// jest.config.js
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    // Handle module aliases
    '^components/(.*)$': '<rootDir>/src/components/$1',
    '^utils/(.*)$': '<rootDir>/src/utils/$1',
    '^hooks/(.*)$': '<rootDir>/src/hooks/$1'
  },
  testMatch: ['**/__tests__/**/*.test.[jt]s?(x)'],
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}'
  ],
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', { presets: ['next/babel'] }],
  },
}
```

### Test Setup
```javascript
// jest.setup.js
import '@testing-library/jest-dom'
```

### Component Testing
```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../components/ui/Button'

describe('Button', () => {
  it('renders correctly', () => {
    render(<Button onClick={() => {}}>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    render(<Button isLoading onClick={() => {}}>Click me</Button>)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('handles click events', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    fireEvent.click(screen.getByText('Click me'))
    expect(handleClick).toHaveBeenCalled()
  })
})
```

### Hook Testing
```typescript
import { renderHook, act } from '@testing-library/react'
import { useApi } from '../hooks/useApi'

describe('useApi', () => {
  it('handles successful requests', async () => {
    const { result } = renderHook(() => useApi<TestData>())
    
    await act(async () => {
      await result.current.execute('/api/test')
    })
    
    expect(result.current.data).toBeDefined()
    expect(result.current.error).toBeNull()
  })

  it('handles errors', async () => {
    const { result } = renderHook(() => useApi<TestData>())
    
    await act(async () => {
      await result.current.execute('/api/error')
    })
    
    expect(result.current.error).toBeDefined()
    expect(result.current.data).toBeNull()
  })
})
```

### API Testing
```typescript
import { fetchApi } from '../utils/api/fetch'

describe('fetchApi', () => {
  it('handles successful responses', async () => {
    const mockResponse = { data: 'test' }
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      text: () => Promise.resolve(JSON.stringify(mockResponse))
    })

    const result = await fetchApi('/api/test')
    expect(result).toEqual(mockResponse)
  })

  it('handles error responses', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 404,
      text: () => Promise.resolve(JSON.stringify({ error: 'Not found' }))
    })

    await expect(fetchApi('/api/test')).rejects.toThrow()
  })
})
```

### Running Tests
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage
```

### Test Organization

1. **Unit Tests**
   - Place test files next to the components they test
   - Use `.test.tsx` extension for component tests
   - Use `.test.ts` for utility and hook tests

2. **Integration Tests**
   - Place in `__tests__` directory
   - Test component interactions
   - Test API integration
   - Test routing and navigation

3. **Coverage Requirements**
   - Maintain high coverage for utilities and hooks
   - Test all error states and edge cases
   - Verify component interactions
   - Test accessibility features

## Performance Optimization

### Code Splitting
```typescript
// Use dynamic imports for large components
const LexicalSection = dynamic(() => import('../components/sections/lexical/LexicalSection'), {
  loading: () => <LoadingSpinner />,
  ssr: false
})
```

### Image Optimization
```typescript
import Image from 'next/image'

function OptimizedImage() {
  return (
    <Image
      src="/path/to/image.jpg"
      alt="Description"
      width={800}
      height={600}
      placeholder="blur"
      priority={true}
    />
  )
}
```

### Memoization
```typescript
// Memoize expensive components
const MemoizedComponent = memo(({ data }: Props) => {
  return <div>{/* Complex rendering */}</div>
}, (prevProps, nextProps) => {
  // Custom comparison function
  return prevProps.data.id === nextProps.data.id
})

// Memoize expensive calculations
const memoizedValue = useMemo(() => {
  return expensiveCalculation(data)
}, [data])

// Memoize callbacks
const memoizedCallback = useCallback(() => {
  handleData(data)
}, [data])
```

### State Management Optimization
```typescript
// Use state batching
function BatchedUpdates() {
  const [state, setState] = useState({ count: 0, total: 0 })
  
  const updateBoth = () => {
    setState(prev => ({
      ...prev,
      count: prev.count + 1,
      total: prev.total + 1
    }))
  }
}

// Split state for better performance
function SplitState() {
  const [count, setCount] = useState(0)
  const [total, setTotal] = useState(0)
  
  // Now updates to count won't cause total to re-render
}
```

## Accessibility

### ARIA Attributes
```typescript
// Button with ARIA support
function AccessibleButton({ isLoading, children }: Props) {
  return (
    <button
      aria-busy={isLoading}
      aria-disabled={isLoading}
      aria-label="Submit form"
      role="button"
    >
      {children}
    </button>
  )
}

// Form with ARIA labels
function AccessibleForm() {
  return (
    <form aria-label="Create lexical value">
      <div role="group" aria-labelledby="form-heading">
        <h2 id="form-heading">Enter Details</h2>
        <label htmlFor="term">Term</label>
        <input
          id="term"
          type="text"
          aria-required="true"
          aria-invalid={hasError}
          aria-describedby="term-error"
        />
        {hasError && (
          <div id="term-error" role="alert">
            Please enter a valid term
          </div>
        )}
      </div>
    </form>
  )
}
```

### Keyboard Navigation
```typescript
function KeyboardNavigation() {
  const handleKeyPress = (event: KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      // Handle activation
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onKeyPress={handleKeyPress}
      onClick={handleClick}
    >
      Clickable Element
    </div>
  )
}
```

### Focus Management
```typescript
function FocusManagement() {
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    // Focus input on mount
    inputRef.current?.focus()
  }, [])

  const handleSubmit = () => {
    // Move focus after action
    submitButtonRef.current?.focus()
  }

  return (
    <div>
      <input ref={inputRef} aria-label="Search" />
      <button onClick={handleSubmit}>Submit</button>
    </div>
  )
}
```

### Screen Reader Support
```typescript
function ScreenReaderSupport() {
  return (
    <div>
      {/* Hide visual elements from screen readers */}
      <div aria-hidden="true">
        <Icon name="decorative" />
      </div>

      {/* Provide screen reader only content */}
      <span className="sr-only">
        Additional context for screen readers
      </span>

      {/* Live regions for dynamic content */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        {statusMessage}
      </div>
    </div>
  )
}
```

### Color Contrast
```typescript
// Use CSS custom properties for theming
:root {
  --primary-color: #007bff;
  --primary-contrast: #ffffff;
  --error-color: #dc3545;
  --error-contrast: #ffffff;
}

// Apply in components
function ContrastAwareButton({ variant = 'primary' }: Props) {
  return (
    <button
      className={`btn btn-${variant}`}
      style={{
        backgroundColor: `var(--${variant}-color)`,
        color: `var(--${variant}-contrast)`
      }}
    >
      Click Me
    </button>
  )
}
```

## Development Workflow

### Starting the Application
1. Start the FastAPI backend:
```bash
python app/run_server.py
```

2. Start the Next.js development server:
```bash
cd next-app
npm run dev
```

### Building for Production
```bash
# Create production build
npm run build

# Start production server
npm run start
```

## Best Practices

1. **Component Development**
   - Use TypeScript interfaces for props
   - Implement proper loading states
   - Handle errors gracefully
   - Use DaisyUI components consistently

2. **State Management**
   - Keep state close to where it's used
   - Use proper TypeScript types
   - Implement loading indicators
   - Handle async operations properly

3. **Error Handling**
   - Use ErrorBoundary for component errors
   - Display user-friendly error messages
   - Log errors appropriately
   - Handle API errors consistently

4. **Performance**
   - Implement proper loading states
   - Use Next.js features appropriately
   - Optimize re-renders
   - Handle large datasets efficiently

5. **Code Organization**
   - Follow consistent file structure
   - Use proper naming conventions
   - Document complex logic
   - Keep components focused
This guide serves as a reference for frontend development patterns and best practices in the Next.js application. Follow these guidelines when adding new features or modifying existing functionality to maintain code quality and consistency.