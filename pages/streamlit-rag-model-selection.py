# ------------------------------------------------------
# Streamlit
# Streamlit chatbot Multi Selection
# ------------------------------------------------------
# ------------!
# LangChain imports
from langchain_community.callbacks.manager import get_bedrock_anthropic_callback

# ------------!
# Misc imports
from datetime import datetime
from dotenv import load_dotenv
import os
import io  # For report file read/write

# ------------!
# Local imports
from utils.RAG_Helpers import (
    accumulated_daily,
    extract_citations,
    get_dynamic_metadata_value,
)
from utils.Langchain_builder import ChainBuilder


# ------------!
# Streamlit imports
import streamlit as st
from streamlit_chat import message

# ------------------------------------------------------

# Date time var
dt = datetime.now()

# load .env file
load_dotenv()

# Citations and context init arrays
citations_page_content = {}
citations_metadata_s3_uri = {}
citations_metadata_score = {}
citations_metadata = {}

# ------------------------------------------------------
# Global vars and global functions

# Region vars
region_name = "us-east-1"


# Global variables, either from .env or default hardcoded local file path
EXTRACTED_KB_ID = os.getenv("EXTRACTED_KB_ID", "<ENTER PATH TO YOUR EXTRACTED KB ID>")

# Read file of kb_id
with open(EXTRACTED_KB_ID, "r") as file:
    retriever_id = file.read()


# Generate the default chain with variables coming from the sidebar picker
def generate_response_chain_from_selection(model, temperature, top_p):
    return ChainBuilder(
        retriever_id=retriever_id,
        model_id=model,
        region_name=region_name,
        temperature=temperature,
        top_p=top_p,
    )


# Generate the custom chain with variables coming from the sidebar picker and new templates and configs
# For now the templates and configs are coming from the code and not user input
def generate_response_custom_model(template, config, model, temperature, top_p):
    custom_chain_builder = ChainBuilder(
        retriever_id=retriever_id,
        model_id=model,
        region_name=region_name,
        temperature=temperature,
        top_p=top_p,
    )
    custom_chain_builder.update_kb_retrieval_config(new_config=config)
    custom_chain_builder.update_prompt_template(new_template=template)

    return custom_chain_builder


# !------
# Customize the free roam chain
new_config = {
    "vectorSearchConfiguration": {
        "numberOfResults": 3,
        "overrideSearchType": "HYBRID",
    }
}

new_template = """Human: You are a product salesperson AI system that specializes specifically in email correspondence.
        Use the following pieces of information to be provided by the {{ context }} a concise answer to the question enclosed in {{ question }} tags.
        The answer structure should be starting with reaching back the person that asked the question and followed by answering the question,
        and finishing with polite ending
        The answer should be written in a human-centric, keep it simple, no need for high-end words

        If no information can be found try to bring any useful information you can, even if they are not based on the facts provided.

        CONTEXT: {% for doc in context %}
                     {{ doc.page_content }}
                 {% endfor %}

        USER: {{ question }}
        """
# -----!
# ------------------------------------------------------
# Streamlit

# Page title
st.set_page_config(page_title="Streamlit chatbot Multi Selection")


# Clear Chat History function
def clear_screen():
    st.session_state["user_responses"] = ["Hey"]
    st.session_state["bot_responses"] = ["Hey there! How may I help you today?"]


# Side bar for the custom metrics selection and model selection
# Sub models here reference the free roam custom chain build or the default ChainBuilder
with st.sidebar:
    st.title("Streamlit chatbot Multi Selection")
    st.button("Clear Screen", on_click=clear_screen)

    st.subheader("Models and parameters")
    model = st.selectbox(
        "Select a model",
        (
            "anthropic.claude-3-haiku-20240307-v1:0",
            "anthropic.claude-3-sonnet-20240229-v1:0",
        ),
        key="model",
    )

    custom_sub_model = st.selectbox(
        "Select a model",
        (
            "Free roam",
            "Facts only",
        ),
        key="custom_sub_model",
    )

    temperature = st.sidebar.slider(
        "temperature",
        min_value=0.01,
        max_value=1.0,
        value=0.7,
        step=0.01,
        help="Randomness of generated output",
    )

    if temperature < 0.1:
        st.warning(
            "Values approaching 0 produces deterministic output. Recommended starting value is 0.7"
        )

    top_p = st.sidebar.slider(
        "top_p",
        min_value=0.01,
        max_value=1.0,
        value=0.9,
        step=0.01,
        help="Top p percentage of most likely tokens for output generation",
    )

# ------------------------------------------------------
# Streamlit-Chat method

# Initialize session state variables
if "user_responses" not in st.session_state:
    st.session_state["user_responses"] = ["Hey"]
if "bot_responses" not in st.session_state:
    st.session_state["bot_responses"] = ["Hey there! How may I help you today?"]

input_container = st.container()
response_container = st.container()

# Capture user input and display bot responses
user_input = st.text_input("You: ", "", key="input")

with response_container:
    if user_input:
        with get_bedrock_anthropic_callback() as cb:
            if custom_sub_model == "Facts only":
                main_chain = generate_response_chain_from_selection(
                    model, temperature, top_p
                )
                response = main_chain.chain.invoke(user_input)
            elif custom_sub_model == "Free roam":
                main_chain = generate_response_custom_model(
                    new_template, new_config, model, temperature, top_p
                )
                response = main_chain.chain.invoke(user_input)
            else:
                st.write("Invocation failed due to no selection in custom sub model")

            # print(response["response"])
            # print(user_input)

            # cb per consumption print
            with io.open(".\\Reports\\Run_costs.txt", "a", encoding="utf8") as f:
                f.write(f"{str(dt)}\n")
                f.write("########\n")
                f.write(f"{str(cb)}\n")
                f.write("!==================!\n")

            accumulated_daily(
                cb.total_cost, dt
            )  # Accumulated daily report generator function for total costs

            citations = extract_citations(response["context"])

            for idx, citation in enumerate(citations):
                citation_key = f"citation_{idx+1}"

                citations_page_content[citation_key] = [citation.page_content]
                citations_metadata_score[citation_key] = [citation.metadata["score"]]
                citations_metadata_s3_uri[citation_key] = [
                    get_dynamic_metadata_value(
                        citation.metadata,
                        main_chain.metadata_document_path,
                    )
                ]

            st.session_state.user_responses.append(user_input)
            st.session_state.bot_responses.append(response["response"])

    if st.session_state["bot_responses"]:
        for i in range(len(st.session_state["bot_responses"])):
            # print(st.session_state["bot_responses"][i])
            message(
                st.session_state["user_responses"][i],
                is_user=True,
                key=str(i) + "_user",
                avatar_style="initials",
                seed="Kavita",
            )
            message(
                st.session_state["bot_responses"][i],
                key=str(i),
                avatar_style="initials",
                seed="AI",
            )

        # Stats regarding latest invocation
        with st.expander(f"Show citations page content >"):
            st.write(citations_page_content)
        with st.expander(f"Show citations s3 location >"):
            st.write(citations_metadata_s3_uri)
        with st.expander(f"Show citations score >"):
            st.write(citations_metadata_score)


with input_container:
    display_input = user_input
