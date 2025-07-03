import streamlit as st
import tempfile
import os
import json
from datetime import datetime
from chunker import PDFChunker
from pdp_sdk import create_embeddings, store_es, chat_completion, vector_search_es, check_aggs

# Configuration
CONFIG = {
    'DEFAULT_INDEX': 'pdf_chatbot',
    'MAX_CHAT_HISTORY': 10,
    'CHAT_HISTORY_FILE': 'chat_history.json',
    'SYSTEM_MESSAGE': "You are a helpful PDF assistant chatbot. You must answer the user questions based ONLY on the context provided and show the references used (Use only the filename).",
    'MAX_FILE_SIZE_MB': 50,
    'CACHE_TTL': 3600,  # 1 hour in seconds
    'DEFAULT_CHUNK_SIZE': 1000,
    'DEFAULT_OVERLAP_SIZE': 100,
    'DEFAULT_VECTOR_SEARCH_SIZE': 3,
    'MIN_CHUNK_SIZE': 100,
    'MAX_CHUNK_SIZE': 2000,
    "MIN_OVERLAP_SIZE": 10,
    'MIN_VECTOR_SEARCH_SIZE': 1,
    'MAX_VECTOR_SEARCH_SIZE': 15,
}

system_msg = [{"role": "system", "content": CONFIG['SYSTEM_MESSAGE']}]

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'display_text': CONFIG['DEFAULT_INDEX'],
        'index_input': CONFIG['DEFAULT_INDEX'],
        'messages': system_msg.copy(),
        'display_messages': [],
        'processing_file': False,
        'chunk_size': CONFIG['DEFAULT_CHUNK_SIZE'],
        'overlap_size': CONFIG['DEFAULT_OVERLAP_SIZE'],
        'vector_search_size': CONFIG['DEFAULT_VECTOR_SEARCH_SIZE'],
        'system_prompt': CONFIG['SYSTEM_MESSAGE'],
        'system_prompt_changed': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def validate_index_name(index_name):
    """Validate index name format"""
    if not index_name or not index_name.strip():
        return False, "Index name cannot be empty"
    
    if len(index_name) > 50:
        return False, "Index name too long (max 50 characters)"
    
    # Check for invalid characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    if any(char in index_name for char in invalid_chars):
        return False, f"Index name contains invalid characters: {', '.join(invalid_chars)}"
    
    return True, ""

def selected_index():
    """Handle index selection with validation"""
    new_index = st.session_state.get("index_input", CONFIG['DEFAULT_INDEX']).strip()
    is_valid, error_msg = validate_index_name(new_index)
    
    if is_valid:
        st.session_state['display_text'] = new_index
        st.success(f"Switched to index: {new_index}")
    else:
        st.error(f"Invalid index name: {error_msg}")
        st.session_state['index_input'] = st.session_state['display_text']

