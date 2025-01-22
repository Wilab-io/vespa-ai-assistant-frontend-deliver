from datetime import datetime
from fastapi import FastAPI, HTTPException, Header, Path, Body
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, Optional
import uvicorn
import os
import logging
import asyncio
from src.services.api.types import AuthResponse, AuthResult, ErrorResponse, User, ConversationRequest, NewConversationResponse, Conversation, ChatMessage, ConversationsResponse, UsersResponse, User, ConversationResult, ConversationsResult, LLM, LLMsResponse, LLMsResult, NewConversationResult, UserResult, GenericActionResponse, GenericActionResult, UsersResult, KnowledgeBase, KnowledgeBasesResponse, KnowledgeBasesResult, KnowledgeBaseResult

app = FastAPI(title="Mock Vespa Agent API")
logger = logging.getLogger("vespa_app")

default_url = "http://localhost:8080"
use_mock = os.getenv("MOCK_API", "false").lower() == "true"
app.base_url = default_url if use_mock else os.getenv("VESPA_AGENT_URL", default_url)

EVENT_CONTENT = "content"
EVENT_END_OF_RESPONSE = "end_of_response"

@app.post("/assistant/auth")
async def authenticate(credentials: Dict[str, str]) -> AuthResult:
    username = credentials.get("username")
    password = credentials.get("password")

    if not username or not password:
        return raise_error("MISSING_DATA", "Username and password are required", 400)

    user = next((u for u in mock_users if u["username"] == username), None)
    if not user:
        return raise_error("UNAUTHORIZED", "Invalid username", 401)

    if password != user["password"]:
        return raise_error("UNAUTHORIZED", "Invalid password", 401)

    return AuthResponse(
        token=f"mock_token_{username}",
        id=user["id"],
        email=user["email"],
        username=user["username"],
        roles=user["roles"]
    )

def verify_token(authorization: str = Header(None)) -> bool:
    if not authorization or not authorization.startswith("Bearer "):
        return False

    token = authorization.split(" ")[1]
    return any(token == f"mock_token_{user['username']}" for user in mock_users)

async def stream_mock_response(conversation_id: str, user_query: str):
    conversation = next((c for c in mock_conversations if c.conversationId == conversation_id), None)
    if not conversation:
        return

    user_message = ChatMessage(
        messageId=get_random_id(),
        sender="user",
        senderType="user",
        content=user_query,
        timestamp=datetime.now().isoformat()
    )
    conversation.messages.append(user_message)

    for msg in mock_messages:
        await asyncio.sleep(0.5)
        logger.debug(f"Mock: [CONTENT] {msg.content}")

        bot_message = ChatMessage(
            messageId=get_random_id(),
            sender="assistant",
            senderType="bot",
            content=msg.content,
            timestamp=datetime.now().isoformat()
        )
        conversation.messages.append(bot_message)

        yield f"event: {EVENT_CONTENT}\ndata: {msg.content}\n\n"

    logger.debug("Mock: [END_OF_RESPONSE]")
    yield f"event: {EVENT_END_OF_RESPONSE}\ndata: \n\n"

@app.post("/assistant/chat")
async def chat_endpoint(request: ConversationRequest, authorization: str = Header(None)):
    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Invalid token", 401)

    if not request.conversationId:
        return raise_error("BAD_REQUEST", "Missing conversation ID", 400)

    conversation = next((c for c in mock_conversations if c.conversationId == request.conversationId), None)
    if conversation and not conversation.messages:
        conversation.title = request.query

    return StreamingResponse(stream_mock_response(request.conversationId, request.query), media_type="text/event-stream")

def validate_admin_permission(authorization: str) -> bool:
    """Validate if the user has admin permissions"""
    if not authorization or not authorization.startswith("Bearer "):
        return False

    token = authorization.split(" ")[1]
    username = token.replace("mock_token_", "")
    user = next((u for u in mock_users if u["username"] == username), None)
    return user and "ADMIN" in [role.upper() for role in user["roles"]]

