from pydantic import BaseModel, Field
from typing import List, Optional, Union

class ErrorResponse(BaseModel):
    errorCode: str = Field(alias="error-code")
    message: str
    statusCode: Optional[int] = None

class AuthResponse(BaseModel):
    token: str
    id: str
    email: str
    username: str
    roles: List[str]

AuthResult = Union[AuthResponse, ErrorResponse]

class LLM(BaseModel):
    id: str
    name: str
    type: str
    description: str
    createdAt: str

class LLMsResponse(BaseModel):
    llms: List[LLM]

LLMsResult = Union[LLMsResponse, ErrorResponse]

class ConversationRequest(BaseModel):
    conversationId: str
    llmId: str
    query: str

class NewConversationResponse(BaseModel):
    conversationId: str
    title: str

class ChatMessage(BaseModel):
    messageId: str
    sender: str
    senderType: str
    content: str
    timestamp: str

class Conversation(BaseModel):
    conversationId: str
    title: str
    messages: List[ChatMessage] | None = None
    createdAt: str
    updatedAt: str

class ConversationsResponse(BaseModel):
    conversations: List[Conversation]

NewConversationResult = Union[NewConversationResponse, ErrorResponse]
ConversationResult = Union[Conversation, ErrorResponse]
ConversationsResult = Union[ConversationsResponse, ErrorResponse]

class User(BaseModel):
    id: str
    username: str
    email: str
    roles: List[str]
    createdAt: Optional[str] = None

class UsersResponse(BaseModel):
    users: List[User]

UserResult = Union[User, ErrorResponse]
UsersResult = Union[UsersResponse, ErrorResponse]

class GenericActionResponse(BaseModel):
    message: str

GenericActionResult = Union[GenericActionResponse, ErrorResponse]

class KnowledgeBase(BaseModel):
    id: str
    title: str
    content: str
    createdAt: str

class KnowledgeBasesResponse(BaseModel):
    knowledgeBases: List[KnowledgeBase]

KnowledgeBasesResult = Union[KnowledgeBasesResponse, ErrorResponse]
KnowledgeBaseResult = Union[KnowledgeBase, ErrorResponse]
