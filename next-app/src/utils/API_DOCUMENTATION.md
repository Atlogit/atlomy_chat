# API Documentation

## Introduction

This document provides information about the API endpoints used in the Ancient Medical Texts Analysis App. The API is organized into three main sections: LLM (Language Model), Lexical, and Corpus.

## Base URL

The base URL for all API endpoints is: `http://localhost:8000`

## Authentication

Currently, there is no authentication required for these endpoints.

## Error Handling

All endpoints may return error responses with the following structure:

```json
{
  "message": "Error message describing the issue",
  "status": 400 // HTTP status code
}
```

## Endpoints

### LLM

#### Query LLM

- **URL**: `/api/llm/query`
- **Method**: POST
- **Description**: Send a query to the Language Model for processing.
- **Request Body**:
  ```json
  {
    "query": "Your question or prompt here"
  }
  ```
- **Response**: The response format may vary depending on the LLM's output.

### Lexical

#### Create Lexical Value

- **URL**: `/api/lexical/create`
- **Method**: POST
- **Description**: Create a new lexical value or propose an update if the lemma already exists.
- **Request Body**:
  ```json
  {
    "lemma": "word",
    "translation": "translation of the word",
    "searchLemma": false // optional, default is false
  }
  ```
- **Response**: 
  - If the lemma doesn't exist:
    ```json
    {
      "success": true,
      "message": "Lexical value created successfully",
      "entry": {
        "lemma": "word",
        "translation": "translation of the word",
        // ... other fields
      },
      "action": "create"
    }
    ```
  - If the lemma already exists:
    ```json
    {
      "success": false,
      "message": "Lexical value already exists",
      "entry": {
        "lemma": "word",
        "translation": "existing translation",
        // ... other fields
      },
      "action": "update"
    }
    ```

#### Batch Create Lexical Values

- **URL**: `/api/lexical/batch-create`
- **Method**: POST
- **Description**: Create multiple lexical values in a single request.
- **Request Body**:
  ```json
  {
    "words": ["word1", "word2", "word3"],
    "searchLemma": true // optional, default is false
  }
  ```
- **Response**: Returns an array of created lexical values.

#### Get Lexical Value

- **URL**: `/api/lexical/get/{lemma}`
- **Method**: GET
- **Description**: Retrieve a lexical value by its lemma.
- **Response**: Returns the requested lexical value.

#### List Lexical Values

- **URL**: `/api/lexical/list`
- **Method**: GET
- **Description**: Retrieve a list of all lexical values.
- **Response**: Returns an array of lexical values.

#### Update Lexical Value

- **URL**: `/api/lexical/update`
- **Method**: PUT
- **Description**: Update an existing lexical value.
- **Request Body**:
  ```json
  {
    "lemma": "word",
    "translation": "updated translation of the word",
    // ... other fields that can be updated
  }
  ```
- **Response**: Returns the updated lexical value.

#### Batch Update Lexical Values

- **URL**: `/api/lexical/batch-update`
- **Method**: PUT
- **Description**: Update multiple lexical values in a single request.
- **Request Body**:
  ```json
  {
    "success": true,
    "message": "Lexical value updated successfully",
    "entry": {
      "lemma": "word",
      "translation": "updated translation of the word",
      // ... other updated fields
    }
  }
  ```
- **Response**: Returns an array of updated lexical values.

#### Delete Lexical Value

- **URL**: `/api/lexical/delete/{lemma}`
- **Method**: DELETE
- **Description**: Delete a lexical value by its lemma.
- **Response**: Returns a confirmation of deletion.

### Corpus

#### List Texts

- **URL**: `/api/corpus/list`
- **Method**: GET
- **Description**: Retrieve a list of all texts in the corpus.
- **Response**: The response can be in one of the following formats:
  1. An array of text metadata:
     ```json
     [
       {
         "id": "text1",
         "title": "Text 1 Title",
         "author": "Author Name",
         "language": "Greek",
         "description": "Description of Text 1"
       },
       // ... more text objects
     ]
     ```
  2. An object with a 'texts' property containing an array of text metadata:
     ```json
     {
       "texts": [
         {
           "id": "text1",
           "title": "Text 1 Title",
           "author": "Author Name",
           "language": "Greek",
           "description": "Description of Text 1"
         },
         // ... more text objects
       ]
     }
     ```
  3. An empty object ({}), which indicates no texts are available in the corpus.

- **Note**: Clients should be prepared to handle all three response formats. An empty array or object indicates that no texts are available in the corpus.

[... Rest of the content unchanged ...]

#### Search Texts

- **URL**: `/api/corpus/search`
- **Method**: POST
- **Description**: Search for texts in the corpus.
- **Request Body**:
  ```json
  {
    "query": "search term",
    "searchLemma": true // optional, default is false
  }
  ```
- **Response**: Returns an array of matching texts.

#### Get All Texts

- **URL**: `/api/corpus/all`
- **Method**: GET
- **Description**: Retrieve the full content of all texts in the corpus.
- **Response**: Returns an array of full text content for all texts in the corpus.

## Note

This API documentation reflects the current implementation of the lexical value creation and update process. The create endpoint now checks for existing lemmas and proposes updates when necessary. The update endpoint allows for modifying multiple fields of a lexical value. Always refer to the most up-to-date backend implementation for the exact behavior of each endpoint.
