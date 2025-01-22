from fasthtml.components import H2 as FastH2

def SettingsHeading(text: str):
    return FastH2(
        text,
        cls="text-2xl font-medium text-gray-900 dark:text-white mb-6"
    ) 