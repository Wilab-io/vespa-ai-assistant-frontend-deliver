
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
            src="/static/img/wilab-logo.png",
            alt="Wilab logo",
            cls="h-full dark:hidden",
        ),
        Img(
            src="/static/img/wilab-logo-white.png",
            alt="Wilab logo dark mode",
            cls="h-full hidden dark:block",
        ),
        cls="h-[40px]",
    )

def Header(theme_toggle=False):
    return Div(
        A(Logo(), href="/"),
        ThemeToggle() if theme_toggle else None,
        cls="min-h-[55px] h-[55px] w-full flex items-center justify-between px-4",
    )
