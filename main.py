import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from collections import deque
import logging
import json
from classifier import AIClassifier
from reddit_stream import RedditStreamer
from database import save_comment, run_query, create_document, update_document, delete_document

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page Config
st.set_page_config(
    page_title="Reddit AI Detector",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for aesthetics
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .css-1d391kg {
        padding-top: 1rem;
    }
    .metric-card {
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .comment-card {
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        color: white;
    }
    .human-card {
        border-left: 5px solid #00ff00;
        background-color: #1c2b1c;
    }
    .ai-card {
        border-left: 5px solid #ff0000;
        background-color: #3b1c1c;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_classifier():
    """Load the classifier once and cache it."""
    return AIClassifier()

def main():
    st.title("🤖 Reddit Live AI Detector")
    st.markdown("Real-time stream analysis of Reddit comments to detect AI-generated text.")

    # Sidebar
    st.sidebar.header("Configuration")
    subreddit = st.sidebar.text_input("Subreddit", value="test")
    start_btn = st.sidebar.button("Start Streaming")
    stop_btn = st.sidebar.button("Stop Streaming") # Basic state control
    
    st.sidebar.divider()
    st.sidebar.subheader("Database Manager")
    
    crud_mode = st.sidebar.selectbox("Operation", ["Read (Query)", "Create (Insert)", "Update", "Delete"])
    
    if crud_mode == "Read (Query)":
        with st.sidebar.expander("Read", expanded=True):
            query_input = st.text_area("Filter (JSON)", value="{}", height=100, key="read_q")
            limit_input = st.number_input("Limit", value=10, min_value=1, max_value=100)
            if st.button("Find Documents"):
                try:
                    query_dict = json.loads(query_input)
                    results = run_query(query_dict, limit=limit_input)
                    st.sidebar.success(f"Found {len(results)} docs")
                    if results:
                        st.json(results)
                    else:
                        st.info("No results found.")
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")

    elif crud_mode == "Create (Insert)":
        with st.sidebar.expander("Create", expanded=True):
            doc_input = st.text_area("Document (JSON)", value='{"test": "data"}', height=100, key="create_q")
            if st.button("Insert Document"):
                try:
                    doc_dict = json.loads(doc_input)
                    result = create_document(doc_dict)
                    if "error" in result:
                        st.sidebar.error(result['error'])
                    else:
                        st.sidebar.success(f"Inserted ID: {result['inserted_id']}")
                        st.json(result)
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")

    elif crud_mode == "Update":
        with st.sidebar.expander("Update", expanded=True):
            filter_input = st.text_area("Filter (JSON)", value='{"test": "data"}', height=70, key="update_f")
            update_input = st.text_area("Update (JSON)", value='{"test": "updated"}', height=70, key="update_u")
            is_raw = st.sidebar.checkbox("Raw Update Operator?", value=False, help="Uncheck to wrap in $set")
            
            if st.button("Update Document"):
                try:
                    filter_dict = json.loads(filter_input)
                    update_dict = json.loads(update_input)
                    result = update_document(filter_dict, update_dict, is_raw)
                    if "error" in result:
                        st.sidebar.error(result['error'])
                    else:
                        st.sidebar.success(f"Modified: {result['modified_count']}")
                        st.json(result)
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")

    elif crud_mode == "Delete":
        with st.sidebar.expander("Delete", expanded=True):
            filter_input = st.text_area("Filter (JSON)", value='{"test": "updated"}', height=100, key="delete_f")
            if st.button("Delete Document"):
                try:
                    filter_dict = json.loads(filter_input)
                    result = delete_document(filter_dict)
                    if "error" in result:
                        st.sidebar.error(result['error'])
                    else:
                        st.sidebar.success(f"Deleted: {result['deleted_count']}")
                        st.json(result)
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")

    # Logic for session state
    if 'streaming' not in st.session_state:
        st.session_state.streaming = False
    if 'comments_data' not in st.session_state:
        st.session_state.comments_data = deque(maxlen=100) # Keep last 100 for stats
    if 'total_processed' not in st.session_state:
        st.session_state.total_processed = 0
    if 'total_ai' not in st.session_state:
        st.session_state.total_ai = 0
    if 'total_negative' not in st.session_state:
        st.session_state.total_negative = 0

    if start_btn:
        st.session_state.streaming = True
    if stop_btn:
        st.session_state.streaming = False

    # Layout: Stats on top, Feed below
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        total_metric = st.empty()
    with col2:
        ai_pct_metric = st.empty()
    with col3:
        human_pct_metric = st.empty()
    with col4:
        neg_metric = st.empty()
    with col5:
        last_pred_metric = st.empty()

    chart_placeholder = st.empty()
    feed_placeholder = st.empty()
    status_placeholder = st.empty()

    # Load resources
    try:
        with st.spinner("Loading AI Model (this may take a moment)..."):
            classifier = load_classifier()
    except Exception as e:
        st.error(f"Failed to load model: {e}")
        return

    streamer = RedditStreamer()

    if st.session_state.streaming:
        status_placeholder.info(f"Streaming r/{subreddit}...")
        
        # The Stream Loop
        # Note: In Streamlit, long running loops block interactions. 
        # This is a simple implementation. For production, asynchronous queues are better.
        try:
            for comment in streamer.stream_comments(subreddit):
                if not st.session_state.streaming:
                    break

                if "error" in comment:
                    status_placeholder.error(f"Error: {comment['error']}")
                    break

                # Classify
                prediction = classifier.predict(comment['body'])
                
                # Update Stats
                st.session_state.total_processed += 1
                is_ai = prediction['label'] == 'AI'
                if is_ai:
                    st.session_state.total_ai += 1
                
                is_negative = prediction['sentiment'] == 'NEGATIVE'
                if is_negative:
                    st.session_state.total_negative += 1
                
                # Save to MongoDB
                # Merge original comment data with prediction
                db_data = comment.copy()
                db_data.update({
                    'ai_label': prediction['label'],
                    'ai_score': prediction['score'],
                    'sentiment': prediction['sentiment'],
                    'sentiment_score': prediction['sentiment_score'],
                    'analyzed_at': datetime.utcnow()
                })
                save_comment(db_data)
                
                comment_entry = {
                    'author': comment['author'],
                    'body': comment['body'],
                    'label': prediction['label'],
                    'score': prediction['score'],
                    'sentiment': prediction['sentiment'],
                    'time': datetime.now().strftime("%H:%M:%S")
                }
                st.session_state.comments_data.appendleft(comment_entry) # Newest first

                # Update Metrics
                total = st.session_state.total_processed
                ai_count = st.session_state.total_ai
                human_count = total - ai_count
                neg_count = st.session_state.total_negative
                
                total_metric.metric("Processed", total)
                ai_pct_metric.metric("AI %", f"{(ai_count/total)*100:.1f}%" if total else "0%")
                human_pct_metric.metric("Human %", f"{(human_count/total)*100:.1f}%" if total else "0%")
                neg_metric.metric("Negative %", f"{(neg_count/total)*100:.1f}%" if total else "0%")
                last_pred_metric.metric("Last", prediction['label'], delta=f"{prediction['score']:.2f}")

                # Update Chart
                if len(st.session_state.comments_data) > 0:
                    df = pd.DataFrame(st.session_state.comments_data)
                    # Simple count over time or just recent history distribution
                    fig = px.pie(names=['AI', 'Human'], values=[ai_count, human_count], 
                                 title="Detection Distribution (Session)", hole=0.4,
                                 color_discrete_map={'AI':'red', 'Human':'green'})
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", height=300)
                    chart_placeholder.plotly_chart(fig, use_container_width=True)

                    # Time Series Chart
                    fig_time = px.scatter(df, x='time', y='score', color='label',
                                          title="Confidence Score / Time",
                                          color_discrete_map={'AI':'red', 'Human':'green'},
                                          range_y=[0, 1])
                    fig_time.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", height=300)
                    st.plotly_chart(fig_time, use_container_width=True)

                # Update Feed (Show last 5)
                with feed_placeholder.container():
                    # Clear previous content is automatic if we overwrite the placeholder content? 
                    # Actually, if we use a placeholder and write to it, it replaces.
                    # But for a list of items, we need to construct them inside the 'with'.
                    # Wait, st.empty() only holds one element. We need a container.
                    
                    # Better approach: Clear the placeholder first or just overwrite it with a new container context
                    pass 
                
                # To make this efficient in the loop, we construct the list and write it.
                # Since 'feed_placeholder' was an st.empty(), we can use it as a container context.
                with feed_placeholder.container():
                    for c in list(st.session_state.comments_data)[:10]:
                        # Use chat_message for native "feed" look
                        role = "assistant" if c['label'] == 'AI' else "user"
                        avatar = "🤖" if c['label'] == 'AI' else "👤"
                        
                        sent_emoji = "👍" if c['sentiment'] == 'POSITIVE' else "👎"
                        sentiment_text = f"**{c['sentiment']}**" if c['sentiment'] == 'NEGATIVE' else c['sentiment']
                        
                        with st.chat_message(role, avatar=avatar):
                            # Header line
                            st.markdown(f"**u/{c['author']}** • {c['label']} ({c['score']:.2f}) • {sent_emoji} {sentiment_text}")
                            st.write(c['body'])
                            st.caption(f"Posted at {c['time']}")
                
        except Exception as e:
            status_placeholder.error(f"Stream Crashed: {e}")
            st.session_state.streaming = False
    else:
        status_placeholder.warning("Stream stopped. Press Start to begin.")

if __name__ == "__main__":
    main()
