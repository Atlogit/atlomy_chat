# Components

This directory contains all the React components used in the Ancient Medical Texts Analysis App. The components are organized into the following categories:

## Layout

Components that define the overall structure of the application.

- `Header`: The main header component of the application.
- `Navigation`: The navigation component for switching between different sections of the app.

## Sections

Components that represent major sections of the application.

### LLM Section

- `LLMSection`: The main component for the LLM (Language Model) section.

### Lexical Section

- `LexicalSection`: The main component for managing lexical values.
- `CreateForm`: Form for creating new lexical entries.
- `BatchCreateForm`: Form for batch creation of lexical entries.
- `GetForm`: Form for retrieving lexical entries.
- `UpdateForm`: Form for updating existing lexical entries.
- `BatchUpdateForm`: Form for batch updating of lexical entries.
- `DeleteForm`: Form for deleting lexical entries.

### Corpus Section

- `CorpusSection`: The main component for managing the corpus of texts.
- `ListTexts`: Component for displaying a list of texts in the corpus.
- `SearchForm`: Form for searching within the corpus.
- `TextDisplay`: Component for displaying individual texts.

## UI

Reusable UI components used throughout the application.

- `Button`: A customizable button component.
- `ResultsDisplay`: Component for displaying results from various operations.
- `ProgressDisplay`: Component for showing progress during batch operations.

Each component is designed to be modular and reusable. They are implemented using functional components and hooks for state management and side effects.

For more detailed information about each component, please refer to the inline documentation within each component file.
