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

    def _format_message_for_history(self, role: str, content: str) -> dict:
        # Clean and validate content
        cleaned_content = content.strip() if content else ""
        if not cleaned_content:
            return None

        # Format message according to Gemini's requirements
        return {"role": role, "parts": [{"text": cleaned_content}]}

    async def stream_response(self, conversation_id: str, query: str) -> AsyncGenerator[str, None]:
        if not self.model:
            raise Exception("Gemini client not initialized")

        try:
            # Get conversation history from mock_conversations
            from .api import mock_conversations
            conversation = next((c for c in mock_conversations if c.conversationId == conversation_id), None)
            history = []

            if conversation and conversation.messages:
                for msg in conversation.messages:
                    role = "user" if msg.senderType == "user" else "model"
                    formatted_msg = self._format_message_for_history(role, msg.content)
                    if formatted_msg:  # Only add non-empty messages
                        history.append(formatted_msg)

            # Create a new chat with valid history
            chat = self.model.start_chat(history=history) if history else self.model.start_chat()

            response = await asyncio.wait_for(
                self._get_response(chat, query),
                timeout=45.0
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
        prompt_with_rule = f"Please follow this rule in your response: You are an HTML code renderer, every one of your answers should contain only HTML code. We already have the HTML initialization and headers, you are responsible for the body only. Don't wrap your response in ```html tags as it will break my HTML code when concatenating your response to it. You are only allowed to use: <strong> <br> <ul> <li>, specific colors for some keywords and emojis. You are not allowed to repeat the user's query in your response. Here is the user's query: {query}"
        for attempt in range(max_retries):
            try:
                response = chat.send_message(prompt_with_rule)

                return response.text
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Retry {attempt + 1} for Gemini API call")
                await asyncio.sleep(1)
