"""
Session Manager for Enterprise AI Knowledge Assistant.
Manages chat history, uploaded files and user session state.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from src.utils.logger import setup_logger
from src.utils.helpers import TimeHelper

logger = setup_logger("SessionManager")


class SessionManager:
    """
    Manages everything about the current user session.

    Tracks:
        ✅ Chat history (all Q&A pairs)
        ✅ Uploaded files list
        ✅ Session statistics
        ✅ User preferences
        ✅ Error history

    Why this matters for internship:
        Shows you understand stateful applications,
        user experience design, and production-ready
        session handling — not just basic scripts!
    """

    def __init__(self):
        """Initialize empty session."""
        self.chat_history:    List[Dict[str, Any]] = []
        self.uploaded_files:  List[Dict[str, Any]] = []
        self.session_start:   str = TimeHelper.get_timestamp()
        self.total_questions: int = 0
        self.total_docs:      int = 0
        self.errors:          List[str] = []
        self.preferences:     Dict[str, Any] = {
            "streaming":     True,
            "show_sources":  True,
            "show_stats":    True,
            "top_k":         5,
            "theme":         "dark"
        }

        logger.info(
            f"New session started: {self.session_start}"
        )

    # ════════════════════════════════════════════════════════════
    #  CHAT HISTORY
    # ════════════════════════════════════════════════════════════

    def add_message(self,
                    question: str,
                    answer: str,
                    sources: Optional[List[Dict]] = None,
                    response_time: Optional[float] = None
                    ) -> None:
        """
        Add a Q&A exchange to chat history.

        Args:
            question:      User's question
            answer:        AI's answer
            sources:       Source documents used
            response_time: How long answer took (seconds)
        """
        message = {
            "id":            len(self.chat_history) + 1,
            "question":      question,
            "answer":        answer,
            "sources":       sources or [],
            "timestamp":     TimeHelper.get_timestamp(),
            "response_time": response_time,
        }
        self.chat_history.append(message)
        self.total_questions += 1

        logger.info(
            f"Message #{self.total_questions} added "
            f"to chat history"
        )

    def get_chat_history(self,
                         last_n: Optional[int] = None
                         ) -> List[Dict[str, Any]]:
        """
        Get chat history.

        Args:
            last_n: If set, return only last N messages

        Returns:
            List of message dicts
        """
        if last_n:
            return self.chat_history[-last_n:]
        return self.chat_history

    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """Get the most recent Q&A exchange."""
        if self.chat_history:
            return self.chat_history[-1]
        return None

    def clear_chat_history(self) -> None:
        """Clear all chat history."""
        self.chat_history = []
        self.total_questions = 0
        logger.info("Chat history cleared")

    def search_history(self,
                       query: str) -> List[Dict[str, Any]]:
        """
        Search through chat history.

        Args:
            query: Search term

        Returns:
            Matching messages
        """
        query = query.lower()
        return [
            msg for msg in self.chat_history
            if query in msg["question"].lower()
            or query in msg["answer"].lower()
        ]

    # ════════════════════════════════════════════════════════════
    #  FILE TRACKING
    # ════════════════════════════════════════════════════════════

    def add_uploaded_file(self,
                          filename: str,
                          file_size: float,
                          chunks: int,
                          file_type: str) -> None:
        """
        Track an uploaded and indexed file.

        Args:
            filename:  Name of the file
            file_size: Size in MB
            chunks:    Number of chunks created
            file_type: Type (pdf, docx, txt, url)
        """
        file_info = {
            "filename":   filename,
            "file_size":  file_size,
            "chunks":     chunks,
            "file_type":  file_type,
            "uploaded_at": TimeHelper.get_timestamp(),
            "status":     "✅ Indexed"
        }
        self.uploaded_files.append(file_info)
        self.total_docs += 1

        logger.info(
            f"File tracked: {filename} "
            f"({chunks} chunks)"
        )

    def get_uploaded_files(self) -> List[Dict[str, Any]]:
        """Get list of all uploaded files."""
        return self.uploaded_files

    def is_file_uploaded(self, filename: str) -> bool:
        """Check if a file was already uploaded."""
        names = [f["filename"] for f in self.uploaded_files]
        return filename in names

    def remove_file(self, filename: str) -> bool:
        """Remove a file from tracking."""
        before = len(self.uploaded_files)
        self.uploaded_files = [
            f for f in self.uploaded_files
            if f["filename"] != filename
        ]
        removed = len(self.uploaded_files) < before
        if removed:
            self.total_docs -= 1
            logger.info(f"File removed: {filename}")
        return removed

    # ════════════════════════════════════════════════════════════
    #  PREFERENCES
    # ════════════════════════════════════════════════════════════

    def update_preference(self,
                          key: str,
                          value: Any) -> None:
        """Update a user preference."""
        self.preferences[key] = value
        logger.info(f"Preference updated: {key}={value}")

    def get_preference(self,
                       key: str,
                       default: Any = None) -> Any:
        """Get a user preference."""
        return self.preferences.get(key, default)

    # ════════════════════════════════════════════════════════════
    #  ERROR TRACKING
    # ════════════════════════════════════════════════════════════

    def log_error(self, error: str) -> None:
        """Track errors for debugging."""
        self.errors.append({
            "error":     error,
            "timestamp": TimeHelper.get_timestamp()
        })
        logger.error(f"Session error: {error}")

    # ════════════════════════════════════════════════════════════
    #  STATISTICS
    # ════════════════════════════════════════════════════════════

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive session statistics.
        Displayed on the UI dashboard.
        """
        # Calculate average response time
        times = [
            m["response_time"]
            for m in self.chat_history
            if m.get("response_time")
        ]
        avg_time = round(
            sum(times) / len(times), 2
        ) if times else 0

        return {
            "session_start":    self.session_start,
            "total_questions":  self.total_questions,
            "total_documents":  self.total_docs,
            "total_chunks":     sum(
                f.get("chunks", 0)
                for f in self.uploaded_files
            ),
            "avg_response_time": f"{avg_time}s",
            "total_errors":     len(self.errors),
            "files_uploaded":   [
                f["filename"]
                for f in self.uploaded_files
            ],
        }

    def export_chat_history(self) -> str:
        """
        Export chat history as formatted text.
        Users can download this.
        """
        if not self.chat_history:
            return "No chat history yet."

        lines = [
            "═" * 50,
            "  ENTERPRISE AI KNOWLEDGE ASSISTANT",
            "  Chat History Export",
            f"  Session: {self.session_start}",
            "═" * 50,
            ""
        ]

        for msg in self.chat_history:
            lines.append(
                f"[{msg['timestamp']}] "
                f"Q{msg['id']}"
            )
            lines.append(f"❓ {msg['question']}")
            lines.append(f"🤖 {msg['answer']}")

            if msg.get("sources"):
                sources = ", ".join([
                    s.get("metadata", {}).get(
                        "source", "Unknown"
                    )
                    for s in msg["sources"][:3]
                ])
                lines.append(f"📚 Sources: {sources}")

            lines.append("-" * 40)
            lines.append("")

        return "\n".join(lines)

    def reset_session(self) -> None:
        """Reset entire session to fresh start."""
        self.chat_history    = []
        self.uploaded_files  = []
        self.total_questions = 0
        self.total_docs      = 0
        self.errors          = []
        self.session_start   = TimeHelper.get_timestamp()
        logger.info("Session reset to fresh start")