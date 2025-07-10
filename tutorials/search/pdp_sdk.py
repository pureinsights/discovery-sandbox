import os 
from dotenv import load_dotenv
from inference.discovery_inference import QueryFlowClient, Credential, Server, Processor

load_dotenv()

qfc = QueryFlowClient(os.getenv("QF_HOST"), os.getenv("QF_KEY"))

# GENERATIVE ANSWERS PROMPT
GEN_ANS_PROMPT = """
You are an excellent question and answer, and chat completion system. Everything that you answer MUST be based on the information provided, use ONLY the information given below. Follow carefully the additional rules provided in the user prompt UNLESS they contradict these initial instructions. 

Guidelines for processing the context:
1. Pay close attention to all details provided in the context.
2. Note any citationIds associated with pieces of information.
3. Identify key facts, figures, and concepts that may be relevant to answering the provided question.

When formulating your answer:
1. Think step-by-step.
2. Use only information from the provided context. Do not include external knowledge or assumptions.
3. Be verbose in your response, especially for short queries. Elaborate on relevant points to provide a fuller understanding. Start with a strong opener that summarizes the answer. 
4. Do not include any information that is not explicitly stated or directly implied by the context.
5. Do not ask follow-up questions or request additional information.
6. If you are not sure about the answer or completion, respond with '' ONLY. Do not provide any explanation for why there is no answer.
7. If you do not have any information, please respond with '' ONLY. Do not provide any explanation for why there is no answer.
8. For each piece of information you use, add a citation using the 'citationId' provided. The citation format is [citationId], e.g., [2]. DO NOT add a separate References or Citations section. ALWAYS USE CITATIONS. 
9. If two or more pieces of information have the same 'citationId' use a single citation [citationId] to avoid duplication.
10. If there's not enough information provided DO NOT mention it in the answer.
11. Before returning the result review your answer against all rules. Return '' if the answer does not follow the rules. Do not provide any explanation for why there is no answer. 
12. Answer concisely unless elaboration is explicitly required. Do not include additional context unless it directly enhances the understanding of the answer.
13. Avoid unnecessary citations. If multiple citations support the same fact, include only one citation, or consolidate them into a single reference.
14. Omit quotes or descriptions of context unless asked for. Only state the key information relevant to the question.
15. Do not explain how the information was determined. Focus solely on delivering the answer, not the process of arriving at it.

Formatting Requirements:
1. Use proper nesting of HTML tags for clarity and maintainability.
2. Ensure all HTML tags are correctly closed.
2. Use lists (<ul>, <ol>, <li>) and bolding (<b>) format for key information. 
4. If a statement functions like a header, separate it using <br> tags before and after the statement.
5. When a list starts and ends (</ul>, </ol>), add a <br> tag for formatting purposes. 
6. Wrap each paragraph in <p> tags.

Remember, your answer must be based solely on the information provided in the context. Do not introduce external knowledge or make assumptions beyond what is given. Ensure your response is detailed, informative, formatted and include relevant citations. Do not use markup headings (H1, H2, H3, etc) format such as #, ##, ###, etc. Check that the opener contains a briefing of the whole answer.

======== CONTEXT ========
{{CONTEXT}}
=========================

======== QUESTION ========
{{QUESTION}}
=========================

======== ANSWER BELOW THIS LINE ========
Write your answer for a Expert.
Do not include any instructions in your answer.
========================================
"""
TOKEN_SIZE = 4
model = { 
    "DEFAULT_MODEL": "gpt-4o-mini",
    "contextWindow": 128000,
    "maxContextFactor": 0.8,
    "maxTokens": 8192
}

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

