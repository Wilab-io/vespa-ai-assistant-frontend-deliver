from fasthtml.components import Div, Label, Form
from src.components.common.heading import SettingsHeading
from src.components.common.text_input import TextInput
from src.components.common.action_buttons import CancelButton, SaveButton

def ConnectionSettings(endpoint_value="", gemini_api_key_value=""):
    return Div(
        Div(
            SettingsHeading("Connection Settings"),
            Form(
                Div(
                    Label(
                        "Wilab Agent connection URL",
                        cls="block text-base font-medium text-gray-700 dark:text-gray-300 mb-2"
                    ),
                    TextInput(
                        type="text",
                        name="endpoint",
                        placeholder="Enter Wilab Agent connection URL",
                        value=endpoint_value,
                        autofocus=not endpoint_value,
                        id="endpoint-input"
                    ),
                    Label(
                        "Gemini API Key",
                        cls="block text-base font-medium text-gray-700 dark:text-gray-300 mb-2 mt-4"
                    ),
                    TextInput(
                        type="text",
                        name="gemini_api_key",
                        placeholder="Enter Gemini API Key",
                        id="gemini-api-key",
                        value=gemini_api_key_value
                    ),
                    Div(
                        CancelButton(),
                        SaveButton("connection-settings-save-button"),
                        cls="flex justify-end mt-6 gap-2"
                    ),
                    cls="max-w-6xl"
                ),
                hx_post="/api/config/connection-endpoint",
                hx_target="#settings-page",
                hx_swap="outerHTML"
            ),
            cls="w-full p-6"
        ),
        cls="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8"
    )
