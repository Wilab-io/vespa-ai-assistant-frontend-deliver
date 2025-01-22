import logging
import os
import httpx
from services.config.config_service import ConfigService
from src.services.api.types import AuthResult, AuthResponse, ErrorResponse, ConversationRequest, NewConversationResponse, ConversationResult, ConversationsResult, ConversationsResponse, UsersResponse, Conversation, NewConversationResult, LLMsResponse, LLMsResult, GenericActionResponse, GenericActionResult, UsersResult, User, UserResult, KnowledgeBase, KnowledgeBaseResult, KnowledgeBasesResponse

class VespaAgentClient:
    def __init__(self, config_service: ConfigService):
        default_url = "http://localhost:8080"
        use_mock = os.getenv("MOCK_API", "false").lower() == "true"

        self.config_service = config_service
        self.base_url = config_service.get_connection_endpoint() or default_url
        self.use_mock = use_mock
        self.client = self._create_client()
        self.logger = logging.getLogger("vespa_app")

    def _create_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url if not self.use_mock else "http://localhost:8080"
        )

    async def update_base_url(self):
        await self.client.aclose()
        self.base_url = self.config_service.get_connection_endpoint() or "http://localhost:8080"
        self.client = self._create_client()

    async def authenticate(self, username: str, password: str) -> AuthResult:
        """
        Authenticate user with Vespa agent.
        Returns a validated AuthResponse on success or ErrorResponse on failure.
        """
        self.logger.debug(f"Authenticating user: {username}")
        response = await self.client.post(
            f"{self.base_url}/assistant/auth",
            json={
                "username": username,
                "password": password
            },
            headers={
                "Content-Type": "application/json"
            }
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        return AuthResponse(**data)

    async def get_llms(self, token: str) -> LLMsResult:
        """
        Fetch available LLM configurations
        Returns the complete LLM information for each model
        """
        response = await self.client.get(
            f"{self.base_url}/assistant/llms",
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        return LLMsResponse(**data)

    async def close(self):
        await self.client.aclose()

    async def create_conversation(self, token: str) -> NewConversationResult:
        """
        Create a new conversation.
        Returns a ConversationResponse on success or ErrorResponse on failure.
        """
        self.logger.debug(f"Creating conversation")

        response = await self.client.post(
            f"{self.base_url}/assistant/conversations",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        response_data = NewConversationResponse(**data)

        self.logger.info(f"Created conversation with ID: {response_data.conversationId}")
        return response_data

    async def stream_conversation(self, llm_id: str, text: str, token: str, conversation_id: str):
        """
        Stream a conversation with the given LLM using SSE.
        Transform form data into proper JSON request before sending to backend.
        """
        request = ConversationRequest(
            llmId=llm_id,
            query=text,
            conversationId=conversation_id
        )

        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/assistant/chat",
                    json=request.model_dump(),
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "text/event-stream",
                        "Content-Type": "application/json"
                    }
                ) as response:
                    self.logger.debug(f"Response status: {response.status_code}")
                    if response.status_code != 200:
                        error_content = await response.aread()
                        self.logger.error(f"Response error content: {error_content.decode()}")
                        return

                    buffer = []
                    async for chunk in response.aiter_bytes():
                        chunk_str = chunk.decode()
                        buffer.append(chunk_str)

                        # If we have a complete message (ends with double newline)
                        if '\n\n' in chunk_str:
                            message = ''.join(buffer)
                            yield message
                            buffer = []

            except Exception as e:
                self.logger.error(f"Error in stream_conversation: {str(e)}")
                raise

    async def get_conversations(self, token: str) -> ConversationsResult:
        """
        Get all conversations for a user
        """
        response = await self.client.get(
            "/assistant/conversations",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        return ConversationsResponse(**data)

    async def get_conversation(self, conversation_id: str, token: str) -> ConversationResult:
        """
        Get a conversation by its ID
        """
        self.logger.debug(f"Getting conversation with ID: {conversation_id}")
        response = await self.client.get(
            f"{self.base_url}/assistant/conversations/{conversation_id}",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        return Conversation(**data)

    async def delete_conversation(
        self,
        conversation_id: str,
        token: str
    ) -> GenericActionResult:
        """
        Delete a conversation by its ID
        """
        response = await self.client.delete(
            f"{self.base_url}/assistant/conversations/{conversation_id}",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)

        return GenericActionResponse(**data)

    async def delete_all_conversations(self, token: str) -> GenericActionResult:
        """
        Delete all conversations for a user
        """
        response = await self.client.delete(
            f"{self.base_url}/assistant/conversations/delete/all",
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        return GenericActionResponse(**data)

    async def get_users(self, token: str) -> UsersResult:
        """Get all users"""
        response = await self.client.get(
            f"{self.base_url}/assistant/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        return UsersResponse(**data)

    async def get_user(self, user_id: str, token: str) -> UserResult:
        """Get a user by their ID"""
        response = await self.client.get(
            f"{self.base_url}/assistant/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        return User(**data)

    async def delete_user(self, user_id: str, token: str) -> GenericActionResponse:
        """Delete a user by their ID"""
        response = await self.client.delete(
            f"{self.base_url}/assistant/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        return GenericActionResponse(**data)

    async def edit_user(self, user_id: str, user_data: dict, token: str) -> GenericActionResult:
        """Edit a user by their ID"""
        roles = ["USER", "ADMIN"] if user_data.get("is_admin") else ["USER"]
        payload = {
            "username": user_data["username"],
            "email": user_data["email"],
            "roles": roles
        }

        if user_data.get("password"):
            payload["password"] = user_data["password"]

        response = await self.client.put(
            f"{self.base_url}/assistant/users/{user_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        return GenericActionResponse(**data)

    async def create_user(self, user_data: dict, token: str) -> GenericActionResult:
        """Create a new user"""
        roles = ["USER", "ADMIN"] if user_data.get("is_admin") else ["USER"]
        payload = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password": user_data["password"],
            "roles": roles
        }

        response = await self.client.post(
            f"{self.base_url}/assistant/users",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        return GenericActionResponse(**data)

    async def get_knowledge_bases(self, token: str) -> KnowledgeBasesResponse:
        """Get all knowledge bases"""
        response = await self.client.get(
            f"{self.base_url}/assistant/knowledge-base",
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        return KnowledgeBasesResponse(**data)

    async def get_knowledge_base(self, kb_id: str, token: str) -> KnowledgeBaseResult:
        """Get a knowledge base by its ID"""
        response = await self.client.get(
            f"{self.base_url}/assistant/knowledge-base/{kb_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        return KnowledgeBase(**data)

    async def delete_knowledge_bases(self, kb_id:str, token: str) -> GenericActionResult:
        """Delete a knowledge base by their ID"""
        response = await self.client.delete(
            f"{self.base_url}/assistant/knowledge-base/{kb_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        return GenericActionResponse(**data)

    async def edit_knowledge_base(self, kb_id: str, kb_data: dict, token: str) -> GenericActionResult:
        """Edit a knowledge base by its ID"""
        payload = {
            "title": kb_data["title"],
            "content": kb_data["content"],
        }

        response = await self.client.put(
            f"{self.base_url}/assistant/knowledge-base/{kb_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        return GenericActionResponse(**data)

    async def create_knowledge_base(self, kb_data: dict, token: str) -> GenericActionResult:
        """Create a new knowledge base"""
        payload = {
            "title": kb_data["title"],
            "content": kb_data["content"],
        }

        response = await self.client.post(
            f"{self.base_url}/assistant/knowledge-base",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        data = response.json()
        if "error-code" in data:
            data["statusCode"] = response.status_code
            return ErrorResponse(**data)
        return GenericActionResponse(**data)
