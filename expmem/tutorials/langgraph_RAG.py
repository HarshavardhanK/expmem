import os

from dotenv import load_dotenv
load_dotenv()

from typing import Annotated, Literal, Sequence
from typing_extensions import TypedDict

from pydantic import BaseModel, Field

from langchain import hub
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition

urls = [
    "https://lilianweng.github.io/posts/2023-06-23-agent/",
    "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
    "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
]

docs = [WebBaseLoader(url).load() for url in urls]
docs_list = [item for sublist in docs for item in sublist]

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=100,
    chunk_overlap=50
)

doc_splits = text_splitter.split_documents(docs_list)

vectore_store = Chroma.from_documents(
    documents=doc_splits,
    collection_name="rag-chroma",
    embedding=OpenAIEmbeddings(),)

retriever = vectore_store.as_retriever()

from langchain.tools.retriever import create_retriever_tool

retriever_tool = create_retriever_tool(retriever,
                                       'retrieve_blog_posts',
                                       "Search and return information about Lilian Weng Blog Posts on LLM Agents, prompt engineering, and adversarial attacks on LLMs.")

tools = [retriever_tool]

# Agent State

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

## Edges

def grade_documents(state) -> Literal['generate', 'rewrite']:
    """
    
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (messages): the current state

    Returns:
        str: A decision for whether the documents are relevant or not
    
    """

    print("----- Checking if documents are relevant -----")

    class grade(BaseModel):
        """Binary score for relevance check"""

        binary_score: str = Field(description="Relevance score 'yes' or 'no'")

        # LLM
    model = ChatOpenAI(temperature=0, 
                           model='gpt-4o-mini-2024-07-18', 
                           api_key=os.getenv("OPENAI_API_KEY"), 
                           streaming=True)
        
    llm_with_tool = model.with_structured_output(grade)

    prompt = PromptTemplate(
        template="""You are a grader assessing relevance of a retrieved document to a user question. \n
                    Here is the retrieved document: \n\n {context} \n\n
                    Here is the user question: {question} \n

                    If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
                    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question.
        """
        ,
        input_variables=["context", "question"]
    )

    chain = prompt | llm_with_tool

    messages = state["messages"]
    last_message = messages[-1]

    question = messages[0].content
    docs = last_message.content

    scored_result = chain.invoke({"question": question, "context": docs})
    score = scored_result.binary_score

    if score == "yes":
        print("----- Documents are relevant -----")
        return "generate"
    
    else:
        print("----- Documents are not relevant -----")
        return "rewrite"

def agent(state):
    """
    Invokes the agent model to generate a response based on the current state. 
    Given the question it will decide to retrieve using the retriever tool, or simply end.
    
    Args:
        state (messages): the current state

    Returns:
        dict: the updated state with the agent resposne appended to the messages
    
    """ 

    print("---- CALL AGENT ----")
    messages = state["messages"]
    model = ChatOpenAI(temperature=0,
                          model_name="gpt-4o-mini-2024-07-18", 
                          api_key=os.getenv("OPENAI_API_KEY"),
                          streaming=True)
    
    model = model.bind_tools(tools)

    response = model.invoke(messages)

    return {"messages": [response]}

def rewrite(state):
    """
    Transforms the query to produce a better question

    Args:
        state (messages) : the current state

    Returns:
        dict: the updated state with re-phrased question
    
    """

    print("---- TRANFORM QUERY ----")
    messages = state["messages"]
    question = messages[0].content

    msg = [
        HumanMessage(
            content=f""" \n
                    Look at the input and try to reason about the underlying semantic intent  / meaning. \n
                     Here is the initial question: 
                      \n ------------ \n
                       {question}
                    \n ----------- \n 
                    
                    Formulate an improved question: """
        )
    ]

    model = ChatOpenAI(temperature=0, 
                       model='gpt-4o-mini-2024-07-18', 
                       api_key=os.getenv("OPENAI_API_KEY"), 
                       streaming=True)
    
    response = model.invoke(msg)

    return {"messages": [response]}

def generate(state):
    """
    Generate answer

    Args:
        state(messages): the current state

    Returns:
        dict: the updated state generated answer
    """

    print("---- GENERATE ----")
    messages = state["messages"]
    question = messages[0].content
    last_message = messages[-1]

    docs = last_message.content

    #Prompt
    prompt = hub.pull("rlm/rag-prompt")

    llm = ChatOpenAI(temperature=0,
                     model_name="gpt-4o-mini-2024-07-18", 
                     api_key=os.getenv("OPENAI_API_KEY"),
                     streaming=True)
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    rag_chain = prompt | llm | StrOutputParser()

    # Run
    response = rag_chain.invoke({"context": docs, "question": question})

    return {"messages": [response]}

print("*" * 20 + "Prompt[rlm/rag-prompt]" + "*" * 20)
prompt = hub.pull("rlm/rag-prompt").pretty_print()

from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode

workflow = StateGraph(AgentState)

workflow.add_node("agent", agent)
retrieve = ToolNode([retriever_tool])
workflow.add_node("retrieve", retrieve)
workflow.add_node("rewrite", rewrite)

workflow.add_node(
    "generate",
    generate
)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    tools_condition,
    {
        "tools": "retrieve",
        END: END
    },
)

workflow.add_conditional_edges(
    "retrieve",
    grade_documents,
)

workflow.add_edge("generate", END)
workflow.add_edge("rewrite", "agent")

graph = workflow.compile()

import pprint

inputs = {
    "messages": [
        ("user", "What does Lilian Weng say about the types of agent memory?"),
    ]
}

for output in graph.stream(inputs):
    for key, value in output.items():
        pprint.pprint(f"Output from node '{key}': ")
        pprint.pprint("----")
        pprint.pprint(value, indent=2, width=80, depth=None)

    pprint.pprint("\n-----\n")