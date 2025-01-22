from fasthtml.components import Button
from lucide_fasthtml import Lucide
from typing import Optional

def BaseButton(*content, cls="", variant="ghost", size="sm", **attributes):
    base_classes = "text-black hover:text-red-600 dark:text-white dark:hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-full"
    return Button(
        *content,
        variant=variant,
        size=size,
        cls=f"{base_classes} {cls}",
        **attributes
    )

def DeleteButton(item_id: str, endpoint: str, confirm_message: Optional[str] = None):
    return BaseButton(
        Lucide("trash-2", cls="h-4 w-4"),
        cls="p-2",
        **{
            "data-item-id": item_id,
            "hx-delete": f"{endpoint}/{item_id}",
            "hx-target": "#settings-page",
            "hx-swap": "innerHTML",
            "hx-confirm": confirm_message or "Are you sure you want to delete this item?",
        }
    )

def DeleteAllButton(endpoint: str, confirm_message: Optional[str] = None, button_text: str = "Delete All"):
    return BaseButton(
        button_text,
        Lucide("trash-2", cls="h-4 w-4 ml-2"),
        variant="outline",
        size="sm",
        cls="flex items-center px-4 py-2 border border-gray-300 hover:border-red-200 dark:border-gray-600 dark:hover:border-red-600",
        **{
            "hx-delete": f"{endpoint}/delete/all",
            "hx-target": "#settings-page",
            "hx-swap": "innerHTML",
            "hx-confirm": confirm_message or "Are you sure you want to delete all items? This cannot be undone.",
        }
    )

def EditButton(item_id: str, endpoint: str, **attributes):
    return Button(
        Lucide("pencil", cls="h-4 w-4"),
        cls="p-2 hover:bg-gray-100 hover:text-gray-800 dark:hover:bg-gray-800 dark:hover:text-white rounded-full",
        **{
            "hx-get": f"{endpoint}/{item_id}",
            "hx-target": "#modal",
            "hx-trigger": "click",
            "data-modal-open": "true"
        },
        **attributes
    )

def AddButton(button_text: str, endpoint: str, **attributes):
    return Button(
        button_text,
        cls="flex items-center px-4 py-2 border border-gray-300 dark:text-white dark:border-gray-600 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800",
        **{
            "hx-get": endpoint,
            "hx-target": "#modal",
            "hx-trigger": "click",
            "data-modal-open": "true"
        },
        **attributes
    )


def ButtonSecondary(text, type="button", cls="", **kwargs):
    base_cls = "mt-6 px-6 py-2 rounded-[10px] hover:opacity-80 w-24 text-center"
    full_cls = f"{base_cls} {cls}" if cls else base_cls

    return Button(
        text,
        type=type,
        cls=full_cls,
        **kwargs
    )

def CancelButton(type="reset", **kwargs):
    return ButtonSecondary(
        "Cancel",
        type=type,
        cls="bg-white text-black border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-white dark:border-gray-600 dark:hover:bg-gray-700 mr-2",
        **kwargs
    )

def SaveButton():
    return ButtonSecondary(
        "Save",
        type="submit",
        cls="bg-black text-white hover:bg-gray-800 dark:bg-white dark:text-black dark:hover:bg-gray-100"
    )
