# ------------!
# AWS imports
import boto3

# ------------!
# LangChain imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_aws import ChatBedrock
from langchain_aws import AmazonKnowledgeBasesRetriever
from langchain_community.callbacks.manager import get_bedrock_anthropic_callback

# ------------------------------------------------------
# Langchain builder class


class ChainBuilder:

    def __init__(
        self,
        retriever_id,
        region_name,
        model_id,
        temperature,
        top_p,
        kb_retrieval_config=None,
    ):
        self.retriever_id = retriever_id
        self.region_name = region_name
        self.model_id = model_id

        self.kb_retrieval_config = kb_retrieval_config or {
            "vectorSearchConfiguration": {
                "numberOfResults": 5,
                "overrideSearchType": "SEMANTIC",
            }
        }  # Default retrieval config

        # AWS Bedrock settings
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=self.region_name,
        )

        # Default LLM model kwargs
        self.model_kwargs = {
            "max_tokens": 2048,
            "temperature": temperature,
            "top_k": 250,
            "top_p": top_p,
            "stop_sequences": ["\n\nHuman"],
        }

        # Default prompt template
        self.template = """Human: You are a product salesperson AI system that specializes specifically in email correspondence.
        provide an answer based on facts only.
        Use the following pieces of information to be provided by the {{ context }} a concise answer to the question enclosed in {{ question }} tags.
        The answer structure should be starting with reaching back the person that asked the question and followed by answering the question,
        and finishing with polite ending, such as "Best regards" 
        If you do not have enough facts to generate a successful sales pitch look at a different {{ context }} source provided.
        The answer should be written in a human-centric, keep it simple, no need for high-end words

        If no information can be found 
        just say that you do not have enough information, don't try to make up false facts.

        CONTEXT: {% for doc in context %}
                     {{ doc.page_content }}
                 {% endfor %}

        USER: {{ question }}
        """
        self.prompt = ChatPromptTemplate.from_template(
            self.template, template_format="jinja2"
        )

        # Initialize retriever dynamically
        self.retriever = self.initialize_retriever()

        # Initialize dynamic metadata document
        self.metadata_document_path = self.get_metadata_documents_path()

        # Initialize model
        self.model = ChatBedrock(
            client=self.bedrock_runtime,
            model_id=self.model_id,
            model_kwargs=self.model_kwargs,
        )

        # Chain initialization
        self.chain = self.build_chain()

    def initialize_retriever(self):
        # Amazon Bedrock - KnowledgeBase Retriever
        return AmazonKnowledgeBasesRetriever(
            knowledge_base_id=self.retriever_id,
            retrieval_config=self.kb_retrieval_config,
        )

    def get_metadata_documents_path(self):
        return ["location", "s3Location", "uri"]

    def build_chain(self):
        return (
            RunnableParallel(
                {"context": self.retriever, "question": RunnablePassthrough()}
            )
            .assign(response=self.prompt | self.model | StrOutputParser())
            .pick(["response", "context"])
        )

    # Dynamic methods to update values
    def update_model_kwargs(self, **kwargs):
        self.model_kwargs.update(kwargs)
        self.retriever = self.initialize_retriever()
        self.chain = self.build_chain()

    def update_prompt_template(self, new_template):
        self.template = new_template
        self.prompt = ChatPromptTemplate.from_template(
            self.template, template_format="jinja2"
        )
        self.retriever = self.initialize_retriever()
        self.chain = self.build_chain()

    def update_model_id(self, new_model_id):
        self.model_id = new_model_id
        self.model = ChatBedrock(
            client=self.bedrock_runtime,
            model_id=self.model_id,
            model_kwargs=self.model_kwargs,
        )

    def update_kb_retrieval_config(self, new_config):
        self.kb_retrieval_config = new_config
        self.retriever = AmazonKnowledgeBasesRetriever(
            knowledge_base_id=self.retriever_id,
            retrieval_config=self.kb_retrieval_config,  # Apply new config
        )
        self.metadata_documents_path = self.get_metadata_documents_path()
        self.chain = self.build_chain()

    def update_retriever_id(self, new_retriever_id):
        self.retriever_id = new_retriever_id
        self.retriever = self.initialize_retriever()
        self.metadata_documents_path = self.get_metadata_documents_path()
        self.chain = self.build_chain()