def get_user_by_id(user_id: str) -> User:
    """Get user by ID from mock_users"""
    user = next((user for user in mock_users if user["id"] == user_id), None)
    if not user:
        return None

    return User(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        roles=user["roles"],
        createdAt=user.get("createdAt", "2024-01-01T00:00:00Z")
    )

@app.get("/assistant/llms")
async def get_llms(authorization: str = Header(None)) -> LLMsResult:
    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot get LLMs list: Missing or invalid authorization token", 401)

    return mock_llms

@app.post("/assistant/conversations")
async def create_conversation(authorization: str = Header(None)) -> NewConversationResult:
    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot create conversation: Missing or invalid authorization token", 401)

    new_conversation = Conversation(
        conversationId=get_random_id(),
        title="New chat",
        messages=[],
        createdAt=datetime.now().isoformat(),
        updatedAt=datetime.now().isoformat()
    )
    mock_conversations.append(new_conversation)

    return NewConversationResponse(
        conversationId=new_conversation.conversationId,
        title=new_conversation.title
    )

@app.get("/assistant/conversations")
async def get_conversations(
    authorization: str = Header(None)
) -> ConversationsResult:
    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot get conversations: Missing or invalid authorization token", 403)

    conversations_without_messages = []
    for conversation in mock_conversations:
        conversation_copy = conversation.model_dump()
        del conversation_copy["messages"]
        conversations_without_messages.append(conversation_copy)

    return ConversationsResponse(conversations=conversations_without_messages)

@app.get("/assistant/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str = Path(...),
    authorization: str = Header(None)
) -> ConversationResult:
    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot get conversation: Missing or invalid authorization token", 401)

    conversation = next((c for c in mock_conversations if c.conversationId == conversation_id), None)

    if not conversation:
        logger.debug(f"Mock: [GET_CONVERSATION] {conversation_id} not found")
        return raise_error("CONVERSATION_NOT_FOUND", "Conversation not found", 404)

    logger.debug(f"Mock: [GET_CONVERSATION] {conversation.conversationId}")
    return conversation

@app.delete("/assistant/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str = Path(...),
    authorization: str = Header(None)
) -> GenericActionResult:
    global mock_conversations

    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot delete conversation: Missing or invalid authorization token", 401)

    conversation = next((c for c in mock_conversations if c.conversationId == conversation_id), None)
    if not conversation:
        return raise_error("CONVERSATION_NOT_FOUND", "Conversation not found", 404)

    mock_conversations = [c for c in mock_conversations if c.conversationId != conversation_id]

    return GenericActionResponse(
        message="Conversation deleted successfully."
    )

@app.delete("/assistant/conversations/delete/all")
async def delete_all_conversations(authorization: str = Header(None)) -> GenericActionResult:
    global mock_conversations

    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot delete conversations: Missing or invalid authorization token", 401)

    mock_conversations = []

    return GenericActionResponse(
        message="All conversations deleted successfully."
    )

@app.get("/assistant/users")
async def get_users(authorization: Optional[str] = Header(None)) -> UsersResult:
    global mock_users

    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot get users: Missing or invalid authorization token", 401)

    users = [
        User(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            roles=user["roles"],
            createdAt=user.get("createdAt", "2024-01-01T00:00:00Z")
        ) for user in mock_users
    ]
    return UsersResponse(users=users)

@app.get("/assistant/users/{user_id}")
async def get_user(
    user_id: str = Path(...),
    authorization: str = Header(None)
) -> UserResult:
    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot get user: Missing or invalid authorization token", 401)

    if not validate_admin_permission(authorization):
        return raise_error("UNAUTHORIZED", "Cannot get user: Missing admin permission", 401)

    user = get_user_by_id(user_id)
    if not user:
        return raise_error("USER_NOT_FOUND", "User not found", 404)

    return user

