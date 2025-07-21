# Multiple Search and RAG example (Sandbox SDK)

A Streamlit-based demonstration showcasing the capabilities of the QueryFlow Sandbox SDK, including keyword search, suggestions, semantic search, and RAG (Retrieval-Augmented Generation) functionality.

## Features
- Keyword Search: Traditional text-based search with exact and fuzzy matching
- Suggestions: Auto-complete and query suggestions for enhanced user experience
- Semantic Search: Vector-based search for finding conceptually similar content
- RAG (Retrieval-Augmented Generation): AI-powered responses using retrieved context

## Installation

### Dependencies

```bash
pip install streamlit python-dotenv
```

### Environment Configuration

Create a `.env` file in the root directory and set the following variables:

```env
OPENAI_API_KEY=your_openai_api_key_here
ES_PASSWORD=your_elasticsearch_password
ES_SERVER=your_elasticsearch_server_url
QF_HOST=your_queryflow_host
QF_KEY=your_queryflow_api_key
```

## Setup Instructions

Before running the application, you need to set up the Elasticsearch index:

1. Create Index Mappings: First, apply the index mappings from `mappings.json` to create the test_index with the proper field configurations.
2. Populate the Index: Run the setup script to load the sample data:
```bash
python setup_index.py
```

This script uses `dataset.json` to populate the test_index with sample documents.
3. Start the Application: Launch the Streamlit interface:
```bash
streamlit run main.py
```

## SDK Implementation Steps

The implementation demonstrates QueryFlow Sandbox SDK usage through various search methodologies:

**1. Initialize QueryFlow Client**

```py
from dotenv import load_dotenv
from sandbox.discovery_sandbox import QueryFlowClient, Credential, Server, Processor

load_dotenv()

qfc = QueryFlowClient(os.getenv("QF_HOST"), os.getenv("QF_KEY"))
```

**2. Configure Credentials and Servers**

**OpenAI Configuration** (for embeddings and chat completions):
```py
openai_credential = Credential("openai", {
    "apiKey": os.getenv("OPENAI_API_KEY")
}) 

oai_server = Server("openai", {}, openai_credential)
```

**Elasticsearch Configuration** (for search and storage):
```py
elastic_credential = Credential("elasticsearch", {
    "username": "elastic",
    "password": os.getenv("ES_PASSWORD")
})

es_server = Server("elasticsearch", { 
    "servers": [ os.getenv("ES_SERVER") ],
    "connection": {
        "readTimeout": "30s",
        "connectTimeout": "1m"
    }
}, elastic_credential)
```

**3. Set-up Search Processors**

- **Keyword Search** - Traditional text matching with fuzzy search capabilities:

```py
def es_keyword_search(query, index='test_search', start=0, size=10, filters=[], sort=[{"_score": {"order": "desc"}}]):
    processor = Processor("elasticsearch", {
        "body": {
            "from": start,
            "size": size,
            "sort": sort,
            "query": {
                "bool": {
                    "filter": filters,
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "title^5",
                                    "description^3", 
                                    "contents"
                                ],
                                "fuzziness": "AUTO"
                            }
                        }
                    ]
                }
            }
        },
        "path": f"/{index}/_search",
        "action": "native",
        "method": "GET"
    }, es_server)
    return qfc.text_to_text(processor, {})
```

- **Autocomplete Suggestions** - Query suggestions for enhanced user experience:

```py
def autocomplete_query(query, index='test_search', size=5):
    es_autocomplete = Processor("elasticsearch", {
        "action": "autocomplete",
        "index": index,
        "text": query,
        "field": "suggest"
    }, es_server)
    return qfc.text_to_text(es_autocomplete, {})
```

- **Vector Search** - Semantic search using embeddings:

```py
def vectorize_query(query):
    oai_vectorize = Processor("openai", {
        "action": "embeddings",
        "user": "pureinsights",
        "input": query,
        "model": "text-embedding-3-small"
    }, oai_server)
    return qfc.text_to_text(oai_vectorize, {})['embeddings'][0]['embedding']

def es_vector_search(embeddings, index='test_search', field='vector'):
    es_vector_request = Processor("elasticsearch", {
        "action": "vector",
        "field": field,
        "index": index,
        "query": {
            "match_all": {}
        },
        "vector": embeddings,
        "function": "cosineSimilarity",
        "minScore": 0.6,
        "maxResults": 10
    }, es_server)
    return qfc.text_to_text(es_vector_request, {})
```

- **RAG (Retrieval-Augmented Generation)** - AI-powered responses using retrieved context:

```py
def oai_ask(content):
    oai_ask = Processor("openai", {
        "action": "chat-completion",
        "user": "pureinsights",
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "maxTokens": 8192
    }, oai_server)
    
    return qfc.text_to_text(oai_ask, {})
```

**4. Set Up the User Interface and Supporting Scripts**

The `main.py` script serves as the user interface, built using Streamlit, providing an interactive front end for the application.
Ensure the necessary scripts are properly configured and integrated according to your project’s requirements.

## Usage

### Basic Workflow

**1. Setup the Index**
    - Apply mappings from mappings.json
    - Run setup_index.py to populate with sample data

**2. Start the Application**
    - Launch with: `streamlit run .\main.py`
    - Access the web interface in your browser

**3. Explore Search Features** 
    - Keyword Search: Enter queries to find documents using traditional text matching
    - Suggestions: Get auto-complete suggestions as you type
    - Semantic Search: Find conceptually similar content using vector embeddings
    - RAG: Ask questions and receive AI-generated answers based on retrieved context