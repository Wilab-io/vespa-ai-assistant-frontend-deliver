from fasthtml.components import Div, Label, Form, Button, Input, Textarea
from src.components.common.text_input import TextInput
from typing import Optional, Dict
from lucide_fasthtml import Lucide
from src.components.common.action_buttons import SaveButton, CancelButton

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

def KnowledgeBaseModal(kb: Optional[Dict] = None):
    is_new_kb = kb is None
    action = "/api/knowledge-base/new" if is_new_kb else f"/api/knowledge-base/edit/{kb['id'] if kb else ''}"
    
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
                                "Title",
                                TextInput(
                                    type="text",
                                    name="title",
                                    value="" if is_new_kb else kb["title"],
                                    autofocus=True if is_new_kb else False,
                                    required=True
                                ),
                                required=True
                            ),
                            FormField(
                                "Content",
                                Textarea(
                                    "" if is_new_kb else kb["content"],
                                    name="content",
                                    required=True,
                                    rows=6,
                                    cls="block p-4 w-full border rounded-[10px] focus:outline-none focus:border-black dark:bg-gray-800 dark:border-gray-700"
                                ),
                                required=True
                            ),
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
                        }
                    ),
                    cls="relative transform overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-2xl transition-all sm:w-full sm:max-w-2xl",  # Increased max-width
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