@app.delete("/assistant/users/{user_id}")
async def delete_user(
    user_id: str = Path(...),
    authorization: str = Header(None)
) -> GenericActionResult:
    global mock_users

    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot delete user: Missing or invalid authorization token", 401)

    if not validate_admin_permission(authorization):
        return raise_error("UNAUTHORIZED", "Cannot delete user: Missing admin permission", 401)

    user = get_user_by_id(user_id)

    if not user:
        return raise_error("USER_NOT_FOUND", "User not found", 404)

    if any(role.upper() == "ADMIN" for role in user.roles):
        return raise_error("FORBIDDEN", "Cannot delete user: Admin users cannot be deleted", 403)

    mock_users = [u for u in mock_users if u["id"] != user_id]

    return GenericActionResponse(
        message="User removed successfully."
    )

@app.put("/assistant/users/{user_id}")
async def edit_user(
    user_id: str = Path(...),
    user_data: str = Body(...),
    authorization: str = Header(None)
) -> GenericActionResult:
    global mock_users

    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot edit user: Missing or invalid authorization token", 401)

    if not validate_admin_permission(authorization):
        return raise_error("UNAUTHORIZED", "Cannot edit user: Missing admin permission", 401)

    user_to_edit = get_user_by_id(user_id)
    if not user_to_edit:
        return raise_error("USER_NOT_FOUND", "User not found", 404)

    new_username = user_data["username"]

    username_exists = any(
        user["username"] == new_username and user["id"] != user_id
        for user in mock_users
    )
    if username_exists:
        return raise_error("FORBIDDEN", "Username already exists", 403)

    for user in mock_users:
        if user["id"] == user_id:
            user["username"] = new_username
            user["email"] = user_data["email"]
            user["roles"] = user_data["roles"]
            if "password" in user_data:
                user["password"] = user_data["password"]
            break

    return GenericActionResponse(
        message="User edited successfully."
    )

@app.post("/assistant/users")
async def create_user(
    user_data: dict = Body(...),
    authorization: str = Header(None)
) -> GenericActionResult:
    global mock_users, mock_users

    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot create user: Missing or invalid authorization token", 401)

    if not validate_admin_permission(authorization):
        return raise_error("UNAUTHORIZED", "Cannot create user: Missing admin permission", 401)

    required_fields = ["username", "email", "password", "roles"]
    missing_fields = [field for field in required_fields if field not in user_data]
    if missing_fields:
        return raise_error("BAD_REQUEST", f"Missing required fields: {', '.join(missing_fields)}", 400)

    username_exists = any(
        user["username"] == user_data["username"]
        for user in mock_users
    )
    if username_exists:
        return raise_error("FORBIDDEN", "Username already exists", 403)

    mock_users.append({
        "id": get_random_id(),
        "username": user_data["username"],
        "email": user_data["email"],
        "roles": user_data["roles"],
        "createdAt": "2024-03-01T10:00:00Z",
        "password": user_data["password"],
    })

    return GenericActionResponse(
        message="User created successfully."
    )

def get_knowledge_base_by_id(kb_id: str) -> Optional[KnowledgeBase]:
    knowledge_base = next((kb for kb in mock_knowledge_bases if kb.id == kb_id), None)
    return knowledge_base

@app.get("/assistant/knowledge-base")
async def get_knowledge_bases(authorization: Optional[str] = Header(None)) -> KnowledgeBasesResult:
    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot get knowledge base: Missing or invalid authorization token", 401)

    return KnowledgeBasesResponse(knowledgeBases=mock_knowledge_bases)

@app.get("/assistant/knowledge-base/{kb_id}")
async def get_knowledge_base(
    kb_id: str = Path(...),
    authorization: str = Header(None)
) -> KnowledgeBaseResult:
    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot get knowledge base: Missing or invalid authorization token", 401)

    kb = get_knowledge_base_by_id(kb_id)

    if not kb:
        return raise_error("KNOWLEDGE_BASE_NOT_FOUND", "Knowledge base not found", 404)

    return kb

@app.delete("/assistant/knowledge-base/{kb_id}")
async def delete_knowledge_base(
    kb_id: str = Path(...),
    authorization: str = Header(None)
) -> GenericActionResult:
    global mock_knowledge_bases

    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot delete knowledge base: Missing or invalid authorization token", 401)

    kb = get_knowledge_base_by_id(kb_id)
    if not kb:
        return raise_error("KNOWLEDGE_BASE_NOT_FOUND", "Knowledge base not found", 404)

    mock_knowledge_bases = [kb for kb in mock_knowledge_bases if kb.id != kb_id]

    return GenericActionResponse(
        message="Knowledge base deleted successfully."
    )

