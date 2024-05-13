import streamlit as st
import requests
from snow import snow_db, snow_llm
from io import BytesIO
from PIL import Image
import time
from streamlit_dashboard import dashboard

st.set_page_config(layout="wide",page_title="Hacker News Summary Streamlit")

def init():
    st.session_state.previous_page = st.session_state.get('current_page')
    st.session_state.current_page = 'page_one'  # Set the current page

init()

def load_image(url):
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    return image

url = "https://upload.wikimedia.org/wikipedia/en/b/bf/Hackernews_logo.png?20220801220016"
image = None
try:
    image = load_image(url)
except Exception as ex:
    print("Failed to load image:", ex)

# Inject custom CSS
st.markdown("""
    <style>
    div[data-testid="stPopover"] {
        padding-bottom: 0px;  /* Adjust the padding as needed */
    }
    div[data-testid="stImage"] {
        padding-top: 4px;  /* Adjust the padding as needed */
    }
    </style>
""", unsafe_allow_html=True)

menu_item1, menu_item2, menu_item3 = st.columns([0.8, 0.6, 6])

with menu_item1:
    if image != None:
        st.image(image)
    
with menu_item2:
    popover = st.popover("Translate")
    selected_value = popover.selectbox("Choose a language:", ["Default", "English", "Spanish", "German", "French"])

with menu_item3:
    popover = st.popover("Filter")
    filter_value = popover.selectbox("Choose a filter:", ["Default", "Top 20", "Top 10", "Best"])

# Initialize or get the cached dataframe
if 'df' not in st.session_state or st.session_state.language_select != selected_value:
    st.session_state.df = snow_db.get_data().to_pandas()
    st.session_state.language_select = selected_value

# Display the dashboard with the current state of the dataframe
dashboard.show_dashboard(st.session_state.df)

if selected_value != 'Default' and selected_value != st.session_state.language_select:
    session = snow_db.get_session()
    #translated_df = snow_llm.translate_articles(session, st.session_state.df, from_lg, selected_value)
    #st.session_state.df = translated_df
    st.session_state.language_select = selected_value
    st.rerun()  # Rerun the app to reflect new changes