def es_keyword_search(query, index='website_data', start=0, size=10, filters=[], sort=[{"_score": {"order": "desc"}}]):
    if not query or query.strip() == "":
        processor = Processor("elasticsearch", {
            "body": {
                "from": start,
                "size": size,
                "sort": [
                    {
                        "publication_date": {
                            "order": "desc"
                        }
                    }
                ],
                "query": {
                    "bool": {
                        "must": {
                            "match_all": {}
                        },
                        "filter": filters
                    }
                }
            },
            "path": f"/{index}/_search",
            "action": "native",
            "method": "GET"
        }, es_server)
    else:
        processor = Processor("elasticsearch", {
            "body": {
                "from": start,
                "size": size,
                "sort": sort,
                "query": {
                    "function_score": {
                        "query": {
                            "bool": {
                                "filter": filters,
                                "should": [
                                    {
                                        "query_string": {
                                            "query": query,
                                            "fields": [
                                                "title.standard^5",
                                                "description^3",
                                                "contents"
                                            ],
                                            "default_operator": 'AND' if (len(query) >= 3) else 'OR',
                                            "fuzziness": "AUTO"
                                        }
                                    }
                                ]
                            }
                        },
                        "functions": [
                            {
                                "gauss": {
                                    "publication_date": {
                                        "origin": "now",
                                        "scale": "180d",
                                        "offset": "90d",
                                        "decay": 0.75
                                    }
                                }
                            }
                        ],
                        "boost_mode": "multiply",
                        "score_mode": "sum"
                    }
                },
                "highlight": {
                    "fields": {
                        "title.standard": {
                            "number_of_fragments": 0
                        },
                        "description": {
                            "number_of_fragments": 0
                        }
                    },
                    "pre_tags": [
                        "<FONT COLOR=\"BLUE\">"
                    ],
                    "post_tags": [
                        "</FONT>"
                    ],
                    "require_field_match": False
                }
            },
            "path": f"/{index}/_search",
            "action": "native",
            "method": "GET"
        }, es_server)
    return qfc.text_to_text(processor, {})

def autocomplete_query(query, index='autocomplete', size=5):
    es_autocomplete = Processor("elasticsearch", {
        "body": {
            "size": size,
            "query": {
                "bool": {
                    "should": [
                        {
                            "match_phrase_prefix": {
                                "title.autocomplete": {
                                    "query": query
                                }
                            }
                        },
                        {
                            "match_phrase_prefix": {
                                "question": {
                                    "query": query
                                }
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
    return qfc.text_to_text(es_autocomplete, {})

def vectorize_query(query):
    oai_vectorize = Processor("openai", {
        "action": "embeddings",
        "user": "pureinsights",
        "input": query,
        "model": "text-embedding-3-small"
    }, oai_server)
    return qfc.text_to_text(oai_vectorize, {})['embeddings'][0]['embedding']
    
def es_vector_search(embeddings, index='vector_data', field='vector'):
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

def es_chunks(vector_search_results):
    chunks = []
    i = 0
    for item in vector_search_results:
        i += 1
        chunk = {
            "number": i,
            "url": item['url'],
            "title": item['title'],
            "text": item['text'],
            "date": item['date']
        }
        chunks.append(chunk)
    
    return chunks

# Generative Answers

def is_question(query):
    return query.endswith('?') or query.endswith('¿')

def build_context(chunks):
    max_tokens = model["maxTokens"] * model["maxContextFactor"]
    context_tokens = 0
    context = ''

    for chunk in chunks:
        chunk_content = chunk['text']
        chunk_tokens = len(chunk_content) // TOKEN_SIZE
        if context_tokens + chunk_tokens < max_tokens:
            context = context + 'context[' + str(chunk['number']) + ']: ' + chunk_content + '\n\n'
        context_tokens += chunk_tokens
    
    return context

def construct_prompt(query, chunks):
    context = build_context(chunks)
    return GEN_ANS_PROMPT.replace('{{CONTEXT}}', context).replace('{{QUESTION}}', query)

def oai_ask(content):
    oai_ask = Processor("openai", {
        "action": "chat-completion",
        "user": "pureinsights",
        "model": model["DEFAULT_MODEL"],
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "maxTokens": model["maxTokens"]
    }, oai_server)
    
    return qfc.text_to_text(oai_ask, {})