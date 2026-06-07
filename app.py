import streamlit as st
import requests
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Multi-AI Search Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 16px;
        font-weight: bold;
    }
    .response-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        min-height: 250px;
        overflow-y: auto;
        max-height: 500px;
    }
    .claude { border-left-color: #3b82f6; }
    .mistral { border-left-color: #a855f7; }
    .perplexity { border-left-color: #10b981; }
    .header-text {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

if 'responses' not in st.session_state:
    st.session_state.responses = {}

if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

# Get API keys from Streamlit secrets
def get_api_keys():
    return {
        'claude': st.secrets.get('CLAUDE_API_KEY', ''),
        'mistral': st.secrets.get('MISTRAL_API_KEY', ''),
        'perplexity': st.secrets.get('PERPLEXITY_API_KEY', ''),
    }

def mask_key(key):
    """Show first 6 and last 4 chars for debugging without leaking the full key."""
    if not key or len(key) < 10:
        return "(empty or too short)"
    return f"{key[:6]}...{key[-4:]}"

# Claude API call
def call_claude(query, api_key):
    try:
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
        }
        data = {
            'model': 'claude-3-5-sonnet-20241022',
            'max_tokens': 1024,
            'messages': [{'role': 'user', 'content': query}]
        }
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result['content'][0]['text']
    except requests.exceptions.HTTPError as e:
        return f"❌ Error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Mistral API call
def call_mistral(query, api_key):
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }
        data = {
            'model': 'mistral-small-latest',
            'messages': [{'role': 'user', 'content': query}],
            'max_tokens': 1024,
        }
        response = requests.post(
            'https://api.mistral.ai/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.exceptions.HTTPError as e:
        return f"❌ Error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Perplexity API call (web search)
def call_perplexity(query, api_key):
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }
        data = {
            'model': 'sonar-small-online',
            'messages': [
                {'role': 'system', 'content': 'Be precise and concise.'},
                {'role': 'user', 'content': query}
            ],
            'max_tokens': 1024,
        }
        response = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.exceptions.HTTPError as e:
        return f"❌ Error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Header
st.markdown('<p class="header-text">🔍 Multi-AI Search Engine</p>', unsafe_allow_html=True)
st.markdown("Compare responses from **Claude**, **Mistral**, and **Perplexity** • Real-time web search • Save your searches")
st.markdown("---")

# Check API Keys
api_keys = get_api_keys()

# Debug panel in sidebar (expandable)
with st.sidebar:
    st.title("⚙️ Settings")
    
    st.subheader("🔐 API Key Status")
    for name, key in api_keys.items():
        if key:
            st.success(f"{name.capitalize()}: key loaded ({mask_key(key)})")
        else:
            st.error(f"{name.capitalize()}: key **missing**")
    
    st.session_state.debug_mode = st.toggle("Show full debug errors", value=False)
    
    st.markdown("---")
    
    if not any(api_keys.values()):
        st.warning("⚠️ API keys not configured!")
        st.info("""
        **How to add API keys:**
        
        **Option A: Streamlit Cloud**
        1. Go to your app dashboard → Manage app
        2. Click **Secrets** (🔐)
        3. Add:
        ```toml
        CLAUDE_API_KEY = "your-key-here"
        MISTRAL_API_KEY = "your-key-here"
        PERPLEXITY_API_KEY = "your-key-here"
        ```
        
        **Option B: Local run**
        Create `.streamlit/secrets.toml` in your project root with the same contents.
        """)
        st.stop()
    
    st.subheader("Select AI Models")
    use_claude = st.checkbox("🤖 Claude", value=True, help="Best for reasoning and complex tasks")
    use_mistral = st.checkbox("⚡ Mistral", value=True, help="Fast and efficient responses")
    use_perplexity = st.checkbox("🔍 Perplexity (Web Search)", value=True, help="Real-time web search")
    
    st.markdown("---")
    st.subheader("📋 Search History")
    if st.session_state.search_history:
        selected_history = st.selectbox(
            "Previous searches:",
            range(len(st.session_state.search_history)),
            format_func=lambda x: st.session_state.search_history[x]['query'][:50] + "..."
        )
        if st.button("Load Selected Search"):
            search = st.session_state.search_history[selected_history]
            st.session_state.responses = search['responses']
            st.rerun()
        
        if st.button("Clear History"):
            st.session_state.search_history = []
            st.rerun()
    else:
        st.info("No search history yet")
    
    st.markdown("---")
    st.subheader("📊 Stats")
    st.metric("Total Searches", len(st.session_state.search_history))
    st.metric("API Keys Set", sum(1 for k in api_keys.values() if k))

# Main content
st.subheader("🔍 Search Multiple AI Models")

col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_area(
        "What would you like to search for?",
        placeholder="Ask anything... (coding help, explanations, ideas, analysis, etc.)",
        height=100,
        label_visibility="visible"
    )
with col2:
    search_button = st.button("🔍 Search", use_container_width=True, type="primary")

if search_button and query:
    st.session_state.responses = {}
    
    # Create progress container
    progress_container = st.container()
    with progress_container:
        col_claude, col_mistral, col_perplexity = st.columns(3)
        
        with col_claude:
            if use_claude and api_keys['claude']:
                with st.spinner("Claude is thinking..."):
                    response = call_claude(query, api_keys['claude'])
                    st.session_state.responses['claude'] = response
        
        with col_mistral:
            if use_mistral and api_keys['mistral']:
                with st.spinner("Mistral is thinking..."):
                    response = call_mistral(query, api_keys['mistral'])
                    st.session_state.responses['mistral'] = response
        
        with col_perplexity:
            if use_perplexity and api_keys['perplexity']:
                with st.spinner("Searching the web..."):
                    response = call_perplexity(query, api_keys['perplexity'])
                    st.session_state.responses['perplexity'] = response
    
    # Save to history
    st.session_state.search_history.insert(0, {
        'query': query,
        'responses': st.session_state.responses,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    st.success("✅ Search complete!")

# Display responses
if st.session_state.responses:
    st.markdown("---")
    st.subheader("📊 Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'claude' in st.session_state.responses:
            st.markdown("### 🤖 Claude")
            st.markdown(f'<div class="response-box claude">{st.session_state.responses["claude"]}</div>', 
                       unsafe_allow_html=True)
            if st.button("📋 Copy Claude", key="copy_claude"):
                st.code(st.session_state.responses["claude"], language="markdown")
    
    with col2:
        if 'mistral' in st.session_state.responses:
            st.markdown("### ⚡ Mistral")
            st.markdown(f'<div class="response-box mistral">{st.session_state.responses["mistral"]}</div>', 
                       unsafe_allow_html=True)
            if st.button("📋 Copy Mistral", key="copy_mistral"):
                st.code(st.session_state.responses["mistral"], language="markdown")
    
    with col3:
        if 'perplexity' in st.session_state.responses:
            st.markdown("### 🔍 Perplexity (Web)")
            st.markdown(f'<div class="response-box perplexity">{st.session_state.responses["perplexity"]}</div>', 
                       unsafe_allow_html=True)
            if st.button("📋 Copy Perplexity", key="copy_perplexity"):
                st.code(st.session_state.responses["perplexity"], language="markdown")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 14px;">
    <p>💡 Free Multi-AI Search Engine | Compare Claude, Mistral & Perplexity</p>
    <p>🔐 Your API keys are kept secure and never logged</p>
</div>
""", unsafe_allow_html=True)