@app.put("/assistant/knowledge-base/{kb_id}")
async def edit_knowledge_base(
    kb_id: str = Path(...),
    kb_data: dict = Body(...),
    authorization: str = Header(None)
) -> GenericActionResult:
    global mock_knowledge_bases

    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot edit knowledge base: Missing or invalid authorization token", 401)

    kb = get_knowledge_base_by_id(kb_id)

    if not kb:
        return raise_error("KNOWLEDGE_BASE_NOT_FOUND", "Knowledge base not found", 404)

    kb.title = kb_data["title"]
    kb.content = kb_data["content"]

    return GenericActionResponse(
        message="Knowledge base updated successfully."
    )

@app.post("/assistant/knowledge-base")
async def create_knowledge_base(
    kb_data: dict = Body(...),
    authorization: str = Header(None)
) -> GenericActionResult:
    global mock_knowledge_bases

    if not verify_token(authorization):
        return raise_error("UNAUTHORIZED", "Cannot create knowledge base: Missing or invalid authorization token", 401)

    required_fields = ["title", "content"]
    missing_fields = [field for field in required_fields if field not in kb_data]
    if missing_fields:
        return raise_error("BAD_REQUEST", f"Missing required fields: {', '.join(missing_fields)}", 400)

    new_mock_kb = KnowledgeBase(
        id=get_random_id(),
        title=kb_data["title"],
        content=kb_data["content"],
        createdAt="2024-03-01T10:00:00Z"
    )

    mock_knowledge_bases.append(new_mock_kb)

    return GenericActionResponse(
        message="Knowledge base created successfully."
    )

def raise_error(error_code: str, message: str, status_code: int):
    error_response = ErrorResponse(
        **{"error-code": error_code},
        message=message
    )
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(by_alias=True)
    )

def get_random_id():
    return os.urandom(8).hex()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

mock_users = [
    {
        "id": "user001",
        "username": "alice",
        "email": "alice@example.com",
        "roles": ["ADMIN", "USER"],
        "password": "1"
    },
    {
        "id": "user002",
        "username": "bob",
        "email": "bob@example.com",
        "roles": ["USER"],
        "password": "1"
    },
    {
        "id": "user003",
        "username": "charlie",
        "email": "charlie@example.com",
        "roles": ["USER"],
        "password": "1"
    },
    {
        "id": "user004",
        "username": "admin",
        "email": "admin@example.com",
        "roles": ["ADMIN", "USER"],
        "password": "1"
    },
    {
        "id": "user005",
        "username": "jane.smith",
        "email": "jane.smith@example.com",
        "roles": ["USER"],
        "password": "1"
    }
]

mock_llms = LLMsResponse(
    llms=[
        LLM(
            id="gpt-4",
            name="GPT-4",
            type="remote",
            description="OpenAI GPT-4 model",
            createdAt="2024-03-15T10:00:00Z"
        ),
        LLM(
            id="claude-3",
            name="Claude 3",
            type="remote",
            description="Anthropic Claude 3 model",
            createdAt="2024-03-15T10:00:00Z"
        ),
        LLM(
            id="gemini",
            name="Gemini",
            type="remote",
            description="Google Gemini model",
            createdAt="2024-03-15T10:00:00Z"
        )
    ]
)

