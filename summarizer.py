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
import deepinfra
import open_ai
import ollama
import hf
import os
import md2html

# Options we present for summary lengths
summary_types = [
    {"name": "2-3 Paragraph Summary", "value": "250"},
    {"name": "Short summary and bullets", "value": "500"},
    {"name": "Longer summary with more details", "value": "1000"},
    {"name": "Summary, Themes, and Analysis with Timings", "value": "2500"},
    {"name": "Full Transcript, no AI summarization of contents", "value": "Full Transcript"},
]

def get_summary(text, length, add_prompt):
    # We use the first word of the length radio button label as our key to find the appropriate
    # prompt file that will (try to) generate a summary of that length
    if " " in length:
        key = length[:length.find(" ")]
    else:
        key = length


    with open(f'prompts/{key}.md', 'r') as f:
        user = f.read()

    # Much nicer than trying to embed prompts inline in the code
    with open('prompts/system_prompt.md', 'r') as f:
        system_prompt = f.read()

    # Patch the transcript into the user prompt
    user = user.replace('{text}', text)

    # If we're alloing additional prompts from the user, add it in
    user = user + '\n' + add_prompt

    # Some diagnostics
    # print(f'user {len(user)} system {len(system_prompt)}', flush=True)

    # We can either use Deep Infra's Llama 3.1 8b model or OpenAI's gpt-4o-mini
    # Llama is way cheaper and seems to work, but  -mini isn't so bad either

    # We will choose which we use by whether there's an environment variable or not for the service
    if os.getenv('USE_OLLAMA') is not None:
        client = ollama.Ollama()
    elif os.getenv('HF_API_KEY') is not None:
        client = hf.HF()
    elif os.getenv('DI_API_KEY') is not None:
        client = deepinfra.DeepInfra()
    else:
        client = open_ai.Open_AI()

    # Actual logic for making the call is in a class
    raw = client.ask(system_prompt, user)

    # # Diagnostic outputs
    # print('Raw content:')
    # print(raw, flush=True)

    # Convert the markdown to HTML and we're done!
    return md2html.convert_md_to_html(raw)
