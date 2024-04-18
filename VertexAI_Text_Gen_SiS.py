#SiS version of Google sample app using Snowflake External Access
#Original code: https://github.com/GoogleCloudPlatform/generative-ai/tree/main/language/sample-apps/chat-streamlit
#Please run ensure you have successfully run Vertex_Demo.sql and created the GET_VERTEX_TEXT_GENERATION Stored Procedure
#Author Alex Ross, Senior Sales Engineer, Snowflake
#Last Modified 18th April 2024

import streamlit as st
from snowflake.snowpark.context import get_active_session

def reset_session() -> None:
    st.session_state["temperature"] = 0.0
    st.session_state["token_limit"] = 256
    st.session_state["top_k"] = 40
    st.session_state["top_p"] = 0.8
    st.session_state["debug_mode"] = False
    st.session_state["prompt"] = []
    st.session_state["response"] = []

def hard_reset_session() -> None:
    st.session_state = {states: [] for states in st.session_state}

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

st.set_page_config(
    page_title="Vertex PaLM Text Generation API",
    page_icon=":robot:",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "# This app shows you how to use Vertex PaLM Text Generator API"
    },
)

# creating session states
create_session_state()

st.image('https://raw.githubusercontent.com/GoogleCloudPlatform/generative-ai/main/language/sample-apps/chat-streamlit/image/palm.jpg', width=None)
st.title(":red[PaLM 2] :blue[Vertex AI] Text Generation")

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


with st.container():
    st.write("Current Generator Settings: ")
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

    prompt = st.text_area("Add your prompt: ", height=100)
    if prompt:
        st.session_state["prompt"].append(prompt)
        session = get_active_session()
        with st.spinner("PaLM is working to generate, wait....."):
            response = session.call("DEMOS.VERTEX.get_vertex_text_generation",
                prompt,
                st.session_state["temperature"],
                st.session_state["token_limit"],
                st.session_state["top_p"],
                st.session_state["top_k"],
            )
            st.session_state["response"].append(response)
            st.markdown(response)