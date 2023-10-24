import openai
def create_text_completion(prompt, model="replicate/a16z-infra/mistral-7b-instruct-v0.1"):
  try:
      return openai.Completion.create(model=model, prompt=prompt)
  except openai.error.OpenAIError as err:
      print(f"Error occurred while doing text completion with Pulze: {err}")
      return None, None
