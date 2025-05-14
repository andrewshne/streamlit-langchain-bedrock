# streamlit-langchain-bedrock project

License MIT for educational purposes

## Description

This project is designed for creating a streamlit chatbot application using AWS Bedrock models and retrievers, together with LangChain library for agent creation.

In this project we will have a main page and the chat page, in the chat page there will be dynamic customization of the model parameters, for now the capabilities are for Temperature, Top p and Top k, model selection.

## Dir structure

```bash
.
├── .streamlit
│   └── config.toml
├── pages
│   └── streamlit-rag-model-selection.py
├── README.md
├── Reports 
├── requirements.txt
├── streamlit-rag-main.py
└── utils
    ├── Langchain_builder.py
    └── RAG_Helpers.py
```

### .streamlit

Dir for streamlit configs, in this case the config was for the theme in TOML format:

Docs:

* <https://docs.streamlit.io/develop/concepts/configuration/theming>
* <https://docs.streamlit.io/develop/api-reference/configuration/config.toml>

### Pages

Dir to store streamlit pages, for every streamlit app page `.py` file stored in this dir it will generate a page for the app, in here we have the Chatbot page

### Reports

Dir to store calculations reports, cost-wise and token-wise for every iteration, Run_costs.txt for calculated tokens and cost for every model invocation using the `get_bedrock_anthropic_callback` function, additionally a custom function to have daily accumulation of the costs of the model invocation runs.

### utils

Consists of 2 helper modules:

#### Bedrock agent builder

For agent creation with given model (from bedrock) and retriever (also from bedrock, currently works with kendra and knowledge base), with the options to update and change configurations such as prompt template and config file for the retriever.

#### RAG helpers

Helper functions for citations attachment for every answer of the agent to the user input (e.g. Which file it used for context and what is the context and overall score of context relevancy)

The accumulated helper function to create a daily report of the cost usage of the model.

### streamlit-rage-main

The first page and driver code for the main streamlit application

---

If you wish to run the solution by your self, clone this project and follow the instructions below

## Instructions to run

### Perquisites

* Since this application is based on using Bedrock resources make sure you have a Knowledge base or Kendra ready to be used since the application will need either ID for the retriever.

* Bedrock model that will be used as the main query LLM for the Agent (Currently using Haiku and Sonnet)

In order to run the application it is advised to create a virtual environment

```bash
python -m venv streamlitvenv
```

If activation is needed run

#### Windows

```bash
streamlitvenv\Scripts\activate
```

#### Mac/linux

```bash
source streamlitvenv/bin/activate
```

On the `venv` run `python -r requirements.txt`

after package installation and all perquisites have met run

```bash
streamlit run streamlit-rag-main.py
```

### IMPORTANT NOTE

Before running on the application make sure that the retriever is ready with data synced already, for the scope of this project data will not be provided, this is up to whoever clones this repo and wish to run this solution, to BYOD(Bring Your Own Data).
