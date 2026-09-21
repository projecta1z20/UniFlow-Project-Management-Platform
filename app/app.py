import reflex as rx

from app import models  # noqa: F401
from app.components.studio import auth, shell
from app.states.studio import StudioState


def index() -> rx.Component:
    return rx.cond(StudioState.signed_in, shell(), auth())


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            cross_origin="",
        ),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(
    index,
    route="/studio/[section]",
    title="UniFlow · Project Studio",
    on_load=StudioState.load,
)
app.add_page(
    index, route="/", title="UniFlow · Project Studio", on_load=StudioState.load
)
