import os
from dotenv import load_dotenv
from inference.discovery_inference import QueryFlowClient, Credential, Server, Processor

load_dotenv()

qfc = QueryFlowClient(os.getenv("QF_HOST"), os.getenv("QF_KEY"))

# Credentials

openai_credential = Credential("openai", {
    "apiKey": os.getenv("OPENAI_API_KEY")
}) 

elastic_credential = Credential("elasticsearch", {
    "username": "elastic",
    "password": os.getenv("ES_PASSWORD")
})

# Servers

oai_server = Server("openai", {}, openai_credential)

es_server = Server("elasticsearch", { 
    "servers": [ os.getenv("ES_SERVER") ],
    "connection": {
        "readTimeout": "30s",
        "connectTimeout": "1m"
    }
}, elastic_credential)

# Processors

def create_embeddings(text):
    vectorize_oai = Processor("openai", {
        "action": "embeddings",
        "user": "pureinsights",
        "input": text,
        "model": "text-embedding-3-small"
    }, oai_server)
    return qfc.text_to_text(vectorize_oai, {})['embeddings'][0]['embedding']

def store_es(doc, index): 
    store_es = Processor("elasticsearch", {
        "action": "store",
        "index": index,
        "document": doc
    }, es_server)

    qfc.text_to_text(store_es, {})

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