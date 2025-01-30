import os
from dotenv import load_dotenv
load_dotenv()

import dspy

import google.generativeai as genai


class GeminiLM(dspy.LM):

    def __init__(self, model, api_key=None, endpoint=None, **kwargs):

        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        self.endpoint = endpoint
        self.history = []

        super().__init__(model, **kwargs)
        self.model = genai.GenerativeModel(model)

    def __call__(self, prompt=None, messages=None, **kwargs):

        prompt = '\n\n'.join([x['content'] for x in messages] + ['BEGIN RESPONSE:'])
        completions = self.model.generate_content(prompt)
        
        self.history.append({"prompt": prompt, "completions": completions})

        return [completions.candidates[0].content.parts[0].text]
