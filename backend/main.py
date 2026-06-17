import shutil
import tempfile

from dotenv import load_dotenv
from core.namespace_manager import cleanup_expired_namespaces, generate_namespace, register_namespace
from utils.audio_processor import process_input
from core.summarize import summarize
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.transcriber import transcribe_all
from core.RAG_Engine import build_rag_chain, ask_question


load_dotenv()

def run_pipeline(source:str, language: str = "english") -> dict:
    #print("Starting AI Video Assistant")

    work_dir = tempfile.mkdtemp(prefix="video-agent-")
    cleanup_expired_namespaces()
    namespace = generate_namespace()
    register_namespace(namespace)

    try:
        chunks = process_input(source=source, output_dir=work_dir)

        transcript = transcribe_all(chunks, language=language, output_dir=work_dir)

        #print(f"Raw transcription(first 300 character): {transcript[:300]}")

        summary_result = summarize(transcript)
        title = summary_result["title"]
        summary_points = summary_result["summary"]

        action_items = extract_action_items(transcript)
        decisions = extract_key_decisions(transcript)
        questions = extract_questions(transcript)

        rag_chain = build_rag_chain(transcript, namespace=namespace)

        return {
            "namespace": namespace,
            "title": title,
            "transcript": transcript,
            "summary": summary_points,
            "action_items": action_items,
            "key_decisions": decisions,
            "open_questions": questions,
            "rag_chain": rag_chain,
        }
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
    
if __name__ == "__main__":
    # CLI entry point
    source = input("Enter YouTube URL or local file path: ").strip()
    language = input("Language (english/hinglish): ").strip() or "english"
    result = run_pipeline(source, language)

    #print("\n" + "=" * 60)
    #print(f"📌 Title: {result['title']}")
    #print(f"\n📋 Summary:\n{result['summary']}")
    #print(f"\n✅ Action Items:\n{result['action_items']}")
    #print(f"\n🔑 Key Decisions:\n{result['key_decisions']}")
    #print(f"\n❓ Open Questions:\n{result['open_questions']}")
    #print("=" * 60)

    # Phase 2 — Chat with your video via RAG
    #print("\n💬 Chat with your video (type 'exit' to quit)\n")
    rag_chain = result["rag_chain"]
    while True:
        question = input("You: ").strip()
        if question.lower() in ["exit", "quit", "q"]:
            #print("👋 Goodbye!")
            break
        if not question:
            continue
        answer = ask_question(rag_chain, question)
        #print(f"\n🤖 Assistant: {answer}\n")
