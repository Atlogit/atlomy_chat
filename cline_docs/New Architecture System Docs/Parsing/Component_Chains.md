# Component Chains and Relationships

## Inheritance Chain

```
CorpusBase
├── Uses SharedComponents for common resources
└── Inherited by:
    └── CorpusCitation
        └── Citation parsing and structure handling
            └── CorpusText
                └── Text processing and line handling
                    └── CorpusNLP
                        └── NLP processing and token mapping
                            └── CorpusDB
                                └── Database operations
                                    └── CorpusProcessor
                                        └── Overall coordination
```

## Singleton Components Chain

```
SharedParsers (singleton)
├── Lazy loads components
├── SentenceUtils (singleton)
│   └── Line normalization and joining
└── CitationParser (singleton)
    └── Citation parsing and structure handling
```

## Processing Flow Chain

```
Input Text
└── CorpusProcessor
    ├── Get work from database
    └── For each division:
        ├── CorpusText
        │   ├── Extract citations
        │   ├── Parse line numbers
        │   └── Create parser lines
        ├── SentenceParser
        │   ├── Group lines into sentences
        │   └── Maintain citation context
        ├── CorpusNLP
        │   ├── Process through spaCy
        │   ├── Extract tokens
        │   └── Map back to lines
        └── CorpusDB
            ├── Create sentence records
            ├── Update line analysis
            └── Commit changes
```

## Data Flow Chain

```
Raw Text
└── Citation Extraction
    ├── Author/Work IDs
    ├── Line Numbers
    └── Structure Info
        └── Sentence Formation
            ├── Line Grouping
            ├── Citation Context
            └── Content Normalization
                └── NLP Processing
                    ├── Token Extraction
                    ├── POS Tagging
                    └── Dependencies
                        └── Database Storage
                            ├── Sentence Records
                            ├── Line Analysis
                            └── Token Mapping
```

## Component Dependencies

```
SharedComponents
├── Provides
│   ├── SentenceParser
│   ├── CitationParser
│   └── NLPPipeline
└── Used by
    ├── CorpusBase
    │   └── Inherits all shared components
    └── All derived classes
        └── Access through inheritance

SentenceParser
├── Depends on
│   ├── SentenceUtils
│   └── CitationParser
└── Used by
    └── CorpusText
        └── For sentence formation

CitationParser
├── Independent component
└── Used by
    ├── SentenceParser
    │   └── For citation context
    └── CorpusCitation
        └── For structure handling

NLPPipeline
├── Independent component
└── Used by
    └── CorpusNLP
        └── For token processing
```

## State Management Chain

```
SharedParsers
├── Manages component lifecycles
└── Reset chain
    ├── CitationParser
    │   └── Clear caches
    ├── SentenceUtils
    │   └── Reset state
    └── NLPPipeline
        └── Clear pipeline

CorpusProcessor
├── Manages processing state
└── Reset chain
    ├── CorpusDB
    │   └── Clear session state
    ├── CorpusNLP
    │   └── Reset NLP state
    ├── CorpusText
    │   └── Clear processed lines
    └── CorpusCitation
        └── Clear structure cache
```

## Transaction Chain

```
CorpusProcessor
└── Work-level transaction
    ├── Begin transaction
    │   └── Process divisions
    │       ├── Success
    │       │   └── Commit changes
    │       └── Failure
    │           └── Rollback
    └── Error handling
        └── Continue with next work
```

## Progress Tracking Chain

```
CorpusProcessor
└── Work progress
    ├── Total works count
    └── For each work
        ├── Division progress
        │   ├── Lines processed
        │   └── Sentences formed
        └── NLP progress
            ├── Tokens extracted
            └── Analysis complete
