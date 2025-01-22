from fasthtml.components import Div, H1, P, Form
from src.components.common.button_primary import ButtonPrimary
from src.components.common.text_input import TextInput
from components.layout.header import Header

def LoginWindow(error_message=None):
    return Div(
        Header(theme_toggle=True),
        Div(
            H1(
                "Account login",
                cls="text-4xl font-bold mb-2"
            ),
            P(
                "Welcome! Enter your credentials to use this platform",
                cls="text-gray-600 dark:text-gray-400 mb-8"
            ),
            Form(
                TextInput(
                    type="text",
                    placeholder="Username",
                    name="username",
                    cls="mb-4"
                ),
                TextInput(
                    type="password",
                    placeholder="Password",
                    name="password",
                    cls="mb-6"
                ),
                P(
                    error_message,
                    cls="text-destructive text-sm mb-4 text-center font-medium"
                ) if error_message and error_message != "None" else None,
                ButtonPrimary(
                    "Login",
                    type="submit"
                ),
                cls="bg-white dark:bg-gray-900 p-8 rounded-[10px] shadow-md w-full max-w-md border border-gray-200 dark:border-gray-700",
                hx_post="/api/login",
                hx_target="#login-form",
                hx_swap="outerHTML",
                hx_trigger="submit",
                hx_indicator="#login-form",
                hx_redirect="/"
            ),
            cls="flex flex-col items-center justify-center h-[calc(100vh-55px)] w-full max-w-screen-xl mx-auto px-4"
        ),
        cls="w-full bg-gray-50 dark:bg-gray-950 min-h-0",
        id="login-form"
    )
