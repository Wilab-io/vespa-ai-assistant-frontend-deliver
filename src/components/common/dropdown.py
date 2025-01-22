from shad4fast import Select, SelectItem, SelectContent, SelectTrigger, SelectValue

def Dropdown(options, name=None, id=None, placeholder=None):
    current_value = next((text for _, text, checked in options if checked), None)

    return Select(
        SelectTrigger(
            SelectValue(placeholder=current_value or placeholder),
            cls="w-[250px]"
        ),
        SelectContent(
            SelectItem(text, value=value, checked=checked) for value, text, checked in options
        ),
        standard=True,
        id=id,
        name=name,
        cls="[&>.select-trigger]:w-full"
    )
