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

## Usage

### Starting the Application

```bash
streamlit run .\main.py
```

## Index Configuration

> Important: The demo uses placeholder index names that must be updated before running:

### Default Placeholder Indices
The following placeholder indices are used in the example and should be replaced with your actual indices:

```python
# Keyword Search Index
keyword_index = 'website_data'
# REQUIRED FIELDS: publication_date, title, description, contents

# Suggestion Index  
autocomplete_index = 'autocomplete'
# REQUIRED FIELDS: title OR question

# Vector Search / RAG Index 
vector_index = {
    "index": 'vector_data',
    "field": "vector"  # Field where the vectors are stored
}
# REQUIRED FIELDS: content (text), vector (dense_vector)
```