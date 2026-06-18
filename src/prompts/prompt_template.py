"""
Prompt Templates for Enterprise AI Knowledge Assistant.
Carefully crafted prompts that make the AI answer correctly.
"""

from typing import List, Dict, Any


class PromptTemplates:
    """
    Collection of prompt templates for different use cases.

    Why prompts matter?
        The same LLM gives completely different quality
        answers based on how you ask the question.

        Bad prompt  → vague, hallucinated answers
        Good prompt → accurate, sourced, structured answers

    These prompts are crafted specifically for RAG
    to make llama3.2:3b perform like a much bigger model!
    """

    # ── System Prompt ────────────────────────────────────────────
    SYSTEM_PROMPT = """You are an expert AI Knowledge Assistant \
for an Enterprise system. Your role is to provide accurate, \
helpful and professional answers based ONLY on the provided \
document context.

STRICT RULES:
1. Answer ONLY from the provided context
2. If answer is not in context, say clearly:
   "I could not find this information in the documents."
3. Always mention which document/source you used
4. Be concise but complete
5. Use bullet points for lists
6. Never make up information
7. If context is partial, say what you found and what's missing

Your answers should be professional, accurate and helpful."""

    # ── RAG Answer Prompt ────────────────────────────────────────
    @staticmethod
    def rag_prompt(question: str,
                   context: str) -> str:
        """
        Main prompt for answering questions from documents.

        Args:
            question: User's question
            context:  Retrieved document chunks

        Returns:
            Formatted prompt string
        """
        return f"""Use the following document context to \
answer the question accurately.

═══════════════════════════════════════
DOCUMENT CONTEXT:
═══════════════════════════════════════
{context}

═══════════════════════════════════════
QUESTION: {question}
═══════════════════════════════════════

INSTRUCTIONS:
- Answer based ONLY on the context above
- Mention the source document name
- If unsure, say so clearly
- Be professional and concise

ANSWER:"""

    # ── Summary Prompt ───────────────────────────────────────────
    @staticmethod
    def summary_prompt(document_text: str,
                       doc_name: str) -> str:
        """
        Prompt to summarize a document.

        Args:
            document_text: Text content to summarize
            doc_name:      Document filename

        Returns:
            Formatted summary prompt
        """
        return f"""Please provide a comprehensive summary \
of the following document.

Document Name: {doc_name}

═══════════════════════════════════════
DOCUMENT CONTENT:
═══════════════════════════════════════
{document_text[:6000]}

═══════════════════════════════════════
SUMMARY INSTRUCTIONS:
═══════════════════════════════════════
Provide a well structured summary with:

1. 📋 OVERVIEW (2-3 sentences)
   What is this document about?

2. 🔑 KEY POINTS (5-7 bullet points)
   Most important information

3. 📊 MAIN TOPICS
   List the main topics covered

4. 💡 KEY INSIGHTS
   Important conclusions or findings

5. 📝 CONCLUSION
   Brief closing summary

SUMMARY:"""

    # ── Multi Document Prompt ────────────────────────────────────
    @staticmethod
    def multi_doc_prompt(question: str,
                         context: str,
                         doc_names: List[str]) -> str:
        """
        Prompt for answering across multiple documents.

        Args:
            question:  User question
            context:   Combined context from all docs
            doc_names: List of document names

        Returns:
            Formatted multi-document prompt
        """
        docs_list = "\n".join(
            f"  • {name}" for name in doc_names
        )

        return f"""You have access to {len(doc_names)} \
documents. Answer the question by synthesizing \
information from all relevant documents.

AVAILABLE DOCUMENTS:
{docs_list}

═══════════════════════════════════════
COMBINED CONTEXT:
═══════════════════════════════════════
{context}

═══════════════════════════════════════
QUESTION: {question}
═══════════════════════════════════════

INSTRUCTIONS:
- Search ALL documents for relevant info
- Mention WHICH document each point comes from
- Compare/contrast if documents differ
- Synthesize a complete answer

COMPREHENSIVE ANSWER:"""

    # ── Follow Up Prompt ─────────────────────────────────────────
    @staticmethod
    def followup_prompt(question: str,
                        context: str,
                        chat_history: List[Dict[str, str]]
                        ) -> str:
        """
        Prompt that includes chat history for follow up questions.

        Args:
            question:     Current question
            context:      Retrieved context
            chat_history: Previous Q&A pairs

        Returns:
            Formatted follow-up prompt
        """
        # Format last 3 exchanges only
        history_text = ""
        if chat_history:
            recent = chat_history[-3:]
            history_lines = []
            for exchange in recent:
                history_lines.append(
                    f"Human: {exchange.get('question', '')}"
                )
                history_lines.append(
                    f"Assistant: {exchange.get('answer', '')}"
                )
            history_text = "\n".join(history_lines)

        return f"""You are continuing a conversation. \
Use the context and chat history to answer.

PREVIOUS CONVERSATION:
{history_text}

═══════════════════════════════════════
RELEVANT CONTEXT:
═══════════════════════════════════════
{context}

═══════════════════════════════════════
FOLLOW UP QUESTION: {question}
═══════════════════════════════════════

Answer naturally continuing the conversation
while using the context provided.

ANSWER:"""

    # ── No Context Prompt ────────────────────────────────────────
    @staticmethod
    def no_context_prompt(question: str) -> str:
        """
        Prompt when no relevant context found.

        Args:
            question: User question

        Returns:
            Formatted no-context prompt
        """
        return f"""The user asked: "{question}"

No relevant information was found in the 
uploaded documents to answer this question.

Please respond by:
1. Clearly stating the information 
   was not found in the documents
2. Suggesting what kind of document
   might contain this information
3. Offering to help with related
   questions that might be in the docs

Be helpful and professional."""