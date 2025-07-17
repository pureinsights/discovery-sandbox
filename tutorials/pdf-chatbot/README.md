# PDF Chatbot 📚 (Sandbox SDK)

A Streamlit-based intelligent PDF chatbot that allows users to upload PDF documents, process them into searchable chunks, and ask questions about their content using vector search and AI-powered responses by using Queryflow Sandbox SDK.

## Features
- PDF Upload & Processing: Upload and process PDF documents with configurable chunking
- Vector Search: Semantic search through document content using embeddings
- AI Chat Interface: Interactive chat with context-aware responses
- Index Management: Organize documents into different indexes for better context separation
- Custom System Prompts: Customize the AI assistant's behavior and instructions
- Chat History Management: Save, clear, and export chat conversations

## Installation

### Dependencies

```bash
pip install streamlit pypdf python-dotenv
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

## SDK Implementation Steps 

The `pdp_sdk.py` module implements the QueryFlow Sandbox SDK through a structured approach:

**1. Initialize QueryFlow Client**

Create the main client that orchestrates all operations:

```py
from dotenv import load_dotenv
from sandbox.discovery_sandbox import QueryFlowClient, Credential, Server, Processor

load_dotenv()

# Create QueryFlow client using environment variables
qfc = QueryFlowClient(QF_HOST, QF_KEY)
```

**2. Configure Credentials and Server**

**OpenAI Configuration** (for embeddings and chat completions)

```py
openai_credential = Credential("openai", {
    "apiKey": os.getenv("OPENAI_API_KEY")
}) 

oai_server = Server("openai", {}, openai_credential)
```

**Elasticsearch Configuration** (for storage, vector search, and aggregations)

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

**3. Create and Use Processors**

All processors follow the same pattern: define the processor with its configuration, execute it using qfc.text_to_text(), then extract and return the relevant data.

**OpenAI Processors:**
- vectorize_oai – Generates embeddings from input text.

```py
def create_embeddings(text):
    vectorize_oai = Processor("openai", {
        "action": "embeddings",
        "user": "pureinsights",
        "input": text,
        "model": "text-embedding-3-small"
    }, oai_server)
    return qfc.text_to_text(vectorize_oai, {})['embeddings'][0]['embedding']
```

- chat_oai – Produces structured chat responses with JSON schema.

```py
def chat_completion(messages):
    chat_oai = Processor("openai", {
        "action": "chat-completion",
        "user": "pureinsights",
        "model": "gpt-4o-mini",
        "messages": messages,
        "responseFormat": {
            "type": "json_schema",
            "json_schema": {
                "name": "name",
                "schema": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string"
                        },
                        "references": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["response", "references"]
                }
            }
        }
    }, oai_server)

    response = qfc.text_to_text(chat_oai, {})
    return response['choices'][0]['message']['content']
```

**Elasticsearch:**
- store_es – Stores documents with embeddings in specified index.
```py
def store_es(doc, index): 
    store_es = Processor("elasticsearch", {
        "action": "store",
        "index": index,
        "document": doc
    }, es_server)

    qfc.text_to_text(store_es, {})
```

- vector_search – Performs semantic similarity search.

```py
def vector_search_es(embeddings, index, max_results=3):
    vector_search = Processor("elasticsearch", {
        "action": "vector",
        "index": index,
        "field": "embedding",
        "vector": embeddings,
        "minScore": 0.6,
        "maxResults": max_results,
        "query": {
            "match_all": {}
        }
    }, es_server)

    response = qfc.text_to_text(vector_search, {})
    return response['hits']['hits']
```

- agg_es – Retrieves filename aggregations for statistics.

```py
def check_aggs(index, field='filename'):
    agg_es = Processor("elasticsearch", {
        "body": {
            "size": 0,
            "aggs": {
                "unique": {
                    "terms": {
                        "field": f"{field}.keyword",
                        "size": 100
                    }
                }
            }
        },
        "path": f"/{index}/_search",
        "action": "native",
        "method": "GET"
    }, es_server)

    return qfc.text_to_text(agg_es, {})['aggregations']['unique']['buckets']
```

**4. Set Up the User Interface and Supporting Scripts**

The `main.py` script serves as the user interface, built using Streamlit, providing an interactive front end for the application.
The `chunker.py` script is responsible for generating the text chunks required for processing in this example.

Ensure the necessary scripts are properly configured and integrated according to your project’s requirements.

## Usage

### Starting the Application

```bash
streamlit run .\main.py
```

## Basic Workflow

1. Set up an Index
    - Use the default index or create a new one in the sidebar
    - Index names help organize different document collections

2. Upload PDF Documents
    - Click "Browse files" in the sidebar
    - Select PDF files (max 50MB each)
    - Configure chunk size and overlap settings
    - Click "Generate Embeddings" to process the document

3. Ask Questions
    - Type questions in the chat input
    - The system will search for relevant context and provide answers
    - References will be shown for each response