from fasthtml.components import Div
from components.layout.settings_table import SettingsTable
from src.components.common.action_buttons import DeleteButton, DeleteAllButton
from datetime import datetime

def format_timestamp(timestamp_str: str) -> str:
    """Convert ISO timestamp to a more readable format"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return timestamp_str

def ChatHistorySettings(conversations=None):
    if conversations is None:
        conversations = []

    def create_delete_button(item_id: str):
        return DeleteButton(
            item_id=item_id,
            endpoint="/api/conversations",
            confirm_message="Are you sure you want to delete this conversation?"
        )

    items = [
        {
            "id": conv.conversationId,
            "col1": conv.title,
            "col2": format_timestamp(conv.createdAt),
        }
        for conv in conversations
    ]

    header_actions = [
        DeleteAllButton(
            endpoint="/api/conversations",
            confirm_message="Are you sure you want to delete all conversations? This cannot be undone.",
            button_text="Delete All"
        )
    ] if items else []

    return Div(
        SettingsTable(
            title="Chat History Management",
            col1_name="Name",
            col2_name="Date Added",
            items=items,
            row_actions=[create_delete_button],
            header_actions=header_actions
        ),
        cls="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8"
    )
