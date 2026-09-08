#    ┌─────────────────────────────────────────────────────────┐
#    │                                                         │
#    │                  Ask OpenAI a Question                  │
#    │                                                         │
#    │   Uses the Responses API, which is where the current    │
#    │  models expose their reasoning-effort control. Note     │
#    │  that these models reject the old `max_tokens` name.    │
#    │                                                         │
#    └─────────────────────────────────────────────────────────┘
import os

from openai import OpenAI, OpenAIError


class LLMError(Exception):
    pass


# Every current model carries a ~1.05M token context window, so even a very
# long transcript fits without chunking. Prices are per million tokens.
MODELS = {
    'gpt-5.6-luna':  {'name': 'Luna — fast and cheap',   'in': 0.20, 'out': 1.20},
    'gpt-5.6-terra': {'name': 'Terra — balanced',        'in': 2.00, 'out': 12.00},
    'gpt-5.6-sol':   {'name': 'Sol — most capable',      'in': 4.00, 'out': 20.00},
}

DEFAULT_MODEL = 'gpt-5.6-luna'

# Summarization is not a heavy reasoning task; keep effort low so the user
# isn't paying for -- or waiting on -- thinking tokens they won't see.
DEFAULT_EFFORT = 'low'

MAX_OUTPUT_TOKENS = 16000


class OpenAIClient:
    def __init__(self, model=None, effort=DEFAULT_EFFORT):
        if not os.getenv('OPENAI_API_KEY'):
            raise LLMError('OPENAI_API_KEY is not set.')

        self.model = model or os.getenv('OPENAI_MODEL', DEFAULT_MODEL)
        if self.model not in MODELS:
            raise LLMError(f'Unknown model "{self.model}".')

        self.effort = effort
        self.client = OpenAI()
        self.last_usage = None

    def ask(self, system_prompt, user_prompt):
        print(f'Asking {self.model} ({len(system_prompt) + len(user_prompt)} chars in)', flush=True)

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=system_prompt,
                input=user_prompt,
                reasoning={'effort': self.effort},
                max_output_tokens=MAX_OUTPUT_TOKENS,
            )
        except OpenAIError as e:
            raise LLMError(f'The AI service returned an error: {e}') from e

        self.last_usage = response.usage
        if response.usage:
            print(f'Used {response.usage.input_tokens} in / '
                  f'{response.usage.output_tokens} out '
                  f'(~${self.estimate_cost():.4f})', flush=True)

        text = response.output_text
        if not text or not text.strip():
            raise LLMError('The AI service returned an empty response.')

        return text

    def converse(self, system_prompt, messages):
        """Ask a follow-up question with prior turns for context.

        `messages` is a list of {'role': 'user'|'assistant', 'content': str},
        oldest first, ending with the question being asked now.
        """
        print(f'Chatting with {self.model} ({len(messages)} messages)', flush=True)

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=system_prompt,
                input=messages,
                reasoning={'effort': self.effort},
                max_output_tokens=MAX_OUTPUT_TOKENS,
            )
        except OpenAIError as e:
            raise LLMError(f'The AI service returned an error: {e}') from e

        self.last_usage = response.usage
        if response.usage:
            print(f'Used {response.usage.input_tokens} in / '
                  f'{response.usage.output_tokens} out '
                  f'(~${self.estimate_cost():.4f})', flush=True)

        text = response.output_text
        if not text or not text.strip():
            raise LLMError('The AI service returned an empty response.')

        return text

    def estimate_cost(self):
        if not self.last_usage:
            return 0.0
        price = MODELS[self.model]
        return (self.last_usage.input_tokens * price['in']
                + self.last_usage.output_tokens * price['out']) / 1_000_000
