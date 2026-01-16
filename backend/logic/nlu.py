import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from .schemas import NLUResponse, Intent
from .prompts import SYSTEM_PROMPT_V1, TAIL_QUESTION_PROMPT

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use a model that supports JSON mode well
MODEL_NAME = "gemini-2.0-flash"

async def analyze_text(text: str) -> NLUResponse:
    """
    Analyzes the input text using Gemini 1.5 Flash to extract intent and slots.
    """
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_PROMPT_V1,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Async generation
        response = await model.generate_content_async(text)
        
        content = response.text
        if not content:
            raise ValueError("Empty response from Gemini")

        data = json.loads(content)
        return NLUResponse(**data)

    except Exception as e:
        print(f"Error in analyze_text: {e}")
        # Fallback
        return NLUResponse(
            intent=Intent.CHIT_CHAT,
            needs_clarification=True,
            generated_question=f"시스템 오류: {str(e)}"
        )

async def generate_tail_question(context: str, slots: dict) -> str:
    """
    Generates a clarifying question when the intent is ambiguous.
    """
    try:
        model = genai.GenerativeModel(model_name=MODEL_NAME)
        
        prompt = TAIL_QUESTION_PROMPT.format(context=context, slots=json.dumps(slots, ensure_ascii=False))
        
        response = await model.generate_content_async(prompt)
        return response.text.strip()

    except Exception as e:
        print(f"Error in generate_tail_question: {e}")
        return "조금 더 구체적으로 말씀해 주실 수 있나요?"
