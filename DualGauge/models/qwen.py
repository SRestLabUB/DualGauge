from .base_model import BaseModel 
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

import torch


class Qwen(BaseModel):

    def __init__(self, model, api_key=None) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(model, device_map="auto")
        self.model = AutoModelForCausalLM.from_pretrained(model, device_map="auto")
        self.ignore_lang_for_code_extraction = True
        print("Model device:", next(self.model.parameters()).device)
    
    def generate(self, prompt, system_prompt=None):
        # Use model device directly
        device = self.model.device
        messages=[{"role": "user", "content": "You are a helpful Assistant. When generating code ensure to put the code within ``` tags."}, {"role": "user", "content": prompt}]

        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            temperature=0.0,
        ).to(device)
        outputs = self.model.generate(**inputs, max_new_tokens=1200)
        completion = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:])
        print("OUTPUT ")
        print(completion)
        return completion
