# File: pulze/api.py
from .config import initialize_openai
from .completion import create_text_completion
from .chat import create_chat_completion
import json

def initialize(api_key, api_base="https://api.pulze.ai/v1"):
    print(f'Initializing with API key {api_key} and base {api_base}')
    initialize_openai(api_key, api_base)

def complete_text(prompt, model="replicate/a16z-infra/mistral-7b-instruct-v0.1"):
    print(f'Completing text with prompt "{prompt}" and model {model}')
    text_completion = create_text_completion(prompt, model)
    if not isinstance(text_completion, dict):
        raise ValueError('Unexpected format: The completion should be dictionary.')
    print('Text completion result:', text_completion)
    # only return the 'text' within 'choices'
    return extract_content_from_choices(text_completion)

def complete_chat(messages, model="openai/gpt-3.5-turbo"):
    print(f'Completing chat with messages {messages} and model {model}')
    chat_completion = create_chat_completion(messages, model)
    if not isinstance(chat_completion, dict):
        raise ValueError('Unexpected format: The chat completion should be dictionary.')
    print('Chat completion result:', chat_completion)
    # only return the 'text' within 'choices'
    return extract_content_from_choices(chat_completion)

def parse_json(data: dict) -> dict:
    print(f'Parsing JSON from data {data}')
    try:
        json_str = json.dumps(data)
        parsed_data = json.loads(json_str)
        print('Parsed data:', parsed_data)
        return parsed_data
    except json.JSONDecodeError:
        print('Invalid JSON data')
        return {"error": "Invalid JSON data"}

def extract_content_from_choices(response: dict) -> str:
    print(f'Extracting content from choices in {response}')
    if not 'choices' in response:
        print("No 'choices' in the response")
        return None

    choices = response.get('choices', [])
    if not choices or not isinstance(choices, list):
        print('Invalid choices:', choices)
        return None

    # For text and chat completion, get the text and content from the message
    choice = choices[0]
    if 'text' in choice:
        print('Text in choice:', choice['text'])
        return choice['text']
    elif 'message' in choice and isinstance(choice['message'], dict) and 'content' in choice['message']:
        print('Content in message:', choice['message']['content'])
        return choice['message']['content']

    print('No text or message content in the choice')
    return None 