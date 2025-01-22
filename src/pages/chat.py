import json
from fasthtml.components import Div
from services.api.types import Conversation
from src.components.layout.search_bar import SearchBar
from src.components.layout.llm_selector import LLMSelector
from src.components.layout.sidebar import Sidebar
from src.components.common.message_card import MessageCard

def Chat(
        user: str = None,
        llm_options=None,
        content=None,
        conversation: Conversation = None,
        success_messages: list[str] = [],
        error_messages: list[str] = []
):
    notifications_container = None
    if error_messages or success_messages:
        notifications = []
        for msg in error_messages or []:
            notifications.append(MessageCard(message=msg, message_type="error"))
        for msg in success_messages or []:
            notifications.append(MessageCard(message=msg, message_type="success"))

        notifications_container = Div(
            *notifications,
            cls="fixed top-0 right-0 z-50 flex flex-col gap-4 p-4"
        )

    user = json.loads(user)
    username = user.get("username")
    is_admin = "ADMIN".upper() in [role.upper() for role in user.get("roles", [])]

    return Div(
        notifications_container,
        Div(
            Sidebar(username=username, content=content, is_admin=is_admin, new_chat_button=True),
            Div(
                LLMSelector(llm_options) if llm_options else None,
                cls="fixed top-0 left-80 p-4 z-10",
            ),
            Div(
                id="chat-messages",
                cls="fixed top-16 bottom-[90px] left-80 right-0 overflow-y-auto p-5",
                data_conversation=conversation.model_dump_json() if conversation and conversation.messages else None
            ),
            Div(
                cls="fixed bottom-[90px] left-80 right-0 h-6 bg-gradient-to-t from-white from-50% dark:from-gray-900 to-transparent pointer-events-none z-[5]"
            ),
            Div(
                SearchBar(
                    hx_post=f"/api/chat{f'?conversation_id={conversation.conversationId}' if conversation else ''}",
                    hx_trigger="keyup[keyCode==13 && this.value.trim() !== '']",
                    hx_swap="none",
                    id="chat-input"
                ),
                cls="fixed bottom-0 left-80 right-0 p-5 flex justify-center z-10 bg-white dark:bg-gray-900"
            )
        )
    )
