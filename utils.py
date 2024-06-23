# utils.py

import openai
import httpx
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Set up OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_response(system_prompt, user_prompt):
    headers = {
        "Content-Type": "application/json",
        "api-key": os.getenv('OPENAI_API_KEY')
    }

    #logger.info(f"system_prompt: {system_prompt}")

    payload = {
        "model": "gpt-35-turbo",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 1500,
        "temperature": 0.1,
        "top_p": 0.9
    }

    try:
        response = httpx.post(os.getenv('LLM_SERVER_URL'), headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()
    except httpx.TimeoutException:
        raise Exception("Request timed out")
    except httpx.RequestError as e:
        raise Exception(f"An error occurred while requesting {e.request.url!r}.")
    
    result = response.json()
    return result['choices'][0]['message']['content']