mock_messages = [
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="Hello! 👋 I'm your Vespa AI assistant. I can help you explore and analyze your data using your knowledge base and Elasticsearch.<br><br>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="<details><summary><strong>🔍 Knowledge Base Search</strong></summary>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="<ul><li>→ Searching through your uploaded documents for relevant information</li><li>→ Analyzing document patterns and relationships</li><li>→ Identifying the most appropriate data structures and query patterns</li><li>→ Learning from similar queries in the documentation</li></ul></details><br>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="<details><summary><strong>⚡ Query Execution</strong></summary>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="<ul><li>→ Formulating optimal Elasticsearch queries based on the knowledge gathered</li><li>→ Applying filters and aggregations for precise results</li><li>→ Executing the query with appropriate parameters</li><li>→ Monitoring query performance and adjusting as needed</li></ul></details><br>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="<details><summary><strong>📊 Results Processing</strong></summary>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="<ul><li>→ Analyzing the raw query results</li><li>→ Organizing and structuring the information</li><li>→ Translating technical data into clear, understandable insights</li><li>→ Preparing visualizations or summaries when appropriate</li></ul></details><br>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="Based on my analysis, here's what I found:<br><br>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="<strong>📈 Overview:</strong><br>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="Your database shows a 23% increase in transaction volume over the past month, with peak activity during weekday afternoons.<br><br>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="<strong>🎯 Key Findings:</strong><br>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="• Most active users: Enterprise accounts (64% of queries)<br>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="• Average response time: 1.2 seconds<br>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="• Storage efficiency: 82% (above recommended threshold)<br><br>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="<strong>💡 Recommendations:</strong><br>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="1. Consider implementing query caching for frequently accessed data<br>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="2. Optimize index settings for better write performance<br>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="3. Review and potentially scale resources during peak hours<br><br>",
        timestamp="2024-01-01T00:00:00Z"
    ),
    ChatMessage(
        messageId=get_random_id(),
        sender="assistant",
        senderType="bot",
        content="Would you like me to dive deeper into any of these aspects? 🤔",
        timestamp="2024-01-01T00:00:00Z"
    )
]

