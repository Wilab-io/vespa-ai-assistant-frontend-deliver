from fasthtml.components import Div
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pages.chat import Chat
from pages.settings import Settings
from src.pages.login import LoginPage
from src.services.api.middleware import login_required
from src.services.api.client import VespaAgentClient
from src.services.config.config_service import ConfigService
from fasthtml.common import Redirect
from src.components.layout.chat_history import ChatHistory
from src.components.layout.chat_history_settings import ChatHistorySettings
from src.components.layout.connection_settings import ConnectionSettings
from src.components.layout.knowledge_base_settings import KnowledgeBaseSettings
from src.components.layout.users_settings import UsersSettings
from src.services.api.types import ErrorResponse, LLMsResponse
from components.layout.edit_user_modal import EditUserModal
from components.layout.knowledge_base_modal import KnowledgeBaseModal
from typing import Any
import logging
import json
import csv
import io
from typing import List, Dict

logger = logging.getLogger("vespa_app")

def setup_routes(app, rt):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.config_service = ConfigService()
    app.client = VespaAgentClient(app.config_service)

    @rt("/login")
    async def get_login(request : Request):
        if request.session.get("user"):
            return Redirect("/")

        message = request.query_params.get("message")
        return LoginPage(error_message=message)

    @rt("/api/login", methods=["POST"])
    async def login(request : Request):
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")

        try:
            response = await app.client.authenticate(username, password)
            if error_response := get_error_response(response):
                logger.warning(f"Login failed for user {username}: {error_response.message}")
                return LoginPage(error_message=error_response.message)

            logger.info(f"Login successful for user: {username}")
            request.session["user"] = response.json()

            return Redirect("/")

        except Exception as e:
            logger.error(f"Login error for user {username}: {str(e)}")
            return LoginPage(error_message="Authentication failed. Please try again.")

    @rt("/")
    @login_required
    async def home(request: Request):
        error_messages = []
        content = None
        llm_options = None
        try:
            user = request.session.get("user")
            user_json = json.loads(user)
            token = user_json.get("token")

            conversations_response = await request.app.client.get_conversations(
                token=token
            )
            if error_response := get_error_response(conversations_response):
                logger.error(f"Error getting conversations: {error_response}")
                error_messages.append(error_response.message)
            else:
                content = ChatHistory(
                    conversations=conversations_response.conversations
                )

            llms = await request.app.client.get_llms(token)
            if error_response := get_error_response(llms):
                logger.error(f"Error getting LLMs: {error_response}")
                error_messages.append(error_response.message)
            else:
                llm_options = _parse_llm_options(request, llms)
        except Exception as e:
            logger.error(f"Error preparing chat page: {e}")
            error_messages.append("Failed to prepare the chat page. Please try again later.")

        return Chat(
            user=user,
            llm_options=llm_options,
            content=content,
            error_messages=error_messages if error_messages else None
        )

    @rt("/conversation/{conversation_id}", methods=["GET"])
    @login_required
    async def conversation(request: Request, conversation_id: str):
        error_messages = []
        content = None
        conversation_result = None
        llm_options = None
        try:
            user = request.session.get("user")
            user_json = json.loads(user)
            token = user_json.get("token")

            response = await app.client.get_conversation(conversation_id, token)
            if error_response := get_error_response(response):
                logger.error(f"Error getting conversation {conversation_id}: {error_response}")
                conversation_result = None
                error_messages.append(error_response.message)
            else:
                conversation_result = response

            conversations_response = await request.app.client.get_conversations(
                token=token
            )
            if error_response := get_error_response(conversations_response):
                logger.error(f"Error getting conversations: {error_response}")
                content = None
                error_messages.append(error_response.message)
            else:
                content = ChatHistory(
                    conversations=conversations_response.conversations
                )

            llms = await request.app.client.get_llms(token)
            if error_response := get_error_response(llms):
                logger.error(f"Error getting LLMs: {error_response}")
                error_messages.append(error_response.message)
            else:
                llm_options = _parse_llm_options(request, llms)
        except Exception as e:
            logger.error(f"Error loading conversation {conversation_id}: {str(e)}")
            error_messages.append("Failed to prepare the chat page. Please try again later.")

        return Chat(
            user=user,
            llm_options=llm_options,
            content=content,
            conversation=conversation_result,
            error_messages=error_messages if error_messages else None
        )

    @rt("/api/set-llm", methods=["POST"])
    async def set_llm(request: Request):
        data = await request.json()
        model = data.get("model")
        if model:
            request.session["selected-llm"] = model
            logger.debug(f"Selected LLM set to: {model}")

            return {"status": "success"}
        return {"status": "error", "message": "No model provided"}, 400

    @rt("/api/logout", methods=["GET", "POST"])
    async def logout(request : Request):
        request.session.clear()

        message = request.query_params.get("message")
        return Redirect(f"/login?message={message}")

    @rt("/api/chat", methods=["POST", "GET"])
    @login_required
    async def chat(request: Request):
        llm_id = request.session.get("selected-llm")
        user = request.session.get("user")
        user = json.loads(user)
        token = user.get("token")
        conversation_id = request.query_params.get("conversation_id")

        # We make a POST first to create the conversation if it doesn't exist
        if request.method == "POST":
            try:
                form = await request.form()
                text = form.get("text")
                if not text:
                    return {"status": "error", "message": "No text provided"}, 400
                if not llm_id:
                    return {"status": "error", "message": "No LLM selected"}, 400

                if not conversation_id:
                    # Create new conversation if none exists
                    response = await app.client.create_conversation(token)
                    if error_response := get_error_response(response):
                        logger.error(f"Error creating conversation: {error_response}")
                        return {"status": "error", "message": "Failed to create conversation"}, 500

                    conversation_id = response.conversationId
                    return {
                        "status": "success",
                        "conversation_id": conversation_id,
                        "initial_text": text
                    }

                return {"status": "success"}
            except Exception as e:
                logger.error(f"Error creating conversation: {str(e)}")
                return {"status": "error", "message": "Failed to create conversation"}, 500
        # Then we make a GET to stream the conversation
        elif request.method == "GET":
            text = request.query_params.get("text")
            if not text:
                return {"status": "error", "message": "No text provided"}, 400
            if not llm_id:
                return {"status": "error", "message": "No LLM selected"}, 400
            if not conversation_id:
                return {"status": "error", "message": "No conversation ID provided"}, 400

            try:
                logger.debug("Starting SSE stream")
                return StreamingResponse(
                    app.client.stream_conversation(
                        llm_id=llm_id,
                        text=text,
                        token=token,
                        conversation_id=conversation_id
                    ),
                    media_type="text/event-stream"
                )
            except Exception as e:
                logger.error(f"Error creating conversation: {str(e)}")
                return {"status": "error", "message": "Failed to create conversation"}, 500

    @rt("/settings/chat-history")
    @login_required
    async def chat_history_settings(request: Request):
        try:
            user = request.session.get("user")
            user = json.loads(user)
            token = user.get("token")
            username = user.get("username")

            conversations_response = await request.app.client.get_conversations(
                token=token
            )
            return await Settings(
                request,
                "chat-history",
                content=ChatHistorySettings(
                    conversations=conversations_response.conversations
                )
            )
        except Exception as e:
            logger.error(f"Error fetching conversations for user {username}: {str(e)}")
            return await Settings(
                request,
                "chat-history",
                content=Div("Failed to load conversations. Please try again later.", cls="text-red-500")
            )

    @rt("/settings/connection-settings")
    @login_required
    async def connection_settings(request: Request):
        user = request.session.get("user")
        user = json.loads(user)
        if not any(role.upper() == "ADMIN" for role in user.get("roles", [])):
            logger.warning(f"Non-admin user tried to access connection settings: {user}")
            return await Settings(
                request,
                "connection-settings",
                content=Div("Access denied. Admin privileges required.", cls="p-6 text-red-500")
            )

        endpoint_value = request.app.config_service.get_connection_endpoint()
        return await Settings(
            request,
            "connection-settings",
            content=ConnectionSettings(endpoint_value=endpoint_value)
        )

    @rt("/api/conversations/{conversation_id}", methods=["DELETE"])
    @login_required
    async def delete_conversation(request: Request, conversation_id: str):
        client = request.app.client
        user = request.session.get("user")
        user = json.loads(user)
        token = user.get("token")

        if not token:
            return await Settings(
                request,
                "chat-history",
                error_messages=["Authentication required"]
            )

        try:
            response = await client.delete_conversation(
                conversation_id=conversation_id,
                token=token
            )

            if error_response := get_error_response(response):
                return await Settings(
                    request,
                    "chat-history",
                    error_messages=[error_response.message]
                )

            conversations_response = await client.get_conversations(token)
            if error_response := get_error_response(conversations_response):
                return await Settings(
                    request,
                    "chat-history",
                    error_messages=[error_response.message]
                )

            return await Settings(
                request,
                "chat-history",
                content=ChatHistorySettings(
                    conversations=conversations_response.conversations
                ),
                success_messages=["Conversation deleted successfully"]
            )

        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
            return await Settings(
                request,
                "chat-history",
                error_messages=["Error deleting conversation"]
            )

    @rt("/api/conversations/delete/all", methods=["DELETE"])
    @login_required
    async def delete_all_conversations(request: Request):
        client = request.app.client
        user = request.session.get("user")
        user = json.loads(user)
        token = user.get("token")

        if not token:
            return await Settings(
                request,
                "chat-history",
                error_messages=["Authentication required"]
            )

        try:
            response = await client.delete_all_conversations(token=token)

            if error_response := get_error_response(response):
                return await Settings(
                    request,
                    "chat-history",
                    error_messages=[error_response.message]
                )

            return await Settings(
                request,
                "chat-history",
                content=ChatHistorySettings(conversations=[]),
                success_messages=["All conversations deleted successfully"]
            )

        except Exception as e:
            logger.error(f"Error deleting all conversations: {str(e)}")
            return await Settings(
                request,
                "chat-history",
                error_messages=[str(e)]
            )

    @rt("/api/config/connection-endpoint", methods=["GET"])
    @login_required
    async def get_connection_endpoint(request: Request):
        try:
            endpoint = request.app.config_service.get_connection_endpoint()
            return endpoint
        except Exception as e:
            logger.error(f"Error getting connection endpoint: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": {"code": 500, "message": str(e)}}
            )

    @rt("/api/config/connection-endpoint", methods=["POST"])
    @login_required
    async def update_connection_endpoint(request: Request):
        try:
            form_data = await request.form()
            endpoint = form_data.get("endpoint", "")
            request.app.config_service.update_connection_endpoint(endpoint)
            await request.app.client.update_base_url()
            return await Settings(
                request,
                "connection-settings",
                content=ConnectionSettings(endpoint_value=endpoint),
                success_messages=["Connection settings saved successfully"]
            )
        except Exception as e:
            logger.error(f"Error updating connection endpoint: {str(e)}")
            return await Settings(
                request,
                "connection-settings",
                content=ConnectionSettings(endpoint_value=endpoint),
                error_messages=[str(e)]
            )

    @rt("/settings/users")
    @login_required
    async def users_settings(request: Request):
        user = request.session.get("user")
        user = json.loads(user)
        token = user.get("token")

        if "ADMIN" not in [role.upper() for role in user.get("roles", [])]:
            logger.warning(f"Non-admin user tried to access users settings: {user}")
            return await Settings(
                request,
                "users",
                content=Div("Access denied. Admin privileges required.", cls="p-6 text-red-500")
            )

        try:
            users_response = await app.client.get_users(token)
            if error_response := get_error_response(users_response):
                return await Settings(
                    request,
                    "users",
                    error_messages=[error_response.message]
                )

            return await Settings(
                request,
                "users",
                content=UsersSettings(
                    users=users_response.users
                )
            )
        except Exception as e:
            logger.error(f"Error fetching users: {str(e)}")
            return await Settings(
                request,
                "users",
                content=Div("Failed to load users. Please try again later.", cls="text-red-500")
            )

    @rt("/api/users/{user_id}", methods=["DELETE"])
    @login_required
    async def delete_user(request: Request, user_id: str):
        try:
            user = request.session.get("user")
            user = json.loads(user)
            token = user.get("token")

            if "ADMIN" not in [role.upper() for role in user.get("roles", [])]:
                return await Settings(
                    request,
                    "users",
                    error_messages=["Admin privileges required"]
                )

            response = await app.client.delete_user(
                user_id=user_id,
                token=token
            )

            if error_response := get_error_response(response):
                return await Settings(
                    request,
                    "users",
                    error_messages=[error_response.message]
                )

            users_response = await app.client.get_users(token=token)
            if error_response := get_error_response(users_response):
                return await Settings(
                    request,
                    "users",
                    error_messages=[error_response.message]
                )

            return await Settings(
                request,
                "users",
                content=UsersSettings(users=users_response.users),
                success_messages=[response.message]
            )
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return await Settings(
                request,
                "users",
                error_messages=["Failed to delete user"]
            )

    @rt("/settings/users/edit/{user_id}")
    @login_required
    async def get_edit_user(request: Request, user_id: str):
        user = request.session.get("user")
        user = json.loads(user)
        token = user.get("token")

        if "ADMIN" not in [role.upper() for role in user.get("roles", [])]:
            return await Settings(
                request,
                "users",
                error_messages=["Admin privileges required"]
            )

        try:
            response = await app.client.get_user(
                user_id=user_id,
                token=token
            )
            if error_response := get_error_response(response):
                return await Settings(
                    request,
                    "users",
                    error_messages=[error_response.message]
                )

            return EditUserModal(user=response.model_dump(), current_user_id=user.get("id"))
        except Exception as e:
            logger.error(f"Error fetching user: {str(e)}")
            return await Settings(
                request,
                "users",
                error_messages=["Failed to fetch user details"]
            )

    @rt("/api/users/edit/{user_id}", methods=["POST"])
    @login_required
    async def edit_user(request: Request, user_id: str):
        user = request.session.get("user")
        user = json.loads(user)
        token = user.get("token")

        if "ADMIN" not in [role.upper() for role in user.get("roles", [])]:
            return await Settings(
                request,
                "users",
                error_messages=["Admin privileges required"]
            )

        try:
            form_data = await request.form()

            password = form_data.get("password")
            user_data = {
                "username": form_data.get("username"),
                "email": form_data.get("email"),
                "is_admin": form_data.get("is_admin") == "on"
            }
            if password:
                user_data["password"] = password

            response = await app.client.edit_user(
                user_id=user_id,
                user_data=user_data,
                token=token
            )

            if error_response := get_error_response(response):
                logger.error(f"Error from edit_user endpoint: {error_response.message}")

                users_response = await app.client.get_users(token=token)
                if error_response_2 := get_error_response(users_response):
                    return await Settings(
                        request,
                        "users",
                        error_messages=[error_response.message, error_response_2.message]
                    )
                else:
                    return await Settings(
                        request,
                        "users",
                        content=UsersSettings(users=users_response.users),
                        error_messages=[error_response.message]
                    )

            user["username"] = user_data["username"]
            if user_id == user.get("id"):
                request.session["user"] = json.dumps({**user})
                request.session["token"] = f"mock_token_{user_data['username']}"

            users_response = await app.client.get_users(token=token)
            if error_response := get_error_response(users_response):
                return await Settings(
                    request,
                    "users",
                    error_messages=[error_response.message]
                )

            return await Settings(
                request,
                "users",
                content=UsersSettings(users=users_response.users),
                success_messages=[response.message]
            )

        except Exception as e:
            logger.error(f"Error editing user: {str(e)}")
            return await Settings(
                request,
                "users",
                error_messages=["Failed to update user"]
            )

    @rt("/settings/users/new")
    @login_required
    async def new_user(request: Request):
        user = request.session.get("user")
        user = json.loads(user)
        if "ADMIN" not in [role.upper() for role in user.get("roles", [])]:
            return await Settings(
                request,
                "users",
                error_messages=["Admin privileges required"]
            )
        return EditUserModal()

    @rt("/api/users/new", methods=["POST"])
    @login_required
    async def create_user(request: Request):
        user = request.session.get("user")
        user = json.loads(user)
        token = user.get("token")

        if "ADMIN" not in [role.upper() for role in user.get("roles", [])]:
            return await Settings(
                request,
                "users",
                error_messages=["Admin privileges required"]
            )

        try:
            form_data = await request.form()

            password = form_data.get("password")
            user_data = {
                "username": form_data.get("username"),
                "email": form_data.get("email"),
                "password": password,
                "is_admin": form_data.get("is_admin") == "on"
            }

            response = await app.client.create_user(
                user_data=user_data,
                token=token
            )

            if error_response := get_error_response(response):
                logger.error(f"Error from create_user endpoint: {error_response.message}")
                users_response = await app.client.get_users(token=token)
                if error_response_2 := get_error_response(users_response):
                    return await Settings(
                        request,
                        "users",
                        error_messages=[error_response.message, error_response_2.message]
                    )
                else:
                    return await Settings(
                        request,
                        "users",
                        content=UsersSettings(users=users_response.users),
                        error_messages=[error_response.message]
                    )

            users_response = await app.client.get_users(token=token)
            if error_response := get_error_response(users_response):
                return await Settings(
                    request,
                    "users",
                    error_messages=[error_response.message]
                )

            return await Settings(
                request,
                "users",
                content=UsersSettings(users=users_response.users),
                success_messages=[response.message]
            )

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return await Settings(
                request,
                "users",
                error_messages=["Failed to create user"]
            )

    @rt("/settings/knowledge-base")
    @login_required
    async def knowledge_bases_settings(request: Request):
        try:
            user = request.session.get("user")
            user = json.loads(user)
            token = user.get("token")

            knowledge_bases_response = await app.client.get_knowledge_bases(token)
            if error_response := get_error_response(knowledge_bases_response):
                return await Settings(
                    request,
                    "knowledge-base",
                    error_messages=[error_response.message]
                )

            return await Settings(
                request,
                "knowledge-base",
                content=KnowledgeBaseSettings(
                    knowledge_bases=knowledge_bases_response.knowledgeBases
                )
            )
        except Exception as e:
            logger.error(f"Error fetching knowledge bases: {str(e)}")
            return await Settings(
                request,
                "knowledge-base",
                content=KnowledgeBaseSettings(
                    knowledge_bases=[]
                ),
                error_messages=["Failed to load knowledge bases. Please try again later."],
            )

    @rt("/api/knowledge-base/{kb_id}", methods=["DELETE"])
    @login_required
    async def delete_knowledge_base(request: Request, kb_id: str):
        user = request.session.get("user")
        user = json.loads(user)
        token = user.get("token")

        if not token:
            return await Settings(
                request,
                "knowledge-base",
                error_messages=["Authentication required"]
            )

        try:
            response = await app.client.delete_knowledge_bases(kb_id, token)
            if error_response := get_error_response(response):
                return await Settings(
                    request,
                    "knowledge-base",
                    error_messages=[error_response.message]
                )

            try:
                knowledge_bases_response = await app.client.get_knowledge_bases(token)
                if error_response := get_error_response(knowledge_bases_response):
                    return await Settings(
                        request,
                        "knowledge-base",
                        error_messages=[error_response.message]
                    )

                return await Settings(
                    request,
                    "knowledge-base",
                    content=KnowledgeBaseSettings(
                        knowledge_bases=knowledge_bases_response.knowledgeBases
                    ),
                    success_messages=["Knowledge base deleted successfully"]
                )
            except Exception as e:
                logger.error(f"Error fetching knowledge bases after delete: {str(e)}")
                return await Settings(
                    request,
                    "knowledge-base",
                    error_messages=["Knowledge base deleted but failed to refresh the list"]
                )

        except Exception as e:
            logger.error(f"Error deleting knowledge base: {str(e)}")
            return await Settings(
                request,
                "knowledge-base",
                error_messages=[f"Failed to delete knowledge base: {str(e)}"]
            )

    @rt("/settings/knowledge-base/edit/{kb_id}")
    @login_required
    async def get_edit_knowledge_base(request: Request, kb_id: str):
        user = request.session.get("user")
        user = json.loads(user)
        token = user.get("token")

        try:
            response = await app.client.get_knowledge_base(kb_id, token)
            if error_response := get_error_response(response):
                return JSONResponse(
                    status_code=error_response.error.code,
                    content={"error": {"code": error_response.error.code, "message": error_response.error.message}}
                )

            return KnowledgeBaseModal(kb=response.model_dump())
        except Exception as e:
            logger.error(f"Error fetching knowledge base: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": {"code": 500, "message": str(e)}}
            )

    @rt("/api/knowledge-base/edit/{kb_id}", methods=["POST"])
    @login_required
    async def edit_knowledge_base(request: Request, kb_id: str):
        user = request.session.get("user")
        user = json.loads(user)
        token = user.get("token")

        if not token:
            return await Settings(
                request,
                "knowledge-base",
                error_messages=["Authentication required"]
            )

        try:
            form_data = await request.form()

            kb_data = {
                "title": form_data.get("title"),
                "content": form_data.get("content"),
            }

            response = await app.client.edit_knowledge_base(kb_id, kb_data, token)
            if error_response := get_error_response(response):
                logger.error(f"Error from edit knowledge base endpoint: {error_response.message}")
                return await Settings(
                    request,
                    "knowledge-base",
                    error_messages=[error_response.message]
                )

            try:
                knowledge_bases_response = await app.client.get_knowledge_bases(token)
                if error_response := get_error_response(knowledge_bases_response):
                    return await Settings(
                        request,
                        "knowledge-base",
                        error_messages=[error_response.message]
                    )

                return await Settings(
                    request,
                    "knowledge-base",
                    content=KnowledgeBaseSettings(
                        knowledge_bases=knowledge_bases_response.knowledgeBases
                    ),
                    success_messages=["Knowledge base updated successfully"]
                )
            except Exception as e:
                logger.error(f"Error fetching knowledge bases after edit: {str(e)}")
                return await Settings(
                    request,
                    "knowledge-base",
                    error_messages=["Knowledge base updated but failed to refresh the list"]
                )

        except Exception as e:
            logger.error(f"Error editing knowledge base: {str(e)}")
            return await Settings(
                request,
                "knowledge-base",
                error_messages=[f"Failed to update knowledge base: {str(e)}"]
            )

    @rt("/settings/knowledge-base/new")
    @login_required
    async def new_knowledge_base(request: Request):
        return KnowledgeBaseModal()

    @rt("/api/knowledge-base/new", methods=["POST"])
    @login_required
    async def create_knowledge_base(request: Request):
        user = request.session.get("user")
        user = json.loads(user)
        token = user.get("token")

        if not token:
            return await Settings(
                request,
                "knowledge-base",
                error_messages=["Authentication required"]
            )

        try:
            form_data = await request.form()

            kb_data = {
                "title": form_data.get("title"),
                "content": form_data.get("content"),
            }

            response = await app.client.create_knowledge_base(kb_data, token)
            if error_response := get_error_response(response):
                logger.error(f"Error from create_knowledge_base endpoint: {error_response.message}")
                return await Settings(
                    request,
                    "knowledge-base",
                    error_messages=[error_response.message]
                )

            try:
                knowledge_bases_response = await app.client.get_knowledge_bases(token)
                if error_response := get_error_response(knowledge_bases_response):
                    return await Settings(
                        request,
                        "knowledge-base",
                        error_messages=[error_response.message]
                    )

                return await Settings(
                    request,
                    "knowledge-base",
                    content=KnowledgeBaseSettings(
                        knowledge_bases=knowledge_bases_response.knowledgeBases
                    ),
                    success_messages=["Knowledge base created successfully"]
                )
            except Exception as e:
                logger.error(f"Error fetching knowledge bases after create: {str(e)}")
                return await Settings(
                    request,
                    "knowledge-base",
                    error_messages=["Knowledge base created but failed to refresh the list"]
                )

        except Exception as e:
            logger.error(f"Error creating knowledge base: {str(e)}")
            return await Settings(
                request,
                "knowledge-base",
                error_messages=[f"Failed to create knowledge base: {str(e)}"]
            )

    @rt("/api/knowledge-base/bulk", methods=["POST"])
    @login_required
    async def create_bulk_knowledge_base(request: Request):
        user = request.session.get("user")
        user = json.loads(user)
        token = user.get("token")

        try:
            form = await request.form()
            file = form.get("csv_file")
            if not file:
                return await Settings(
                    request,
                    "knowledge-base",
                    error_messages=["No file uploaded"]
                )

            try:
                knowledge_bases = await _process_csv_file(file)
            except ValueError as e:
                return await Settings(
                    request,
                    "knowledge-base",
                    error_messages=[str(e)]
                )

            success_count = 0
            error_messages = []

            for kb_data in knowledge_bases:
                try:
                    response = await app.client.create_knowledge_base(kb_data, token)
                    if error_response := get_error_response(response):
                        error_messages.append(f"Failed to create knowledge base '{kb_data['title']}': {error_response.message}")
                    else:
                        success_count += 1
                except Exception as e:
                    error_messages.append(f"Failed to create knowledge base '{kb_data['title']}': {str(e)}")

            try:
                knowledge_bases_response = await app.client.get_knowledge_bases(token)
                if error_response := get_error_response(knowledge_bases_response):
                    error_messages.append(f"Failed to refresh knowledge bases list: {error_response.message}")
                    return await Settings(
                        request,
                        "knowledge-base",
                        error_messages=error_messages
                    )

                messages = []
                if success_count > 0:
                    messages.append(f"Successfully created {success_count} knowledge base(s)")

                return await Settings(
                    request,
                    "knowledge-base",
                    content=KnowledgeBaseSettings(
                        knowledge_bases=knowledge_bases_response.knowledgeBases
                    ),
                    success_messages=messages if messages else None,
                    error_messages=error_messages if error_messages else None
                )
            except Exception as e:
                logger.error(f"Error fetching knowledge bases after bulk create: {str(e)}")
                error_messages.append("Failed to refresh knowledge bases list")
                return await Settings(
                    request,
                    "knowledge-base",
                    error_messages=error_messages
                )

        except Exception as e:
            logger.error(f"Error creating bulk knowledge bases: {str(e)}")
            return await Settings(
                request,
                "knowledge-base",
                error_messages=[f"Failed to process bulk upload: {str(e)}"]
            )

    async def _process_csv_file(file) -> List[Dict[str, str]]:
        try:
            content = await file.read()
            content_str = content.decode()

            knowledge_bases = []
            csv_reader = csv.DictReader(io.StringIO(content_str))
            for row in csv_reader:
                if 'Title' not in row or 'Content' not in row:
                    raise ValueError("CSV must have 'Title' and 'Content' columns")
                knowledge_bases.append({
                    "title": row["Title"],
                    "content": row["Content"],
                })
            return knowledge_bases
        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}")
            raise

    def _parse_llm_options(request: Request, llms: LLMsResponse):
        selected_llm = request.session.get("selected-llm")
        llms = llms.llms
        if not selected_llm and llms:
            selected_llm = llms[0].id
            request.session["selected-llm"] = selected_llm

        # Extract just id and name for the dropdown options
        llm_options = [
            (llm.id, llm.name, llm.id == selected_llm)
            for llm in llms
        ]

        return llm_options

    @app.on_event("shutdown")
    async def shutdown_event():
        await app.client.close()

    return app

def get_error_response(response: Any) -> ErrorResponse:
    if isinstance(response, ErrorResponse):
        if response.statusCode == 401:
            response.message = "UNAUTHORIZED"
        return response
    return None
