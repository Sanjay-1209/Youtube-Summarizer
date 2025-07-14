# # import streamlit as st
# # import pandas as pd
# # from googleapiclient.discovery import build
# # from googleapiclient.errors import HttpError
# # import re
# # import requests
# # import plotly.express as px
# # from nltk.sentiment.vader import SentimentIntensityAnalyzer
# # import nltk
# # import time

# # # --- 1. PAGE CONFIGURATION AND STYLING ---
# # # This must be the first Streamlit command.
# # st.set_page_config(
# #     page_title="YouTube Comment Analyzer",
# #     page_icon="⚡",
# #     layout="wide",
# #     initial_sidebar_state="expanded",
# # )

# # # Apply global styles for a cleaner look.
# # st.markdown("""
# #     <style>
# #         .stTabs [data-baseweb="tab-list"] {
# #             gap: 24px;
# #         }
# #         .stTabs [data-baseweb="tab"] {
# #             height: 50px;
# #             white-space: pre-wrap;
# #             background-color: #F0F2F6;
# #             border-radius: 4px 4px 0px 0px;
# #             gap: 1px;
# #             padding-top: 10px;
# #             padding-bottom: 10px;
# #         }
# #         .stTabs [aria-selected="true"] {
# #             background-color: #FFFFFF;
# #         }
# #         h1, h2, h3 {
# #             text-align: center;
# #         }
# #     </style>""", unsafe_allow_html=True)

# # # Download VADER lexicon for sentiment analysis if not already present.
# # try:
# #     nltk.data.find('sentiment/vader_lexicon.zip')
# # except LookupError:
# #     with st.spinner("Downloading language model (one-time setup)..."):
# #         nltk.download('vader_lexicon')

# # # --- 2. API KEY MANAGEMENT & SIDEBAR UI ---

# # with st.sidebar:
# #     st.header("🔑 API Configuration")
# #     st.markdown("Enter your API keys below to activate the analyzer.")

# #     # Input for API Keys
# #     youtube_api_key = st.text_input("YouTube Data API v3 Key", type="password", help="Required for fetching YouTube comments.")
# #     gemini_api_key = st.text_input("Google Gemini API Key", type="password", help="Required for AI-powered summaries.")

# #     st.markdown("---")
# #     st.subheader("How to get your API keys:")
# #     st.markdown("""
# #     1.  **YouTube API Key:**
# #         - Go to the [Google Cloud Console](https://console.cloud.google.com/).
# #         - Create a new project.
# #         - Enable the "YouTube Data API v3" for your project.
# #         - Create credentials and choose "API Key".
# #         - [Full Guide Here](https://developers.google.com/youtube/v3/getting-started)

# #     2.  **Gemini API Key:**
# #         - Go to [Google AI Studio](https://aistudio.google.com/).
# #         - Sign in and click "Get API Key".
# #         - Create an API key in a new or existing project.

# #     ⚠️ **Important Note on Quotas:**
# #     The free YouTube Data API has a daily limit of **10,000 units**. Fetching comments from one video costs about 100 units. This app is optimized to use your quota efficiently.
# #     """)

# # # Store API keys in session state to persist them.
# # if youtube_api_key:
# #     st.session_state.youtube_api_key = youtube_api_key
# # if gemini_api_key:
# #     st.session_state.gemini_api_key = gemini_api_key

# # # --- 3. CORE FUNCTIONS (WITH PERFORMANCE CACHING) ---

# # @st.cache_data(show_spinner=False)
# # def fetch_comments(video_id: str, api_key: str, max_comments: int = 500) -> list | None:
# #     """
# #     Fetches comments from a YouTube video using the provided API key.
# #     Results are cached to prevent re-fetching for the same video.
# #     """
# #     if not api_key:
# #         st.error("YouTube API Key is missing. Please enter it in the sidebar.")
# #         return None
# #     try:
# #         youtube = build('youtube', 'v3', developerKey=api_key)
# #         comments, next_page_token = [], None
        
# #         while len(comments) < max_comments:
# #             request = youtube.commentThreads().list(
# #                 part="snippet",
# #                 videoId=video_id,
# #                 textFormat="plainText",
# #                 maxResults=100,
# #                 pageToken=next_page_token,
# #                 order='time'
# #             )
# #             response = request.execute()
            
# #             for item in response.get('items', []):
# #                 comment = item['snippet']['topLevelComment']['snippet']
# #                 comments.append({'text': comment['textDisplay']})
            
# #             next_page_token = response.get('nextPageToken')
# #             if not next_page_token:
# #                 break
        
# #         return comments
# #     except HttpError as e:
# #         if "commentsDisabled" in str(e):
# #             st.error("Comments are disabled for this video.")
# #         else:
# #             st.error(f"Failed to fetch comments. Is your YouTube API key valid and enabled? (Error: {e})")
# #         return None

# # @st.cache_data
# # def analyze_sentiments(comments: list) -> pd.DataFrame:
# #     """
# #     Performs sentiment analysis on a list of comments.
# #     Caches results for performance.
# #     """
# #     sid = SentimentIntensityAnalyzer()
# #     df = pd.DataFrame(comments)
# #     df['compound'] = df['text'].apply(lambda text: sid.polarity_scores(text)['compound'])
    
# #     def classify_sentiment(compound):
# #         if compound >= 0.05: return 'Positive'
# #         elif compound <= -0.05: return 'Negative'
# #         else: return 'Neutral'
        
# #     df['sentiment'] = df['compound'].apply(classify_sentiment)
# #     return df

# # @st.cache_data(show_spinner="🧠 Generating AI summary...")
# # def generate_gemini_summary(comments_sample: tuple, api_key: str, custom_prompt: str = None) -> str:
# #     """
# #     Generates a summary using the Gemini API.
# #     Takes a tuple of comments to be cache-friendly.
# #     """
# #     if not api_key:
# #         st.error("Gemini API Key is missing. Please enter it in the sidebar.")
# #         return ""
        
