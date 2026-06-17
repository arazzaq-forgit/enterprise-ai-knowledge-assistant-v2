"""
Enterprise AI Knowledge Assistant
Main Streamlit Application
Author: Mohd Abdul Razzaq
"""

import streamlit as st
import time
from src.config.settings import (
    AppSettings, OllamaSettings,
    VectorStoreSettings, UISettings
)
from src.pipeline.rag_pipeline import RAGPipeline
from src.utils.session_manager import SessionManager
from src.utils.helpers import (
    FileHelper, DisplayHelper, TimeHelper
)
from src.evaluation.evaluator import RAGEvaluator

# ── Page Configuration ───────────────────────────────────────────
st.set_page_config(
    page_title = UISettings.PAGE_TITLE,
    page_icon  = UISettings.PAGE_ICON,
    layout     = UISettings.LAYOUT,
    initial_sidebar_state = "expanded"
)

# ── Custom CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(
            135deg, #0B0F1A 0%, #141927 100%
        );
        color: #E2E8F0;
    }

    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer    {visibility: hidden;}
    header    {visibility: hidden;}

    /* Chat message styling */
    .user-message {
        background: linear-gradient(
            135deg, #1C2438, #252D40
        );
        border-left: 4px solid #E05C3B;
        padding: 1rem 1.2rem;
        border-radius: 0 12px 12px 0;
        margin: 0.5rem 0;
        color: #E2E8F0;
    }

    .ai-message {
        background: linear-gradient(
            135deg, #141927, #1C2438
        );
        border-left: 4px solid #3B9EE0;
        padding: 1rem 1.2rem;
        border-radius: 0 12px 12px 0;
        margin: 0.5rem 0;
        color: #E2E8F0;
    }

    /* Source card */
    .source-card {
        background: #1C2438;
        border: 1px solid #252D40;
        border-radius: 8px;
        padding: 0.6rem 0.9rem;
        margin: 0.3rem 0;
        font-size: 0.85rem;
        color: #94A3B8;
    }

    /* Stats card */
    .stats-card {
        background: linear-gradient(
            135deg, #1C2438, #252D40
        );
        border: 1px solid #252D40;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        color: #E2E8F0;
    }

    /* Hero banner */
    .hero-banner {
        background: linear-gradient(
            135deg, #E05C3B22, #3B9EE022
        );
        border: 1px solid #E05C3B44;
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        text-align: center;
    }

    /* Upload area */
    .upload-area {
        border: 2px dashed #252D40;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        background: #141927;
    }

    /* Metric value */
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #E05C3B;
    }

    /* Status badge */
    .status-ok  { color: #3BE07A; font-weight: 600; }
    .status-err { color: #E05C3B; font-weight: 600; }

    /* Input box */
    .stTextInput input, .stTextArea textarea {
        background: #1C2438 !important;
        color: #E2E8F0 !important;
        border: 1px solid #252D40 !important;
        border-radius: 8px !important;
    }

    /* Buttons */
    .stButton button {
        background: linear-gradient(
            135deg, #E05C3B, #C04828
        ) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }

    .stButton button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px #E05C3B44 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #0B0F1A !important;
        border-right: 1px solid #252D40;
    }

    /* Divider */
    hr {
        border-color: #252D40 !important;
    }

    /* Success/Error messages */
    .stSuccess { background: #3BE07A22 !important; }
    .stError   { background: #E05C3B22 !important; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  INITIALIZE SESSION STATE
# ════════════════════════════════════════════════════════════════

@st.cache_resource
def init_pipeline() -> RAGPipeline:
    """Initialize RAG pipeline (cached across reruns)."""
    return RAGPipeline(
        chunk_size    = VectorStoreSettings.CHUNK_SIZE,
        chunk_overlap = VectorStoreSettings.CHUNK_OVERLAP,
        top_k         = VectorStoreSettings.TOP_K,
        persist_dir   = str(VectorStoreSettings.PERSIST_DIR),
        llm_model     = OllamaSettings.LLM_MODEL,
        embed_model   = OllamaSettings.EMBEDDING_MODEL,
        base_url      = OllamaSettings.BASE_URL,
    )


def init_session():
    """Initialize session state variables."""
    if "session_manager" not in st.session_state:
        st.session_state.session_manager = SessionManager()
    if "evaluator" not in st.session_state:
        st.session_state.evaluator = RAGEvaluator()
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "chat"
    if "processing" not in st.session_state:
        st.session_state.processing = False


# ════════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════════

def render_sidebar(pipeline: RAGPipeline):
    """Render the sidebar with upload and settings."""
    session: SessionManager = st.session_state.session_manager

    with st.sidebar:
        # ── Logo and Title ───────────────────────────────────────
        st.markdown("""
        <div style='text-align:center; padding:1rem 0'>
            <div style='font-size:2.5rem'>🧠</div>
            <div style='font-size:1.1rem; font-weight:800;
                        color:#E2E8F0'>AI Knowledge</div>
            <div style='font-size:1.1rem; font-weight:800;
                        color:#E05C3B'>Assistant</div>
            <div style='font-size:0.7rem; color:#64748B;
                        margin-top:0.3rem'>
                Enterprise RAG System v2.0
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # ── System Status ────────────────────────────────────────
        st.markdown("### 🔌 System Status")
        status = pipeline.check_system()

        col1, col2 = st.columns(2)
        with col1:
            llm_ok = status.get("ollama_llm", False)
            st.markdown(
                f"{'🟢' if llm_ok else '🔴'} **LLM**"
            )
            emb_ok = status.get("ollama_embeddings", False)
            st.markdown(
                f"{'🟢' if emb_ok else '🔴'} **Embed**"
            )
        with col2:
            vs_ok = status.get("vector_store", False)
            st.markdown(
                f"{'🟢' if vs_ok else '🔴'} **VectorDB**"
            )
            doc_ok = status.get("docs_loaded", False)
            st.markdown(
                f"{'🟢' if doc_ok else '🔴'} **Docs**"
            )

        st.divider()

        # ── File Upload ──────────────────────────────────────────
        st.markdown("### 📁 Upload Documents")
        uploaded_files = st.file_uploader(
            "Drop files here",
            type    = ["pdf", "docx", "txt", "md", "csv"],
            accept_multiple_files = True,
            help    = "Supported: PDF, Word, TXT, MD, CSV"
        )

        if uploaded_files:
            for uploaded_file in uploaded_files:
                if not session.is_file_uploaded(
                    uploaded_file.name
                ):
                    with st.spinner(
                        f"📄 Indexing {uploaded_file.name}..."
                    ):
                        file_bytes = uploaded_file.read()
                        result = pipeline.index_file(
                            file_bytes,
                            uploaded_file.name
                        )

                        if result["success"]:
                            session.add_uploaded_file(
                                filename  = uploaded_file.name,
                                file_size = FileHelper\
                                    .get_file_size_mb(
                                        file_bytes
                                    ),
                                chunks    = result["chunks"],
                                file_type = FileHelper\
                                    .get_file_extension(
                                        uploaded_file.name
                                    )
                            )
                            st.success(
                                f"✅ {uploaded_file.name}\n"
                                f"📦 {result['chunks']} chunks"
                            )
                        else:
                            st.error(
                                f"❌ {uploaded_file.name}\n"
                                f"{result.get('error','')}"
                            )

        st.divider()

        # ── URL Input ────────────────────────────────────────────
        st.markdown("### 🌐 Add URL")
        url_input = st.text_input(
            "Enter website URL",
            placeholder = "https://example.com",
        )

        if st.button("🌐 Index URL", use_container_width=True):
            if url_input:
                with st.spinner("🌐 Scraping URL..."):
                    result = pipeline.index_url(url_input)
                    if result["success"]:
                        session.add_uploaded_file(
                            filename  = url_input,
                            file_size = 0,
                            chunks    = result["chunks"],
                            file_type = "url"
                        )
                        st.success(
                            f"✅ URL indexed!\n"
                            f"📦 {result['chunks']} chunks"
                        )
                    else:
                        st.error(
                            f"❌ {result.get('error','')}"
                        )

        st.divider()

        # ── Loaded Documents ─────────────────────────────────────
        files = session.get_uploaded_files()
        if files:
            st.markdown("### 📚 Loaded Documents")
            for f in files:
                icon = DisplayHelper.get_file_icon(
                    f["filename"]
                )
                name = DisplayHelper.clean_source_name(
                    f["filename"], max_length=25
                )
                st.markdown(
                    f"{icon} `{name}` "
                    f"*({f['chunks']} chunks)*"
                )

        st.divider()

        # ── Settings ─────────────────────────────────────────────
        st.markdown("### ⚙️ Settings")
        streaming = st.toggle(
            "⚡ Streaming Mode",
            value = True
        )
        show_sources = st.toggle(
            "📚 Show Sources",
            value = True
        )
        show_eval = st.toggle(
            "📊 Show Evaluation",
            value = True
        )

        session.update_preference("streaming", streaming)
        session.update_preference("show_sources", show_sources)
        session.update_preference("show_eval", show_eval)

        st.divider()

        # ── Actions ──────────────────────────────────────────────
        st.markdown("### 🛠️ Actions")

        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "🗑️ Clear Chat",
                use_container_width=True
            ):
                session.clear_chat_history()
                st.rerun()

        with col2:
            if st.button(
                "🔄 Reset All",
                use_container_width=True
            ):
                pipeline.clear_knowledge_base()
                session.reset_session()
                st.rerun()

        # ── Export Chat ──────────────────────────────────────────
        if session.get_chat_history():
            export_text = session.export_chat_history()
            st.download_button(
                label     = "💾 Export Chat",
                data      = export_text,
                file_name = f"chat_{TimeHelper.get_date()}.txt",
                mime      = "text/plain",
                use_container_width = True
            )


# ════════════════════════════════════════════════════════════════
#  MAIN CHAT TAB
# ════════════════════════════════════════════════════════════════

def render_chat(pipeline: RAGPipeline):
    """Render the main chat interface."""
    session: SessionManager = st.session_state.session_manager
    evaluator: RAGEvaluator = st.session_state.evaluator

    # ── Hero Banner ──────────────────────────────────────────────
    st.markdown("""
    <div class='hero-banner'>
        <h1 style='color:#E2E8F0; margin:0; font-size:1.8rem'>
            🧠 Enterprise AI Knowledge Assistant
        </h1>
        <p style='color:#94A3B8; margin:0.5rem 0 0 0'>
            Upload documents → Ask questions →
            Get AI-powered answers with sources
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats Row ────────────────────────────────────────────────
    stats = session.get_session_stats()
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class='stats-card'>
            <div class='metric-value'>
                {stats.get('total_documents', 0)}
            </div>
            <div style='color:#94A3B8; font-size:0.8rem'>
                Documents
            </div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class='stats-card'>
            <div class='metric-value' style='color:#3B9EE0'>
                {stats.get('total_chunks', 0)}
            </div>
            <div style='color:#94A3B8; font-size:0.8rem'>
                Chunks Indexed
            </div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class='stats-card'>
            <div class='metric-value' style='color:#3BE07A'>
                {stats.get('total_questions', 0)}
            </div>
            <div style='color:#94A3B8; font-size:0.8rem'>
                Questions Asked
            </div>
        </div>""", unsafe_allow_html=True)

    with col4:
        eval_summary = evaluator.get_evaluation_summary()
        avg = eval_summary.get("average_overall", 0)
        st.markdown(f"""
        <div class='stats-card'>
            <div class='metric-value' style='color:#F5A623'>
                {int(avg * 100)}%
            </div>
            <div style='color:#94A3B8; font-size:0.8rem'>
                Avg Quality
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Chat History ─────────────────────────────────────────────
    chat_history = session.get_chat_history()

    if not chat_history:
        st.markdown("""
        <div style='text-align:center; padding:3rem;
                    color:#64748B'>
            <div style='font-size:3rem'>💬</div>
            <div style='font-size:1.1rem; margin-top:1rem'>
                No conversations yet
            </div>
            <div style='font-size:0.85rem; margin-top:0.5rem'>
                Upload a document and ask your first question!
            </div>
        </div>
        """, unsafe_allow_html=True)

    for msg in chat_history:
        # ── User Message ─────────────────────────────────────────
        st.markdown(f"""
        <div class='user-message'>
            <strong>❓ You</strong><br>
            {msg['question']}
        </div>
        """, unsafe_allow_html=True)

        # ── AI Message ───────────────────────────────────────────
        st.markdown(f"""
        <div class='ai-message'>
            <strong>🤖 AI Assistant</strong><br>
            {msg['answer']}
        </div>
        """, unsafe_allow_html=True)

        # ── Sources ──────────────────────────────────────────────
        if (session.get_preference("show_sources")
                and msg.get("sources")):
            with st.expander(
                f"📚 Sources ({len(msg['sources'])} found)"
            ):
                for src in msg["sources"]:
                    meta  = src.get("metadata", {})
                    score = src.get("similarity", 0)
                    color = DisplayHelper.get_similarity_color(
                        score
                    )
                    st.markdown(f"""
                    <div class='source-card'>
                        {color} <strong>
                        {meta.get('source','Unknown')}
                        </strong>
                        {'— Page ' + str(meta.get(
                            'page_number',''))
                         if meta.get('page_number') else ''}
                        <br>
                        <span style='color:#64748B'>
                        Relevance: {int(score*100)}%
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

    # ── Question Input ───────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)

    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])

        with col1:
            question = st.text_input(
                "Ask a question about your documents...",
                placeholder=(
                    "e.g. What are the main findings? "
                    "Summarize chapter 1..."
                ),
                label_visibility="collapsed"
            )

        with col2:
            submit = st.form_submit_button(
                "Send 🚀",
                use_container_width=True
            )

    # ── Process Question ─────────────────────────────────────────
    if submit and question.strip():
        start_time = time.time()

        # ── Show streaming answer ────────────────────────────────
        with st.container():
            st.markdown(
                "<div class='ai-message'>"
                "<strong>🤖 AI Assistant</strong><br>",
                unsafe_allow_html=True
            )

            answer_placeholder = st.empty()
            full_answer = ""

            # Stream the answer
            with st.spinner("🧠 Thinking..."):
                for chunk in pipeline.ask(
                    question     = question,
                    chat_history = session.get_chat_history(
                                       last_n=3
                                   ),
                    stream       = session.get_preference(
                                       "streaming", True
                                   )
                ):
                    full_answer += chunk
                    answer_placeholder.markdown(full_answer)

            st.markdown("</div>", unsafe_allow_html=True)

        response_time = round(time.time() - start_time, 2)

        # ── Get sources ──────────────────────────────────────────
        sources = pipeline.get_sources(question)

        # ── Evaluate response ────────────────────────────────────
        if session.get_preference("show_eval", True):
            context = "\n".join(
                [s.get("content","") for s in sources]
            )
            evaluation = evaluator.evaluate_response(
                question      = question,
                answer        = full_answer,
                context       = context,
                sources       = sources,
                response_time = response_time
            )

            # Show evaluation metrics
            scores = evaluation["scores"]
            grade  = evaluation["grade"]

            cols = st.columns(6)
            metrics = [
                ("Relevance",    scores["relevance"]),
                ("Coverage",     scores["coverage"]),
                ("Sources",      scores["sources"]),
                ("Faithfulness", scores["faithfulness"]),
                ("Speed",        scores["speed"]),
                ("Overall",      scores["overall"]),
            ]

            for col, (name, score) in zip(cols, metrics):
                with col:
                    color = (
                        "#3BE07A" if score >= 0.7 else
                        "#F5A623" if score >= 0.5 else
                        "#E05C3B"
                    )
                    st.markdown(f"""
                    <div class='stats-card'
                         style='padding:0.5rem'>
                        <div style='color:{color};
                                    font-size:1.2rem;
                                    font-weight:800'>
                            {int(score*100)}%
                        </div>
                        <div style='color:#64748B;
                                    font-size:0.7rem'>
                            {name}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown(
                f"**Grade: {grade}** | "
                f"⏱️ {response_time}s | "
                f"📝 {len(full_answer.split())} words"
            )

        # ── Save to session ──────────────────────────────────────
        session.add_message(
            question      = question,
            answer        = full_answer,
            sources       = sources,
            response_time = response_time
        )

        st.rerun()


# ════════════════════════════════════════════════════════════════
#  ANALYTICS TAB
# ════════════════════════════════════════════════════════════════

def render_analytics(pipeline: RAGPipeline):
    """Render analytics and stats dashboard."""
    session:   SessionManager = st.session_state.session_manager
    evaluator: RAGEvaluator   = st.session_state.evaluator

    st.markdown("## 📊 Analytics Dashboard")
    st.divider()

    # ── Session Stats ────────────────────────────────────────────
    stats = session.get_session_stats()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📄 Documents",
                  stats.get("total_documents", 0))
        st.metric("💬 Questions Asked",
                  stats.get("total_questions", 0))
    with col2:
        st.metric("📦 Total Chunks",
                  stats.get("total_chunks", 0))
        st.metric("⚡ Avg Response",
                  stats.get("avg_response_time", "N/A"))
    with col3:
        eval_summary = evaluator.get_evaluation_summary()
        avg = eval_summary.get("average_overall", 0)
        st.metric("🎯 Avg Quality",
                  f"{int(avg * 100)}%")
        st.metric("📊 Evaluations",
                  eval_summary.get("total_evaluations", 0))

    st.divider()

    # ── Pipeline Stats ───────────────────────────────────────────
    st.markdown("### 🔧 Pipeline Info")
    pipe_stats = pipeline.get_stats()

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"🤖 LLM Model: `{pipe_stats['llm_model']}`")
        st.info(
            f"🧮 Embed Model: "
            f"`{pipe_stats['embed_model']}`"
        )
    with col2:
        st.info(
            f"💾 Chunks in DB: "
            f"`{pipe_stats['total_chunks']}`"
        )
        llm_status = (
            "🟢 Online" if pipe_stats["llm_available"]
            else "🔴 Offline"
        )
        st.info(f"🔌 Ollama Status: `{llm_status}`")

    st.divider()

    # ── Evaluation History ───────────────────────────────────────
    if evaluator.evaluation_history:
        st.markdown("### 📈 Evaluation History")

        import plotly.graph_objects as go

        scores_over_time = {
            "relevance":    [],
            "coverage":     [],
            "faithfulness": [],
            "overall":      [],
        }

        for ev in evaluator.evaluation_history:
            for metric in scores_over_time:
                scores_over_time[metric].append(
                    ev["scores"][metric]
                )

        fig = go.Figure()
        colors = {
            "relevance":    "#E05C3B",
            "coverage":     "#3B9EE0",
            "faithfulness": "#3BE07A",
            "overall":      "#F5A623",
        }

        for metric, values in scores_over_time.items():
            fig.add_trace(go.Scatter(
                y     = values,
                name  = metric.capitalize(),
                mode  = "lines+markers",
                line  = dict(
                    color = colors[metric], width=2
                ),
            ))

        fig.update_layout(
            title      = "Response Quality Over Time",
            paper_bgcolor = "#141927",
            plot_bgcolor  = "#1C2438",
            font          = dict(color="#E2E8F0"),
            legend        = dict(
                bgcolor="#1C2438",
                bordercolor="#252D40"
            ),
            xaxis = dict(
                title="Question Number",
                gridcolor="#252D40"
            ),
            yaxis = dict(
                title="Score",
                range=[0, 1],
                gridcolor="#252D40"
            ),
        )

        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Loaded Documents Table ───────────────────────────────────
    files = session.get_uploaded_files()
    if files:
        st.markdown("### 📁 Loaded Documents")
        import pandas as pd
        df = pd.DataFrame(files)
        df = df[[
            "filename", "file_type",
            "file_size", "chunks",
            "status", "uploaded_at"
        ]]
        df.columns = [
            "Filename", "Type",
            "Size (MB)", "Chunks",
            "Status", "Uploaded At"
        ]
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# ════════════════════════════════════════════════════════════════
#  SUMMARIZE TAB
# ════════════════════════════════════════════════════════════════

def render_summarize(pipeline: RAGPipeline):
    """Render document summarization tab."""
    session: SessionManager = st.session_state.session_manager

    st.markdown("## 📋 Document Summarizer")
    st.markdown(
        "Generate AI-powered summaries of your documents"
    )
    st.divider()

    files = session.get_uploaded_files()

    if not files:
        st.info(
            "📤 Upload documents in the sidebar first!"
        )
        return

    # ── Select Document ──────────────────────────────────────────
    doc_names = [f["filename"] for f in files]
    selected  = st.selectbox(
        "Select document to summarize:",
        options = doc_names
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button(
            "📋 Generate Summary",
            use_container_width=True
        ):
            st.markdown("### 📄 Summary")
            summary_placeholder = st.empty()
            full_summary = ""

            with st.spinner(
                f"📖 Summarizing {selected}..."
            ):
                for chunk in pipeline.summarize(selected):
                    full_summary += chunk
                    summary_placeholder.markdown(
                        full_summary
                    )

            st.success("✅ Summary complete!")

            # Download button for summary
            st.download_button(
                label     = "💾 Download Summary",
                data      = full_summary,
                file_name = f"summary_{selected}.txt",
                mime      = "text/plain"
            )


# ════════════════════════════════════════════════════════════════
#  MAIN APP
# ════════════════════════════════════════════════════════════════

def main():
    """Main application entry point."""

    # ── Initialize ───────────────────────────────────────────────
    init_session()
    pipeline = init_pipeline()

    # ── Sidebar ──────────────────────────────────────────────────
    render_sidebar(pipeline)

    # ── Navigation Tabs ──────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "💬 Chat",
        "📊 Analytics",
        "📋 Summarize"
    ])

    with tab1:
        render_chat(pipeline)

    with tab2:
        render_analytics(pipeline)

    with tab3:
        render_summarize(pipeline)


if __name__ == "__main__":
    main()