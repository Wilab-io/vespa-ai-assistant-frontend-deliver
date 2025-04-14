import google.generativeai as genAI
import asyncio
from typing import AsyncGenerator
import logging

logger = logging.getLogger("Wilab_app")

class GeminiService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = None
        self._initialize_client()

    def _initialize_client(self):
        try:
            genAI.configure(api_key=self.api_key)
            self.model = genAI.GenerativeModel('models/gemini-1.5-pro')
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            raise

    async def stream_response(self, conversation_id: str, query: str) -> AsyncGenerator[str, None]:
        if not self.model:
            raise Exception("Gemini client not initialized")

        try:
            chat = self.model.start_chat(history=[])

            response = await asyncio.wait_for(
                self._get_response(chat, query),
                timeout=45.0  # Increased timeout to 45 seconds
            )

            # Split response into lines and stream them
            lines = response.split('\n')
            for line in lines:
                if line.strip():
                    yield line
                    await asyncio.sleep(0.1)

        except asyncio.TimeoutError:
            logger.error("Gemini API request timed out")
            yield "I apologize, but the request timed out. Please try again."
        except Exception as e:
            logger.error(f"Error in Gemini API call: {str(e)}")
            yield f"I apologize, but I encountered an error: {str(e)}. Please try again."

    async def _get_response(self, chat, query: str, max_retries: int = 3) -> str:
        prompt_with_rule = f"Please follow this rule in your response: You are an HTML code renderer, every one of your answers should contain only HTML code. Format every answer to be a valid HTML code that you could put inside the body tag, don't add additional text to your response, we already have the HTML initialization and headers, you are responsible for the body only. Don't add ``` to your response. You are allowed to use: <strong> <br> <ul> <li>, specific colors and emojis. Here is the user's query: {query}"
        for attempt in range(max_retries):
            try:
                response = chat.send_message(prompt_with_rule)

                return response.text
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Retry {attempt + 1} for Gemini API call")
                await asyncio.sleep(1)