# #     prompt = ""
# #     if custom_prompt:
# #         prompt = f"Based on the following YouTube comments, please provide a specific answer to this user's question: '{custom_prompt}'. Comments: {comments_sample}"
# #     else:
# #         prompt = f"Please provide a concise but insightful summary of the key themes, topics, and overall sentiment from the following YouTube comments. Identify what people liked and disliked. Comments: {comments_sample}"

# #     try:
# #         url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
# #         headers = {'Content-Type': 'application/json'}
# #         data = {"contents": [{"parts": [{"text": prompt}]}]}
        
# #         with requests.post(url, headers=headers, json=data, timeout=60) as response:
# #             response.raise_for_status()
# #             return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()

# #     except requests.exceptions.RequestException as e:
# #         st.error(f"Failed to connect to Gemini API. Check your network or API key. (Error: {e})")
# #         return "*Summary could not be generated due to a network error.*"
# #     except (KeyError, IndexError):
# #         return "*Could not parse a valid response from the Gemini API.*"

# # def extract_video_id(url: str) -> str | None:
# #     """Extracts YouTube video ID from various URL formats."""
# #     pattern = r'(?:https?:\/\/(?:www\.)?youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=))([^"&?/\s]{11})'
# #     match = re.search(pattern, url)
# #     return match.group(1) if match else None


# # # --- 4. MAIN APPLICATION UI ---

# # st.title("⚡ YouTube Comment Analyzer")
# # st.markdown("### Instantly analyze video comments, gauge sentiment, and get AI-powered insights.")

# # # Check if API keys are provided before showing the main interface.
# # if 'youtube_api_key' not in st.session_state or 'gemini_api_key' not in st.session_state:
# #     st.warning("Please enter your API keys in the sidebar to begin.")
# #     st.stop()

# # # Main Application Tabs
# # tab1, tab2 = st.tabs(["📊 Video Analyzer", "✨ Custom Analyzer"])

# # with tab1:
# #     st.header("General Sentiment Analysis")
# #     video_url_1 = st.text_input("Enter a YouTube Video URL", key="url1", placeholder="e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ")

# #     if st.button("Analyze Video Sentiment", key="analyze1", use_container_width=True):
# #         if not video_url_1:
# #             st.warning("Please enter a video URL.")
# #         else:
# #             video_id = extract_video_id(video_url_1)
# #             if not video_id:
# #                 st.error("Invalid YouTube URL. Please enter a valid video link.")
# #             else:
# #                 with st.spinner("Step 1/3: Fetching recent comments..."):
# #                     comments = fetch_comments(video_id, st.session_state.youtube_api_key)
                
# #                 if comments:
# #                     with st.spinner("Step 2/3: Analyzing sentiment of comments..."):
# #                         # Introduce a small delay for a smoother UX flow
# #                         time.sleep(0.5)
# #                         sentiment_df = analyze_sentiments(comments)
                    
# #                     # Convert to tuple for caching in the next step
# #                     comments_for_summary = tuple(sentiment_df['text'].head(300))
                    
# #                     # This step uses its own spinner defined in the function decorator
# #                     ai_summary = generate_gemini_summary(comments_for_summary, st.session_state.gemini_api_key)

# #                     st.subheader("💡 AI-Powered Summary")
# #                     st.success(ai_summary, icon="🤖")

# #                     st.subheader("📊 Sentiment Breakdown")
# #                     sentiment_counts = sentiment_df['sentiment'].value_counts()
                    
# #                     # Layout for metrics and pie chart
# #                     col1, col2 = st.columns([1, 1.5])
# #                     with col1:
# #                         st.metric("✅ Positive Comments", sentiment_counts.get('Positive', 0))
# #                         st.metric("❌ Negative Comments", sentiment_counts.get('Negative', 0))
# #                         st.metric("😐 Neutral Comments", sentiment_counts.get('Neutral', 0))

# #                     with col2:
# #                         fig = px.pie(
# #                             values=sentiment_counts.values, 
# #                             names=sentiment_counts.index, 
# #                             color=sentiment_counts.index,
# #                             color_discrete_map={'Positive':'#2ECC71', 'Negative':'#E74C3C', 'Neutral':'#95A5A6'},
# #                             hole=0.3
# #                         )
# #                         fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
# #                         st.plotly_chart(fig, use_container_width=True)

# # with tab2:
# #     st.header("Custom Query Analysis")
# #     video_url_2 = st.text_input("Enter a YouTube Video URL", key="url2", placeholder="e.g., https://www.youtube.com/watch?v=Rok8W2agHcw")
# #     custom_prompt = st.text_area("What specific question do you have about the comments?", placeholder="e.g., What are the main feature requests or bug reports mentioned?")

# #     if st.button("Get Custom Insights", key="analyze2", use_container_width=True):
# #         if not video_url_2 or not custom_prompt:
# #             st.warning("Please enter both a video URL and your custom question.")
# #         else:
# #             video_id = extract_video_id(video_url_2)
# #             if not video_id:
# #                 st.error("Invalid YouTube URL. Please enter a valid video link.")
# #             else:
# #                 with st.spinner("Fetching comments for your custom query..."):
# #                     comments = fetch_comments(video_id, st.session_state.youtube_api_key)

# #                 if comments:
# #                     comments_for_summary = tuple(pd.DataFrame(comments)['text'].head(300))
# #                     ai_response = generate_gemini_summary(comments_for_summary, st.session_state.gemini_api_key, custom_prompt)
                    
# #                     st.subheader("🔮 AI Response to Your Query")
# #                     st.info(ai_response, icon="🧠")






