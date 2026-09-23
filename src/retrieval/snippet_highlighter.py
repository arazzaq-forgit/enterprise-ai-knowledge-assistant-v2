"""
Snippet Highlighter
====================
Given a retrieved chunk's full content and the question that retrieved it,
finds the single sentence within the chunk that best matches the question
lexically, and builds a display-ready windowed snippet with character
offsets marking that sentence — so the frontend can show *exactly* which
sentence justifies the citation, not just "page 4" and a blind truncation.

Deliberately dependency-free (no NLTK, no embedding model, no LLM call):
this runs once per source chunk per answer, so it needs to be fast and
have zero failure modes that could break the response. Scoring is plain
lexical word-overlap — good enough to point a reader at the right
sentence; it doesn't need to be semantically perfect since the reader is
about to read the sentence themselves.
"""
import re
from typing import List, Tuple, Dict, Any


# Small stopword list — enough to stop short question words ("what",
# "does", "the") from dominating the overlap score. Not exhaustive by
# design; this only needs to bias the score, not be linguistically pure.
_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "of", "in", "on", "to", "for", "with", "and", "or", "but", "as",
    "at", "by", "from", "this", "that", "these", "those", "it", "its",
    "what", "how", "why", "when", "where", "who", "which", "does",
    "do", "did", "can", "could", "would", "should", "will", "shall",
    "i", "you", "he", "she", "we", "they", "me", "my", "your",
}

_WORD_RE = re.compile(r"[a-zA-Z0-9']+")

# Matches one sentence including its trailing punctuation and whitespace,
# or (as a fallback for the final fragment) any run of text with no
# terminal punctuation. Uses a lazy body (`.+?`) rather than a `[^.!?]`
# exclusion class so that mid-sentence periods with no following
# whitespace — e.g. "pd.merge()", "np.array()", version strings like
# "3.11" — are swallowed as ordinary characters instead of being
# treated as sentence boundaries. A real sentence boundary requires the
# punctuation to be followed by whitespace or end-of-string.
# re.DOTALL so chunk text spanning multiple lines is still one search space.
_SENTENCE_RE = re.compile(r".+?[.!?]+(?:\s+|$)|.+$", re.DOTALL)


def _tokenize(text: str) -> set:
    return {
        w.lower() for w in _WORD_RE.findall(text)
        if w.lower() not in _STOPWORDS and len(w) > 2
    }


def _split_sentences_with_offsets(content: str) -> List[Tuple[int, int, str]]:
    """
    Returns a list of (start, end, text) tuples. start/end are offsets
    into `content` with surrounding whitespace trimmed off; text is the
    trimmed sentence itself. Empty/whitespace-only matches are skipped.
    """
    spans = []
    for m in _SENTENCE_RE.finditer(content):
        start, end = m.start(), m.end()
        # Trim whitespace from both ends without losing correct offsets.
        while start < end and content[start].isspace():
            start += 1
        while end > start and content[end - 1].isspace():
            end -= 1
        if end > start:
            spans.append((start, end, content[start:end]))
    return spans


def highlight_best_sentence(query: str,
                             content: str,
                             window_chars: int = 320) -> Dict[str, Any]:
    """
    Find the best-matching sentence in `content` for `query`, and build
    a windowed snippet around it for display.

    Returns a dict:
        snippet:          str  — the display-ready excerpt (may be
                                  shorter than `content`, with "…" added
                                  where text was trimmed off either end)
        highlight_start:   int  — start offset of the matched sentence,
                                  relative to `snippet`
        highlight_end:     int  — end offset of the matched sentence,
                                  relative to `snippet`
        matched:          bool  — False if no sentence had any lexical
                                  overlap with the query (frontend should
                                  render `snippet` plainly, with no
                                  highlight, in that case)

    Never raises — worst case (empty content, no sentences found, no
    overlap) degrades to a plain truncated snippet with matched=False.
    """
    if not content or not content.strip():
        return {"snippet": "", "highlight_start": 0, "highlight_end": 0, "matched": False}

    try:
        query_tokens = _tokenize(query)
        sentences = _split_sentences_with_offsets(content)

        if not sentences:
            snippet = content[:window_chars]
            if len(content) > window_chars:
                snippet += "…"
            return {"snippet": snippet, "highlight_start": 0, "highlight_end": 0, "matched": False}

        best_idx, best_score = 0, 0.0
        for i, (_, _, sent_text) in enumerate(sentences):
            sent_tokens = _tokenize(sent_text)
            if not sent_tokens or not query_tokens:
                continue
            overlap = len(query_tokens & sent_tokens)
            # Jaccard-style, but normalized by the smaller set so a short,
            # highly-relevant sentence isn't penalized for being short.
            score = overlap / min(len(query_tokens), len(sent_tokens))
            if score > best_score:
                best_idx, best_score = i, score

        matched = best_score > 0
        best_start, best_end, _ = sentences[best_idx]

        # Build a window of `window_chars` centered on the matched
        # sentence (or from the top, if nothing matched) so the
        # relevant part is never silently cut off by a naive head-only
        # truncation.
        if len(content) <= window_chars:
            win_start, win_end = 0, len(content)
        else:
            center = (best_start + best_end) // 2
            half = window_chars // 2
            win_start = max(0, center - half)
            win_end = min(len(content), win_start + window_chars)
            win_start = max(0, win_end - window_chars)

        snippet = content[win_start:win_end]
        prefix = "…" if win_start > 0 else ""
        suffix = "…" if win_end < len(content) else ""
        snippet = prefix + snippet + suffix

        # Shift the sentence offsets into snippet-relative coordinates,
        # accounting for the "…" prefix, then clip in case the window
        # cut across the sentence boundary.
        offset_shift = len(prefix) - win_start
        h_start = max(0, best_start + offset_shift)
        h_end = min(len(snippet) - len(suffix), best_end + offset_shift)
        if h_end <= h_start:
            # Window clipped the match down to nothing — safer to show
            # the snippet unhighlighted than to emit an inverted range.
            matched = False
            h_start = h_end = 0

        return {
            "snippet": snippet,
            "highlight_start": h_start,
            "highlight_end": h_end,
            "matched": matched,
        }

    except Exception:
        # Absolute last resort — this must never break a chat response.
        snippet = content[:window_chars]
        if len(content) > window_chars:
            snippet += "…"
        return {"snippet": snippet, "highlight_start": 0, "highlight_end": 0, "matched": False}