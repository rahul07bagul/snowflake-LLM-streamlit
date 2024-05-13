import replicate
from openai import OpenAI
import re
import pandas as pd
import json
import streamlit as st
from snow import prompts

LLAMA2_MODEL = 'llama2-70b-chat'
SNOW_ARCTIC = 'snowflake-arctic'
session = ''

language_codes = {"English": "en", "Spanish":"es", "German":"de","French":"fr"}

def truncate_article(article, max_length=2500):
    if len(article) > max_length:
        return article[:max_length]
    return article

def summarize_article(article):
    response_content = ""
    try:
        article = truncate_article(article)
        article = article.replace("'","\\'")
        # Constructing the LLM prompt
        prompt = f"[INST] Summarize this article in less than 200 words: {article} [/INST]"
        
        # Execute the LLM query in Snowflake
        query = f"select snowflake.cortex.complete('{LLAMA2_MODEL}', '{prompt}') AS response"
        #query = f"select snowflake.cortex.summerize('{article}') AS response"
        df = pd.DataFrame(session.sql(query).collect())
        
        # Extract the response
        response_content = df.iloc[0]['RESPONSE'].replace("'", "\\'")
        
    except Exception as e:
        response_content = f'Caught {type(e).__name__} >>> {str(e)} <<<'
    
    return response_content

def summerize_articles(snow_session,articles_list):
    print("Summerizing articles....")
    global session
    session = snow_session
    articles = []
    for article in articles_list:
        if article is not None and not is_empty(article.maintext):
            summary = summarize_article(article.maintext)
            article.summary = summary
            articles.append(article)
    
    return articles

def is_empty(s):
    return not s or s.strip() == ''

def translate_articles(session, df, from_lg, to_lg):
    print("Translating articles...")
    source_lg = language_codes[from_lg]
    target_lg = language_codes[to_lg]
    if source_lg != target_lg:
        print("Source language:", source_lg)
        print("Target language:", target_lg)

        # Using a temporary list to collect updates
        updates = []
        
        for index, row in df.iterrows():
            summary = row["SUMMARY"].replace("'", "\'")
            title = row["TITLE"].replace("'", "\'")
            translate_text = f"{title} :||: {summary}"
                        
            # Constructing query
            query = f"SELECT snowflake.cortex.translate('{translate_text}', '{source_lg}', '{target_lg}') AS translation"
            try:
                # Execute the LLM query in Snowflake
                result_df = session.sql(query).collect()
                if result_df:
                    translated_text = result_df[0][0]
                    parts = translated_text.split(':||:')
                    if len(parts) > 1:
                        updates.append((index, parts[0], parts[1]))
            except Exception as e:
                print(f"Error translating text: {e}")

        # Update the DataFrame outside of the loop
        for index, title, summary in updates:
            df.loc[index, "TITLE"] = title
            df.loc[index, "SUMMARY"] = summary
    return df

def snow_complete_chat(session, model, article, question, chat_history):
    print("Chatting")
    response_content = ''
    try:
        print(article)
        if article:
            # Prepare the system prompt with escaping handled outside of f-string
            system_content = "Use the provided context and your knowledge about the topic to answer the question. Be concise. CONTEXT: " + article.replace("'", "\\'")
             # Start with a system-level prompt in the conversation history
            prompt_history = [{
                "role": "system",
                "content": system_content
            }]
        else:
            system_content = "Start conversation with user"
            prompt_history = []
        
        # Add user questions and assistant responses to the conversation history
        for q, a in chat_history:
            prompt_history.append({"role": "user", "content": q.replace('\'', '\\\'')})
            prompt_history.append({"role": "assistant", "content": a.replace('\'', '\\\'')})

        # Add the current user question
        prompt_history.append({"role": "user", "content": question.replace('\'', '\\\'')})
        
        # Convert the prompt history to a JSON string and escape single quotes for SQL
        prompt_json = json.dumps(prompt_history).replace('\'', '\\\'')
        
        #prompt = f"[INST] Use the provided context, your knowledge about the topic, and previous interactions to answer the question and also use previous response history. Be concise. First check if the user is really asking a question, then only answer, else proceed with a normal chat. ###Previous response history : {history_str} ###CONTEXT: {article} ###QUESTION: {question} ANSWER:[/INST]"
        query = f"select snowflake.cortex.complete('{model}', '{prompt_json}') AS response"

        # Execute the query
        df = pd.DataFrame(session.sql(query).collect())

        # Extract the response
        response_content = df.iloc[0]['RESPONSE'].replace("'", "\\'")
        #print(response_content)

        return response_content
    except Exception as e:
        response_content = f'Caught {type(e).__name__} >>> {str(e)} <<<'
        return response_content