# import streamlit as st
# import pandas as pd
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
# import re
# import requests
# import plotly.express as px
# from nltk.sentiment.vader import SentimentIntensityAnalyzer
# import nltk
# import time

# # --- 1. PAGE CONFIGURATION AND STYLING ---
# st.set_page_config(
#     page_title="YouTube Comment Analyzer",
#     page_icon="⚡",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# st.markdown("""
#     <style>
#         .stTabs [data-baseweb="tab-list"] { gap: 24px; }
#         .stTabs [data-baseweb="tab"] {
#             height: 50px;
#             white-space: pre-wrap;
#             background-color: #F0F2F6;
#             border-radius: 4px 4px 0px 0px;
#             gap: 1px;
#             padding-top: 10px;
#             padding-bottom: 10px;
#         }
#         .stTabs [aria-selected="true"] { background-color: #FFFFFF; }
#         h1, h2, h3 { text-align: center; }
#     </style>""", unsafe_allow_html=True)

# try:
#     nltk.data.find('sentiment/vader_lexicon.zip')
# except LookupError:
#     with st.spinner("Downloading language model (one-time setup)..."):
#         nltk.download('vader_lexicon')

# # --- 2. API KEY MANAGEMENT & SIDEBAR UI ---
# with st.sidebar:
#     st.header("🔑 API Configuration")
#     st.markdown("Enter your API keys below to activate the analyzer.")

#     youtube_api_key = st.text_input("YouTube Data API v3 Key", type="password")
#     gemini_api_key = st.text_input("Google Gemini API Key", type="password")

#     st.markdown("---")
#     st.subheader("How to get your API keys:")
#     st.markdown("""
#     1.  **YouTube API Key:**
#         - Go to the [Google Cloud Console](https://console.cloud.google.com/).
#         - Create a project, enable the "YouTube Data API v3", and create an API Key.
#     2.  **Gemini API Key:**
#         - Go to [Google AI Studio](https://aistudio.google.com/) and click "Get API Key".
#     ⚠️ **Note on Quotas:** The free YouTube API has a daily limit of ~10,000 units. This app is optimized for efficient use.
#     """)

# if youtube_api_key: st.session_state.youtube_api_key = youtube_api_key
# if gemini_api_key: st.session_state.gemini_api_key = gemini_api_key


# # --- 3. CORE FUNCTIONS (WITH PERFORMANCE CACHING & DEDICATED AI CALLS) ---

# @st.cache_data(show_spinner=False)
# def fetch_comments(video_id: str, api_key: str, max_comments: int = 500) -> list | None:
#     if not api_key:
#         st.error("YouTube API Key is missing. Please enter it in the sidebar.")
#         return None
#     try:
#         youtube = build('youtube', 'v3', developerKey=api_key)
#         comments, next_page_token = [], None
#         while len(comments) < max_comments:
#             request = youtube.commentThreads().list(part="snippet", videoId=video_id, textFormat="plainText", maxResults=100, pageToken=next_page_token, order='time')
#             response = request.execute()
#             for item in response.get('items', []):
#                 comment = item['snippet']['topLevelComment']['snippet']
#                 comments.append({'text': comment['textDisplay']})
#             next_page_token = response.get('nextPageToken')
#             if not next_page_token: break
#         return comments
#     except HttpError as e:
#         st.error(f"Failed to fetch comments. Is your YouTube API key valid? (Error: {e})")
#         return None

# @st.cache_data
# def analyze_sentiments(comments: list) -> pd.DataFrame:
#     sid = SentimentIntensityAnalyzer()
#     df = pd.DataFrame(comments)
#     if 'text' not in df.columns: return df
#     df['compound'] = df['text'].apply(lambda text: sid.polarity_scores(text)['compound'])
#     def classify(compound):
#         if compound >= 0.05: return 'Positive'
#         elif compound <= -0.05: return 'Negative'
#         else: return 'Neutral'
#     df['sentiment'] = df['compound'].apply(classify)
#     return df

# # --- FIX: DEDICATED FUNCTION FOR GENERAL SUMMARY ---
# @st.cache_data(show_spinner="🧠 Generating general summary...")
# def get_general_summary(comments_tuple: tuple, api_key: str) -> str:
#     if not api_key: return "Error: Gemini API Key is missing."
#     prompt = f"Please provide a concise but insightful summary of the key themes, topics, and overall sentiment from the following YouTube comments. Identify what people liked and disliked. Comments: {comments_tuple}"
#     try:
#         url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
#         with requests.post(url, headers={'Content-Type': 'application/json'}, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60) as response:
#             response.raise_for_status()
#             return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
#     except requests.exceptions.RequestException as e:
#         return f"Error: Failed to connect to Gemini API. Check your network or API key. ({e})"
#     except (KeyError, IndexError):
#         return "Error: Could not parse a valid response from the Gemini API."

# # --- FIX: DEDICATED FUNCTION FOR CUSTOM SUMMARY ---
# @st.cache_data(show_spinner="🧠 Getting custom insights...")
# def get_custom_summary(comments_tuple: tuple, api_key: str, custom_prompt: str) -> str:
#     if not api_key: return "Error: Gemini API Key is missing."
#     prompt = f"Based on the following YouTube comments, please provide a specific answer to this user's question: '{custom_prompt}'. Comments: {comments_tuple}"
#     try:
#         url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
#         with requests.post(url, headers={'Content-Type': 'application/json'}, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60) as response:
#             response.raise_for_status()
#             return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
#     except requests.exceptions.RequestException as e:
#         return f"Error: Failed to connect to Gemini API. Check your network or API key. ({e})"
#     except (KeyError, IndexError):
#         return "Error: Could not parse a valid response from the Gemini API."

# def extract_video_id(url: str) -> str | None:
#     pattern = r'(?:https?:\/\/(?:www\.)?youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=))([^"&?/\s]{11})'
#     match = re.search(pattern, url)
#     return match.group(1) if match else None

