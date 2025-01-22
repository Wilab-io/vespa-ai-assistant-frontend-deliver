from typing import List
from fasthtml.components import Div, H1, A
from src.services.api.types import Conversation

def ChatHistory(conversations: List[Conversation] = None):
    items = []
    if conversations is not None:
        items = [
            {
                "id": conv.conversationId,
                "title": conv.title,
            }
            for conv in sorted(conversations, key=lambda x: x.updatedAt, reverse=True)
        ]

    return Div(
            Div(
                H1(
                    "Recent Chats",
                    cls="text-xl font-normal text-black dark:text-white px-4"
                ),
                cls="flex items-center justify-between mb-4"
            ),
            Div(
                "No recent chats" if not items else "",
                cls="px-4 py-2 text-sm text-gray-500 dark:text-gray-400"
            ) if not items else None,
            *[
                A(
                    item.get("title", "New Chat"),
                    href=f"/conversation/{item.get('id')}",
                    cls="block px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-800 rounded-lg truncate"
                ) for item in items
            ],
            cls="space-y-1 w-full"
        )