def display_index_badge():
    """Display current index as a badge"""
    st.markdown(f"""
        <div style="display: inline-block; padding: 5px 10px; border-radius: 5px; 
                   background-color: #007BFF; color: white; margin-bottom: 10px;">
            Current Index: {st.session_state['display_text']}
        </div>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=CONFIG['CACHE_TTL'])
def process_pdf_cached(file_content, filename, chunk_size, overlap_size):
    """Cache PDF processing to avoid reprocessing same files"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(file_content)
        tmp_path = tmp_file.name
    
    try:
        chunker = PDFChunker(chunk_size, overlap_size)
        chunks = chunker.process_pdf(tmp_path)
        return chunks
    except Exception as e:
        st.error(f"Error processing PDF {filename}: {str(e)}")
        return []
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def generate_embeddings(filename, chunks):
    """Generate embeddings for PDF chunks with progress tracking"""
    if not chunks:
        st.error("No chunks provided for embedding generation")
        return False
    
    # Filter out empty chunks
    valid_chunks = [chunk for chunk in chunks if chunk.strip()]
    if not valid_chunks:
        st.error("No valid chunks found after filtering")
        return False
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        successful_chunks = 0
        for i, chunk in enumerate(valid_chunks):
            status_text.text(f"Processing chunk {i+1} of {len(valid_chunks)}...")
            
            try:
                embeddings = create_embeddings(chunk)
                doc = {
                    "filename": filename,
                    "text": chunk,
                    "embedding": embeddings
                }
                store_es(doc, st.session_state.get("index_input"))
                successful_chunks += 1
                
            except Exception as e:
                st.warning(f"Failed to process chunk {i+1}: {str(e)}")
                continue
            
            # Update progress bar
            progress_bar.progress((i + 1) / len(valid_chunks))
        
        if successful_chunks > 0:
            st.success(f"Successfully generated {successful_chunks} embeddings out of {len(valid_chunks)} chunks")
            return True
        else:
            st.error("Failed to generate any embeddings")
            return False
            
    except Exception as e:
        st.error(f"Error generating embeddings: {str(e)}")
        return False
    finally:
        progress_bar.empty()
        status_text.empty()

def add_context_to_prompt(prompt):
    """Add relevant context to user prompt"""
    if not prompt.strip():
        return prompt
    
    with st.spinner("Searching for relevant context..."):
        try:
            vectorized_prompt = create_embeddings(prompt)
            # Use the configured vector search size
            vector_search_size = st.session_state.get('vector_search_size', CONFIG['DEFAULT_VECTOR_SEARCH_SIZE'])
            docs = vector_search_es(vectorized_prompt, st.session_state.get("index_input"), vector_search_size)
            
            if not docs:
                st.warning("No relevant context found in the current index.")
                return prompt
            
            context = "\n===CONTEXT START===\n"
            for doc in docs:
                text = doc['_source']['text']
                name = doc['_source']['filename']
                context += f"- Source [{name}]: {text}\n"
            
            context += "===CONTEXT END===\n"
            return prompt + context
            
        except Exception as e:
            st.error(f"Error obtaining context: {str(e)}")
            return prompt

def manage_chat_history():
    """Keep chat history within reasonable limits"""
    # Get current system message from session state
    current_system_msg = [{"role": "system", "content": st.session_state.get('system_prompt', CONFIG['SYSTEM_MESSAGE'])}]
    other_msgs = [msg for msg in st.session_state.messages if msg["role"] != "system"]
    
    if len(other_msgs) > CONFIG['MAX_CHAT_HISTORY']:
        other_msgs = other_msgs[-CONFIG['MAX_CHAT_HISTORY']:]
    
    st.session_state.messages = current_system_msg + other_msgs

def save_chat_history():
    """Save chat history to file"""
    try:
        with open(CONFIG['CHAT_HISTORY_FILE'], "w") as f:
            json.dump(st.session_state.messages, f, indent=4)
    except Exception as e:
        st.error(f"Error saving chat history: {str(e)}")

def clear_chat_history():
    """Clear chat history"""
    # Use current system prompt
    current_system_msg = [{"role": "system", "content": st.session_state.get('system_prompt', CONFIG['SYSTEM_MESSAGE'])}]
    st.session_state.messages = current_system_msg
    st.session_state.display_messages = []
    if os.path.exists(CONFIG['CHAT_HISTORY_FILE']):
        try:
            os.remove(CONFIG['CHAT_HISTORY_FILE'])
        except Exception as e:
            st.error(f"Error clearing chat history file: {str(e)}")

def export_chat_history():
    """Export chat history as downloadable file"""
    if st.session_state.display_messages:
        chat_data = json.dumps(st.session_state.display_messages, indent=2)
        return st.download_button(
            label="📥 Download Chat History",
            data=chat_data,
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    return None

def display_chat_history():
    """Display chat messages from session state"""
    for message in st.session_state.display_messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                # Handle both dict and JSON string responses
                if isinstance(message["content"], dict):
                    response = message["content"]
                else:
                    try:
                        response = json.loads(message["content"])
                    except json.JSONDecodeError:
                        st.markdown(message["content"])
                        continue
                
                # Display the response
                st.markdown(response["response"])
                if response.get("references"):
                    with st.expander("📘 References", expanded=False):
                        for ref in response["references"]:
                            st.write(f"- {ref}")
            else:
                st.markdown(message["content"])

def handle_chat_input():
    """Handle user chat input and generate response"""
    if prompt := st.chat_input("What would you like to talk about?"):
        if not prompt.strip():
            st.warning("Please enter a valid question.")
            return
        
        # Manage chat history length
        manage_chat_history()
        
        # Add context to prompt
        new_prompt = add_context_to_prompt(prompt)
        
        # Add to session state
        st.session_state.display_messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "user", "content": new_prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display assistant response
        try:
            with st.spinner("Generating response..."):
                response_string = chat_completion(st.session_state.messages)
            
            # Try to parse JSON response
            try:
                response = json.loads(response_string)
                
                with st.chat_message("assistant"):
                    st.markdown(response["response"])
                    if response.get("references"):
                        with st.expander("📘 References", expanded=False):
                            for ref in response["references"]:
                                st.write(f"- {ref}")
                
                # Add to session state
                st.session_state.messages.append({"role": "assistant", "content": response_string})
                st.session_state.display_messages.append({"role": "assistant", "content": response})
                
            except json.JSONDecodeError:
                # Handle plain text response
                with st.chat_message("assistant"):
                    st.markdown(response_string)
                
                st.session_state.messages.append({"role": "assistant", "content": response_string})
                st.session_state.display_messages.append({"role": "assistant", "content": response_string})
            
            # Save chat history
            save_chat_history()
            
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")

def check_pdfs_in_index():
    """Check and display PDFs in current index"""
    try:
        with st.spinner("Checking PDFs in index..."):
            files_used = check_aggs(st.session_state.get('index_input'))
        
        if files_used:
            st.success(f"Found {len(files_used)} PDF(s) in index:")
            for file in files_used:
                st.write(f"- **{file['key']}** ({file['doc_count']} chunks)")
        else:
            st.info("No PDFs found in current index")
            
    except Exception as e:
        st.error("No PDFs found in current index")

def handle_file_upload():
    """Handle PDF file upload and processing"""
    uploaded_file = st.file_uploader(
        "Select PDF", 
        type="pdf",
        help=f"Maximum file size: {CONFIG['MAX_FILE_SIZE_MB']}MB"
    )
    
    if uploaded_file is not None:
        # Check file size
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        if file_size_mb > CONFIG['MAX_FILE_SIZE_MB']:
            st.error(f"File size ({file_size_mb:.1f}MB) exceeds limit ({CONFIG['MAX_FILE_SIZE_MB']}MB)")
            return
        
        # Process PDF
        try:
            chunk_size = st.session_state.get('chunk_size', CONFIG['DEFAULT_CHUNK_SIZE'])
            overlap_size = st.session_state.get('overlap_size', CONFIG['DEFAULT_OVERLAP_SIZE'])
            with st.spinner("Processing PDF..."):
                chunks = process_pdf_cached(uploaded_file.getvalue(), uploaded_file.name, chunk_size, overlap_size)
            
            if chunks:
                st.success(f"PDF processed successfully! Generated {len(chunks)} chunks.")
                
                # Display chunk statistics
                with st.expander("📊 Chunk Statistics", expanded=True):
                    chunk_lengths = [len(chunk) for chunk in chunks]
                    st.json({
                        "Total Chunks": len(chunks),
                        "Min Chunk Length": min(chunk_lengths) if chunk_lengths else 0,
                        "Max Chunk Length": max(chunk_lengths) if chunk_lengths else 0,
                        "Chunk Size Setting": chunk_size,
                        "Overlap Size Setting": overlap_size
                    })
                
                # Generate embeddings button
                if st.button(f"🚀 Generate Embeddings to '{st.session_state.get('index_input')}'"):
                    if generate_embeddings(uploaded_file.name, chunks):
                        st.balloons()
                        st.rerun()
                    
            else:
                st.error("No text could be extracted from the PDF.")
                
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")

def reset_system_prompt():
    """Reset system prompt to default"""
    if 'system_prompt' in st.session_state:
        del st.session_state['system_prompt']
    st.session_state.system_prompt = CONFIG['SYSTEM_MESSAGE']
    st.session_state.system_prompt_changed = False

def apply_system_prompt():
    """Apply the current system prompt to chat history"""
    # Update the system message in the chat history
    current_system_msg = [{"role": "system", "content": st.session_state.system_prompt}]
    other_msgs = [msg for msg in st.session_state.messages if msg["role"] != "system"]
    st.session_state.messages = current_system_msg + other_msgs
    st.session_state.system_prompt_changed = False
    st.success("System prompt applied!")

def on_system_prompt_change():
    """Handle system prompt changes"""
    if st.session_state.system_prompt != CONFIG['SYSTEM_MESSAGE']:
        st.session_state.system_prompt_changed = True
    else:
        st.session_state.system_prompt_changed = False

def setup_sidebar():
    """Setup sidebar with all controls"""
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Index management
        with st.expander("Index Management", expanded=True, icon="📇"):
            st.text_input(
                "Change Index", 
                placeholder=f"Default index: '{CONFIG['DEFAULT_INDEX']}'", 
                key="index_input", 
                on_change=selected_index,
                help="Enter a new index name to switch contexts"
            )
            
            # Check PDFs button
            if st.button(f"🔍 Check PDFs in '{st.session_state.get('index_input')}'"):
                check_pdfs_in_index()

        # File upload
        with st.expander("Upload PDF", expanded=True, icon="📄"):
            # Chunk size setting
            chunk_size = st.slider(
                "Chunk Size",
                min_value=CONFIG['MIN_CHUNK_SIZE'],
                max_value=CONFIG['MAX_CHUNK_SIZE'],
                value=st.session_state.get('chunk_size', CONFIG['DEFAULT_CHUNK_SIZE']),
                step=100,
                help="Size of text chunks for processing PDFs"
            )
            st.session_state.chunk_size = chunk_size

            # Overlap size setting
            overlap_size = st.slider(
                "Overlap Size",
                min_value=CONFIG['MIN_OVERLAP_SIZE'],
                max_value=st.session_state.chunk_size // 2,
                value=st.session_state.get('overlap_size', CONFIG['DEFAULT_OVERLAP_SIZE']),
                step=10,
                help="Overlap size for the chunking process"
            )
            st.session_state.overlap_size = overlap_size

            handle_file_upload()

        # System Prompt Settings & Vector Search Settings
        with st.expander("Chatbot Settings", expanded=True, icon="🧩"):
            # Vector search size setting
            vector_search_size = st.slider(
                "Vector Search Results",
                min_value=CONFIG['MIN_VECTOR_SEARCH_SIZE'],
                max_value=CONFIG['MAX_VECTOR_SEARCH_SIZE'],
                value=st.session_state.get('vector_search_size', CONFIG['DEFAULT_VECTOR_SEARCH_SIZE']),
                step=1,
                help="Number of relevant chunks to retrieve for context"
            )
            st.session_state.vector_search_size = vector_search_size
            
            # Show default prompt
            with st.expander("🔍 View Default Prompt", expanded=False):
                st.text_area(
                    "Default System Prompt",
                    value=CONFIG['SYSTEM_MESSAGE'],
                    height=100,
                    disabled=True,
                    key="default_prompt_display"
                )
            
            # Editable system prompt
            system_prompt = st.text_area(
                "Custom System Prompt",
                value=st.session_state.get('system_prompt', CONFIG['SYSTEM_MESSAGE']),
                height=120,
                key="system_prompt",
                on_change=on_system_prompt_change,
                help="Customize the AI assistant's behavior and instructions"
            )
            
            # System prompt controls
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Reset", help="Reset to default prompt"):
                    reset_system_prompt()
                    st.rerun()
            
            with col2:
                if st.button("✅ Apply", help="Apply current prompt"):
                    apply_system_prompt()
            
            # Show change indicator
            if st.session_state.get('system_prompt_changed', False):
                st.warning("⚠️ System prompt changed. Click 'Apply' to use new prompt.")
        
        # Chat management
        with st.expander("Chat Management", expanded=True, icon="💬"):
            # Display chat stats
            if st.session_state.display_messages:
                st.info(f"Messages: {len(st.session_state.display_messages)}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Clear Chat", help="Clear all chat history"):
                    clear_chat_history()
                    st.rerun()
            
            with col2:
                export_chat_history()

def main():
    """Main application function"""
    # Page configuration
    st.set_page_config(
        page_title="PDF Chatbot",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    display_index_badge()
    st.title("📚 PDF Chatbot")
    st.markdown("Ask questions about your uploaded PDFs and get contextual answers with references!")
    
    # Main chat interface
    display_chat_history()
    handle_chat_input()
    
    # Sidebar
    setup_sidebar()
    
    # Footer
    st.markdown("---")
    st.markdown("💡 **Tip:** Upload PDFs, ask questions, and get answers with references!")

if __name__ == "__main__":
    main()