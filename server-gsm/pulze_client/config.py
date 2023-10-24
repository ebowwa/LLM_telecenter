import openai

def initialize_openai(api_key, api_base="https://api.pulze.ai/v1"):
    if not api_key:
        raise ValueError('API key is missing.')
    openai.api_key = api_key
    openai.api_base = api_base
