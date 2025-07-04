# PDF Chatbot 📚 (Inference SDK)

A Streamlit-based intelligent PDF chatbot that allows users to upload PDF documents, process them into searchable chunks, and ask questions about their content using vector search and AI-powered responses by using Queryflow Inference SDK.

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

### QueryFlow Configuration
The QF instance must have inference enabled. Update your `queryflow-api/src/main/resources/application.yml`:

```yml
queryflow:
  inference:
    enabled: true
```

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