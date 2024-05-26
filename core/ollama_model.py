from time import sleep
import os
from ollama import Client
from utils import custom_print

class IncompleteResponse(Exception):
    pass

class ServiceRequestError(Exception):
    pass

class HttpResponseError(Exception):
    pass

class OllamaMistral:
    def __init__ (self, api_key):
        # ollama instance
        self.client = Client(host='http://localhost:11434')

    def ask(self, messages, token_limit=50, model="mistral", temp=0.8, retry_limit=5, continuation_limit=3):
        while retry_limit >= 0:
            retry_limit -= 1

            try:
                response = self.client.chat(
                    model=model,
                    messages=messages,
                    options = {
                        "num_predict": token_limit,
                        "temperature": temp
                    }
                )
                print(response)
                # if response['choices'][0]['finish_reason'] != "stop":
                if response['done'] != True:
                    continue

                else:
                    tokens_used = "\n    ".join([
                        (lambda x: f"Prompt Tokens:     {x['prompt_eval_count']}" if x and 'prompt_eval_count' in x and x['prompt_eval_count'] is not None else 'Prompt Tokens:     None')(response),
                        (lambda x: f"Completion Tokens: {x['eval_count']}" if x and 'eval_count' in x and x['eval_count'] is not None else 'Completion Tokens: None')(response)
                        #(lambda x: f"Total Tokens:      {x['total_tokens']}")(response["prompt_eval_count"]+response["eval_count"])
                    ])
                    print(f"Tokens Used:\n    {tokens_used}")
                    return response["message"]["content"].strip()

            except IncompleteResponse:
                custom_print("Response not complete. Retrying in 60 seconds...")
                sleep(60)

            # except self.openai.error.RateLimitError:
            #     custom_print("Rate limit exceeded. Retrying in 60 seconds...")
            #     sleep(60)

            # except self.openai.error.ServiceUnavailableError:
            #     custom_print("The server is overloaded or not ready yet.  Retrying in 60 seconds...")
            #     sleep(60)

        return None