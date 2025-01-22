from fasthtml.components import Div
import uuid

def MessageCard(message: str = None, message_type: str = None):
    if not message:
        return None

    bg_class = 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100' if message_type == 'error' else 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100'

    return Div(
        message,
        cls=f"p-4 rounded-lg shadow-lg transition-opacity duration-300 opacity-0 {bg_class}",
        id=f"notification-card-{uuid.uuid4()}",
        data_message_type=message_type
    )
