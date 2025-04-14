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
                    cls="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800 rounded-[10px]"
                ),
                href=settings_href
            ),
            A(
                Div(
                    Lucide("log-out", cls="w-4 h-4 mr-2 dark:brightness-0 dark:invert"),
                    "Sign out",
                    cls="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800 rounded-[10px]"
                ),
                hx_post="/api/logout",
                href="#"
            ),
            cls="py-1",
        ),
        cls="absolute bottom-12 z-10 w-full rounded-[10px] bg-white dark:bg-gray-700 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none",
    )

def Sidebar(username=None, content=None, is_admin=False, new_chat_button=False):
    user_display = (
        Div(
            Div(
                Div(
                    Lucide("circle-user-round", cls="w-6 h-6 dark:brightness-0 dark:invert"),
                    Span(
                        username,
                        cls="text-base text-black dark:text-white font-medium ml-2"
                    ),
                    cls="flex items-center"
                ),
                Div(
                    Lucide("chevron-down", cls="w-5 h-5 dark:brightness-0 dark:invert hidden", id="chevron-down"),
                    Lucide("chevron-up", cls="w-5 h-5 dark:brightness-0 dark:invert", id="chevron-up"),
                    cls="flex items-center"
                ),
                cls="flex items-center justify-between w-full cursor-pointer hover:opacity-80 px-4 py-2",
                **{"_": "on click toggle .hidden on #user-menu toggle .hidden on #chevron-up toggle .hidden on #chevron-down"}
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
            Div(
                A(Logo(), href="/"),
                Div(
                    ThemeToggle(),
                    A(
                        Lucide("message-square-plus", cls="w-5 h-5 dark:brightness-0 dark:invert"),
                        href="/",
                        cls="hover:opacity-80 ml-2"
                    ),
                    cls="flex items-center gap-2"
                ),
                cls="h-full w-full flex items-center justify-between gap-2 px-4"
            ),
            cls="bg-white dark:bg-gray-800 rounded-[10px] mx-4 mt-4 shadow-md h-[70px] ring-1 ring-black ring-opacity-5"
        ),
        Div(
            content,
            cls="flex-1 overflow-y-auto px-4 py-2"
        ) if content else None,
        Div(
            Div(
                user_display,
                cls="bg-white dark:bg-gray-800 rounded-[10px] shadow-md ring-1 ring-black ring-opacity-5"
            ),
            cls="absolute bottom-0 left-0 w-full p-4"
        ),
        cls="w-80 h-screen bg-[#F3F3F3] dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 fixed left-0 top-0 flex flex-col"
    )
