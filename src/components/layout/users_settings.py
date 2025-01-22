from src.components.layout.settings_table import SettingsTable
from src.components.common.action_buttons import DeleteButton, EditButton, AddButton
from components.layout.edit_user_modal import EditUserModal
from typing import List
from src.services.api.types import User
from fasthtml.components import Div

def UsersSettings(users: List[User] = []):
    sorted_users = sorted(users,
        key=lambda u: (
            "0" if any(role.upper() == "ADMIN" for role in u.roles) else "1",
            u.username.lower()
        )
    )

    table_items = [
        {
            "id": user.id,
            "col1": user.username,
            "col2": "••••••••",
        }
        for user in sorted_users
    ]

    def create_edit_button(user_id: str):
        return EditButton(
            item_id=user_id,
            endpoint=f"/settings/users/edit"
        )

    def create_delete_button(user_id: str):
        user = next((u for u in users if u.id == user_id), None)
        if user and any(role.upper() == "ADMIN" for role in user.roles):
            return None

        return DeleteButton(
            item_id=user_id,
            endpoint="/api/users",
            confirm_message="Are you sure you want to delete this user? This cannot be undone."
        )

    header_actions = [
        AddButton(
            button_text="Add new",
            endpoint="/settings/users/new"
        )
    ]

    return Div(
        SettingsTable(
            title="Users Management",
            col1_name="Username",
            col2_name="Password",
            items=table_items,
            row_actions=[create_edit_button, create_delete_button],
            header_actions=header_actions
        ),
        Div(id="modal"),
        cls="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8"
    )
