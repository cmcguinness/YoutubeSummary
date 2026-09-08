#    ┌─────────────────────────────────────────────────────────┐
#    │                                                         │
#    │                       Summarizer                        │
#    │                                                         │
#    │   Given a transcript, produce a summary of it in the    │
#    │                    requested length.                    │
#    │                                                         │
#    │         Length is not well honored, but we try.         │
#    │                                                         │
#    └─────────────────────────────────────────────────────────┘
import re
from pathlib import Path

import markdown

import llm

PROMPTS = Path(__file__).parent / 'prompts'

FULL_TRANSCRIPT = 'Full Transcript'

# Options we present for summary lengths
summary_types = [
    {"name": "2-3 Paragraph Summary", "value": "250"},
    {"name": "Short summary and bullets", "value": "500"},
    {"name": "Longer summary with more details", "value": "1000"},
    {"name": "Summary, Themes, and Analysis with Timings", "value": "2500"},
    {"name": "Full Transcript, no AI summarization of contents", "value": FULL_TRANSCRIPT},
]

# LLMs like to wrap their whole answer in a ```markdown fence even when asked
# not to, and sometimes add a line of chat before it. Strip that back off.
_FENCE_RE = re.compile(
    r'^\s*(?:[^\n`]*\n)??```(?:markdown|md|text)?\s*\n(?P<body>.*?)\n?\s*```\s*$',
    re.DOTALL | re.IGNORECASE,
)


def strip_code_fence(text):
    """Return the contents of a fence wrapping the entire response, if any."""
    match = _FENCE_RE.match(text.strip())
    if match:
        return match.group('body')
    return text.strip()


_LIST_ITEM_RE = re.compile(r'^(?P<indent>[ \t]*)(?P<marker>[-*+]|\d+[.)])(?P<rest>\s+\S.*)$')
_FENCE_LINE_RE = re.compile(r'^\s*(```|~~~)')


def normalize_list_indents(text):
    """Re-indent nested list items to the 4 spaces Python-Markdown requires.

    Models habitually indent nested bullets by two spaces, which Python-Markdown
    reads as a sibling rather than a child -- the whole reason this project
    originally shipped a hand-written markdown parser. Rescaling the indentation
    lets us use the library instead.
    """
    lines = text.split('\n')
    output = []
    # Stack of source indent widths, one per open nesting level
    levels = []
    in_fence = False

    for line in lines:
        if _FENCE_LINE_RE.match(line):
            in_fence = not in_fence
            output.append(line)
            continue

        if in_fence:
            output.append(line)
            continue

        match = _LIST_ITEM_RE.match(line)
        if not match:
            # A blank line keeps a list open; anything else at column 0 ends it
            if line.strip() and not line.startswith((' ', '\t')):
                levels = []
            output.append(line)
            continue

        width = len(match.group('indent').expandtabs(4))

        while levels and width < levels[-1]:
            levels.pop()
        if not levels or width > levels[-1]:
            levels.append(width)

        depth = len(levels) - 1
        output.append(' ' * (4 * depth) + match.group('marker') + match.group('rest'))

    return '\n'.join(output)


def md_to_html(text):
    """Convert model markdown to HTML, handling nested lists and tables."""
    cleaned = normalize_list_indents(strip_code_fence(text))
    return markdown.markdown(cleaned, extensions=['extra', 'sane_lists'])


def _load_prompt(name):
    return (PROMPTS / name).read_text(encoding='utf-8')


# Keep a chat from growing without bound; the transcript dominates the cost
# anyway, but there's no reason to resend fifty turns of it.
MAX_HISTORY_MESSAGES = 20


def answer_question(transcript, question, history=None, model=None):
    """Answer a follow-up question about a transcript. Returns HTML."""
    if not question or not question.strip():
        raise ValueError('Please enter a question.')

    system_prompt = _load_prompt('chat_system.md')

    history = list(history or [])[-MAX_HISTORY_MESSAGES:]

    # The transcript rides along with the first user turn so it stays inside
    # the conversation the model sees, rather than in the system instructions.
    messages = [{
        'role': 'user',
        'content': f'Here is the transcript of the video I want to ask about:\n\n{transcript}',
    }, {
        'role': 'assistant',
        'content': "I've read the transcript. What would you like to know?",
    }]

    for message in history:
        role = message.get('role')
        content = (message.get('content') or '').strip()
        if role in ('user', 'assistant') and content:
            messages.append({'role': role, 'content': content})

    messages.append({'role': 'user', 'content': question.strip()})

    client = llm.OpenAIClient(model=model)
    return md_to_html(client.converse(system_prompt, messages))


def get_summary(text, length, add_prompt='', model=None):
    """Summarize a transcript. Returns HTML."""

    # We use the first word of the length radio button label as our key to find
    # the appropriate prompt file that will (try to) generate that length
    key = length.split(' ')[0]

    if not key.isdigit():
        raise ValueError(f'Unknown summary length "{length}"')

    user = _load_prompt(f'{key}.md')
    system_prompt = _load_prompt('system_prompt.md')

    # Patch the transcript into the user prompt
    user = user.replace('{text}', text)

    # If we're allowing additional prompts from the user, add it in
    if add_prompt:
        user = user + '\n' + add_prompt

    client = llm.OpenAIClient(model=model)
    raw = client.ask(system_prompt, user)

    return md_to_html(raw)