# # --- 4. MAIN APPLICATION UI ---
# st.title("⚡ YouTube Comment Analyzer")
# st.markdown("### Instantly analyze video comments, gauge sentiment, and get AI-powered insights.")

# if 'youtube_api_key' not in st.session_state or 'gemini_api_key' not in st.session_state:
#     st.warning("Please enter your API keys in the sidebar to begin.")
#     st.stop()

# tab1, tab2 = st.tabs(["📊 Video Analyzer", "✨ Custom Analyzer"])

# with tab1:
#     st.header("General Sentiment Analysis")
#     video_url_1 = st.text_input("Enter a YouTube Video URL", key="url1", placeholder="e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ")

#     if st.button("Analyze Video Sentiment", key="analyze1", use_container_width=True):
#         if video_url_1 and (video_id := extract_video_id(video_url_1)):
#             with st.spinner("Step 1/2: Fetching & analyzing comments..."):
#                 comments = fetch_comments(video_id, st.session_state.youtube_api_key)
#                 if comments:
#                     sentiment_df = analyze_sentiments(comments)
            
#             if not sentiment_df.empty:
#                 comments_for_summary = tuple(sentiment_df['text'].head(300))
#                 # --- FIX: CALL THE DEDICATED GENERAL SUMMARY FUNCTION ---
#                 ai_summary = get_general_summary(comments_for_summary, st.session_state.gemini_api_key)

#                 st.subheader("💡 AI-Powered Summary")
#                 if ai_summary.startswith("Error:"):
#                     st.error(ai_summary)
#                 else:
#                     st.success(ai_summary, icon="🤖")

#                 st.subheader("📊 Sentiment Breakdown")
#                 sentiment_counts = sentiment_df['sentiment'].value_counts()
#                 col1, col2 = st.columns([1, 1.5])
#                 with col1:
#                     st.metric("✅ Positive", sentiment_counts.get('Positive', 0))
#                     st.metric("❌ Negative", sentiment_counts.get('Negative', 0))
#                     st.metric("😐 Neutral", sentiment_counts.get('Neutral', 0))
#                 with col2:
#                     fig = px.pie(values=sentiment_counts.values, names=sentiment_counts.index, color=sentiment_counts.index,
#                                  color_discrete_map={'Positive':'#2ECC71', 'Negative':'#E74C3C', 'Neutral':'#95A5A6'}, hole=0.3)
#                     fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
#                     st.plotly_chart(fig, use_container_width=True)
#         else:
#             st.warning("Please enter a valid YouTube video URL.")

# with tab2:
#     st.header("Custom Query Analysis")
#     video_url_2 = st.text_input("Enter a YouTube Video URL", key="url2", placeholder="e.g., https://www.youtube.com/watch?v=Rok8W2agHcw")
#     custom_prompt = st.text_area("What specific question do you have about the comments?", placeholder="e.g., What are the main feature requests or bug reports mentioned?")

#     if st.button("Get Custom Insights", key="analyze2", use_container_width=True):
#         if video_url_2 and custom_prompt and (video_id := extract_video_id(video_url_2)):
#             with st.spinner("Fetching comments for your custom query..."):
#                 comments = fetch_comments(video_id, st.session_state.youtube_api_key)

#             if comments:
#                 comments_for_summary = tuple(pd.DataFrame(comments)['text'].head(300))
#                 # --- FIX: CALL THE DEDICATED CUSTOM SUMMARY FUNCTION ---
#                 ai_response = get_custom_summary(comments_for_summary, st.session_state.gemini_api_key, custom_prompt)
                