def chat_gpt(client):
    prompt, plot_flag = prompts.create_chart_prompt(st.session_state.messages)
    response = ''
    for delta in client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": m["role"], "content": m["content"]} for m in prompt],
                    stream=True,
                ):
                    response += (delta.choices[0].delta.content or "")

    if plot_flag:
        code = extract_python_code(response)
        print(code)
        if code is None:
            st.warning(
                "Couldn't find data to plot in the chat. Check if the number of tokens is too low for the data at hand.",
                icon="🚨"
            )
        else:
            code = code.replace("fig.show()", "")
            code += "st.plotly_chart(fig, theme='streamlit', use_container_width=True)"
            #st.write(f"```{code}")
            try:
                exec(code)
            except Exception as ex:
                st.exception(ex)

    return response

def snow_arctic():
    plot_flag = False

    if "plot" in st.session_state["messages"][-1]["content"].lower():
        plot_flag = True
        code_prompt = """
            Generate the code for plotting the previous data or {data} but always use some type of data as per request,
            in the requested format. The solution should be given using Plotly only.
            Always Return the code in the following format: ```python <code>```
        """
        if "results" in st.session_state["messages"][-1]:
            code_prompt = code_prompt.format(data="use data : "+st.session_state["messages"][-1]["results"])
        else:
            code_prompt = code_prompt.format(data="use random data if there is no data in previous messages")
        
        print(code_prompt)

        st.session_state["messages"].append({
            "role": "assistant",
            "content": code_prompt
        })

    response_content = ""
    prompt = []
    for dict_message in st.session_state.messages:
        dict_message = dict_message.replace("'","\\'")
        if dict_message["role"] == "user":
            prompt.append("<|im_start|>user\n" + dict_message["content"] + "<|im_end|>")
        else:
            prompt.append("<|im_start|>assistant\n" + dict_message["content"] + "<|im_end|>")
    
    prompt.append("<|im_start|>assistant")
    prompt.append("")
    try:        
        # Execute the LLM query in Snowflake
        query = f"select snowflake.cortex.complete('{SNOW_ARCTIC}', '{prompt}') AS response"

        df = pd.DataFrame(session.sql(query).collect())
        
        # Extract the response
        response_content = df.iloc[0]['RESPONSE'].replace("'", "\\'")

        if plot_flag:
            code = extract_python_code(response_content)
            #print(code)
            if code is None:
                st.warning(
                    "Couldn't find data to plot in the chat. Check if the number of tokens is too low for the data at hand.",
                    icon="🚨"
                )
            else:
                code = code.replace("fig.show()", "")
                code += "st.plotly_chart(fig, theme='streamlit', use_container_width=True)"
                #st.write(f"```{code}")
                try:
                    exec(code)
                except Exception as ex:
                    st.exception(ex)
        
    except Exception as e:
        response_content = f'Caught {type(e).__name__} >>> {str(e)} <<<'
    
    return response_content

#def snow_arctic():
#    plot_flag = False
#
#    if "plot" in st.session_state["messages"][-1]["content"].lower():
#        plot_flag = True
#        code_prompt = """
#            Generate the code for plotting the previous data or {data} but always use some type of data as per request,
#            in the requested format. The solution should be given using Plotly only.
#            Always Return the code in the following format: ```python <code>```
#        """
#        if "results" in st.session_state["messages"][-1]:
#            code_prompt = code_prompt.format(data="use data : "+st.session_state["messages"][-1]["results"])
#        else:
#            code_prompt = code_prompt.format(data="use random data if there is no data in previous messages")
#        
#        print(code_prompt)
#
#        st.session_state["messages"].append({
#            "role": "assistant",
#            "content": code_prompt
#        })
#
#    full_response = ""
#    for part in generate_arctic_response():
#        full_response += part
#
#    #print(full_response)
#    if plot_flag:
#        code = extract_python_code(full_response)
#        print(code)
#        if code is None:
#            st.warning(
#                "Couldn't find data to plot in the chat. Check if the number of tokens is too low for the data at hand.",
#                icon="🚨"
#            )
#        else:
#            code = code.replace("fig.show()", "")
#            code += "st.plotly_chart(fig, theme='streamlit', use_container_width=True)"
#            #st.write(f"```{code}")
#            try:
#                exec(code)
#            except Exception as ex:
#                st.exception(ex)
#
#    return full_response

def extract_python_code(text):
    pattern = r'```python\s(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    if not matches:
        return None
    else:
        return matches[0]  

def generate_arctic_response():
    prompt = []
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            prompt.append("<|im_start|>user\n" + dict_message["content"] + "<|im_end|>")
        else:
            prompt.append("<|im_start|>assistant\n" + dict_message["content"] + "<|im_end|>")
    
    prompt.append("<|im_start|>assistant")
    prompt.append("")
    
    for event in replicate.stream("snowflake/snowflake-arctic-instruct",
                           input={"prompt": "\n".join(prompt),
                                  "prompt_template": r"{prompt}",
                                  "temperature": 0.6,
                                  "top_p": 0.9,
                                  }):
        yield str(event)