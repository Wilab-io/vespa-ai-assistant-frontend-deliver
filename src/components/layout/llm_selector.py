from fasthtml.components import Div
from src.components.common.dropdown import Dropdown

def LLMSelector(llm_options):
    return Div(
        Dropdown(
            options=llm_options,
            name="llm_model",
            id="llm_selector",
            placeholder="Choose an LLM model",
        ),
        cls="w-32"
    )
