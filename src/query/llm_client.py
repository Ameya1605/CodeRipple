import time
import logging
import os
from typing import List, Dict
from src.config import LLM_MODEL, GEMINI_API_KEY, LLM_PROVIDER
import google.generativeai as genai

logger = logging.getLogger(__name__)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

try:
    from openai import OpenAI
    openai_client = OpenAI() if os.environ.get("OPENAI_API_KEY") else None
except ImportError:
    openai_client = None

def call_llm(messages: List[Dict]) -> str:
    if LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
        return _call_gemini(messages)
        
    if not openai_client:
        raise Exception("No LLM provider configured.")

    retries = 3
    for attempt in range(retries):
        try:
            response = openai_client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e) or "529" in str(e):
                logger.warning(f"Overload error. Retrying... ({attempt + 1}/{retries})")
                time.sleep(10)
            else:
                raise e
    raise Exception("Max retries exceeded for LLM API.")

def _call_gemini(messages: List[Dict]) -> str:
    gemini_messages = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        gemini_messages.append({"role": role, "parts": [m["content"]]})
        
    system_instruction = None
    if len(gemini_messages) > 0 and gemini_messages[0]["role"] == "system":
        system_instruction = gemini_messages.pop(0)["parts"][0]

    model = genai.GenerativeModel(
        model_name=LLM_MODEL,
        system_instruction=system_instruction
    )
    
    chat = model.start_chat(history=gemini_messages[:-1])
    response = chat.send_message(gemini_messages[-1]["parts"][0])
    return response.text
