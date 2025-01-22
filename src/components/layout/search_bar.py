from src.components.common.text_input import TextInput

def SearchBar(**kwargs):
    return TextInput(
        type="text",
        name="text",
        placeholder="Ask me anything...",
        cls="bg-[#F3F3F3] dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700",
        **kwargs
    )