mock_conversations = [
    Conversation(
        conversationId=get_random_id(),
        title="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
        updatedAt="2024-12-20T12:34:56Z",
        createdAt="2024-12-20T12:34:56Z",
        messages= [
            ChatMessage(
                messageId=get_random_id(),
                sender="user",
                senderType="user",
                content="Can you analyze the performance of my Elasticsearch cluster and suggest optimizations?",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="Hello! 👋 I'm your Vespa AI assistant. I can help you explore and analyze your data using your knowledge base and Elasticsearch.<br><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<details><summary><strong>🔍 Knowledge Base Search</strong></summary>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<ul><li>→ Searching through your uploaded documents for relevant information</li><li>→ Analyzing document patterns and relationships</li><li>→ Identifying the most appropriate data structures and query patterns</li><li>→ Learning from similar queries in the documentation</li></ul></details><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<details><summary><strong>⚡ Query Execution</strong></summary>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<ul><li>→ Formulating optimal Elasticsearch queries based on the knowledge gathered</li><li>→ Applying filters and aggregations for precise results</li><li>→ Executing the query with appropriate parameters</li><li>→ Monitoring query performance and adjusting as needed</li></ul></details><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<details><summary><strong>📊 Results Processing</strong></summary>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<ul><li>→ Analyzing the raw query results</li><li>→ Organizing and structuring the information</li><li>→ Translating technical data into clear, understandable insights</li><li>→ Preparing visualizations or summaries when appropriate</li></ul></details><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="Based on my analysis, here's what I found:<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<strong>📈 Overview:</strong><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="User activity shows a steady growth rate of 18% month over month.<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<strong>🎯 Key Findings:</strong><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="• Average session duration: 12 minutes<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="• Peak login time: 9 AM to 11 AM<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="• Bounce rate reduced by 6% compared to last month<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<strong>💡 Recommendations:</strong><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="1. Enhance mobile user experience to maintain growth<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="2. Introduce personalized email campaigns for inactive users<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="3. Optimize landing pages for better engagement<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            )
        ]
    ),
    Conversation(
        conversationId=get_random_id(),
        title="Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
        updatedAt="2024-12-21T09:10:15Z",
        createdAt="2024-12-21T09:10:15Z",
        messages= [
            ChatMessage(
                messageId=get_random_id(),
                sender="user",
                senderType="user",
                content="What are the usage patterns and key trends of my platform over the last month?",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="Hello! 👋 I'm your Vespa AI assistant. I can help you explore and analyze your data using your knowledge base and Elasticsearch.<br><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<details><summary><strong>🔍 Knowledge Base Search</strong></summary>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<ul><li>→ Searching through your uploaded documents for relevant information</li><li>→ Analyzing document patterns and relationships</li><li>→ Identifying the most appropriate data structures and query patterns</li><li>→ Learning from similar queries in the documentation</li></ul></details><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<details><summary><strong>⚡ Query Execution</strong></summary>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<ul><li>→ Formulating optimal Elasticsearch queries based on the knowledge gathered</li><li>→ Applying filters and aggregations for precise results</li><li>→ Executing the query with appropriate parameters</li><li>→ Monitoring query performance and adjusting as needed</li></ul></details><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<details><summary><strong>📊 Results Processing</strong></summary>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<ul><li>→ Analyzing the raw query results</li><li>→ Organizing and structuring the information</li><li>→ Translating technical data into clear, understandable insights</li><li>→ Preparing visualizations or summaries when appropriate</li></ul></details><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="Based on my analysis, here's what I found:<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<strong>📈 Overview:</strong><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="The top-performing product category achieved a 32% increase in revenue this quarter.<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<strong>🎯 Key Findings:</strong><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="• Best-selling product: Premium headphones<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="• Average cart size: 2.4 items<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="• Sales conversion rate: 4.8%<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<strong>💡 Recommendations:</strong><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="1. Highlight customer reviews to boost product trust<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="2. Offer discounts for bulk purchases to increase cart size<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="3. Optimize product pages for mobile users<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            )
        ]
    ),
    Conversation(
        conversationId=get_random_id(),
        title="Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
        updatedAt="2024-12-20T12:34:56Z",
        createdAt="2024-12-20T12:34:56Z",
        messages= [
            ChatMessage(
                messageId=get_random_id(),
                sender="user",
                senderType="user",
                content="Why is my application experiencing high latency in certain regions? Can you identify the cause?",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="Hello! 👋 I'm your Vespa AI assistant. I can help you explore and analyze your data using your knowledge base and Elasticsearch.<br><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<details><summary><strong>🔍 Knowledge Base Search</strong></summary>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<ul><li>→ Searching through your uploaded documents for relevant information</li><li>→ Analyzing document patterns and relationships</li><li>→ Identifying the most appropriate data structures and query patterns</li><li>→ Learning from similar queries in the documentation</li></ul></details><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<details><summary><strong>⚡ Query Execution</strong></summary>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<ul><li>→ Formulating optimal Elasticsearch queries based on the knowledge gathered</li><li>→ Applying filters and aggregations for precise results</li><li>→ Executing the query with appropriate parameters</li><li>→ Monitoring query performance and adjusting as needed</li></ul></details><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<details><summary><strong>📊 Results Processing</strong></summary>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<ul><li>→ Analyzing the raw query results</li><li>→ Organizing and structuring the information</li><li>→ Translating technical data into clear, understandable insights</li><li>→ Preparing visualizations or summaries when appropriate</li></ul></details><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="Based on my analysis, here's what I found:<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<strong>📈 Overview:</strong><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="The latest email marketing campaign generated 3,200 leads.<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<strong>🎯 Key Findings:</strong><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="• Open rate: 42% (above industry average)<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="• Click-through rate: 14%<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="• Conversion rate: 6%<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<strong>💡 Recommendations:</strong><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="1. A/B test subject lines for higher open rates<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="2. Use personalized CTAs to improve click-through rates<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="3. Retarget leads who didn't convert<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            )
        ]
    ),
    Conversation(
        conversationId=get_random_id(),
        title="Excepteur sint occaecat cupidatat non proident",
        updatedAt="2024-11-20T12:34:56Z",
        createdAt="2024-11-20T12:34:56Z",
        messages= [
            ChatMessage(
                messageId=get_random_id(),
                sender="user",
                senderType="user",
                content="There has been an increase in server errors recently. Can you identify the most common issues and suggest fixes?",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="Hello! 👋 I'm your Vespa AI assistant. I can help you explore and analyze your data using your knowledge base and Elasticsearch.<br><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<details><summary><strong>🔍 Knowledge Base Search</strong></summary>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<ul><li>→ Searching through your uploaded documents for relevant information</li><li>→ Analyzing document patterns and relationships</li><li>→ Identifying the most appropriate data structures and query patterns</li><li>→ Learning from similar queries in the documentation</li></ul></details><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<details><summary><strong>⚡ Query Execution</strong></summary>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<ul><li>→ Formulating optimal Elasticsearch queries based on the knowledge gathered</li><li>→ Applying filters and aggregations for precise results</li><li>→ Executing the query with appropriate parameters</li><li>→ Monitoring query performance and adjusting as needed</li></ul></details><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<details><summary><strong>📊 Results Processing</strong></summary>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<ul><li>→ Analyzing the raw query results</li><li>→ Organizing and structuring the information</li><li>→ Translating technical data into clear, understandable insights</li><li>→ Preparing visualizations or summaries when appropriate</li></ul></details><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="Based on my analysis, here's what I found:<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<strong>📈 Overview:</strong><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="System error logs indicate a 15% increase in 500-level server errors over the past week.<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<strong>🎯 Key Findings:</strong><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="• Top recurring error: Database connection timeout<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="• Error peak time: 3-5 PM EST<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="• Most affected endpoint: `/api/v1/orders`<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<strong>💡 Recommendations:</strong><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="1. Optimize database query performance for high-traffic endpoints<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="2. Increase connection pool size for database handling<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="3. Implement circuit breaker patterns to reduce impact on users<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            )
        ]
    ),
    Conversation(
        conversationId=get_random_id(),
        title="Ut enim ad minim veniam.",
        updatedAt="2024-12-31T09:10:15Z",
        createdAt="2024-12-31T09:10:15Z",
        messages= [
            ChatMessage(
                messageId=get_random_id(),
                sender="user",
                senderType="user",
                content="Can you analyze customer support interactions and identify areas for improvement?",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="Hello! 👋 I'm your Vespa AI assistant. I can help you explore and analyze your data using your knowledge base and Elasticsearch.<br><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<details><summary><strong>🔍 Knowledge Base Search</strong></summary>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<ul><li>→ Searching through your uploaded documents for relevant information</li><li>→ Analyzing document patterns and relationships</li><li>→ Identifying the most appropriate data structures and query patterns</li><li>→ Learning from similar queries in the documentation</li></ul></details><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<details><summary><strong>⚡ Query Execution</strong></summary>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<ul><li>→ Formulating optimal Elasticsearch queries based on the knowledge gathered</li><li>→ Applying filters and aggregations for precise results</li><li>→ Executing the query with appropriate parameters</li><li>→ Monitoring query performance and adjusting as needed</li></ul></details><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<details><summary><strong>📊 Results Processing</strong></summary>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<ul><li>→ Analyzing the raw query results</li><li>→ Organizing and structuring the information</li><li>→ Translating technical data into clear, understandable insights</li><li>→ Preparing visualizations or summaries when appropriate</li></ul></details><br>",
                timestamp="2024-01-01T00:00:00Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="Based on my analysis, here's what I found:<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<strong>📈 Overview:</strong><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="Customer support inquiries have increased by 22% this month, primarily regarding order tracking issues.<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<strong>🎯 Key Findings:</strong><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="• Top inquiry type: Order tracking (35%)<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="• Average response time: 5 minutes<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="• Positive feedback rate: 72%<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="<strong>💡 Recommendations:</strong><br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="1. Implement a self-service order tracking portal to reduce inquiries<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="2. Improve response time by training additional support agents<br>",
                timestamp="2024-12-20T12:34:56Z"
            ),
            ChatMessage(
                messageId=get_random_id(),
                sender="assistant",
                senderType="bot",
                content="3. Use proactive communication (e.g., email updates) to minimize order tracking queries<br><br>",
                timestamp="2024-12-20T12:34:56Z"
            )
        ]
    )
]

mock_knowledge_bases = [
    KnowledgeBase(
        id="base001",
        title="text 1 title",
        content="text 1 body",
        createdAt="2024-01-15T08:30:00Z",
    ),
    KnowledgeBase(
        id="base002",
        title="text 2 title",
        content="text 2 body",
        createdAt="2024-01-15T08:30:00Z",
    )
]
