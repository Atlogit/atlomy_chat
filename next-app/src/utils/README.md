# Utils

This directory contains utility functions and helper modules used throughout the Ancient Medical Texts Analysis App. These utilities provide common functionality that can be shared across different components and modules.

## Available Utilities

### api.ts

This module contains functions and configurations for making API calls to the backend server.

Key exports:
- `fetchApi`: A function for making HTTP requests to the API.
- `API`: An object containing API endpoint configurations.

Usage:
```javascript
import { fetchApi, API } from 'utils/api';

// Example API call
const result = await fetchApi(API.llm.query, {
  method: 'POST',
  body: JSON.stringify({ query: 'Your query here' }),
});
```

### [Add other utility modules here as they are created]

Each utility module is designed to provide specific functionality that can be used across the application. They help in keeping the code DRY (Don't Repeat Yourself) and promote consistency in how common tasks are performed.

For more detailed information about each utility module, please refer to the inline documentation within each file.
