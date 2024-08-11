#    ┌─────────────────────────────────────────────────────────┐
#    │                                                         │
#    │                  Ask OpenAI a Question                  │
#    │                                                         │
#    │                  Pretty simple stuff.                   │
#    │                                                         │
#    └─────────────────────────────────────────────────────────┘
from openai import OpenAI

class Open_AI:
    def __init__(self):
        self.client = OpenAI()

    def ask(self, system_prompt, user):
        print('Making Request to GPT', flush=True)
        completion = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user}
            ]
        )

        raw = completion.choices[0].message.content
        return raw
