from fasthtml.components import Div, Label, Button
from lucide_fasthtml import Lucide
from src.components.common.text_input import TextInput

def PasswordInput(name: str, label: str, required: bool = False, placeholder: str = "", value: str = "", autofocus: bool = False):
    """Password input component with show/hide toggle"""
    return Div(
        Label(
            label,
            Div("*", cls="text-red-500 inline-block ml-1") if required else None,
            cls="block text-sm font-medium text-gray-600 dark:text-gray-300 mb-1"
        ),
        Div(
            TextInput(
                type="password",
                name=name,
                value=value,
                required=required,
                placeholder=placeholder,
                cls="w-full p-4 border rounded-[10px] focus:outline-none focus:border-black dark:bg-gray-800 dark:border-gray-700 dark:text-white pr-12",
                autofocus=autofocus,
                autocomplete="new-password"
            ),
            Button(
                Div(
                    Lucide("eye", cls="h-4 w-4"),
                    cls="text-gray-500 hover:text-indigo-500 dark:text-gray-400 dark:hover:text-indigo-400 transition-colors duration-200"
                ),
                type="button",
                cls="absolute right-4 top-1/2 transform -translate-y-1/2 hover:opacity-80",
                **{
                    "hx-on:mousedown": f"togglePasswordVisibility('{name}', true)",
                    "hx-on:mouseup": f"togglePasswordVisibility('{name}', false)",
                    "hx-on:mouseleave": f"togglePasswordVisibility('{name}', false)"
                }
            ),
            cls="relative"
        ),
        cls="mb-6"
    )
