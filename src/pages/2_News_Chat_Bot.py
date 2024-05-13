import streamlit as st 
from streamlit_searchbox import st_searchbox
from typing import List, Dict, Optional

# Assuming 'snow_db' and 'snow_llm' are modules you've created or imported that contain specific functionalities.
from snow import snow_db, snow_llm

def init():
    if st.session_state.get('previous_page') == "page_one" and st.session_state.get('current_page') == "page_two":
        st.session_state.summary = None  # Reset summary if coming from page one to page two
    
    st.session_state.previous_page = st.session_state.get('current_page')
    st.session_state.current_page = 'page_two'  # Update current page status

    # Ensure 'summary' and 'messages' are initialized in session_state if not present.
    st.session_state.setdefault('summary', None)
    if "messages" in st.session_state.keys():
        st.session_state.messages.clear()
        st.session_state.messages = [{"role": "assistant", "content": "Ask me a question about your News Data or anything"}]
    else:
        st.session_state.setdefault('messages', [{"role": "assistant", "content": "Ask me a question about your News Data or anything"}])
    st.session_state.setdefault('chat_history', [])

# Chat functionality.
def chat():
    session = snow_db.get_session()
    prompt = st.chat_input("Your question:")  # Streamlit's chat input for user questions.
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

    for message in st.session_state.messages:  # Display all previous chat messages.
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Generate response from the assistant if the last message was not from the assistant.
    if st.session_state.messages and st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Loading.."):
                response = snow_llm.snow_complete_chat(session, model, st.session_state.summary, prompt, st.session_state.chat_history)
                st.write(response)
                message = {"role": "assistant", "content": response}
                st.session_state.messages.append(message)  # Append assistant's response to the chat history.
                st.session_state.chat_history.append((prompt, response))
                
init()

# Creating two columns with adjusted widths.
menu_item1, menu_item2 = st.columns([1, 2])

# Select model interface.
model = 'llama2-70b-chat'
with menu_item1:
    model = st.selectbox('Select your model:', ('mistral-7b', 'llama2-70b-chat', 'mixtral-8x7b', 'gemma-7b'), key="model_name", index=1)

def search_news(searchterm: str) -> List[any]:
    return snow_db.search_data(searchterm) if searchterm else []

# Search box for news, integrated with a callback for searching news data.
st.session_state.summary = st_searchbox(
    search_news,
    key="news_searchbox",
    label="Search News for chatting",
    default=''
)

# Reset summary when changing from page one.
if st.session_state.previous_page == "page_one":
    st.session_state.summary = None

chat()
