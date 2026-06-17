from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
#iska main kaam hai input ko bina change kiye aage pass karna, especially jab tum multiple values ke saath dictionary-based pipelines bana rahe ho. - runnable passthrough
#RunnableLambda tab use hota hai jab tum kisi normal Python function ko LangChain pipeline ka part banana chahti ho.
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from dotenv import load_dotenv
load_dotenv()
import os

def get_llm():
    return ChatMistralAI(model="mistral-small-latest", mistral_api_key = os.getenv("MISTRAL_API_KEY"), temperature=0.3)

def split_transcript(transcript:str) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 3000,
        chunk_overlap = 200
    )
    return splitter.split_text(transcript)

def summarize(transcript:str)->str:
    llm = get_llm()
    map_prompt = ChatPromptTemplate.from_messages(
    [
        ("system","Summarize this portion of the transcript concisely in 2-3 sentences."),
        ("human","{text}")
    ]
)
    #Jab bhi koi input aayega, pehle prompt mein daalna, phir llm ko bhejna, phir output parse karna.

    #1. map_chain define hua
    #     ↓
    # 2. transcript split hui
    #     ↓
    # 3. chunks mil gaye
    #     ↓
    # 4. invoke() call hua
    #     ↓
    # 5. har chunk llm ko gaya
    map_chain = map_prompt | llm | StrOutputParser()
    chunks = split_transcript(transcript)
    
    # List Comprehension
    # new_list = [expression for item in iterable]
    chunk_summaries = map_chain.batch(
    [{"text": chunk} for chunk in chunks]
    )
    #separator.join(iterable_of_strings)
    combined= "\n\n".join(chunk_summaries)
    parser = JsonOutputParser()
    parser = JsonOutputParser()

    combined_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are an expert content summarizer.

                Analyze the provided partial summaries of a transcript and generate:

                1. A concise title that captures the main topic (maximum 8 words)
                2. Key bullet-point summary of the main ideas

                Return ONLY valid JSON.

                {format_instructions}

                Note:
                - Strictly follow the provided content.
                - Do not hallucinate.
                - Keep the title concise.
                """
            ),
            (
                "human",
                """
                Partial Summaries:

                {text}
                """
            )
        ]
    )
    combined_chain = (
        RunnablePassthrough()
        | RunnableLambda(lambda x: {"text": x, "format_instructions": parser.get_format_instructions()})
        | combined_prompt
        | llm
        | JsonOutputParser()
    )
    
    return combined_chain.invoke(combined)

# following can also be done as chat prompt template epects the input in {"text" : somevalue} format, so either convert in this format using RunnableLambda or manually

# combined_chain = (
#     combined_prompt
#     | llm
#     | StrOutputParser()
# )

# combined_chain.invoke({
#     "text": combined
# })

