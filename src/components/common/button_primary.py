from fasthtml.components import Button

def ButtonPrimary(text, type="button", **kwargs):
    return Button(
        text,
        type=type,
        cls="w-full p-4 bg-black text-white rounded-[10px] hover:bg-gray-800 transition-colors",
        **kwargs
    )
