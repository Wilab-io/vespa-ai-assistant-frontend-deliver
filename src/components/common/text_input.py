from fasthtml.components import Input

def TextInput(type="text", placeholder="", name="", cls="", **kwargs):
    base_cls = "w-full p-4 border rounded-[10px] focus:outline-none focus:border-black dark:bg-gray-800 dark:border-gray-700"
    full_cls = f"{base_cls} {cls}" if cls else base_cls

    return Input(
        type=type,
        placeholder=placeholder,
        name=name,
        cls=full_cls,
        **kwargs
    )
