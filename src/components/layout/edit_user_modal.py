from fasthtml.components import Div, Label, Form, Button, Input
from typing import Optional, Dict
from lucide_fasthtml import Lucide
from src.components.common.action_buttons import SaveButton, CancelButton
from src.components.common.text_input import TextInput
from src.components.common.password_input import PasswordInput

def FormField(label: str, input_component, required: bool = False):
    """Helper component for form fields with consistent styling"""
    return Div(
        Label(
            label,
            Div("*", cls="text-red-500 inline-block ml-1") if required else None,
            cls="block text-sm font-medium text-gray-600 dark:text-gray-300 mb-1"
        ),
        input_component,
        cls="mb-6"
    )

def EditUserModal(user: Optional[Dict] = None, current_user_id: str = None):
    """Modal component for editing user information"""
    is_new_user = user is None
    action = "/api/users/new" if is_new_user else f"/api/users/edit/{user['id'] if user else ''}"

    return Div(
        Div(
            cls="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm transition-opacity modal-backdrop",
            **{"hx-on:click": "closeModal()"}
        ),
        Div(
            Div(
                Div(
                    Form(
                        Div(
                            Div(
                                "Add New User" if is_new_user else "Edit User",
                                cls="text-2xl font-semibold text-gray-800 dark:text-white"
                            ),
                            Button(
                                Lucide("x", cls="h-5 w-5"),
                                type="button",
                                cls="text-gray-400 hover:text-gray-500 dark:text-gray-300 dark:hover:text-gray-200 transition-colors duration-200",
                                **{"hx-on:click": "closeModal()"}
                            ),
                            cls="flex items-center justify-between mb-6"
                        ),
                        Div(
                            FormField(
                                "Username",
                                TextInput(
                                    type="text",
                                    name="username",
                                    value="" if is_new_user else user["username"],
                                    autofocus=True if is_new_user else False,
                                    required=True,
                                    autocomplete="username",
                                    pattern="[^\s]+",
                                    title="Username cannot contain spaces"
                                ),
                                required=True
                            ),
                            FormField(
                                "Email",
                                TextInput(
                                    type="email",
                                    name="email",
                                    value="" if is_new_user else user["email"],
                                    required=True,
                                    autocomplete="email"
                                ),
                                required=True
                            ),
                            PasswordInput(
                                name="password",
                                label="Password",
                                required=is_new_user,
                                placeholder="Leave blank to keep current password" if not is_new_user else "Enter password",
                                autofocus=False if is_new_user else True
                            ),
                            PasswordInput(
                                name="password_confirm",
                                label="Confirm Password",
                                required=is_new_user,
                                placeholder="Confirm your password"
                            ),
                            Div(
                                Label(
                                    Input(
                                        type="checkbox",
                                        name="is_admin",
                                        checked=not is_new_user and user and "ADMIN" in [role.upper() for role in user["roles"]],
                                        disabled=not is_new_user and user and current_user_id and user.get("id") == current_user_id,
                                        cls="h-5 w-5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 mr-3 dark:border-gray-600 dark:bg-gray-700"
                                    ),
                                    "Administrator privileges",
                                    cls="inline-flex items-center text-sm font-medium text-gray-600 dark:text-gray-300 cursor-pointer hover:text-gray-800 dark:hover:text-gray-100 transition-colors duration-200"
                                ),
                                cls="mb-8"
                            ),
                            cls="space-y-4"
                        ),
                        Div(
                            CancelButton(
                                type="button",
                                **{"hx-on:click": "closeModal()"}
                            ),
                            SaveButton(),
                            cls="flex justify-end gap-3 pt-6 border-t border-gray-200 dark:border-gray-700"
                        ),
                        cls="bg-white dark:bg-gray-800 p-6 sm:p-8",
                        **{
                            "hx-post": action,
                            "hx-target": "#settings-page",
                            "hx-swap": "innerHTML",
                            "hx-validate": "true",
                            "hx-on::before-request": "return validatePasswordsAndSubmit(this);"
                        }
                    ),
                    cls="relative transform overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-2xl transition-all sm:w-full sm:max-w-lg",
                    onclick="event.stopPropagation()"
                ),
                cls="flex min-h-full items-center justify-center p-4"
            ),
            cls="fixed inset-0 z-10 overflow-y-auto"
        ),
        cls="relative z-10",
        role="dialog",
        aria_modal="true"
    )
