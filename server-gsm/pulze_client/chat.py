import openai

def create_chat_completion(prompt_message, model="openai/gpt-3.5-turbo"):
  try:
      return openai.ChatCompletion.create(model=model, messages=prompt_message)
  except openai.error.OpenAIError as err:
      print(f"Error occurred while completing chat with Pulze: {err}")
      return None, None
