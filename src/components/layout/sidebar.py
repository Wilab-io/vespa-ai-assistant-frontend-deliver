from fasthtml.components import Div, A, Span
from lucide_fasthtml import Lucide
from components.layout.header import ThemeToggle, Logo
import json

def UserMenu(is_admin=None):
    settings_href = "/settings/connection-settings" if is_admin else "/settings/knowledge-base"

    return Div(
        Div(
            A(
                Div(
                    Lucide("cog", cls="w-4 h-4 mr-2 dark:brightness-0 dark:invert"),
                    "Settings",
                    cls="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800 rounded-[16px]"
                ),
                href=settings_href
            ),
            A(
                Div(
                    Lucide("log-out", cls="w-4 h-4 mr-2 dark:brightness-0 dark:invert"),
                    "Sign out",
                    cls="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800 rounded-[16px]"
                ),
                hx_post="/api/logout",
                href="#"
            ),
            cls="py-1",
        ),
        cls="absolute bottom-12 left-4 right-4 z-10 rounded-[16px] bg-white dark:bg-gray-700 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none",
    )

def Sidebar(username=None, content=None, is_admin=False, new_chat_button=False):
    user_display = (
        Div(
            Div(
                Lucide("circle-user-round", cls="w-6 h-6 dark:brightness-0 dark:invert"),
                Span(
                    username,
                    cls="text-base text-black dark:text-white font-medium ml-2"
                ),
                cls="flex items-center cursor-pointer hover:opacity-80 px-4 py-2",
                **{"_": "on click toggle .hidden on #user-menu"}
            ),
            Div(
                UserMenu(is_admin),
                id="user-menu",
                cls="hidden transition-all duration-200 ease-in-out"
            ),
            cls="relative"
        )
        if username else
        A(
            "Login",
            href="/login",
            cls="text-base text-black dark:text-white font-medium hover:opacity-80 px-4 py-2"
        )
    )

    return Div(
        Div(
            A(Logo(), href="/"),
            ThemeToggle(),
            cls="min-h-[55px] h-[55px] w-full flex items-center justify-between gap-2 px-4"
        ),
        A(
            Div(
                Lucide("pencil", cls="w-4 h-4 mr-2 dark:brightness-0 dark:invert"),
                "New chat",
                cls="hover:opacity-80 flex items-center bg-white dark:bg-gray-800 rounded-full px-3 py-2 mb-4 shadow-md hover:shadow-lg"
            ),
            href="/",
            cls="block mt-4 px-4 w-fit mx-4"
        ) if new_chat_button else None,
        Div(
            content,
            cls="flex-1 overflow-y-auto px-4 py-2"
        ) if content else None,
        Div(
            user_display,
            cls="absolute bottom-0 left-0 w-full p-4"
        ),
        cls="w-80 h-screen bg-[#F3F3F3] dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 fixed left-0 top-0 flex flex-col"
    )
