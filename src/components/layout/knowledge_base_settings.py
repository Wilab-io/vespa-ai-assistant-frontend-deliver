from fasthtml.components import Div, Form, Input, Button
from components.layout.settings_table import SettingsTable
from src.components.common.action_buttons import DeleteButton, EditButton, AddButton
from datetime import datetime

def format_timestamp(timestamp_str: str) -> str:
    """Convert ISO timestamp to a more readable format"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return timestamp_str

def KnowledgeBaseSettings(knowledge_bases=None):

    if knowledge_bases is None:
        knowledge_bases = []

    sorted_knowledge_bases = sorted(knowledge_bases, 
        key=lambda kb: ( 
            kb.title.lower() 
        )
    )

    def create_edit_button(kb_id: str):
        return EditButton(
            item_id=kb_id,
            endpoint=f"/settings/knowledge-base/edit"
        )

    def create_delete_button(kb_id: str):
        return DeleteButton(
            item_id=kb_id,
            endpoint="/api/knowledge-base",
            confirm_message="Are you sure you want to delete this knowledge base? This cannot be undone."
        )

    items = [
        {
            "id": kb.id,
            "col1": kb.title,
            "col2": format_timestamp(kb.createdAt),
        }
        for kb in sorted_knowledge_bases
    ]

    header_actions = [
        AddButton(
            button_text="Add new",
            endpoint="/settings/knowledge-base/new"
        ),
        Form(
            Input(
                type="file",
                name="csv_file",
                accept=".csv",
                cls="hidden",
                id="bulk-upload-input",
                **{
                    "hx-post": "/api/knowledge-base/bulk",
                    "hx-target": "#settings-page",
                    "hx-swap": "innerHTML",
                    "hx-encoding": "multipart/form-data",
                    "_": "on change if files.length > 0 then trigger submit"
                }
            ),
            Button(
                "Add bulk",
                type="button",
                cls="flex items-center px-4 py-2 border border-gray-300 dark:text-white dark:border-gray-600 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800",
                **{"onclick": "document.getElementById('bulk-upload-input').click()"}
            )
        )
    ]

    return Div(
        SettingsTable(
            title="Knowledge Base Management",
            col1_name="Name",
            col2_name="Date Added",
            items=items,
            row_actions=[create_edit_button, create_delete_button],
            header_actions=header_actions
        ),
        Div(id="modal"),
        cls="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8"
    )
