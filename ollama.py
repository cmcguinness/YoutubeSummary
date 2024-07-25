import requests

class Ollama:
    def ask(self, sys, usr):
        history = [
            {"role": "system", "content": sys},
            {"role": "user", "content": usr}
        ]

        print(f'Calling Ollama with {len(sys+usr)} bytes of input.', flush=True)
        response = requests.post('http://127.0.0.1:11434/api/chat',
                                 json={
                                     "model": 'llama3.1',
                                     "messages": history,
                                     "stream" : False,
                                     "options": {"temperature": 0.1, "max_tokens": 4096},
                                 }
                                 )

        answer = response.json()['message']['content']
        print(f'Returned {len(answer)} bytes of output.', flush=True)
        return answer

if __name__ == "__main__":
    print(Ollama().ask('You are a helpful chatbot', 'Who was president in 1952?'))