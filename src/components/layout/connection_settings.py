from fasthtml.components import Div, Label, Form
from src.components.common.heading import SettingsHeading
from src.components.common.text_input import TextInput
from src.components.common.action_buttons import CancelButton, SaveButton

def ConnectionSettings(endpoint_value=""):
    return Div(
        Div(
            SettingsHeading("Connection Settings"),
            Form(
                Div(
                    Label(
                        "Assistant Webservice Endpoint",
                        cls="block text-base font-medium text-gray-700 dark:text-gray-300 mb-2"
                    ),
                    TextInput(
                        type="text",
                        name="endpoint",
                        placeholder="Enter Vespa connection URL",
                        value=endpoint_value,
                        autofocus=not endpoint_value,
                        id="endpoint-input"
                    ),
                    Div(
                        CancelButton(),
                        SaveButton(),
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