#                 st.subheader("🔮 AI Response to Your Query")
#                 if ai_response.startswith("Error:"):
#                     st.error(ai_response)
#                 else:
#                     st.info(ai_response, icon="🧠")
#         else:
#             st.warning("Please enter both a valid video URL and your custom question.")









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
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 1. PAGE CONFIGURATION AND STYLING ---
st.set_page_config(
    page_title="YouTube Comment Analyzer Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Enhanced CSS styling
st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] { 
            gap: 24px; 
            justify-content: center;
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
            color: #1f77b4;
        }
        h1, h2, h3 { 
            text-align: center; 
            color: #1f77b4;
        }
        .metric-card { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .success-box {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            padding: 20px;
            border-radius: 15px;
            color: white;
            margin: 15px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .error-box {
            background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
            padding: 20px;
            border-radius: 15px;
            color: white;
            margin: 15px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .info-box {
            background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
            padding: 20px;
            border-radius: 15px;
            color: white;
            margin: 15px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .contact-container {
            background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
            padding: 25px;
            border-radius: 20px;
            color: white;
            text-align: center;
            margin: 20px 0;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }
        .contact-button {
            background: white;
            color: #FF6B6B;
            padding: 12px 25px;
            border: none;
            border-radius: 25px;
            font-weight: bold;
            text-decoration: none;
            display: inline-block;
            margin: 10px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .contact-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        .stProgress .st-bo {
            background-color: #667eea;
        }
        .sidebar-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            border-left: 4px solid #667eea;
        }
        .template-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px;
            border-radius: 10px;
            width: 100%;
            margin: 5px 0;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .template-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        .comment-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .positive-comment {
            border-left-color: #4CAF50;
        }
        .negative-comment {
            border-left-color: #f44336;
        }
        .footer {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            margin: 30px 0;
        }
    </style>""", unsafe_allow_html=True)

# Download NLTK data with proper error handling
@st.cache_resource
def download_nltk_data():
    try:
        nltk.data.find('vader_lexicon')
    except LookupError:
        with st.spinner("Downloading sentiment analysis model (one-time setup)..."):
            nltk.download('vader_lexicon', quiet=True)
    return True

download_nltk_data()

# # --- 2. ENHANCED API KEY MANAGEMENT & SIDEBAR UI ---
# with st.sidebar:
#     st.header("🔑 API Configuration")
#     st.markdown("Enter your API keys below to activate the analyzer.")
    
#     youtube_api_key = st.text_input("YouTube Data API v3 Key", type="password")
#     gemini_api_key = st.text_input("Google Gemini API Key", type="password")
    
#     # Advanced settings
#     st.markdown("---")
#     st.subheader("⚙️ Advanced Settings")
#     max_comments = st.slider("Maximum Comments to Analyze", 100, 1000, 500, 50)
#     timeout_duration = st.slider("API Timeout (seconds)", 30, 120, 60, 10)
#     retry_attempts = st.slider("Retry Attempts", 1, 5, 3, 1)
    
#     st.markdown("---")
#     st.subheader("📖 How to get API keys:")
#     st.markdown("""
#     <div class="sidebar-info">
#         <strong>1. YouTube API Key:</strong><br>
#         • Go to <a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a><br>
#         • Create a project, enable "YouTube Data API v3"<br>
#         • Create credentials (API Key)<br><br>
        
#         <strong>2. Gemini API Key:</strong><br>
#         • Go to <a href="https://aistudio.google.com/" target="_blank">Google AI Studio</a><br>
#         • Click "Get API Key"<br><br>
        
#         <strong>⚠️ Quota Info:</strong><br>
#         Free YouTube API: ~10,000 units/day
#     </div>
#     """, unsafe_allow_html=True)
    
#     # Contact Information
#     st.markdown("---")
#     st.subheader("📞 Need Help?")
#     st.markdown("""
#     <div class="contact-container">
#         <h4>🚀 Contact Developer</h4>
#         <p>For support, feature requests, or bug reports:</p>
#         <a href="https://wa.me/919360734551" target="_blank" class="contact-button">
#             📱 WhatsApp: +91 9360734551
#         </a>
#         <br>
#         <a href="mailto:sanjaydharand@gmail.com" target="_blank" class="contact-button">
#             📧 Email: sanjaydharand@gmail.com
#         </a>
#     </div>
#     """, unsafe_allow_html=True)



# --- 2. ENHANCED API KEY MANAGEMENT & SIDEBAR UI ---
with st.sidebar:
    st.header("🔑 API Configuration")
    st.markdown("Securely enter your API keys to activate the analyzer.")

    youtube_api_key = st.text_input("YouTube Data API v3 Key", type="password", help="Used to fetch comments from public YouTube videos.")
    gemini_api_key = st.text_input("Google Gemini API Key", type="password", help="Used to generate AI insights using Gemini model.")

    st.divider()

    st.subheader("⚙️ Advanced Settings")
    max_comments = st.slider("Max Comments to Analyze", min_value=100, max_value=1000, value=500, step=50,
                             help="Number of comments to fetch and analyze (affects speed and API usage).")
    timeout_duration = st.slider("Gemini API Timeout (seconds)", min_value=30, max_value=120, value=60, step=10,
                                 help="Time to wait for a response from Gemini before retrying.")
    retry_attempts = st.slider("Gemini API Retry Attempts", min_value=1, max_value=5, value=3,
                               help="Number of retries if Gemini API fails due to timeout.")

    st.divider()

    st.subheader("📖 How to Get Your API Keys")
    st.markdown("""
    <ul>
        <li><strong>YouTube API:</strong><br>
            <a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a> → Create Project → Enable <em>YouTube Data API v3</em> → Create API Key.
        </li><br>
        <li><strong>Gemini API:</strong><br>
            <a href="https://aistudio.google.com/" target="_blank">Google AI Studio</a> → Sign In → Click "Get API Key".
        </li>
    </ul>
    <small><strong>⚠️ Note:</strong> YouTube API has a daily limit of ~10,000 units. Use efficiently.</small>
    """, unsafe_allow_html=True)

    st.divider()

    st.subheader("📞 Need Help?")
    st.markdown("""
    <div style="font-size: 14px;">
        <p>For support, custom tools, or collaborations:</p>
        <a href="https://wa.me/919360734551" target="_blank">📱 WhatsApp Me</a><br>
        <a href="mailto:sanjaydharand@gmail.com" target="_blank">📧 sanjaydharand@gmail.com</a>
    </div>
    """, unsafe_allow_html=True)


# Store API keys in session state
if youtube_api_key: 
    st.session_state.youtube_api_key = youtube_api_key
if gemini_api_key: 
    st.session_state.gemini_api_key = gemini_api_key

# --- 3. ENHANCED CORE FUNCTIONS WITH RETRY LOGIC ---

def retry_with_backoff(func, max_retries=3, backoff_factor=2):
    """Decorator for retry logic with exponential backoff"""
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                wait_time = backoff_factor ** attempt
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
        return None
    return wrapper

@st.cache_data(show_spinner=False, ttl=3600)  # Cache for 1 hour
def fetch_comments_optimized(video_id: str, api_key: str, max_comments: int = 500) -> Optional[List[Dict]]:
    """Enhanced comment fetching with better error handling and progress tracking"""
    if not api_key:
        st.error("YouTube API Key is missing. Please enter it in the sidebar.")
        return None
    
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        comments = []
        next_page_token = None
        
        # Create progress tracking
        progress_container = st.empty()
        progress_bar = st.progress(0)
        
        while len(comments) < max_comments:
            try:
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    textFormat="plainText",
                    maxResults=min(100, max_comments - len(comments)),
                    pageToken=next_page_token,
                    order='time'
                )
                response = request.execute()
                
                batch_comments = []
                for item in response.get('items', []):
                    comment = item['snippet']['topLevelComment']['snippet']
                    batch_comments.append({
                        'text': comment['textDisplay'],
                        'author': comment['authorDisplayName'],
                        'likes': comment['likeCount'],
                        'published': comment['publishedAt']
                    })
                
                comments.extend(batch_comments)
                
                # Update progress
                progress = min(len(comments) / max_comments, 1.0)
                progress_bar.progress(progress)
                progress_container.text(f"📥 Fetched {len(comments)} comments...")
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except HttpError as e:
                if e.resp.status == 403:
                    st.error("🚫 YouTube API quota exceeded. Please try again later.")
                    return None
                else:
                    st.error(f"❌ Error fetching comments: {e}")
                    return None
        
        # Clear progress indicators
        progress_bar.empty()
        progress_container.empty()
        
        return comments
        
    except Exception as e:
        st.error(f"❌ Failed to fetch comments: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def analyze_sentiments_enhanced(comments: List[Dict]) -> pd.DataFrame:
    """Enhanced sentiment analysis with additional metrics"""
    if not comments:
        return pd.DataFrame()
    
    sid = SentimentIntensityAnalyzer()
    df = pd.DataFrame(comments)
    
    if 'text' not in df.columns:
        return df
    
    # Progress tracking for large datasets
    progress_container = st.empty()
    progress_bar = st.progress(0)
    
    # Analyze sentiments in batches for better performance
    def analyze_batch(batch_texts):
        return [sid.polarity_scores(text) for text in batch_texts]
    
    batch_size = 50
    all_scores = []
    
    for i in range(0, len(df), batch_size):
        batch = df['text'].iloc[i:i+batch_size].tolist()
        batch_scores = analyze_batch(batch)
        all_scores.extend(batch_scores)
        
        progress = min((i + batch_size) / len(df), 1.0)
        progress_bar.progress(progress)
        progress_container.text(f"🔍 Analyzing sentiment: {i + len(batch)}/{len(df)} comments")
    
    # Clear progress indicators
    progress_bar.empty()
    progress_container.empty()
    
    # Extract sentiment scores
    df['compound'] = [score['compound'] for score in all_scores]
    df['positive'] = [score['pos'] for score in all_scores]
    df['negative'] = [score['neg'] for score in all_scores]
    df['neutral'] = [score['neu'] for score in all_scores]
    
    # Classify sentiments
    def classify_sentiment(compound):
        if compound >= 0.05:
            return 'Positive'
        elif compound <= -0.05:
            return 'Negative'
        else:
            return 'Neutral'
    
    df['sentiment'] = df['compound'].apply(classify_sentiment)
    
    # Add sentiment intensity
    df['intensity'] = df['compound'].abs()
    
    return df

def call_gemini_api_with_retry(prompt: str, api_key: str, max_retries: int = 3, timeout: int = 60) -> str:
    """Enhanced Gemini API call with retry logic and better error handling"""
    if not api_key:
        return "Error: Gemini API Key is missing."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 2048,
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'YouTube-Comment-Analyzer/1.0'
    }
    
    for attempt in range(max_retries):
        try:
            # Use a session for connection pooling
            with requests.Session() as session:
                response = session.post(
                    url, 
                    headers=headers, 
                    json=payload, 
                    timeout=timeout,
                    stream=False
                )
                response.raise_for_status()
                
                result = response.json()
                return result['candidates'][0]['content']['parts'][0]['text'].strip()
                
        except requests.exceptions.Timeout:
            error_msg = f"Request timed out (attempt {attempt + 1}/{max_retries})"
            logger.warning(error_msg)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                return f"Error: Request timed out after {max_retries} attempts. Try reducing the number of comments or increasing timeout."
                
        except requests.exceptions.ConnectionError:
            error_msg = f"Connection error (attempt {attempt + 1}/{max_retries})"
            logger.warning(error_msg)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return "Error: Unable to connect to Gemini API. Please check your internet connection."
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                return "Error: API rate limit exceeded. Please wait and try again."
            elif e.response.status_code == 403:
                return "Error: Invalid API key or insufficient permissions."
            else:
                return f"Error: HTTP {e.response.status_code} - {e.response.text}"
                
        except (KeyError, IndexError, json.JSONDecodeError):
            return "Error: Invalid response format from Gemini API."
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return f"Error: Unexpected error occurred - {str(e)}"
    
    return "Error: Maximum retry attempts exceeded."

@st.cache_data(show_spinner=False, ttl=1800)  # Cache for 30 minutes
def get_general_summary_enhanced(comments_tuple: tuple, api_key: str, timeout: int = 60) -> str:
    """Enhanced general summary with better prompting"""
    prompt = f"""
    Analyze the following YouTube comments and provide a comprehensive summary including:
    
    1. **Overall Sentiment**: What's the general mood of viewers?
    2. **Key Themes**: What are the main topics discussed?
    3. **Popular Opinions**: What do viewers commonly like/dislike?
    4. **Notable Insights**: Any interesting patterns or standout comments?
    5. **Engagement Level**: How engaged are the viewers?
    
    Please be concise but insightful. Focus on actionable insights.
    
    Comments to analyze: {comments_tuple[:300]}  # Limit to first 300 comments
    """
    
    return call_gemini_api_with_retry(prompt, api_key, timeout=timeout)

@st.cache_data(show_spinner=False, ttl=1800)  # Cache for 30 minutes
def get_custom_summary_enhanced(comments_tuple: tuple, api_key: str, custom_prompt: str, timeout: int = 60) -> str:
    """Enhanced custom summary with better prompting"""
    prompt = f"""
    Based on the YouTube comments provided, please answer this specific question: "{custom_prompt}"
    
    Provide a detailed, accurate response based on the actual content of the comments.
    If the comments don't contain relevant information, please state that clearly.
    
    Comments to analyze: {comments_tuple[:300]}  # Limit to first 300 comments
    """
    
    return call_gemini_api_with_retry(prompt, api_key, timeout=timeout)

def extract_video_id(url: str) -> Optional[str]:
    """Enhanced video ID extraction with better pattern matching"""
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([^&\n?#]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([^&\n?#]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/v\/([^&\n?#]+)',
        r'(?:https?:\/\/)?youtu\.be\/([^&\n?#]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/.*[?&]v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def display_enhanced_metrics(sentiment_df: pd.DataFrame):
    """Display enhanced metrics with better visualizations"""
    sentiment_counts = sentiment_df['sentiment'].value_counts()
    total_comments = len(sentiment_df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        positive_count = sentiment_counts.get('Positive', 0)
        positive_pct = (positive_count / total_comments) * 100
        st.markdown(f"""
        <div class="metric-card">
            <h3>✅ Positive</h3>
            <h2>{positive_count}</h2>
            <p>{positive_pct:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        negative_count = sentiment_counts.get('Negative', 0)
        negative_pct = (negative_count / total_comments) * 100
        st.markdown(f"""
        <div class="metric-card">
            <h3>❌ Negative</h3>
            <h2>{negative_count}</h2>
            <p>{negative_pct:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        neutral_count = sentiment_counts.get('Neutral', 0)
        neutral_pct = (neutral_count / total_comments) * 100
        st.markdown(f"""
        <div class="metric-card">
            <h3>😐 Neutral</h3>
            <h2>{neutral_count}</h2>
            <p>{neutral_pct:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_sentiment = sentiment_df['compound'].mean()
        sentiment_emoji = "😊" if avg_sentiment > 0 else "😢" if avg_sentiment < 0 else "😐"
        st.markdown(f"""
        <div class="metric-card">
            <h3>📊 Avg Score</h3>
            <h2>{avg_sentiment:.3f}</h2>
            <p>{sentiment_emoji}</p>
        </div>
        """, unsafe_allow_html=True)

def show_contact_info(query_type: str):
    """Display contact information for support requests"""
    st.markdown(f"""
    <div class="contact-container">
        <h3>🚀 {query_type} Support</h3>
        <p>Thank you for your interest! Please contact the developer for assistance:</p>
        <div style="margin: 20px 0;">
            <a href="https://wa.me/919360734551?text=Hi! I need help with {query_type} for YouTube Comment Analyzer" target="_blank" class="contact-button">
                📱 WhatsApp: +91 9360734551
            </a>
            <br>
            <a href="mailto:sanjaydharand@gmail.com?subject={query_type} - YouTube Comment Analyzer&body=Hi! I need help with {query_type} for the YouTube Comment Analyzer app." target="_blank" class="contact-button">
                📧 Email: sanjaydharand@gmail.com
            </a>
        </div>
        <p style="font-size: 14px; opacity: 0.9;">
            💡 Include details about your request for faster assistance!
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- 4. ENHANCED MAIN APPLICATION UI ---
st.markdown("""
<div style="text-align: center; margin-bottom: 30px;">
    <h1>⚡ YouTube Comment Analyzer Pro</h1>
    <p style="font-size: 18px; color: #666;">🚀 Advanced AI-powered comment analysis with real-time insights</p>
</div>
""", unsafe_allow_html=True)

# Check for API keys
if 'youtube_api_key' not in st.session_state or 'gemini_api_key' not in st.session_state:
    st.markdown("""
    <div class="error-box">
        <h3>🔑 API Keys Required</h3>
        <p>Please enter your YouTube and Gemini API keys in the sidebar to begin analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Enhanced tabs with better alignment
tab1, tab2, tab3 = st.tabs(["📊 Sentiment Analysis", "🔍 Custom Query", "📞 Support"])

with tab1:
    st.markdown("<h2>🎯 General Sentiment Analysis</h2>", unsafe_allow_html=True)
    
    # Centered input section
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        video_url_1 = st.text_input(
            "Enter YouTube Video URL", 
            key="url1", 
            placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        analyze_button = st.button("🔍 Analyze Video", key="analyze1", use_container_width=True)
    
    if analyze_button and video_url_1:
        video_id = extract_video_id(video_url_1)
        if not video_id:
            st.markdown("""
            <div class="error-box">
                <h3>❌ Invalid URL</h3>
                <p>Please enter a valid YouTube video URL and try again.</p>
            </div>
            """, unsafe_allow_html=True)
            st.stop()
        
        # Analysis process with better UI
        with st.spinner("🔄 Step 1/3: Fetching comments..."):
            comments = fetch_comments_optimized(
                video_id, 
                st.session_state.youtube_api_key, 
                max_comments
            )
        
        if not comments:
            st.markdown("""
            <div class="error-box">
                <h3>❌ Failed to Fetch Comments</h3>
                <p>Please check your API key and try again.</p>
            </div>
            """, unsafe_allow_html=True)
            st.stop()
        
        with st.spinner("🔄 Step 2/3: Analyzing sentiments..."):
            sentiment_df = analyze_sentiments_enhanced(comments)
        
        if sentiment_df.empty:
            st.markdown("""
            <div class="error-box">
                <h3>❌ No Comments Found</h3>
                <p>This video has no comments to analyze.</p>
            </div>
            """, unsafe_allow_html=True)
            st.stop()
        
        # Prepare data for AI analysis
        comments_for_ai = tuple(sentiment_df['text'].head(300).tolist())
        
        with st.spinner("🔄 Step 3/3: Generating AI insights..."):
            ai_summary = get_general_summary_enhanced(
                comments_for_ai, 
                st.session_state.gemini_api_key,
                timeout_duration
            )
        
        # Display results with enhanced styling
        st.markdown("<h3>🤖 AI-Generated Insights</h3>", unsafe_allow_html=True)
        if ai_summary.startswith("Error:"):
            st.markdown(f"""
            <div class="error-box">
                <h4>❌ AI Analysis Error</h4>
                <p>{ai_summary}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="success-box">
                <h4>🧠 AI Analysis Results</h4>
                <p>{ai_summary}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<h3>📊 Sentiment Distribution</h3>", unsafe_allow_html=True)
        display_enhanced_metrics(sentiment_df)
        
        # Enhanced visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart
            sentiment_counts = sentiment_df['sentiment'].value_counts()
            fig_pie = px.pie(
                values=sentiment_counts.values, 
                names=sentiment_counts.index,
                color=sentiment_counts.index,
                color_discrete_map={
                    'Positive': '#4CAF50', 
                    'Negative': '#f44336', 
                    'Neutral': '#9E9E9E'
                },
                hole=0.4,
                title="Sentiment Distribution"
            )
            fig_pie.update_layout(showlegend=True, height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Sentiment intensity histogram
            fig_hist = px.histogram(
                sentiment_df, 
                x='compound', 
                nbins=20,
                title="Sentiment Intensity Distribution",
                labels={'compound': 'Sentiment Score', 'count': 'Number of Comments'},
                color_discrete_sequence=['#667eea']
            )
            fig_hist.update_layout(height=400)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        # Top comments section with better styling
        st.markdown("<h3>🔝 Notable Comments</h3>", unsafe_allow_html=True)
        
        if not sentiment_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Most Positive Comments**")
                top_positive = sentiment_df.nlargest(3, 'compound')
                for _, comment in top_positive.iterrows():
                    comment_text = comment['text'][:200] + "..." if len(comment['text']) > 200 else comment['text']
                    st.markdown(f"""
                    <div class="comment-card positive-comment">
                        <p>❤️ {comment_text}</p>
                        <small>Score: {comment['compound']:.3f}</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("**Most Negative Comments**")
                top_negative = sentiment_df.nsmallest(3, 'compound')
                for _, comment in top_negative.iterrows():
                    comment_text = comment['text'][:200] + "..." if len(comment['text']) > 200 else comment['text']
                    st.markdown(f"""
                    <div class="comment-card negative-comment">
                        <p>💔 {comment_text}</p>
                        <small>Score: {comment['compound']:.3f}</small>
                    </div>
                    """, unsafe_allow_html=True)

with tab2:
    st.header("🔍 Custom Query Analysis")
    _, main_col, _ = st.columns([1, 2, 1])
    with main_col:
        video_url_2 = st.text_input("Enter YouTube Video URL", key="url2", placeholder="https://www.youtube.com/watch?v=example")
        if 'prompt_template' in st.session_state:
            custom_prompt = st.text_area("Your specific question about the comments:", value=st.session_state.prompt_template, key="custom_prompt_area", height=100)
            del st.session_state.prompt_template # Clear after use
        else:
            custom_prompt = st.text_area("Your specific question about the comments:", placeholder="e.g., What bugs are users reporting?", key="custom_prompt_area", height=100)

        st.markdown("**Quick Templates:**")
        t_col1, t_col2, t_col3 = st.columns(3)
        if t_col1.button("Feature Requests"): st.session_state.prompt_template = "What features or improvements are users requesting?" ; st.rerun()
        if t_col2.button("Bug Reports"): st.session_state.prompt_template = "What bugs, errors, or issues are users reporting?" ; st.rerun()
        if t_col3.button("General Feedback"): st.session_state.prompt_template = "What is the general feedback and what do users like most about this?" ; st.rerun()
        
        analyze_button_2 = st.button("Get Custom Insights", key="analyze2", use_container_width=True)

    if analyze_button_2 and video_url_2 and custom_prompt:
        if video_id := extract_video_id(video_url_2):
            comments = fetch_comments_optimized(video_id, st.session_state.youtube_api_key, max_comments)
            if comments:
                comments_tuple = tuple(pd.DataFrame(comments)['text'].head(300).tolist())
                ai_response = get_custom_summary_enhanced(comments_tuple, st.session_state.gemini_api_key, custom_prompt, timeout_duration)
                st.subheader("🔮 AI Response to Your Query")
                st.markdown(f'<div class="{"info-box" if not ai_response.startswith("Error:") else "error-box"}">{ai_response}</div>', unsafe_allow_html=True)
        else:
            st.error("❌ Invalid URL. Please enter a valid YouTube video URL.")
    elif analyze_button_2:
        st.warning("⚠️ Please provide both a valid video URL and your custom question.")

with tab3:
    st.header("📞 Support & Contact")
    st.markdown("Have an idea for a new feature, found a bug, or just want to connect? Reach out!")

    def show_contact_info(query_type: str):
        st.markdown(f"""
        <div class="contact-container">
            <h4 style="color:#333;">Contact me for {query_type}</h4>
            <p style="color:#555;">I'm happy to help! Please include details about your request for a faster response.</p>
            <a href="https://wa.me/919360734551?text=Hi! I have a {query_type} for your YouTube Analyzer App." target="_blank" class="contact-button">
                📱 WhatsApp Me
            </a>
            <a href="mailto:sanjaydharand@gmail.com?subject=YouTube Analyzer - {query_type}&body=Hi! I have a {query_type} regarding the YouTube Comment Analyzer app." target="_blank" class="contact-button">
                📧 Email Me
            </a>
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 Feature Request", use_container_width=True):
            st.session_state.contact_reason = "Feature Request"
    with col2:
        if st.button("🐛 Report a Bug", use_container_width=True):
            st.session_state.contact_reason = "Bug Report"
    with col3:
        if st.button("⭐ General Feedback", use_container_width=True):
            st.session_state.contact_reason = "General Feedback"
            
    if 'contact_reason' in st.session_state:
        show_contact_info(st.session_state.contact_reason)

