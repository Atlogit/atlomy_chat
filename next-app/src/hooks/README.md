# Hooks

This directory contains custom React hooks used throughout the Ancient Medical Texts Analysis App. These hooks encapsulate reusable stateful logic that can be shared across different components.

## Available Hooks

### useLoading

`useLoading` is a custom hook that manages loading states and error handling for asynchronous operations.

Usage:
```javascript
const { isLoading, error, execute } = useLoading();

// Use the execute function to wrap your async operations
const handleSubmit = async () => {
  const result = await execute(asyncOperation());
  // Handle the result
};
```

Properties:
- `isLoading`: A boolean indicating whether an operation is in progress.
- `error`: An error object if the operation failed, null otherwise.
- `execute`: A function that wraps an async operation, managing its loading state and error handling.

### [Add other hooks here as they are created]

Each hook is designed to solve a specific problem or encapsulate a particular behavior. They help in keeping the components clean and promote code reuse.

For more detailed information about each hook, please refer to the inline documentation within each hook file.
