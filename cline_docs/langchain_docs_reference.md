# LangChain Documentation Reference

## Introduction

LangChain is a comprehensive framework for developing applications powered by large language models (LLMs). It simplifies the entire LLM application lifecycle, from development and productionization to deployment.

LangChain's core functionalities include:
- **Development**: Build applications using open-source building blocks, components, and third-party integrations.
- **Productionization**: Utilize LangSmith to inspect, monitor, and evaluate chains for continuous optimization and confident deployment.
- **Deployment**: Transform LangGraph applications into production-ready APIs and Assistants with LangGraph Cloud.

### Key Components:
- **langchain-core**: Provides base abstractions and the LangChain Expression Language (LCEL).
- **langchain-community**: Offers a wide range of third-party integrations.
- **langchain**: Contains chains, agents, and retrieval strategies that form an application's cognitive architecture.
- **LangGraph**: Enables building robust and stateful multi-actor applications with LLMs by modeling steps as edges and nodes in a graph.
- **LangServe**: Allows deployment of LangChain chains as REST APIs.
- **LangSmith**: A developer platform for debugging, testing, evaluating, and monitoring LLM applications.

## API Reference

The LangChain API is structured around several key packages, each focusing on different aspects of LLM-powered application development.

### langchain

Core package containing main LangChain functionalities. [API Reference](https://python.langchain.com/api_reference/langchain/langchain.html)

- `agents`: [API Reference](https://python.langchain.com/api_reference/langchain/agents/agents.html)
- `chains`: [API Reference](https://python.langchain.com/api_reference/langchain/chains/chains.html)
- `chat_models`: [API Reference](https://python.langchain.com/api_reference/langchain/chat_models/chat_models.html)
- `document_loaders`: [API Reference](https://python.langchain.com/api_reference/langchain/document_loaders/document_loaders.html)
- `embeddings`: [API Reference](https://python.langchain.com/api_reference/langchain/embeddings/embeddings.html)
- `llms`: [API Reference](https://python.langchain.com/api_reference/langchain/llms/llms.html)
- `memory`: [API Reference](https://python.langchain.com/api_reference/langchain/memory/memory.html)
- `prompts`: [API Reference](https://python.langchain.com/api_reference/langchain/prompts/prompts.html)
- `retrievers`: [API Reference](https://python.langchain.com/api_reference/langchain/retrievers/retrievers.html)
- `vectorstores`: [API Reference](https://python.langchain.com/api_reference/langchain/vectorstores/vectorstores.html)

### langchain_community

Integrations with third-party tools and services. [API Reference](https://python.langchain.com/api_reference/langchain_community/langchain_community.html)

### langchain_core

Core abstractions and LangChain Expression Language (LCEL). [API Reference](https://python.langchain.com/api_reference/langchain_core/langchain_core.html)

### langchain_experimental

Experimental features and components. [API Reference](https://python.langchain.com/api_reference/langchain_experimental/langchain_experimental.html)

### langgraph

Library for building stateful multi-actor applications with LLMs. [API Reference](https://python.langchain.com/api_reference/langgraph/langgraph.html)

### langserve

Tools for deploying LangChain applications as web services. [API Reference](https://python.langchain.com/api_reference/langserve/langserve.html)

## Tutorials

Tutorials are the best place to get started with LangChain. Key tutorials include:
- Build a Simple LLM Application
- Build a Chatbot
- Build an Agent
- Introduction to LangGraph

Additional resources:
- Full list of LangChain tutorials: [LangChain Tutorials](https://python.langchain.com/docs/tutorials/)
- LangGraph tutorials: [LangGraph Tutorials](https://langchain-ai.github.io/langgraph/tutorials/)
- LangChain Academy course on LangGraph: [Introduction to LangGraph](https://academy.langchain.com/courses/intro-to-langgraph)

## How-to Guides

These guides provide quick answers to specific "How do I...?" questions, covering common tasks without going into depth. They are designed to help users quickly accomplish tasks and complement the more in-depth material found in the Tutorials and API Reference.

LangGraph-specific how-to guides can be found [here](https://langchain-ai.github.io/langgraph/how-tos/).

## Conceptual Guide

This section provides in-depth explanations of LangChain's concepts and components. It offers high-level explanations of all LangChain concepts, helping users understand the framework's architecture and design principles.

For LangGraph concepts, refer to [this page](https://langchain-ai.github.io/langgraph/concepts/).

## LangGraph

LangGraph is a crucial part of the LangChain ecosystem, designed for building robust and stateful multi-actor applications with LLMs. It allows modeling of application steps as edges and nodes in a graph, providing a powerful way to create complex, interactive LLM-powered systems.

## Security

LangChain provides comprehensive information on [security best practices and considerations](https://python.langchain.com/docs/security/) when using the framework. This section is crucial for developers to ensure they're building secure applications with LangChain.

## Ecosystem

The LangChain ecosystem includes:
- 🦜🛠️ **LangSmith**: A developer platform for debugging, testing, evaluating, and monitoring LLM applications. It allows for tracing and evaluating language model applications and intelligent agents.
- 🦜🕸️ **LangGraph**: A library for building stateful multi-actor applications with LLMs. It integrates smoothly with LangChain but can also be used independently.

## Versions

LangChain provides documentation for different versions, including migration guides from older versions. This includes:
- Information on changes in v0.3
- Migration guides for legacy code
- Versioning policies

Users can find version-specific information and migration guides in the [Versions section](https://python.langchain.com/docs/versions/v0_3/) of the documentation.

## Conclusion

This documentation reference provides an overview of the LangChain framework, its key components, and API structure. LangChain offers a powerful set of tools for developing LLM-powered applications, including a modular architecture, integrations with various LLMs and vector stores, and deployment solutions.

For the most up-to-date and detailed information, always refer to the official LangChain documentation:

- Main documentation: https://python.langchain.com/docs/
- API reference: https://python.langchain.com/api_reference/
- GitHub repository: https://github.com/langchain-ai/langchain

By leveraging LangChain's components and following best practices, developers can create sophisticated, LLM-powered applications efficiently and effectively.
