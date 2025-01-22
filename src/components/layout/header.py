
from fasthtml.components import Button, Div, Img, A
from lucide_fasthtml import Lucide

def ThemeToggle(variant="ghost", cls=None, **kwargs):
    return Button(
        Lucide("sun", cls="dark:flex hidden"),
        Lucide("moon", cls="dark:hidden"),
        variant=variant,
        size="icon",
        cls=f"theme-toggle {cls}",
        **kwargs,
    )

def Logo():
    return Div(
        Img(
            src="https://assets.vespa.ai/logos/vespa-logo-black.svg",
            alt="Vespa Logo",
            cls="h-full dark:hidden",
        ),
        Img(
            src="https://assets.vespa.ai/logos/vespa-logo-white.svg",
            alt="Vespa Logo Dark Mode",
            cls="h-full hidden dark:block",
        ),
        cls="h-[27px]",
    )

def Header(theme_toggle=False):
    return Div(
        A(Logo(), href="/"),
        ThemeToggle() if theme_toggle else None,
        cls="min-h-[55px] h-[55px] w-full flex items-center justify-between px-4",
    )
