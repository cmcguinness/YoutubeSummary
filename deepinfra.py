#    ┌─────────────────────────────────────────────────────────┐
#    │                Ask Deep Infra a Question                │
#    │                                                         │
#    │   They "pretend" to be OpenAI so you can use OpenAI's   │
#    │ python library, but you have to add in Deep Infra's URL │
#    │               to make it all work right.                │
#    │                                                         │
#    └─────────────────────────────────────────────────────────┘
import os
from openai import OpenAI


class DeepInfra:
    def __init__(self):
        # Create an OpenAI client with your deepinfra token and endpoint
        self.openai = OpenAI(
            api_key=os.getenv('DI_API_KEY'),
            base_url="https://api.deepinfra.com/v1/openai",
        )

    def ask(self,system_prompt, user_prompt):
        chat_completion = self.openai.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=4096     # Defaults to 512, which is far too little for 1K or 2.5K summaries
        )
        print(chat_completion.usage.prompt_tokens, chat_completion.usage.completion_tokens)
        return chat_completion.choices[0].message.content
