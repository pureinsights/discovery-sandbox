import streamlit as st
from datetime import datetime
from pdp_sdk import autocomplete_query, vectorize_query, es_vector_search, es_keyword_search, is_question, es_chunks, construct_prompt, oai_ask

MOCKUP_IMAGE = "https://media.licdn.com/dms/image/C4D0BAQFc43DVkxpVjg/company-logo_200_200/0/1630474077735/pureinsights_technology_logo?e=2147483647&v=beta&t=BUJJM6bpwWgw5tFW61Xvfa9j5_BEiL1wP_Wprcoo0ng"

######### Placeholder values #########

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

######################################

# Page configuration
st.set_page_config(page_title="Search Interface", layout="centered")

# Custom CSS for styling
st.markdown("""
<style>
    .search-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .carousel-card {
        background: white;
        border-radius: 10px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        flex-grow: 1;
        position: relative;
        padding: 20px;
        min-height: 20px;
        max-height: 400px;
        height: 260px;
        width: 100%;
        box-shadow: 0px 4px 12px rgba(115, 115, 124, 0.15);
        min-width: 50px;
    }
            
    .carousel-imagecontainer {
        width: 100%;
        height: 100px;
    }
            
    .carousel-img {
        height: 65%;
        width: 100%;
        object-fit: cover;
        border-radius: 4px;
        object-position: 0% 17%; 
    }
    
    .carousel-title {
        overflow: hidden;
        white-space: normal;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        margin-top: -7%;
        color: #333;
    }
    
    .carousel-description {
        overflow: hidden;
        white-space: normal;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        line-height: 1.4;
        margin-bottom: 1rem;
        color: #333;
    }
    
    .carousel-date {
        margin: 5px;
        position: absolute;
        bottom: 0px;
        right: 5px;
        color: #bfbfbf;
    }
    
    .keyword-result {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border-left: 4px solid #667eea;
    }
            
    .keyword-image {
        width: 200px;
        height: auto;
        max-height: 110px;
        object-fit: cover;
        margin: -5px 30px 0px 0;
        float: left;
    }      

    .keyword-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    .keyword-description {
        color: #666;
        line-height: 1.5;
        margin-bottom: 0.5rem;
    }
    
    .keyword-date {
        color: #999;
        font-size: 0.9rem;
    }
    
    .highlight {
        background-color: #e3f2fd;
        padding: 2px 4px;
        border-radius: 3px;
        font-weight: bold;
        color: #1976d2;
    }
    
    .pagination-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2rem 0;
        gap: 1rem;
    }
    
    .pagination-info {
        color: #666;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

def get_autocomplete_suggestions(query, autocomplete_index):
    """Get autocomplete suggestions using Elasticsearch format"""
    res = autocomplete_query(query, autocomplete_index)
    suggestions = []
    for i in res["hits"]["hits"]:
        suggestions.append(i["_source"]["title"] if "website_data" in i["_index"] else i["_source"]["question"])

    suggestions = list(set(suggestions))  # Remove duplicates
    if query in suggestions:
        suggestions.remove(query)  # Remove the exact query from suggestions

    if query:
        return [s for s in suggestions if query.lower() in s.lower()]
    return suggestions

def get_vector_search_results(embeddings, vector_index, field):
    """Get vector search results using Elasticsearch format"""
    res = es_vector_search(embeddings, index=vector_index, field=field)

    # Parse the Elasticsearch response
    results = []
    for hit in res["hits"]["hits"]:
        source = hit["_source"]
        
        # Format publication date
        pub_date = datetime.fromisoformat(source["publication_date"].replace('Z', '+00:00'))
        formatted_date = format_relative_date(pub_date)
        
        results.append({
            "title": source["title_data"][0],
            "description": source["title_data"][1].replace("___", "") if len(source["title_data"]) > 1 else "No description available.",
            "date": formatted_date,
            "author": "Unknown",
            "image": source["image"][0] if 'image' in source else MOCKUP_IMAGE,
            "url": source["uri"],
            "text": source["chunk"],
            "score": hit["_score"]
        })
    
    return results

def get_keyword_search_results(query, keyword_index, sort, start=0, size=10):
    """Get keyword search results using Elasticsearch format"""
    res = es_keyword_search(query, keyword_index, sort=sort, start=start, size=size)
    
    # Parse the Elasticsearch response
    total_results = res["hits"]["total"]["value"]
    results = []
    
    for hit in res["hits"]["hits"]:
        source = hit["_source"]
        
        # Format publication date
        pub_date = datetime.fromisoformat(source["publication_date"].replace('Z', '+00:00'))
        formatted_date = pub_date.strftime("%Y-%m-%d")
        
        # Create highlight (mock highlighting for demo)
        highlight = source["description"] if "description" in source else "No description available."
        if query:
            highlight = highlight.replace(query, f"<span class='highlight'>{query}</span>")
            highlight = highlight.replace(query.upper(), f"<span class='highlight'>{query.upper()}</span>")
            highlight = highlight.replace(query.lower(), f"<span class='highlight'>{query.lower()}</span>")
        
        results.append({
            "title": source["title"],
            "description": highlight,
            "date": formatted_date,
            "url": source["reference"],
            "image": source["image"][0] if "image" in source else MOCKUP_IMAGE,
            "highlight": highlight,
            "author": source["author"][0] if source["author"] else "Unknown",
            "score": hit["_score"] if hit["_score"] else 1.0
        })
    
    return {
        "total": total_results,
        "results": results
    }

def get_answers(query, chunks):
    prompt = construct_prompt(query, chunks)
    answer = oai_ask(prompt)
    return answer['choices'][0]['message']['content']

def format_relative_date(date):
    """Format date as relative time (e.g., '2 months ago')"""
    now = datetime.now(date.tzinfo)
    diff = now - date
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 7:
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"


# Initialize session state
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'show_suggestions' not in st.session_state:
    st.session_state.show_suggestions = False
if "carousel_index" not in st.session_state:
    st.session_state.carousel_index = 0
if "vector_results" not in st.session_state:
    st.session_state.vector_results = []
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "results_per_page" not in st.session_state:
    st.session_state.results_per_page = 10

# Search bar
col1, col2 = st.columns([12, 1])
with col1:
    search_query = st.text_input(
        "Search",
        value=st.session_state.search_query,
        placeholder="Enter your search query...",
        key="search_input",
        label_visibility="collapsed"
    )

with col2:
    search_button = st.button("🔍", help="Search")

# Handle search input changes
if search_query != st.session_state.search_query:
    st.session_state.search_query = search_query
    st.session_state.show_suggestions = len(search_query) > 0
    st.session_state.current_page = 1  # Reset to first page when query changes

# Show autocomplete suggestions
if st.session_state.show_suggestions and search_query:
    suggestions = get_autocomplete_suggestions(search_query, autocomplete_index)
    if suggestions:
        with st.expander("**Suggestions**", expanded=True, icon="💡"): 
            # put all suggestions in columns, with 3 per row for example
            n_cols = 3  # or adjust to taste
            cols = st.columns(n_cols)

            for idx, suggestion in enumerate(suggestions):
                col = cols[idx % n_cols]
                with col:
                    if st.button(f"{suggestion}", key=f"sugg_{idx}"):
                        st.session_state.search_query = suggestion
                        st.session_state.show_suggestions = True
                        st.session_state.current_page = 1  # Reset to first page
                        st.rerun()


st.markdown('</div>', unsafe_allow_html=True)

if search_query or search_button:
    # Only re-run vector search if the query is new
    if (
        search_query is not None and (
        "last_query" not in st.session_state
        or st.session_state.last_query != search_query)
    ):
        st.session_state.embeddings = vectorize_query(search_query)
        st.session_state.vector_results = get_vector_search_results(st.session_state.embeddings, vector_index["index"], vector_index["field"])
        st.session_state.carousel_index = 0  # reset to first window
        st.session_state.last_query = search_query

    vector_results = st.session_state.vector_results

    # Generative answers
    if is_question(search_query):
        st.subheader("Generative Answers")

        chunks = es_chunks(vector_results)
        generated_answer = get_answers(search_query, chunks)

        if generated_answer:
            st.markdown(f"""
            <div class="generated-answer">
                <p>{generated_answer}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("No answer could be generated for this query.")

        st.markdown("---")

    # Vector Search Results (Carousel)
    st.subheader("Semantic Search")
    
    # Create carousel using columns
    col1, col2, col3 = st.columns([1,12,1], vertical_alignment="center")

    cards = 2

    with col1:
        if st.button("←"):
            if st.session_state.carousel_index - cards >= 0:
                st.session_state.carousel_index -= cards
    with col3:
        if st.button("→"):
            if st.session_state.carousel_index + cards < len(vector_results):
                st.session_state.carousel_index += cards

    with col2:
        # Display 3 documents at a time
        start = st.session_state.carousel_index
        end = start + cards
        current_window = vector_results[start:end]

        cols = st.columns(cards)
        
        for idx, result in enumerate(current_window):
            with cols[idx]:
                st.markdown(
                    f"""
                    <div class="carousel-card">
                        <div class="carousel-imagecontainer">
                            <img src="{result['image']}" alt="{result['title']}" class="carousel-img">
                        </div>
                        <div class="carousel-title"><b>{result['title']}</b></div>
                        <div class="carousel-description">{result['description']}</div>
                        <div class="carousel-date">{result['date']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("---")

# Keyword Search Results
st.subheader("Keyword Search")

col1, col2 = st.columns([3, 1])
with col2:
    sort_option = st.selectbox("Sort By", ["Relevance", "Date"], label_visibility="collapsed")
    if sort_option == "Date":
        sort = [{"publication_date": {"order": "desc"}}]
    else:
        sort = [{"_score": {"order": "desc"}}]

# Calculate start index for pagination
start = (st.session_state.current_page - 1) * st.session_state.results_per_page
keyword_results = get_keyword_search_results(search_query, keyword_index, sort, start=start, size=st.session_state.results_per_page)

# Results count and sort options
with col1:
    st.write(f"About {keyword_results['total']} results")

# Display keyword search results
for result in keyword_results['results']:
    st.markdown(f"""
    <div class="keyword-result">
        <img src="{result['image']}" alt="{result['title']}" class="keyword-image">
        <div class="keyword-title">{result['title']}</div>
        <div class="keyword-description">{result['highlight']}</div>
        <div class="keyword-date">{result['date']} • by {result['author']} • Score: {result['score']:.2f}</div>
    </div>
    """, unsafe_allow_html=True)

# Pagination controls
if keyword_results['total'] > st.session_state.results_per_page:
    total_pages = (keyword_results['total'] + st.session_state.results_per_page - 1) // st.session_state.results_per_page
    
    st.markdown('<div class="pagination-container">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Show current page info
        start_result = (st.session_state.current_page - 1) * st.session_state.results_per_page + 1
        end_result = min(st.session_state.current_page * st.session_state.results_per_page, keyword_results['total'])
        st.markdown(f'<div class="pagination-info">Page {st.session_state.current_page} of {total_pages}</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div class="pagination-info">Showing {start_result}-{end_result} of {keyword_results["total"]} results</div>', unsafe_allow_html=True)
    
    with col3:
        # Page jump functionality
        new_page = st.number_input("Go to page:", min_value=1, max_value=total_pages, value=st.session_state.current_page, key="page_jump")
        if new_page != st.session_state.current_page:
            st.session_state.current_page = new_page
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)