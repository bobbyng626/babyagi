import openai
import time
import tiktoken
from settings import SETTINGS
from aexlutils import logger


class OpenAIQuery:
    @classmethod
    def get_prompt_tokens(cls, prompt: str) -> int:
        # return math.ceil(len(prompt.split(" ")) / 0.75)
        encodings = tiktoken.encoding_for_model("gpt-3.5-turbo")
        num_token = len(encodings.encode(prompt))
        return num_token
    
    @classmethod
    def limit_tokens_from_string(cls, string: str, model: str, limit: int) -> str:
        """Limits the string to a number of tokens (estimated)."""

        try:
            encoding = tiktoken.encoding_for_model(model)
        except:
            encoding = tiktoken.encoding_for_model('gpt2')  # Fallback for others.

        encoded = encoding.encode(string)

        return encoding.decode(encoded[:limit])

    
    @classmethod
    def generate_response(cls, prompt: str,
                                      max_completion_token=120,
                                      response_timeout=20) -> str:
        # openai settings
        openai.api_type = SETTINGS.AZURE.OPENAI_API_TYPE
        # openai.api_version = SETTINGS.AZURE.OPENAI_API_VERSION_CHAT_COMPLETION
        openai.api_version = SETTINGS.AZURE.OPENAI_API_VERSION_COMPLETION
        openai.api_base = SETTINGS.AZURE.OPENAI_ENDPOINT
        openai.api_key = SETTINGS.AZURE.OPENAI_API_KEY

        trimmed_prompt = cls.limit_tokens_from_string(prompt, "", 4000 - max_completion_token)

        # prompt_tokens = cls.get_prompt_tokens(prompt)
        # token count
        message = [{
            "role": "user",
            "content": trimmed_prompt
        }]
        response = ""
        for attempt in range(1, 4):
            try:
                response = openai.ChatCompletion.create(
                    # engine="gpt-35-turbo",
                    engine="Test-gpt-35-model",
                    # engine="gpt-4",
                    messages=message,
                    temperature=0,
                    max_tokens=120,
                    top_p=0,  # change from 1 to 0 to 0.5
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None,
                    request_timeout=response_timeout)
            except openai.error.RateLimitError:
                print(
                    "   *** The OpenAI API rate limit has been exceeded. Waiting 10 seconds and trying again. ***"
                )
                time.sleep(10)  # Wait 10 seconds and try again
            except openai.error.Timeout:
                print(
                    "   *** OpenAI API timeout occurred. Waiting 10 seconds and trying again. ***"
                )
                time.sleep(10)  # Wait 10 seconds and try again
            except openai.error.APIError:
                print(
                    "   *** OpenAI API error occurred. Waiting 10 seconds and trying again. ***"
                )
                time.sleep(10)  # Wait 10 seconds and try again
            except openai.error.APIConnectionError:
                print(
                    "   *** OpenAI API connection error occurred. Check your network settings, proxy configuration, SSL certificates, or firewall rules. Waiting 10 seconds and trying again. ***"
                )
                time.sleep(10)  # Wait 10 seconds and try again
            except openai.error.InvalidRequestError:
                print(
                    "   *** OpenAI API invalid request. Check the documentation for the specific API method you are calling and make sure you are sending valid and complete parameters. Waiting 10 seconds and trying again. ***"
                )
                time.sleep(10)  # Wait 10 seconds and try again
            except openai.error.ServiceUnavailableError:
                print(
                    "   *** OpenAI API service unavailable. Waiting 10 seconds and trying again. ***"
                )
                time.sleep(10)  # Wait 10 seconds and try again
            else:
                break
        if not response:
            return ""

        logger.debug("Actual Token usage from OpenAI: " +
                     f"Completion-{str(response['usage']['completion_tokens'])}, " +
                     f"Prompt-{str(response['usage']['prompt_tokens'])}")
        return response['choices'][0].message.content

