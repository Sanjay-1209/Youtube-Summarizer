import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
import requests
import plotly.express as px
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import time

# --- 1. PAGE CONFIGURATION AND STYLING ---
# This must be the first Streamlit command.
st.set_page_config(
    page_title="YouTube Comment Analyzer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply global styles for a cleaner look.
st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #F0F2F6;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF;
        }
        h1, h2, h3 {
            text-align: center;
        }
    </style>""", unsafe_allow_html=True)

# Download VADER lexicon for sentiment analysis if not already present.
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    with st.spinner("Downloading language model (one-time setup)..."):
        nltk.download('vader_lexicon')

# --- 2. API KEY MANAGEMENT & SIDEBAR UI ---

with st.sidebar:
    st.header("🔑 API Configuration")
    st.markdown("Enter your API keys below to activate the analyzer.")

    # Input for API Keys
    youtube_api_key = st.text_input("YouTube Data API v3 Key", type="password", help="Required for fetching YouTube comments.")
    gemini_api_key = st.text_input("Google Gemini API Key", type="password", help="Required for AI-powered summaries.")

    st.markdown("---")
    st.subheader("How to get your API keys:")
    st.markdown("""
    1.  **YouTube API Key:**
        - Go to the [Google Cloud Console](https://console.cloud.google.com/).
        - Create a new project.
        - Enable the "YouTube Data API v3" for your project.
        - Create credentials and choose "API Key".
        - [Full Guide Here](https://developers.google.com/youtube/v3/getting-started)

    2.  **Gemini API Key:**
        - Go to [Google AI Studio](https://aistudio.google.com/).
        - Sign in and click "Get API Key".
        - Create an API key in a new or existing project.

    ⚠️ **Important Note on Quotas:**
    The free YouTube Data API has a daily limit of **10,000 units**. Fetching comments from one video costs about 100 units. This app is optimized to use your quota efficiently.
    """)

# Store API keys in session state to persist them.
if youtube_api_key:
    st.session_state.youtube_api_key = youtube_api_key
if gemini_api_key:
    st.session_state.gemini_api_key = gemini_api_key

# --- 3. CORE FUNCTIONS (WITH PERFORMANCE CACHING) ---

@st.cache_data(show_spinner=False)
def fetch_comments(video_id: str, api_key: str, max_comments: int = 500) -> list | None:
    """
    Fetches comments from a YouTube video using the provided API key.
    Results are cached to prevent re-fetching for the same video.
    """
    if not api_key:
        st.error("YouTube API Key is missing. Please enter it in the sidebar.")
        return None
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        comments, next_page_token = [], None
        
        while len(comments) < max_comments:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                textFormat="plainText",
                maxResults=100,
                pageToken=next_page_token,
                order='time'
            )
            response = request.execute()
            
            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({'text': comment['textDisplay']})
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        return comments
    except HttpError as e:
        if "commentsDisabled" in str(e):
            st.error("Comments are disabled for this video.")
        else:
            st.error(f"Failed to fetch comments. Is your YouTube API key valid and enabled? (Error: {e})")
        return None

@st.cache_data
def analyze_sentiments(comments: list) -> pd.DataFrame:
    """
    Performs sentiment analysis on a list of comments.
    Caches results for performance.
    """
    sid = SentimentIntensityAnalyzer()
    df = pd.DataFrame(comments)
    df['compound'] = df['text'].apply(lambda text: sid.polarity_scores(text)['compound'])
    
    def classify_sentiment(compound):
        if compound >= 0.05: return 'Positive'
        elif compound <= -0.05: return 'Negative'
        else: return 'Neutral'
        
    df['sentiment'] = df['compound'].apply(classify_sentiment)
    return df

@st.cache_data(show_spinner="🧠 Generating AI summary...")
def generate_gemini_summary(comments_sample: tuple, api_key: str, custom_prompt: str = None) -> str:
    """
    Generates a summary using the Gemini API.
    Takes a tuple of comments to be cache-friendly.
    """
    if not api_key:
        st.error("Gemini API Key is missing. Please enter it in the sidebar.")
        return ""
        
    prompt = ""
    if custom_prompt:
        prompt = f"Based on the following YouTube comments, please provide a specific answer to this user's question: '{custom_prompt}'. Comments: {comments_sample}"
    else:
        prompt = f"Please provide a concise but insightful summary of the key themes, topics, and overall sentiment from the following YouTube comments. Identify what people liked and disliked. Comments: {comments_sample}"

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        with requests.post(url, headers=headers, json=data, timeout=60) as response:
            response.raise_for_status()
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to Gemini API. Check your network or API key. (Error: {e})")
        return "*Summary could not be generated due to a network error.*"
    except (KeyError, IndexError):
        return "*Could not parse a valid response from the Gemini API.*"

def extract_video_id(url: str) -> str | None:
    """Extracts YouTube video ID from various URL formats."""
    pattern = r'(?:https?:\/\/(?:www\.)?youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=))([^"&?/\s]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None


# --- 4. MAIN APPLICATION UI ---

st.title("⚡ YouTube Comment Analyzer")
st.markdown("### Instantly analyze video comments, gauge sentiment, and get AI-powered insights.")

# Check if API keys are provided before showing the main interface.
if 'youtube_api_key' not in st.session_state or 'gemini_api_key' not in st.session_state:
    st.warning("Please enter your API keys in the sidebar to begin.")
    st.stop()

# Main Application Tabs
tab1, tab2 = st.tabs(["📊 Video Analyzer", "✨ Custom Analyzer"])

with tab1:
    st.header("General Sentiment Analysis")
    video_url_1 = st.text_input("Enter a YouTube Video URL", key="url1", placeholder="e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    if st.button("Analyze Video Sentiment", key="analyze1", use_container_width=True):
        if not video_url_1:
            st.warning("Please enter a video URL.")
        else:
            video_id = extract_video_id(video_url_1)
            if not video_id:
                st.error("Invalid YouTube URL. Please enter a valid video link.")
            else:
                with st.spinner("Step 1/3: Fetching recent comments..."):
                    comments = fetch_comments(video_id, st.session_state.youtube_api_key)
                
                if comments:
                    with st.spinner("Step 2/3: Analyzing sentiment of comments..."):
                        # Introduce a small delay for a smoother UX flow
                        time.sleep(0.5)
                        sentiment_df = analyze_sentiments(comments)
                    
                    # Convert to tuple for caching in the next step
                    comments_for_summary = tuple(sentiment_df['text'].head(300))
                    
                    # This step uses its own spinner defined in the function decorator
                    ai_summary = generate_gemini_summary(comments_for_summary, st.session_state.gemini_api_key)

                    st.subheader("💡 AI-Powered Summary")
                    st.success(ai_summary, icon="🤖")

                    st.subheader("📊 Sentiment Breakdown")
                    sentiment_counts = sentiment_df['sentiment'].value_counts()
                    
                    # Layout for metrics and pie chart
                    col1, col2 = st.columns([1, 1.5])
                    with col1:
                        st.metric("✅ Positive Comments", sentiment_counts.get('Positive', 0))
                        st.metric("❌ Negative Comments", sentiment_counts.get('Negative', 0))
                        st.metric("😐 Neutral Comments", sentiment_counts.get('Neutral', 0))

                    with col2:
                        fig = px.pie(
                            values=sentiment_counts.values, 
                            names=sentiment_counts.index, 
                            color=sentiment_counts.index,
                            color_discrete_map={'Positive':'#2ECC71', 'Negative':'#E74C3C', 'Neutral':'#95A5A6'},
                            hole=0.3
                        )
                        fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
                        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Custom Query Analysis")
    video_url_2 = st.text_input("Enter a YouTube Video URL", key="url2", placeholder="e.g., https://www.youtube.com/watch?v=Rok8W2agHcw")
    custom_prompt = st.text_area("What specific question do you have about the comments?", placeholder="e.g., What are the main feature requests or bug reports mentioned?")

    if st.button("Get Custom Insights", key="analyze2", use_container_width=True):
        if not video_url_2 or not custom_prompt:
            st.warning("Please enter both a video URL and your custom question.")
        else:
            video_id = extract_video_id(video_url_2)
            if not video_id:
                st.error("Invalid YouTube URL. Please enter a valid video link.")
            else:
                with st.spinner("Fetching comments for your custom query..."):
                    comments = fetch_comments(video_id, st.session_state.youtube_api_key)

                if comments:
                    comments_for_summary = tuple(pd.DataFrame(comments)['text'].head(300))
                    ai_response = generate_gemini_summary(comments_for_summary, st.session_state.gemini_api_key, custom_prompt)
                    
                    st.subheader("🔮 AI Response to Your Query")
                    st.info(ai_response, icon="🧠")