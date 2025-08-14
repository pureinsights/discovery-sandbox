# Pureinsights Discovery Platform
 
Discovery Platform is an AI-powered search and data platform that connects search technologies with Large Language Models (LLMs) to build Retrieval Augmented Generation (RAG) applications, intelligent chatbots, and enterprise knowledge solutions.
 
With Discovery, you can integrate leading search engines like Elasticsearch, Apache Solr, OpenSearch, and MongoDB Atlas Search with top LLM providers such as OpenAI, Hugging Face, and Amazon Bedrock.
 
### Key capabilities:
- Combine keyword search, semantic search, and vector search for smarter retrieval.
- Build AI-driven search applications and context-aware chatbots.
- Process and summarize content using state-of-the-art LLMs.
- Deploy custom REST APIs for your search + AI workflows.

### Use cases:
- AI search engines.
- RAG pipelines for domain-specific data.
- Enterprise document search & insights.
- Conversational AI with real-time data retrieval.
- Automated content summarization & classification.
 
With Discovery, you can go from raw data to AI-powered insights quickly, using tools you already know.

# Pureinsights Discovery Platform: Sandbox SDK 
_Discovery Sandbox SDK_ is a Python package that allows developers to programatically access Discovery features. Currently, it supports executing one or multiple QueryFlow processors. 

> [!IMPORTANT]
> The current version of the Discovery Sandbox supports connections to internet-accessible services only. Support for local deployments is planned for an upcoming release.

## Requirements
- Python 3.13+ 
- `pip` 

## Installation 

```bash
pip install discovery-sandbox
```

## Testing
Testing is done using the `pytest` framework. These commands are run from the root folder.

To run the full test suite:
```bash
pytest --verbose
```
To run tests from a single file or directory:
```bash
pytest <path_to_test> --verbose
```
To generate a XML coverage report:
```bash
pytest --verbose --cov=. --cov-report xml:coverage.xml 
```
To generate a HTML coverage report:
```bash
pytest --cov=. --cov-report html
```
## Implementation
The SDK currently provides classes that represent Discovery entities (`Server`, `Credential`, `Processor`) as well as clients to interact with distinct endpoints. The API requests are made using the [httpx](https://www.python-httpx.org/) library, and serialization is done using the `json` built-in module. 
This client does the following: 

- Provides methods to execute standalone QueryFlow processors using `text_to_text/text_to_stream` that return the JSON execution output as a dictionary or text stream respectively.
- Supports overloading with the [multimethod](https://pypi.org/project/multimethod/) library to allow the usage of UUIDs instead of full entity objects.
- Supports the execution of a sequence of processors using the `QueryFlowSequenceProcessor` and `QueryFlowSequence` classes and the `execute` method. 

Currently, the SDK provides a `QueryFlowClient` class, that can be instanced with the base url of the QueryFlow instance and an API key.
