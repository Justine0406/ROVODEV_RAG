"""
Thesis Panelist AI - Main Streamlit Application
"""

import streamlit as st
import time
from io import BytesIO

# Import utility modules
from utils.pdf_processor import validate_pdf, extract_text_with_metadata, chunk_text
from utils.embeddings import load_embedding_model, generate_embeddings, create_vector_store, retrieve_relevant_chunks
from utils.groq_client import (
    get_groq_client, generate_critique, parse_critique_for_issues,
    parse_rewrite_suggestions, parse_section_summaries, test_groq_connection
)
from utils.annotator import create_annotated_pdf, add_summary_page
from utils.prompts import build_prompt


# Page configuration
st.set_page_config(
    page_title="Thesis Panelist AI - Professional Thesis Review",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4CAF50;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        color: #155724;
    }
    </style>
""", unsafe_allow_html=True)


# Initialize session state
def initialize_session_state():
    """Initialize all session state variables."""
    if 'pdf_processed' not in st.session_state:
        st.session_state.pdf_processed = False
    if 'critique_generated' not in st.session_state:
        st.session_state.critique_generated = False
    if 'waitlist_count' not in st.session_state:
        st.session_state.waitlist_count = 0
    if 'pdf_data' not in st.session_state:
        st.session_state.pdf_data = None
    if 'chunks' not in st.session_state:
        st.session_state.chunks = None
    if 'collection' not in st.session_state:
        st.session_state.collection = None
    if 'critique_text' not in st.session_state:
        st.session_state.critique_text = ""
    if 'annotated_pdf' not in st.session_state:
        st.session_state.annotated_pdf = None
    if 'last_request_time' not in st.session_state:
        st.session_state.last_request_time = 0
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None


def process_pdf(pdf_bytes, file_name):
    """Process uploaded PDF and create vector store."""
    try:
        # Validate PDF
        is_valid, error_msg = validate_pdf(pdf_bytes)
        if not is_valid:
            st.error(f"❌ {error_msg}")
            return False
        
        # Extract text
        with st.spinner("📄 Extracting text from PDF..."):
            pdf_data = extract_text_with_metadata(pdf_bytes)
            st.session_state.pdf_data = pdf_data
        
        st.success(f"✅ Extracted {pdf_data['total_pages']} pages ({pdf_data['total_chars']:,} characters)")
        
        # Chunk text
        with st.spinner("✂️ Chunking text..."):
            chunks = chunk_text(pdf_data['pages'])
            st.session_state.chunks = chunks
        
        st.success(f"✅ Created {len(chunks)} text chunks")
        
        # Generate embeddings
        with st.spinner("🧠 Generating embeddings..."):
            model = load_embedding_model()
            embeddings = generate_embeddings(chunks, model)
        
        st.success(f"✅ Generated embeddings")
        
        # Create vector store
        with st.spinner("💾 Creating vector store..."):
            collection = create_vector_store(chunks, embeddings)
            st.session_state.collection = collection
        
        st.success("✅ Vector store ready!")
        
        st.session_state.pdf_processed = True
        st.session_state.uploaded_file_name = file_name
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error processing PDF: {str(e)}")
        return False


def generate_review(groq_api_key, mode, custom_query=None):
    """Generate critique using RAG and Groq."""
    try:
        # Rate limiting check
        time_since_last = time.time() - st.session_state.last_request_time
        if time_since_last < 5:
            st.warning("⏳ Please wait a moment between requests (rate limiting)")
            time.sleep(5 - time_since_last)
        
        # Get embedding model and collection
        model = load_embedding_model()
        collection = st.session_state.collection
        
        # Determine query for retrieval
        if custom_query and custom_query.strip():
            retrieval_query = custom_query
            prompt_mode = "custom"
        else:
            # Use mode-specific query
            mode_queries = {
                "Full Panelist Review": "research methodology problem statement objectives findings conclusions",
                "Methodology Check": "research design methodology sampling data collection analysis validity",
                "Writing Quality": "grammar writing style clarity structure flow citations",
                "Citation & References": "citations references bibliography in-text citations reference list",
                "Consistency Check": "terminology tense format spelling acronyms consistency",
                "Research Alignment": "research questions objectives methodology variables analysis conclusions alignment"
            }
            retrieval_query = mode_queries.get(mode, mode_queries["Full Panelist Review"])

            # Map mode names to prompt mode identifiers
            mode_mapping = {
                "Full Panelist Review": "full_review",
                "Methodology Check": "methodology",
                "Writing Quality": "writing_quality",
                "Citation & References": "citation_check",
                "Consistency Check": "consistency_check",
                "Research Alignment": "alignment_check"
            }
            prompt_mode = mode_mapping.get(mode, "full_review")
        
        # Retrieve relevant chunks
        with st.spinner("🔍 Retrieving relevant sections..."):
            relevant_chunks = retrieve_relevant_chunks(retrieval_query, collection, model, top_k=5)
        
        if not relevant_chunks:
            st.error("❌ Could not retrieve relevant sections. Please try again.")
            return
        
        st.success(f"✅ Retrieved {len(relevant_chunks)} relevant sections")
        
        # Build prompt
        prompt = build_prompt(prompt_mode, relevant_chunks, custom_query if custom_query else None)
        
        # Generate critique with streaming
        groq_client = get_groq_client(groq_api_key)
        
        st.subheader("📝 Generated Review")
        critique_placeholder = st.empty()
        full_critique = ""
        
        with st.spinner("🤖 Generating critique..."):
            try:
                stream = generate_critique(groq_client, prompt, stream=True)
                
                for chunk in stream:
                    full_critique += chunk
                    critique_placeholder.markdown(full_critique)
                
            except Exception as e:
                st.error(f"❌ Error generating critique: {str(e)}")
                st.info("💡 Tip: Check your API key or try again in a moment")
                return
        
        st.session_state.critique_text = full_critique
        st.session_state.critique_generated = True
        st.session_state.last_request_time = time.time()
        
        st.success("✅ Review generated successfully!")
        
        # Parse issues, rewrites, and section summaries for advanced annotations
        with st.spinner("🔍 Analyzing feedback for annotations..."):
            issues = parse_critique_for_issues(full_critique)
            rewrites = parse_rewrite_suggestions(full_critique)
            section_summaries = parse_section_summaries(full_critique)

        # Show annotation statistics
        stats_cols = st.columns(4)
        with stats_cols[0]:
            st.metric("Issues Found", len(issues))
        with stats_cols[1]:
            st.metric("Rewrites", len(rewrites))
        with stats_cols[2]:
            st.metric("Section Reviews", len(section_summaries))
        with stats_cols[3]:
            critical_count = sum(1 for i in issues if i.get('severity') == 'critical')
            st.metric("Critical Issues", critical_count, delta_color="inverse")

        # Create enhanced annotated PDF
        if issues or rewrites or section_summaries:
            with st.spinner("✏️ Creating professional annotated PDF..."):
                try:
                    # Get original PDF bytes
                    original_pdf = st.session_state.get('original_pdf_bytes')
                    if original_pdf:
                        annotated_pdf = create_annotated_pdf(
                            original_pdf,
                            issues,
                            section_summaries=section_summaries if section_summaries else None,
                            rewrites=rewrites if rewrites else None,
                            include_legend=True
                        )
                        st.session_state.annotated_pdf = annotated_pdf
                        st.success("✅ Professional annotated PDF ready with color-coded highlights, margin comments, and rewrite suggestions!")
                except Exception as e:
                    st.warning(f"⚠️ Could not create annotations: {str(e)}")
        
    except Exception as e:
        st.error(f"❌ Error generating review: {str(e)}")


# Initialize session state
initialize_session_state()

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    # API Key input
    groq_api_key = st.text_input(
        "Groq API Key",
        type="password",
        help="Get free API key at https://console.groq.com",
        placeholder="gsk_..."
    )
    
    if not groq_api_key:
        st.warning("⚠️ Enter your Groq API key to continue")
        st.info("💡 Free tier includes 14,400 requests/day")
        st.markdown("[Get API Key →](https://console.groq.com)")
    else:
        # Test API key button
        if st.button("🔐 Test API Key"):
            with st.spinner("Testing connection..."):
                is_valid, message = test_groq_connection(groq_api_key)
                if is_valid:
                    st.success(message)
                else:
                    st.error(message)
    
    st.divider()
    
    # Upload section
    st.subheader("📄 Upload Thesis")
    uploaded_file = st.file_uploader(
        "Choose PDF file",
        type=['pdf'],
        help="Max 10MB, under 50 pages recommended"
    )
    
    if uploaded_file:
        # Check if it's a new file
        if st.session_state.uploaded_file_name != uploaded_file.name:
            # Reset processing state for new file
            st.session_state.pdf_processed = False
            st.session_state.critique_generated = False
            st.session_state.annotated_pdf = None
        
        # Store original PDF bytes
        pdf_bytes = uploaded_file.read()
        st.session_state.original_pdf_bytes = pdf_bytes
        
        if not st.session_state.pdf_processed:
            if st.button("🚀 Process PDF", type="primary"):
                process_pdf(pdf_bytes, uploaded_file.name)
        else:
            st.success(f"✅ Processed: {uploaded_file.name}")
            if st.button("🔄 Process New File"):
                st.session_state.pdf_processed = False
                st.rerun()
    
    st.divider()
    
    # Waitlist section
    st.subheader("🚀 Join Waitlist")
    st.write("Want unlimited reviews?")
    waitlist_email = st.text_input("Email address", key="waitlist_email")
    if st.button("Join Waitlist"):
        if waitlist_email and '@' in waitlist_email:
            st.session_state.waitlist_count += 1
            st.success("✅ You're on the list!")
            st.balloons()
        else:
            st.error("Please enter a valid email")
    
    st.caption(f"👥 {st.session_state.waitlist_count} people signed up")

# Main area
st.markdown('<div class="main-header">🎓 Thesis Panelist AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Get Expert Thesis Feedback in Minutes</div>', unsafe_allow_html=True)

# Value propositions
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### ✅ Comprehensive")
    st.write("Critique like a real committee member")
with col2:
    st.markdown("### ✅ Visual")
    st.write("Annotations showing what to fix")
with col3:
    st.markdown("### ✅ Free")
    st.write("Demo - no signup required")

st.divider()

# Tabs for different sections
tab1, tab2, tab3 = st.tabs(["📝 Review", "📊 Demo Example", "ℹ️ How It Works"])

with tab1:
    if not st.session_state.pdf_processed:
        st.info("👈 Upload your thesis PDF in the sidebar to get started")
        
        # Show example prompt
        st.subheader("What You'll Get")

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**📝 Basic Reviews:**")
            st.markdown("""
            - 🔍 **Full Panelist Review** - Comprehensive analysis
            - 🧪 **Methodology Check** - Research design review
            - ✍️ **Writing Quality** - Grammar & clarity check
            """)

        with col_b:
            st.markdown("**🔬 Advanced Analysis:**")
            st.markdown("""
            - 📚 **Citation & References** - Validate all citations
            - ✅ **Consistency Check** - Find inconsistencies
            - 🎯 **Research Alignment** - Verify component alignment
            """)

        st.markdown("- 💬 **Custom Questions** - Ask specific questions about your research")
        
    else:
        # Show review interface
        st.subheader("🎯 Select Review Mode")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Mode selection with tabs for better organization
            review_type = st.selectbox(
                "Select Review Type:",
                ["Basic Reviews", "Advanced Analysis"],
                index=0
            )

            if review_type == "Basic Reviews":
                mode = st.radio(
                    "Choose focus area:",
                    ["Full Panelist Review", "Methodology Check", "Writing Quality"],
                    horizontal=True,
                    help="Standard review modes for quick feedback"
                )
            else:  # Advanced Analysis
                mode = st.radio(
                    "Choose advanced analysis:",
                    ["Citation & References", "Consistency Check", "Research Alignment"],
                    horizontal=True,
                    help="Deep analysis of specific aspects"
                )

            custom_query = st.text_area(
                "Or ask a specific question (optional):",
                placeholder="e.g., 'Is my sampling method appropriate?' or 'Are my conclusions well-supported?'",
                height=80
            )
            
            if st.button("🔍 Generate Review", type="primary", disabled=not groq_api_key):
                if not groq_api_key:
                    st.error("❌ Please enter your Groq API key in the sidebar")
                else:
                    generate_review(groq_api_key, mode, custom_query)
        
        with col2:
            st.subheader("📊 Document Info")
            if st.session_state.pdf_data:
                pdf_data = st.session_state.pdf_data
                st.metric("Pages", pdf_data['total_pages'])
                st.metric("Characters", f"{pdf_data['total_chars']:,}")
                st.metric("Chunks", len(st.session_state.chunks))
        
        # Show critique if generated
        if st.session_state.critique_generated and st.session_state.critique_text:
            st.divider()
            st.subheader("📝 Your Review")
            st.markdown(st.session_state.critique_text)
            
            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                # Download critique as text
                st.download_button(
                    label="📥 Download Review (TXT)",
                    data=st.session_state.critique_text,
                    file_name="thesis_review.txt",
                    mime="text/plain"
                )
            
            with col2:
                # Download annotated PDF if available
                if st.session_state.annotated_pdf:
                    st.download_button(
                        label="📥 Download Annotated PDF",
                        data=st.session_state.annotated_pdf,
                        file_name="thesis_annotated.pdf",
                        mime="application/pdf"
                    )

with tab2:
    st.subheader("📊 Example Output")
    st.write("Here's what you'll get after processing your thesis:")
    
    st.markdown("""
    ### Sample Critique
    
    **## Major Issues**
    
    1. **Unclear Research Problem**: The problem statement in the introduction lacks specificity. 
       - *"The study aims to investigate factors affecting student performance"* is too broad.
       - **Suggestion**: Specify which factors, which aspects of performance, and in what context.
    
    2. **Methodology Gap**: The sampling method is mentioned but not justified.
       - *"50 students were selected"* - How? Random? Convenience? Purposive?
       - **Suggestion**: Explain your sampling strategy and justify why it's appropriate.
    
    **## Writing Quality**
    
    - Several passive voice constructions could be made more direct
    - Inconsistent citation format (mix of APA and Chicago)
    - Some paragraphs exceed 200 words - consider breaking them up
    
    **## Suggestions for Improvement**
    
    1. Revise problem statement to be specific and measurable
    2. Add a section justifying your sampling methodology
    3. Ensure consistent citation formatting throughout
    4. Review for passive voice and simplify where possible
    """)
    
    st.info("💡 Your actual review will be customized to your specific thesis content!")

with tab3:
    st.subheader("ℹ️ How It Works")
    st.markdown("""
    ### The Process
    
    1. **📤 Upload** - Your thesis is processed securely (not saved anywhere)
    2. **🧠 Analyze** - AI reads and understands your content using advanced embeddings
    3. **💬 Critique** - Expert-level feedback generated based on your selected mode
    4. **✏️ Annotate** - Visual highlights added to problematic sections in the PDF
    5. **📥 Download** - Get annotated PDF and text review
    
    ### Technology Stack
    
    - **LLM**: Groq API (llama-3.3-70b-versatile)
    - **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
    - **Vector Store**: ChromaDB (in-memory)
    - **PDF Processing**: PyMuPDF
    
    ### Privacy & Security
    
    🔒 **Your document is processed in memory only.**
    - Nothing is saved or stored on our servers
    - No database, no file storage
    - Session data resets when you refresh the page
    
    ### Limitations (MVP Phase)
    
    - Max 10MB file size
    - Recommended under 50 pages for optimal performance
    - Requires your own Groq API key (free tier available)
    - No persistent storage between sessions
    
    ### Get Your Free API Key
    
    1. Visit [console.groq.com](https://console.groq.com)
    2. Sign up for a free account
    3. Generate an API key
    4. Paste it in the sidebar
    
    Free tier includes **14,400 requests per day**! 🎉
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>Built with ❤️ using Streamlit, Groq, and ChromaDB</p>
    <p>Phase 1 MVP - Validation Demo</p>
</div>
""", unsafe_allow_html=True)

