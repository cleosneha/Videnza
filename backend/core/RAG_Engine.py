import os
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from core.vector_store import build_vector_store, load_vector_store, get_retriever

def get_llm():
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.3,
    )

def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])

def build_rag_chain(transcript: str, namespace: str):
    if not namespace:
        raise ValueError("namespace is required to build RAG chain")
    if not transcript or not transcript.strip():
        raise ValueError("transcript is empty — cannot build RAG chain")

    #print(f"[RAG] Building RAG chain for namespace: {namespace}")
    vector_store = build_vector_store(transcript, namespace=namespace)
    retriever = get_retriever(vector_store, k=4)
    #print(f"[RAG] Retriever created for namespace: {namespace}")

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [(
            "system",
            """You are an expert content analyst. Answer the user's question 
based ONLY on the transcript context provided below.

If the answer is not found in the context, say: 
"I could not find this information in the transcript."

Always be concise and precise. If quoting someone, mention who said it.

Context from transcript:
{context}""",
        ),
        ("human", "{question}"),
    ])

    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    #print(f"[RAG] RAG chain ready for namespace: {namespace}")
    return rag_chain


def load_rag_chain(namespace: str):
    if not namespace:
        raise ValueError("namespace is required to load RAG chain")

    #print(f"[RAG] Loading RAG chain for namespace: {namespace}")
    vector_store = load_vector_store(namespace=namespace)
    retriever = get_retriever(vector_store)
    #print(f"[RAG] Retriever loaded for namespace: {namespace}")

    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert content analyst. Answer the user's question 
based ONLY on the transcript context provided below.

If the answer is not found in the context, say: 
"I could not find this information in the transcript."

Always be concise and precise. If quoting someone, mention who said it.

Context from transcript:
{context}""",
        ),
        ("human", "{question}"),
    ])

    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def ask_question(rag_chain, question: str) -> str:
    #print(f"Question: {question}")
    answer = rag_chain.invoke(question)
    #print(f"Answer: {answer}")
    return answer
