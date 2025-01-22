import json
from fasthtml.components import Div, H1, A
from src.components.layout.sidebar import Sidebar
from src.components.layout.chat_history_settings import ChatHistorySettings
from src.components.layout.connection_settings import ConnectionSettings
from src.components.layout.knowledge_base_settings import KnowledgeBaseSettings
from src.components.layout.users_settings import UsersSettings
from fastapi import Request
from lucide_fasthtml import Lucide
from src.components.layout.users_settings import UsersSettings
from src.components.common.message_card import MessageCard

def BackButton():
    return Div(
        A(
            Lucide("arrow-left", cls="w-6 h-6 text-black dark:text-white"),
            href="/",
            cls="hover:opacity-80 flex items-center bg-white dark:bg-gray-800 rounded-full p-1 shadow-md hover:shadow-lg"
        ),
        H1(
            "Settings",
            cls="text-3xl font-normal text-black dark:text-white ml-4"
        ),
        cls="flex items-center mb-8"
    )

def NavigationTab(section: str, is_admin: bool = False):
    return Div(
        A(
            Div(
                Lucide("cable", cls="w-4 h-4 text-black dark:text-white"),
                "Vespa Connection",
                cls=f"flex items-center gap-2 text-lg {'font-medium' if section == 'connection-settings' else 'font-light'} text-black dark:text-white mb-2 cursor-pointer hover:opacity-80",
            ),
            href="/settings/connection-settings",
        ) if is_admin else None,
        A(
            Div(
                Lucide("book-open-text", cls="w-4 h-4 text-black dark:text-white"),
                "Knowledge Base",
                cls=f"flex items-center gap-2 text-lg {'font-medium' if section == 'knowledge-base' else 'font-light'} text-black dark:text-white mb-2 cursor-pointer hover:opacity-80",
            ),
            href="/settings/knowledge-base",
        ),
        A(
            Div(
                Lucide("book-open-text", cls="w-4 h-4 text-black dark:text-white"),
                "Chat history",
                cls=f"flex items-center gap-2 text-lg {'font-medium' if section == 'chat-history' else 'font-light'} text-black dark:text-white mb-2 cursor-pointer hover:opacity-80",
            ),
            href="/settings/chat-history",
        ),
        A(
            Div(
                Lucide("users", cls="w-4 h-4 text-black dark:text-white"),
                "Users",
                cls=f"flex items-center gap-2 text-lg {'font-medium' if section == 'users' else 'font-light'} text-black dark:text-white mb-2 cursor-pointer hover:opacity-80",
            ),
            href="/settings/users",
            cls="block"
        ) if is_admin else None,
        cls="w-full max-w-2xl"
    )

def GetSettingsContent(section: str, is_admin: bool = False):
    return Div(
        BackButton(),
        NavigationTab(section, is_admin),
        cls="p-6"
    )

async def Settings(
    request: Request,
    section: str,
    content=None,
    success_messages: list[str] = [],
    error_messages: list[str] = [],
):
    user = request.session.get("user")
    user = json.loads(user)
    username = user.get("username")
    is_admin = "ADMIN".upper() in [role.upper() for role in user.get("roles", [])]

    if section == "users" and not is_admin:
        return Div("Access denied. Admin privileges required.", cls="p-6 text-red-500")
    if section == "connection-settings" and not is_admin:
        return Div("Access denied. Admin privileges required.", cls="p-6 text-red-500")

    if section == "chat-history" and content is None:
        content = ChatHistorySettings()
    elif section == "connection-settings" and content is None:
        content = ConnectionSettings()
    elif section == "knowledge-base" and content is None:
        content = KnowledgeBaseSettings()
    elif section == "users" and content is None:
        content = UsersSettings()
    else:
        content = content or Div("Select a valid option.", cls="p-6 text-gray-500")

    settings_content = GetSettingsContent(section, is_admin)

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

    return Div(
        notifications_container,
        Div(
            Sidebar(username=username, content=settings_content, is_admin=is_admin),
            Div(content, cls="ml-80 p-6 flex-1"),
            id="settings-page"
        )
    )
