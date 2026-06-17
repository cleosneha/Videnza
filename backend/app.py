import shutil
import tempfile

import streamlit as st
from core.namespace_manager import (
    cleanup_expired_namespaces,
    ensure_session_namespace,
    get_session_namespace,
    reset_session_namespace,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0F1117;
    color: #E2E8F0;
}
.stApp { background-color: #0F1117; }
.block-container { padding: 2rem 2.5rem 4rem; max-width: 1100px; margin: auto; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Typography ── */
h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 700; letter-spacing: -0.02em; }

/* ── Hero header ── */
.hero {
    text-align: center;
    padding: 3rem 0 2rem;
    border-bottom: 1px solid #1E2330;
    margin-bottom: 2.5rem;
}
.hero-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.18em;
    color: #6C63FF;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 700;
    color: #F8FAFC;
    line-height: 1.15;
    margin: 0 0 0.5rem;
}
.hero-title span { color: #6C63FF; }
.hero-sub {
    font-size: 0.95rem;
    color: #64748B;
    font-weight: 400;
}

/* ── Input card ── */
.input-card {
    background: #161B2C;
    border: 1px solid #1E2748;
    border-radius: 14px;
    padding: 1.8rem 2rem;
    margin-bottom: 2rem;
}

/* ── Pipeline tracker ── */
.pipeline-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    margin: 2rem 0;
    flex-wrap: wrap;
}
.pipe-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.4rem;
    flex: 1;
    min-width: 90px;
}
.pipe-icon {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    border: 2px solid #1E2748;
    background: #0F1117;
    color: #3A4266;
    transition: all 0.3s ease;
}
.pipe-icon.done   { border-color: #6C63FF; background: #1A1838; color: #A99FF5; }
.pipe-icon.active { border-color: #6C63FF; background: #211E4A; color: #6C63FF;
                    box-shadow: 0 0 14px rgba(108,99,255,0.45); }
.pipe-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.06em;
    color: #3A4266;
    text-align: center;
}
.pipe-label.done   { color: #8B83E8; }
.pipe-label.active { color: #6C63FF; }
.pipe-connector {
    height: 2px;
    flex: 1;
    background: #1E2748;
    min-width: 20px;
    margin-bottom: 20px;
}
.pipe-connector.done { background: #6C63FF; }

/* ── Section cards ── */
.result-card {
    background: #161B2C;
    border: 1px solid #1E2748;
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
}
.card-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 1rem;
}
.card-icon { font-size: 1.1rem; }
.card-title {
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #6C63FF;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Transcript box ── */
.transcript-box {
    background: #0C0F1A;
    border: 1px solid #1A2035;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    line-height: 1.8;
    color: #94A3B8;
    max-height: 240px;
    overflow-y: auto;
}

/* ── Bullet items ── */
.bullet-item {
    display: flex;
    gap: 0.6rem;
    align-items: flex-start;
    padding: 0.55rem 0;
    border-bottom: 1px solid #1A2035;
    font-size: 0.88rem;
    color: #CBD5E1;
    line-height: 1.55;
}
.bullet-item:last-child { border-bottom: none; }
.bullet-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #6C63FF;
    margin-top: 0.45rem;
    flex-shrink: 0;
}

/* ── RAG chat ── */
.chat-container {
    background: #0C0F1A;
    border: 1px solid #1A2035;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    max-height: 380px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-bottom: 1rem;
}
.msg-user {
    align-self: flex-end;
    background: #211E4A;
    border: 1px solid #2E2975;
    border-radius: 10px 10px 2px 10px;
    padding: 0.6rem 0.9rem;
    font-size: 0.86rem;
    color: #C4BFFF;
    max-width: 78%;
}
.msg-bot {
    align-self: flex-start;
    background: #161B2C;
    border: 1px solid #1E2748;
    border-radius: 10px 10px 10px 2px;
    padding: 0.6rem 0.9rem;
    font-size: 0.86rem;
    color: #E2E8F0;
    max-width: 82%;
    line-height: 1.6;
}
.msg-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.08em;
    color: #4A5568;
    margin-bottom: 0.2rem;
}

/* ── Streamlit widget overrides ── */
.stTextInput > div > div > input,
.stSelectbox > div > div > div {
    background-color: #0C0F1A !important;
    border: 1px solid #1E2748 !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #6C63FF !important;
    box-shadow: 0 0 0 2px rgba(108,99,255,0.2) !important;
}
div[data-testid="stButton"] > button {
    background: #6C63FF !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.04em !important;
    padding: 0.55rem 1.8rem !important;
    transition: background 0.2s !important;
}
div[data-testid="stButton"] > button:hover {
    background: #5A52E0 !important;
}
.stSelectbox label, .stTextInput label {
    color: #64748B !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stAlert { border-radius: 8px !important; }
div[data-testid="stExpander"] {
    border: 1px solid #1E2748 !important;
    border-radius: 10px !important;
    background: #161B2C !important;
}

/* ── Boot loader ── */
.boot-loader {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 1rem 2.5rem;
    gap: 1.6rem;
}
.boot-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #6C63FF;
    animation: pulse-text 1.4s ease-in-out infinite;
}
@keyframes pulse-text {
    0%, 100% { opacity: 0.5; }
    50%       { opacity: 1; }
}

/* Indigo orbital spinner */
.orbital {
    position: relative;
    width: 56px;
    height: 56px;
}
.orbital-ring {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 2px solid transparent;
    border-top-color: #6C63FF;
    border-right-color: #6C63FF44;
    animation: spin 0.9s linear infinite;
}
.orbital-ring-outer {
    inset: -8px;
    border-width: 1.5px;
    border-top-color: #A99FF540;
    border-right-color: transparent;
    border-bottom-color: transparent;
    border-left-color: #A99FF520;
    animation: spin-reverse 1.5s linear infinite;
}
.orbital-dot {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 10px; height: 10px;
    border-radius: 50%;
    background: #6C63FF;
    box-shadow: 0 0 14px 4px rgba(108,99,255,0.5);
    animation: dot-glow 1.4s ease-in-out infinite;
}
@keyframes spin         { to { transform: rotate(360deg); } }
@keyframes spin-reverse { to { transform: rotate(-360deg); } }
@keyframes dot-glow {
    0%, 100% { box-shadow: 0 0 10px 3px rgba(108,99,255,0.4); }
    50%       { box-shadow: 0 0 22px 7px rgba(108,99,255,0.7); }
}

/* Animated bar track */
.boot-bar-track {
    width: 240px;
    height: 3px;
    background: #1A2035;
    border-radius: 99px;
    overflow: hidden;
}
.boot-bar-fill {
    height: 100%;
    width: 40%;
    background: linear-gradient(90deg, transparent, #6C63FF, #A99FF5, transparent);
    border-radius: 99px;
    animation: bar-sweep 1.3s ease-in-out infinite;
}
@keyframes bar-sweep {
    0%   { transform: translateX(-100%); }
    100% { transform: translateX(350%); }
}

/* Dots row */
.boot-dots {
    display: flex;
    gap: 0.45rem;
    align-items: center;
}
.boot-dot {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: #6C63FF;
    animation: dot-bounce 1.1s ease-in-out infinite;
}
.boot-dot:nth-child(2) { animation-delay: 0.18s; background: #8B83E8; }
.boot-dot:nth-child(3) { animation-delay: 0.36s; background: #A99FF5; }
@keyframes dot-bounce {
    0%, 80%, 100% { transform: translateY(0);    opacity: 0.4; }
    40%            { transform: translateY(-6px); opacity: 1;   }
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">AI · Video · Intelligence</div>
  <div class="hero-title">🎬 Video <span>Assistant</span></div>
  <div class="hero-sub">Transcribe · Summarize · Extract · Chat with any video</div>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for key in ["result", "chat_history", "processing", "current_step"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "chat_history" else []

# Ensure namespace exists — this runs once per session
ns = ensure_session_namespace(st.session_state)
#print(f"[App] Session initialized with namespace: {ns}")


def clear_session_state():
    st.session_state.result = None
    st.session_state.chat_history = []
    st.session_state.processing = None
    st.session_state.current_step = None
    st.session_state.chat_input = ""


def render_pipeline(active_step: int, done_steps: list):
    """Render the pipeline progress tracker."""
    steps = [
        ("📥", "Ingest"),
        ("🎙️", "Transcribe"),
        ("📝", "Summarize"),
        ("🔍", "Extract"),
        ("🧠", "Build RAG"),
    ]
    html = '<div class="pipeline-wrap">'
    for i, (icon, label) in enumerate(steps):
        if i > 0:
            cls = "done" if (i - 1) in done_steps else ""
            html += f'<div class="pipe-connector {cls}"></div>'
        if i in done_steps:
            step_cls = "done"
            label_cls = "done"
        elif i == active_step:
            step_cls = "active"
            label_cls = "active"
        else:
            step_cls = ""
            label_cls = ""
        html += f"""
        <div class="pipe-step">
          <div class="pipe-icon {step_cls}">{icon}</div>
          <div class="pipe-label {label_cls}">{label}</div>
        </div>"""
    html += '</div>'
    return html


def render_bullets(items):
    """Render a list of strings as styled bullets."""
    if isinstance(items, str):
        items = [line.strip("- •*").strip() for line in items.strip().split("\n") if line.strip()]
    html = ""
    for item in items:
        if item:
            html += f'<div class="bullet-item"><div class="bullet-dot"></div><span>{item}</span></div>'
    return html


# ── Input section ─────────────────────────────────────────────────────────────
st.markdown('<div class="input-card">', unsafe_allow_html=True)
col1, col2 = st.columns([3, 1])
with col1:
    source = st.text_input(
        "Video Source",
        placeholder="https://youtube.com/watch?v=... or /path/to/video.mp4",
        key="source_input",
    )
with col2:
    language = st.selectbox("Language", ["english", "hinglish"], key="lang_select")

_, btn_col, _ = st.columns([2, 1, 2])
with btn_col:
    run_btn = st.button("▶  Analyze Video", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── Processing pipeline ───────────────────────────────────────────────────────
if run_btn:
    if not source.strip():
        st.warning("Please enter a YouTube URL or local file path.")
    else:
        #print(f"[App] Run button clicked — source: {source[:80]}... language: {language}")
        current_namespace = get_session_namespace(st.session_state)
        #print(f"[App] Current namespace before reset: {current_namespace}")
        cleanup_expired_namespaces(exclude_namespaces={current_namespace} if current_namespace else None)
        namespace = reset_session_namespace(st.session_state, register=True)
        #print(f"[App] Pipeline will use namespace: {namespace}")
        clear_session_state()

        # ── Immediate boot loader — renders BEFORE any imports ────────────────
        boot_placeholder = st.empty()
        boot_placeholder.markdown("""
        <div class="boot-loader">
          <div class="orbital">
            <div class="orbital-ring orbital-ring-outer"></div>
            <div class="orbital-ring"></div>
            <div class="orbital-dot"></div>
          </div>
          <div class="boot-bar-track">
            <div class="boot-bar-fill"></div>
          </div>
          <div class="boot-dots">
            <div class="boot-dot"></div>
            <div class="boot-dot"></div>
            <div class="boot-dot"></div>
          </div>
          <div class="boot-label">Initializing pipeline…</div>
        </div>
        """, unsafe_allow_html=True)

        pipeline_placeholder = st.empty()
        status_placeholder = st.empty()

        def update_pipeline(step, done):
            boot_placeholder.empty()
            pipeline_placeholder.markdown(render_pipeline(step, done), unsafe_allow_html=True)

        work_dir = tempfile.mkdtemp(prefix="video-agent-")

        try:
            done = []
            update_pipeline(0, done)
            status_placeholder.markdown(
                '<p style="text-align:center;color:#64748B;font-size:0.8rem;font-family:\'JetBrains Mono\',monospace;">Ingesting source…</p>',
                unsafe_allow_html=True,
            )

            # We run the full pipeline and inject progress updates at key stages
            # by monkey-patching / splitting the pipeline steps visually

            # Step 0 → 1: process_input + transcribe
            from utils.audio_processor import process_input
            chunks = process_input(source=source, output_dir=work_dir)
            done = [0]
            update_pipeline(1, done)
            status_placeholder.markdown(
                '<p style="text-align:center;color:#64748B;font-size:0.8rem;font-family:\'JetBrains Mono\',monospace;">Transcribing audio…</p>',
                unsafe_allow_html=True,
            )

            from core.transcriber import transcribe_all
            transcript = transcribe_all(chunks, language=language, output_dir=work_dir)
            done = [0, 1]
            update_pipeline(2, done)
            status_placeholder.markdown(
                '<p style="text-align:center;color:#64748B;font-size:0.8rem;font-family:\'JetBrains Mono\',monospace;">Summarizing content…</p>',
                unsafe_allow_html=True,
            )

            from core.summarize import summarize
            summary_result = summarize(transcript)
            title = summary_result["title"]
            summary_points = summary_result["summary"]
            done = [0, 1, 2]
            update_pipeline(3, done)
            status_placeholder.markdown(
                '<p style="text-align:center;color:#64748B;font-size:0.8rem;font-family:\'JetBrains Mono\',monospace;">Extracting key insights…</p>',
                unsafe_allow_html=True,
            )

            from core.extractor import extract_action_items, extract_key_decisions, extract_questions
            action_items = extract_action_items(transcript)
            decisions = extract_key_decisions(transcript)
            questions = extract_questions(transcript)
            done = [0, 1, 2, 3]
            update_pipeline(4, done)
            status_placeholder.markdown(
                '<p style="text-align:center;color:#64748B;font-size:0.8rem;font-family:\'JetBrains Mono\',monospace;">Building RAG index…</p>',
                unsafe_allow_html=True,
            )

            from core.RAG_Engine import build_rag_chain
            rag_chain = build_rag_chain(transcript, namespace=namespace)
            done = [0, 1, 2, 3, 4]
            update_pipeline(-1, done)
            status_placeholder.markdown(
                '<p style="text-align:center;color:#6C63FF;font-size:0.8rem;font-family:\'JetBrains Mono\',monospace;">✓ Pipeline complete</p>',
                unsafe_allow_html=True,
            )

            st.session_state.result = {
                "namespace": namespace,
                "title": title,
                "transcript": transcript,
                "summary": summary_points,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
                "rag_chain": rag_chain,
            }
            #print(f"[App] Pipeline complete — namespace={namespace} title={title[:50]}...")

        except Exception as e:
            boot_placeholder.empty()
            pipeline_placeholder.empty()
            status_placeholder.empty()
            st.error(f"Pipeline error: {e}")
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result
    st.divider()

    # Title
    st.markdown(f"""
    <div style="margin-bottom:1.8rem;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;letter-spacing:0.12em;color:#6C63FF;text-transform:uppercase;margin-bottom:0.3rem;">Detected Title</div>
      <div style="font-size:1.55rem;font-weight:700;color:#F8FAFC;line-height:1.3;">{r['title']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Summary + Transcript side by side
    col_l, col_r = st.columns([1, 1], gap="medium")

    with col_l:
        st.markdown("""
        <div class="result-card">
          <div class="card-header">
            <span class="card-icon">📋</span>
            <span class="card-title">Summary</span>
          </div>
        """, unsafe_allow_html=True)
        summary = r["summary"]
        st.markdown(render_bullets(summary), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown("""
        <div class="result-card">
          <div class="card-header">
            <span class="card-icon">🎙️</span>
            <span class="card-title">Transcript</span>
          </div>
        """, unsafe_allow_html=True)
        st.markdown(
            f'<div class="transcript-box">{r["transcript"]}</div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇ Download Transcript",
            data=r["transcript"],
            file_name="transcript.txt",
            mime="text/plain",
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # Three-column insights
    col_a, col_b, col_c = st.columns(3, gap="medium")

    def insight_card(icon, label, content):
        items_html = render_bullets(content)
        return f"""
        <div class="result-card" style="height:100%;">
          <div class="card-header">
            <span class="card-icon">{icon}</span>
            <span class="card-title">{label}</span>
          </div>
          {items_html}
        </div>
        """

    with col_a:
        st.markdown(insight_card("✅", "Action Items", r["action_items"]), unsafe_allow_html=True)
    with col_b:
        st.markdown(insight_card("🔑", "Key Decisions", r["key_decisions"]), unsafe_allow_html=True)
    with col_c:
        st.markdown(insight_card("❓", "Open Questions", r["open_questions"]), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.divider()

    # ── RAG Chat ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-bottom:1rem;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;letter-spacing:0.12em;color:#6C63FF;text-transform:uppercase;margin-bottom:0.3rem;">RAG Chat</div>
      <div style="font-size:1.15rem;font-weight:600;color:#F8FAFC;">Chat with your video</div>
    </div>
    """, unsafe_allow_html=True)

    # Render chat history
    if st.session_state.chat_history:
        chat_html = '<div class="chat-container">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f'<div><div class="msg-label">YOU</div><div class="msg-user">{msg["content"]}</div></div>'
            else:
                chat_html += f'<div><div class="msg-label">ASSISTANT</div><div class="msg-bot">{msg["content"]}</div></div>'
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

    # Chat input row
    q_col, btn_col2 = st.columns([5, 1])
    with q_col:
        question = st.text_input(
            "Question",
            placeholder="Ask anything about the video…",
            key="chat_input",
            label_visibility="collapsed",
        )
    with btn_col2:
        ask_btn = st.button("Ask →", use_container_width=True, key="ask_btn")

    if ask_btn and question.strip():
        from core.RAG_Engine import ask_question, load_rag_chain
        session_ns = get_session_namespace(st.session_state)
        result_ns = r.get("namespace")
        print(f"[App] Chat question — session_ns={session_ns} result_ns={result_ns}")
        if result_ns and result_ns != session_ns:
            print(f"[App] WARNING: namespace mismatch — result stored under {result_ns} but session is {session_ns}")
        with st.spinner(""):
            chain = r["rag_chain"] if r.get("rag_chain") else load_rag_chain(namespace=result_ns or session_ns)
            answer = ask_question(chain, question.strip())
        st.session_state.chat_history.append({"role": "user", "content": question.strip()})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        print(f"[App] Chat answer generated for namespace: {session_ns}")
        st.rerun()
