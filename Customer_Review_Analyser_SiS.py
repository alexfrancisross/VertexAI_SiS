#SiS Customer Review Analyser App using Snowflake External Access & Vertex AI
#Please run ensure you have successfully run Vertex_Demo.sql and created the GET_VERTEX_REVIEW_SENTIMENT_UDF Function
#Author Alex Ross, Senior Sales Engineer, Snowflake
#Last Modified 18th April 2024

import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd
import json
from snowflake.snowpark.functions import col, lit, sum as sum_, max as max_, count as count_

def reset_session() -> None:
    st.session_state["temperature"] = 0.0
    st.session_state["token_limit"] = 256
    st.session_state["top_k"] = 40
    st.session_state["top_p"] = 0.8
    st.session_state["debug_mode"] = False
    st.session_state["prompt"] = []
    st.session_state["response"] = []

def create_session_state():
    if "temperature" not in st.session_state:
        st.session_state["temperature"] = 0.0
    if "token_limit" not in st.session_state:
        st.session_state["token_limit"] = 256
    if "top_k" not in st.session_state:
        st.session_state["top_k"] = 40
    if "top_p" not in st.session_state:
        st.session_state["top_p"] = 0.8
    if "debug_mode" not in st.session_state:
        st.session_state["debug_mode"] = False
    if "prompt" not in st.session_state:
        st.session_state["prompt"] = []
    if "response" not in st.session_state:
        st.session_state["response"] = []

def dataframe_with_selections(df):
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Select", False)

    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={"Select": st.column_config.CheckboxColumn(required=True)},
        disabled=df.columns,
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Select]
    return selected_rows.drop('Select', axis=1)

def write_customer_review(selection, index):
    st.title(":snowflake: :green[Customer Review]")   
    st.write("**Customer**: " + selection["CUSTOMER_NAME"][index])
    st.write('**Review**: ' + selection["REVIEW"][index])
    st.write('**Review Date**: ' + str(selection["REVIEW_DATE"][index]))
    st.write('**Rating**: ' + str(selection["RATING"][index]))

def write_vertex_response(json_resp):
    col1, col2 = st.columns([2,20])
    with col1:
        st.image('https://lh3.googleusercontent.com/e5M3Bi_o8iVajobAcS0LLDDJ2RN4LzchraKjfEKWvXaTkBw2WU50kuTnF6xHzMOifL6DMe16SCUqNt5w2gB9ZA=w80-h80', width=60)
    with col2:
        st.title(":blue[Vertex AI] Response")
    st.write("**Summary**: " + json_resp["summary"])
    st.write("**Product**: " + json_resp["product"])
    st.write("**Sentiment**: " + json_resp["sentiment"])
    st.write("**Explanation**: " + json_resp["explanation"])

st.set_page_config(
    page_title="Customer Review Analyser",
    page_icon=":snowflake:",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "# This app is a sample customer review analyser using Snowflake External Access & the Vertex PaLM Text Generator API"
    },
)

with st.sidebar:
    st.image('https://raw.githubusercontent.com/GoogleCloudPlatform/generative-ai/main/language/sample-apps/chat-streamlit/image/sidebar_image.jpg', width=None)
    st.write("Model Settings:")

    # define the temeperature for the model
    temperature_value = st.slider("Temperature :", 0.0, 1.0, 0.2)
    st.session_state["temperature"] = temperature_value

    # define the temeperature for the model
    token_limit_value = st.slider("Token limit :", 1, 1024, 256)
    st.session_state["token_limit"] = token_limit_value

    # define the temeperature for the model
    top_k_value = st.slider("Top-K  :", 1, 40, 40)
    st.session_state["top_k"] = top_k_value

    # define the temeperature for the model
    top_p_value = st.slider("Top-P :", 0.0, 1.0, 0.8)
    st.session_state["top_p"] = top_p_value

    if st.button("Reset Session"):
        reset_session()

# creating session states
create_session_state()

st.title(":shopping_trolley: Customer Review Analyser 	:bar_chart:")
st.subheader(":snowflake: Powered by Snowflake & Vertex AI")
session = get_active_session()

df_reviews = session.table("DEMOS.VERTEX.REVIEWS")

col1, col2 = st.columns(2)
with col1:
    chart_data = df_reviews.group_by("REVIEW_DATE").agg((count_("*")).alias("REVIEW_COUNT"))
    st.line_chart(chart_data, x = chart_data.columns[0], y = chart_data.columns[1], color="#29B5E8")
with col2:
    chart_data = df_reviews.group_by("RATING").agg((count_("*")).alias("REVIEW_COUNT"))
    st.bar_chart(chart_data, x = chart_data.columns[0], y = chart_data.columns[1], color = "#71D3DC")

rating_min, rating_max = st.select_slider('Filter Ratings To Display:',options=[1,2,3,4,5],value=(1, 5))

if rating_min or rating_max:
    st.write("**Reviews Matching Rating Filter**")
    reviews = df_reviews.filter(f"RATING >= {rating_min} AND RATING <={rating_max}").to_pandas()  
    selection = dataframe_with_selections(reviews)

    st.write("Current Vertex AI Settings: ")
    # if st.session_state['temperature'] or st.session_state['debug_mode'] or :
    st.write(
        "Temperature: ",
        st.session_state["temperature"],
        " \t \t Token limit: ",
        st.session_state["token_limit"],
        " \t \t Top-K: ",
        st.session_state["top_k"],
        " \t \t Top-P: ",
        st.session_state["top_p"],
        " \t \t Debug Model: ",
        st.session_state["debug_mode"],
    )
    
    if st.button("Submit To Vertex GenAI"):
        if selection.empty:
            st.write("Please select at least one review to submit to Vertex AI")
        for index in selection.index:
            session = get_active_session()
            col1, col2 = st.columns(2)
            with col1:
                write_customer_review(selection, index)
            with col2:        
                with st.spinner("PaLM is working to generate, wait....."):
                    review = selection["REVIEW"][index].replace("'", "\\'")
                    response = session.sql(f"SELECT DEMOS.VERTEX.GET_VERTEX_REVIEW_SENTIMENT_UDF(\
                        '{review}',\
                        '{st.session_state['temperature']}',\
                        '{st.session_state['token_limit']}',\
                        '{st.session_state['top_p']}',\
                        '{st.session_state['top_k']}') AS RESPONSE")
                    json_resp = json.loads(response.to_pandas()["RESPONSE"][0])
                    write_vertex_response(json_resp)
            st.markdown("""---""")
        
    
    
