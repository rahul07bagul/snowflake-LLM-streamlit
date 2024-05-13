import streamlit as st
import replicate
from openai import OpenAI
import os
import re
import pandas as pd
from snow import snow_llm, snow_util, prompts

os.environ['REPLICATE_API_TOKEN'] = "r8_YqqzAHfaj7bG8F0lLpXck2642RERyuJ2vtHWy"
client = OpenAI(api_key=st.secrets.OPENAI_API_KEY)

# App title
st.set_page_config(page_title="Snowflake Arctic")
session = '' #snow_util.get_session()

def init():
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{"role": "assistant", "content": "Hi. I'm Arctic, a new, efficient, intelligent, and truly open language model created by Snowflake AI Research. Ask me anything."}]

    st.session_state.previous_page = st.session_state.get('current_page')
    st.session_state.current_page = 'page_three'  # Update current page status

    if st.session_state.previous_page == "page_two":
        st.session_state.messages.clear()
        st.session_state.messages = [{"role": "assistant", "content": "Hi. I'm Arctic, a new, efficient, intelligent, and truly open language model created by Snowflake AI Research. Ask me anything."}]

def chat():
    prompt = st.chat_input("Your question:")
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

    # Display messages
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "results" in message:
                st.dataframe(message["results"])

    # Generate a new response if last message is not from assistant
    if st.session_state.messages and st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Loading.."):
                #response = snow_llm.snow_arctic()
                response = snow_llm.chat_gpt(client)
                st.write(response)
                message = {"role": "assistant", "content": response}
                sql_match = re.search(r"```sql\n(.*)\n```", response, re.DOTALL)
                if sql_match:
                    sql = sql_match.group(1)
                    conn = st.connection("snowflake")
                    message["results"] = conn.query(sql)
                    st.dataframe(message["results"])
                st.session_state.messages.append(message)

def get_database():
    #global session
    #if not session:
    #    session = snow_util.get_session()
    if "databases" not in st.session_state.keys():
        st.session_state.databases = snow_util.list_databases(session)

def get_schemas(database_val):
    #session = snow_util.get_session()
    schemas = snow_util.list_schemas(session,database_val)
    if "schemas" not in st.session_state.keys():
        st.session_state.schemas = schemas
    st.session_state.schemas = schemas

def get_table_view(db_name,sc_name):
    tables = snow_util.list_tables(db_name+"."+sc_name)
    if "tables" not in st.session_state.keys():
        st.session_state.tables = tables
    st.session_state.tables = tables

init()

with st.sidebar:
    st.title('Snowflake Arctic')
    use_snow = st.toggle('Use Snowflake Data', on_change=get_database)
    if use_snow and "databases" in st.session_state.keys():
        database_val = st.selectbox('Select your database:', st.session_state.databases, key="db_name", index=1)
        if database_val:
            get_schemas(database_val)
            if "schemas" in st.session_state.keys():
                schema_val = st.selectbox('Select your schema:', st.session_state.schemas, key="sc_name")
                if schema_val:
                    get_table_view(database_val,schema_val)
                    table_name = st.selectbox('Select your table/view:', st.session_state.tables, key="tb_name")
                    if st.button("Submit Database, Schema and Table"):
                        print("Button Pressed")
                        schema_path = database_val+"."+schema_val
                        st.session_state.messages = []
                        st.session_state.messages = [{"role": "system", "content": prompts.get_system_prompt(session,schema_path, table_name)}]
chat()