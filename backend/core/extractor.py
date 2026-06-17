# Actionable Items, Decisions, Questions

from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
import os
from dotenv import load_dotenv
load_dotenv()

def get_llm():
    return ChatMistralAI(model="mistral-small-latest", mistral_api_key = os.getenv("MISTRAL_API_KEY"), temperature=0.2)

def build_chain(system_prompt: str):
    llm = get_llm()
    return (
        RunnablePassthrough()
        | RunnableLambda(lambda x: {"text": x})
        | ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{text}"),
        ])
        | llm
        | StrOutputParser()
    )
    
def extract_action_items(transcript)->str:
    chain = build_chain(
        "From the transcript, extract any action items, recommendations, or tasks mentioned. "
        "For each provide:\n"
        "- Description\n"
        "- Who it applies to (if mentioned, else write 'General audience')\n"
        "- Timeline (if mentioned, else write 'Not specified')\n\n"
        "Format as a numbered list. If none found say 'No action items found.'"
    )
    return chain.invoke(transcript)

def extract_key_decisions(transcript: str) -> str:
    chain = build_chain(
        "From the transcript, extract all key insights, findings, or important conclusions. "
        "Format as a numbered list. If none found say 'No key insights found.'"
    )
    return chain.invoke(transcript)

def extract_questions(transcript: str) -> str:
    chain = build_chain(
        "From the transcript, extract all questions posed, problems raised, or topics needing "
        "further exploration. Format as a numbered list. If none found say 'No questions found.'"
    )
    return chain.invoke(transcript)

