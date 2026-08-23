"""Fast, dependency-free intent classification for automatic model routing.

This runs on every chat request, so importing and training a machine-learning
pipeline here adds a large cold-start delay for very little benefit. A small
keyword scorer is deterministic, starts instantly, and preserves the existing
route categories.
"""
import re


_TOKEN_RE = re.compile(r"[a-z0-9+#.-]+")
_KEYWORDS = {
    'code': {
        'api', 'bug', 'code', 'coding', 'css', 'database', 'debug', 'django',
        'error', 'exception', 'html', 'java', 'javascript', 'node', 'php',
        'program', 'programming', 'python', 'react', 'sql', 'traceback',
        'typescript',
    },
    'research': {
        'compare', 'current', 'evidence', 'fact', 'facts', 'latest', 'news',
        'research', 'source', 'sources', 'study', 'today', 'verify',
    },
    'shopping': {
        'buy', 'order', 'price', 'product', 'recommend', 'shop', 'shopping',
        'store',
    },
    'document': {
        'document', 'file', 'pdf', 'presentation', 'spreadsheet', 'summarize',
        'summary',
    },
    'creative': {
        'brainstorm', 'caption', 'creative', 'email', 'poem', 'rewrite',
        'story',
    },
}
_CATEGORY_PRIORITY = ('code', 'research', 'shopping', 'document', 'creative')


def classify(text):
    tokens = set(_TOKEN_RE.findall((text or '').lower()))
    if not tokens:
        return 'general'

    scores = {
        category: len(tokens.intersection(keywords))
        for category, keywords in _KEYWORDS.items()
    }
    best_score = max(scores.values(), default=0)
    if not best_score:
        return 'general'
    return next(category for category in _CATEGORY_PRIORITY if scores[category] == best_score)


def choose_model(text, default_model):
    category = classify(text)
    return {'code': 'code', 'research': 'light'}.get(category, default_model), category


# ---- "save this as a note" intent, for the My Notes sidebar feature ----
# Fixed idiomatic phrases ("take this note", "note it down"), not topic
# keywords — a plain regex match is a better fit here than classify()'s
# token-set scoring above.
_NOTE_INTENT_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in (
        r"\btake (?:a |this )?note\b",
        r"\bmake (?:a |this )?note\b",
        r"\bnote (?:it |this |that )?down\b",
        r"\bjot (?:it |this |that )?down\b",
        r"\bsave (?:the |all |my )?details?\b",
    )
]


def is_note_intent(text):
    """True if the user is asking to save something to their notes — 'take
    this note', 'note it down', 'save details related to it', etc."""
    text = text or ''
    return any(pattern.search(text) for pattern in _NOTE_INTENT_PATTERNS)


def strip_note_intent(text):
    """Removes the matched trigger phrase from `text`, leaving whatever else
    was typed along with it (e.g. 'note down: buy milk' -> 'buy milk') so
    that can be used as the note's content directly instead of falling back
    to the assistant's last reply. Safe to call even with no match."""
    text = text or ''
    for pattern in _NOTE_INTENT_PATTERNS:
        match = pattern.search(text)
        if match:
            return (text[:match.start()] + text[match.end():]).strip()
    return text.strip()
