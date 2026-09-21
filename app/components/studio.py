import reflex as rx
import reflex_xy
from app.states.studio import StudioState as S


BUTTON = "inline-flex items-center justify-center gap-2 rounded-sm border border-[#183b48] bg-[#183b48] px-4 py-2.5 text-sm font-medium text-white transition hover:bg-[#245365] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600 disabled:opacity-40 disabled:cursor-not-allowed"
SECONDARY = "inline-flex items-center justify-center gap-2 rounded-sm border border-[#d7d6cc] bg-[#faf9f4] px-3 py-2 text-sm font-medium text-[#183b48] transition hover:bg-[#eeeee5] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600 disabled:opacity-40"
PANEL = "border border-[#d9d8ce] rounded-sm bg-[#faf9f4] p-5 md:p-6"
INPUT = "w-full rounded-sm border border-[#cccec6] bg-[#fffef9] px-3 py-2.5 text-sm text-[#162e3b] outline-hidden focus:border-teal-700 focus:ring-1 focus:ring-teal-700 disabled:opacity-50"


def hidden(name: str, value) -> rx.Component:
    return rx.el.input(type="hidden", name=name, value=value)


def field(
    label: str,
    name: str,
    default="",
    kind: str = "text",
    required: bool = False,
    placeholder: str = "",
) -> rx.Component:
    return rx.el.label(
        rx.el.span(
            label,
            class_name="block text-xs font-semibold text-[#41525a] mb-1.5",
        ),
        rx.el.input(
            name=name,
            type=kind,
            default_value=default,
            key=default,
            required=required,
            placeholder=placeholder,
            class_name=INPUT,
        ),
        class_name="block min-w-0",
    )


def area(
    label: str, name: str, default="", placeholder: str = ""
) -> rx.Component:
    return rx.el.label(
        rx.el.span(
            label,
            class_name="block text-xs font-semibold text-[#41525a] mb-1.5",
        ),
        rx.el.textarea(
            name=name,
            default_value=default,
            key=default,
            placeholder=placeholder,
            rows=3,
            class_name=INPUT,
        ),
        class_name="block",
    )


def select_field(
    label: str,
    name: str,
    options,
    value_key: str = "id",
    label_key: str = "name",
) -> rx.Component:
    return rx.el.label(
        rx.el.span(
            label,
            class_name="block text-xs font-semibold text-[#41525a] mb-1.5",
        ),
        rx.el.div(
            rx.el.select(
                rx.el.option("Select…", value="", disabled=True),
                rx.foreach(
                    options,
                    lambda item: rx.el.option(
                        item[label_key], value=item[value_key]
                    ),
                ),
                name=name,
                default_value="",
                required=True,
                class_name="appearance-none w-full rounded-sm border border-[#cccec6] bg-[#fffef9] pl-3 pr-8 py-2.5 text-sm text-[#162e3b] focus:ring-1 focus:ring-teal-700",
            ),
            rx.icon(
                "chevron-down",
                class_name="absolute right-3 top-3 h-4 w-4 pointer-events-none text-[#53656b]",
            ),
            class_name="relative",
        ),
        class_name="block min-w-0",
    )


def choice(label: str, name: str, options: list[str]) -> rx.Component:
    return rx.el.label(
        rx.el.span(
            label,
            class_name="block text-xs font-semibold text-[#41525a] mb-1.5",
        ),
        rx.el.div(
            rx.el.select(
                rx.foreach(
                    options,
                    lambda item: rx.el.option(
                        item.replace("_", " "), value=item
                    ),
                ),
                name=name,
                class_name="appearance-none w-full rounded-sm border border-[#cccec6] bg-[#fffef9] pl-3 pr-8 py-2.5 text-sm text-[#162e3b] focus:ring-1 focus:ring-teal-700",
            ),
            rx.icon(
                "chevron-down",
                class_name="absolute right-3 top-3 h-4 w-4 pointer-events-none text-[#53656b]",
            ),
            class_name="relative",
        ),
    )


def form(
    title: str, action: str, *children, submit: str = "Save"
) -> rx.Component:
    return rx.el.form(
        rx.el.h3(title, class_name="font-serif text-xl text-[#173747] mb-1"),
        hidden("action", action),
        *children,
        rx.el.button(
            submit,
            rx.icon("arrow-right", class_name="h-4 w-4"),
            type="submit",
            disabled=S.busy,
            class_name=BUTTON,
        ),
        on_submit=S.save,
        class_name="flex flex-col gap-4",
    )


def disclosure(title: str, *children) -> rx.Component:
    return rx.el.details(
        rx.el.summary(
            title,
            class_name="cursor-pointer font-medium text-sm text-[#183b48] py-3 focus-visible:outline-2 focus-visible:outline-teal-600",
        ),
        rx.el.div(*children, class_name="py-4"),
        class_name="border-t border-[#dbdcd2]",
    )


def empty(title: str, detail: str) -> rx.Component:
    return rx.el.div(
        rx.icon("notebook-pen", class_name="h-7 w-7 text-[#78928c] mb-3"),
        rx.el.h3(title, class_name="text-lg font-serif text-[#233f49]"),
        rx.el.p(
            detail,
            class_name="text-sm leading-relaxed text-[#697673] mt-2 max-w-lg",
        ),
        class_name="flex flex-col items-center justify-center text-center px-6 py-12 border border-dashed border-[#d1d5c8] bg-[#f5f5ec] rounded-sm w-full",
    )


def chip(label) -> rx.Component:
    return rx.el.span(
        label.replace("_", " "),
        class_name="inline-flex w-fit rounded-sm bg-[#e3ede6] px-2 py-1 text-[11px] font-medium tracking-wide text-[#32645d]",
    )


def ribbon() -> rx.Component:
    return rx.el.div(
        rx.foreach(
            [
                {
                    "n": "01",
                    "title": "Proposal",
                    "desc": "Define the opportunity",
                },
                {"n": "02", "title": "Review", "desc": "Shape & approve"},
                {
                    "n": "03",
                    "title": "Matching",
                    "desc": "Build the right team",
                },
                {
                    "n": "04",
                    "title": "Delivery",
                    "desc": "Learn through practice",
                },
                {
                    "n": "05",
                    "title": "Evaluation",
                    "desc": "Reflect & recognise",
                },
            ],
            lambda step: rx.el.div(
                rx.el.div(
                    rx.el.span(
                        step["n"],
                        class_name="text-[10px] text-[#64867c] font-semibold tracking-widest",
                    ),
                    rx.el.div(class_name="h-px flex-1 bg-[#c9d6c9]"),
                    class_name="flex gap-3 items-center mb-3",
                ),
                rx.el.p(
                    step["title"],
                    class_name="font-serif text-lg text-[#1e414a]",
                ),
                rx.el.p(
                    step["desc"],
                    class_name="hidden lg:block text-[11px] text-[#6d7d76] mt-1",
                ),
                class_name="min-w-[110px] flex-1",
            ),
        ),
        class_name="flex gap-5 overflow-x-auto border-y border-[#d4dbce] bg-[#edf0e5] px-5 py-5 md:px-7 w-full",
    )


def auth() -> rx.Component:
    return rx.el.main(
        rx.el.header(
            rx.el.div(
                rx.icon("library", class_name="h-6 w-6"),
                rx.el.span("UniFlow", class_name="font-serif text-2xl"),
                class_name="flex gap-3 items-center",
            ),
            rx.el.span(
                "THE UNIVERSITY PROJECT STUDIO",
                class_name="hidden sm:block text-[10px] tracking-[0.22em] text-[#b9c7c7]",
            ),
            class_name="flex justify-between items-center px-7 md:px-14 h-20 border-b border-white/15 bg-[#102d3c] text-[#faf8ed]",
        ),
        rx.el.div(
            rx.el.section(
                rx.el.p(
                    "IDEAS INTO IMPACT",
                    class_name="text-xs tracking-[0.24em] text-[#85b6a5] mb-8",
                ),
                rx.el.h1(
                    "A shared purpose.",
                    rx.el.br(),
                    "A clear path forward.",
                    class_name="font-serif text-5xl lg:text-6xl leading-[1.12] tracking-tight text-[#fffbea]",
                ),
                rx.el.p(
                    "Where students, faculty, and partners turn ambitious proposals into meaningful project work.",
                    class_name="text-base leading-7 text-[#becdcc] max-w-md mt-7",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.icon("compass", class_name="h-5 w-5 text-[#88b9a7]"),
                        rx.el.span(
                            "Find your project. Build your team.",
                            class_name="text-sm",
                        ),
                        class_name="flex gap-3 items-center",
                    ),
                    rx.el.div(
                        rx.icon("route", class_name="h-5 w-5 text-[#88b9a7]"),
                        rx.el.span(
                            "One connected journey, from idea to evaluation.",
                            class_name="text-sm",
                        ),
                        class_name="flex gap-3 items-center",
                    ),
                    class_name="flex flex-col gap-5 mt-12 border-t border-white/15 pt-7 text-[#d0dbd6]",
                ),
                rx.el.p(
                    "PURPOSEFUL COLLABORATION / THOUGHTFUL DELIVERY",
                    class_name="text-[9px] tracking-[0.16em] text-[#72908f] mt-16",
                ),
                class_name="bg-[#102d3c] px-7 md:px-14 py-12 lg:py-20",
            ),
            rx.el.section(
                rx.el.div(
                    rx.el.p(
                        "WELCOME TO YOUR STUDIO",
                        class_name="text-[10px] tracking-[0.2em] text-[#597971] font-semibold mb-4",
                    ),
                    rx.el.h2(
                        rx.cond(
                            S.registering, "Begin your journey", "Welcome back"
                        ),
                        class_name="font-serif text-4xl text-[#183b48] mb-3",
                    ),
                    rx.el.p(
                        rx.cond(
                            S.registering,
                            "Create your account to join the project community.",
                            "Sign in to pick up where you left off.",
                        ),
                        class_name="text-sm text-[#748078] mb-8",
                    ),
                    rx.el.form(
                        rx.cond(
                            S.registering,
                            field(
                                "Full name",
                                "name",
                                required=True,
                                placeholder="Your full name",
                            ),
                        ),
                        field(
                            "University or work email",
                            "email",
                            kind="email",
                            required=True,
                            placeholder="you@university.edu",
                        ),
                        field(
                            "Password",
                            "password",
                            kind="password",
                            required=True,
                            placeholder="At least 10 characters for a new account",
                        ),
                        rx.cond(
                            S.error != "",
                            rx.el.p(
                                S.error,
                                role="alert",
                                class_name="text-sm text-red-700 bg-red-50 border border-red-200 p-3",
                            ),
                        ),
                        rx.el.button(
                            rx.cond(
                                S.busy,
                                "Please wait…",
                                rx.cond(
                                    S.registering, "Create account", "Sign in"
                                ),
                            ),
                            rx.icon("arrow-right", class_name="h-4 w-4"),
                            type="submit",
                            disabled=S.busy,
                            class_name=BUTTON,
                        ),
                        on_submit=S.authenticate,
                        reset_on_submit=True,
                        class_name="flex flex-col gap-5",
                    ),
                    rx.el.div(
                        rx.el.span(
                            rx.cond(
                                S.registering,
                                "Already part of UniFlow?",
                                "New to the studio?",
                            ),
                            class_name="text-sm text-[#758078]",
                        ),
                        rx.el.button(
                            rx.cond(
                                S.registering, "Sign in", "Create an account"
                            ),
                            on_click=S.toggle_registration,
                            class_name="text-sm text-teal-800 font-semibold underline underline-offset-4 hover:text-teal-600",
                        ),
                        class_name="flex flex-wrap gap-2 mt-7",
                    ),
                    rx.el.p(
                        "Your role determines your workspace. New members join as students; the first account establishes the studio administrator.",
                        class_name="text-xs text-[#8a9085] leading-5 border-t border-[#deded2] mt-8 pt-6",
                    ),
                    class_name="w-full max-w-md",
                ),
                class_name="flex items-center justify-center px-7 md:px-14 py-12 bg-[#f8f7ef]",
            ),
            class_name="grid lg:grid-cols-2 min-h-[calc(100dvh-80px)]",
        ),
        class_name="font-['Inter'] bg-[#f8f7ef] min-h-dvh",
    )


def masthead() -> rx.Component:
    return rx.el.header(
        rx.el.a(
            rx.icon("library", class_name="h-5 w-5 text-[#8fb7a6]"),
            rx.el.span(
                "UniFlow", class_name="font-serif text-2xl text-[#fffbea]"
            ),
            href="/studio/dashboard",
            class_name="flex gap-3 items-center",
        ),
        rx.el.span(
            "UNIVERSITY PROJECT STUDIO",
            class_name="hidden md:block text-[10px] tracking-[0.22em] text-[#abc0ba]",
        ),
        rx.el.div(
            rx.el.a(
                rx.icon("bell", class_name="h-4 w-4"),
                rx.cond(
                    S.unread > 0,
                    rx.el.span(
                        S.unread,
                        class_name="text-[10px] rounded-full bg-[#9dbb9b] text-[#173747] px-1.5",
                    ),
                ),
                href="/studio/notifications",
                aria_label="Notifications",
                class_name="flex gap-1 items-center text-[#d6e1d6]",
            ),
            rx.el.span(
                S.name, class_name="hidden sm:block text-xs text-[#d6e1d6]"
            ),
            rx.el.button(
                rx.icon("log-out", class_name="h-4 w-4"),
                on_click=S.logout,
                aria_label="Sign out",
                title="Sign out",
                class_name="text-[#d6e1d6] hover:text-white p-2 focus-visible:outline-2 focus-visible:outline-teal-300",
            ),
            class_name="flex gap-4 items-center",
        ),
        class_name="h-16 shrink-0 px-5 md:px-7 flex justify-between items-center bg-[#112e3c] border-b border-[#2c4852] text-white",
    )


def navigation() -> rx.Component:
    return rx.el.aside(
        rx.el.div(
            rx.el.p(
                "STUDIO DIRECTORY",
                class_name="text-[9px] font-semibold tracking-[0.18em] text-[#809086]",
            ),
            rx.el.p(
                "Your workspace",
                class_name="text-sm text-[#304e51] font-serif mt-2",
            ),
            class_name="hidden md:block p-6 border-b border-[#dddfd1]",
        ),
        rx.el.nav(
            rx.foreach(
                S.nav,
                lambda item: rx.el.a(
                    rx.icon("chevron-right", class_name="h-3.5 w-3.5 shrink-0"),
                    rx.el.span(item["label"]),
                    href=f"/studio/{item['id']}",
                    class_name=rx.cond(
                        S.section_name == item["id"],
                        "flex shrink-0 gap-3 items-center px-3 py-3 text-xs font-semibold text-[#214f48] bg-[#dfe8dc] border-l-2 border-[#527a68]",
                        "flex shrink-0 gap-3 items-center px-3 py-3 text-xs text-[#63736e] hover:bg-[#e7ebdf] border-l-2 border-transparent",
                    ),
                ),
            ),
            class_name="flex md:flex-col gap-1 p-3 overflow-x-auto md:overflow-y-auto flex-1 min-h-0",
        ),
        rx.el.div(
            rx.icon("sprout", class_name="h-6 w-6 text-[#75957d] mb-3"),
            rx.el.p(
                "Good work grows",
                class_name="font-serif text-base text-[#496457]",
            ),
            rx.el.p(
                "with a little structure.",
                class_name="font-serif text-base text-[#496457]",
            ),
            rx.el.p(
                "UniFlow · Academic operations",
                class_name="text-[9px] text-[#8d998c] mt-4",
            ),
            class_name="hidden md:block border-t border-[#dddfd1] p-6",
        ),
        class_name="flex flex-col md:w-56 w-full shrink-0 bg-[#f0f1e7] md:border-r border-b md:border-b-0 border-[#d8ddce] min-h-0",
    )


def page_header(title: str, description: str, number: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                f"STUDIO / {number}",
                class_name="text-[9px] tracking-[0.2em] font-semibold text-[#778c7e] mb-3",
            ),
            rx.el.h1(
                title,
                class_name="font-serif text-3xl md:text-4xl text-[#193a48] tracking-tight",
            ),
            rx.el.p(
                description, class_name="text-sm text-[#798479] mt-2 leading-6"
            ),
        ),
        rx.el.button(
            rx.icon("refresh-cw", class_name="h-4 w-4"),
            "Refresh",
            on_click=S.load,
            class_name=SECONDARY,
        ),
        class_name="flex items-start justify-between gap-4 mb-7",
    )


def stat(label: str, value, icon: str, note: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                label, class_name="text-[11px] font-medium text-[#62786e]"
            ),
            rx.icon(icon, class_name="h-4 w-4 text-[#839886]"),
            class_name="flex gap-2 items-center justify-between",
        ),
        rx.el.p(value, class_name="font-serif text-4xl text-[#193c48] mt-4"),
        rx.el.p(note, class_name="text-[10px] text-[#899080] mt-2"),
        class_name="w-full border-b-2 border-[#c4d3c1] bg-[#f0f2e7] p-5",
    )


def project_card(p) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            chip(p["label"]),
            rx.el.span(
                p["team_size"],
                " students",
                class_name="text-[11px] text-[#78877b]",
            ),
            class_name="flex justify-between items-center gap-3",
        ),
        rx.el.button(
            p["title"],
            on_click=S.open_project(p["id"]),
            class_name="block text-left font-serif text-xl leading-7 text-[#234550] hover:text-teal-700 mt-4 focus-visible:outline-2 focus-visible:outline-teal-600",
        ),
        rx.el.p(
            p["summary"],
            class_name="text-sm text-[#778075] leading-6 line-clamp-2 mt-2",
        ),
        rx.el.p(
            p["skills"], class_name="text-[11px] text-[#648575] mt-4 min-h-4"
        ),
        rx.el.div(
            rx.el.span(p["sponsor"], class_name="text-xs text-[#8a8f81]"),
            rx.el.button(
                "Open project",
                rx.icon("arrow-up-right", class_name="h-3.5 w-3.5"),
                on_click=S.open_project(p["id"]),
                class_name="flex gap-1 items-center text-xs font-semibold text-[#376b60]",
            ),
            class_name="border-t border-[#e0e2d5] pt-4 mt-5 flex items-center justify-between gap-3",
        ),
        class_name="border border-[#d9dcd0] bg-[#faf9f3] p-5 rounded-sm h-full",
    )


def project_grid() -> rx.Component:
    return rx.cond(
        S.visible_projects.length() > 0,
        rx.el.div(
            rx.foreach(S.visible_projects, project_card),
            class_name="grid sm:grid-cols-2 xl:grid-cols-3 gap-4",
        ),
        empty(
            "A place for the next great idea",
            "Projects will appear here as proposals are created and approved. Use the project tools to start your first proposal.",
        ),
    )


def dashboard() -> rx.Component:
    return rx.el.div(
        page_header(
            "The studio, at a glance",
            "A connected view of ideas, teams, and the work ahead.",
            "01 — OVERVIEW",
        ),
        ribbon(),
        rx.cond(
            S.is_admin,
            rx.el.div(
                stat(
                    "Projects in the studio",
                    S.stats["projects"],
                    "folders",
                    "Across the project lifecycle",
                ),
                stat(
                    "Behind schedule",
                    S.stats["late"],
                    "clock-3",
                    "Projects with overdue milestones",
                ),
                stat(
                    "Missing submissions",
                    S.stats["missing"],
                    "file-clock",
                    "Student–milestone obligations",
                ),
                stat(
                    "Top-three choice",
                    S.stats["choice"],
                    "list-checks",
                    "Current team assignments",
                ),
                stat(
                    "Unstaffed projects",
                    S.stats["unstaffed"],
                    "users",
                    "Open work without a team",
                ),
                class_name="grid grid-cols-2 lg:grid-cols-5 gap-3 mt-7",
            ),
            rx.el.div(
                rx.el.h2(
                    f"Welcome, {S.name}",
                    class_name="font-serif text-2xl text-[#234450]",
                ),
                rx.el.p(
                    "Explore opportunities, keep your preferences up to date, and follow your project’s progress.",
                    class_name="text-sm text-[#738276] mt-2",
                ),
                class_name="py-7",
            ),
        ),
        rx.el.div(
            rx.el.section(
                rx.el.div(
                    rx.el.h2(
                        "From the project studio",
                        class_name="font-serif text-2xl text-[#24434c]",
                    ),
                    rx.el.a(
                        "View marketplace →",
                        href="/studio/marketplace",
                        class_name="text-xs text-teal-800 font-medium",
                    ),
                    class_name="flex justify-between items-center gap-4 mb-5",
                ),
                project_grid(),
                class_name="min-w-0 flex-1",
            ),
            rx.el.aside(
                rx.el.p(
                    "THE NEXT CHAPTER",
                    class_name="text-[9px] tracking-[0.2em] text-[#66836f] font-semibold",
                ),
                rx.el.h3(
                    "Make room for good work.",
                    class_name="font-serif text-2xl leading-8 text-[#234a4a] mt-4",
                ),
                rx.el.p(
                    "Every project starts with a clear opportunity. Every team grows with shared expectations.",
                    class_name="text-sm leading-6 text-[#73806d] mt-3",
                ),
                rx.el.div(
                    rx.icon(
                        "calendar-days", class_name="h-5 w-5 text-[#5e836b]"
                    ),
                    rx.el.div(
                        rx.el.p(
                            S.round_info["name"],
                            class_name="text-sm font-medium text-[#3c5c4b]",
                        ),
                        rx.el.p(
                            S.round_info["closes"],
                            class_name="text-xs text-[#778c74] mt-1",
                        ),
                    ),
                    class_name="flex gap-3 mt-7 pt-5 border-t border-[#d0d9c8]",
                ),
                rx.cond(
                    S.is_admin,
                    rx.el.a(
                        "Open assignment studio →",
                        href="/studio/assignments",
                        class_name="block text-xs text-teal-800 font-semibold mt-6",
                    ),
                    rx.el.a(
                        "Discover projects →",
                        href="/studio/marketplace",
                        class_name="block text-xs text-teal-800 font-semibold mt-6",
                    ),
                ),
                class_name="lg:w-64 shrink-0 bg-[#e9eede] border border-[#d6decc] p-6 rounded-sm",
            ),
            class_name="flex flex-col lg:flex-row gap-6 mt-9 items-start",
        ),
    )


def proposal_form(editing: bool = False) -> rx.Component:
    return form(
        rx.cond(editing, "Edit proposal", "Create a proposal"),
        "proposal",
        hidden("target", rx.cond(editing, S.selected["id"], "")),
        hidden("version", rx.cond(editing, S.selected["version"], "")),
        field(
            "Project title",
            "title",
            rx.cond(editing, S.selected["title"], ""),
            required=True,
        ),
        area("Summary", "summary", rx.cond(editing, S.selected["summary"], "")),
        area(
            "Project brief",
            "description",
            rx.cond(editing, S.selected["description"], ""),
        ),
        area(
            "Objectives · one per line",
            "objectives",
            rx.cond(editing, S.selected["objectives"], ""),
        ),
        field(
            "Skill tags · comma separated",
            "skills",
            rx.cond(editing, S.selected["skills"], ""),
            placeholder="research, python, product design",
        ),
        rx.el.div(
            field(
                "Minimum team size",
                "min",
                rx.cond(editing, S.selected["min"], "3"),
                "number",
                True,
            ),
            field(
                "Maximum team size",
                "max",
                rx.cond(editing, S.selected["max"], "5"),
                "number",
                True,
            ),
            class_name="grid grid-cols-2 gap-4",
        ),
        field(
            "Proposal deadline · UTC (admin controls later changes)",
            "deadline",
            rx.cond(editing, S.selected["deadline"], ""),
            "datetime-local",
        ),
        rx.el.p(
            "Save the draft first, then attach supporting documents in the project panel.",
            class_name="text-xs text-[#7b8879]",
        ),
        submit="Save proposal",
    )


def project_page() -> rx.Component:
    return rx.el.div(
        page_header(
            rx.match(
                S.section_name,
                ("marketplace", "Find your next challenge"),
                ("reviews", "Proposal review desk"),
                "Projects & workspaces",
            ),
            rx.match(
                S.section_name,
                (
                    "marketplace",
                    "Explore approved opportunities. Find the work that fits your skills and ambitions.",
                ),
                (
                    "reviews",
                    "Move proposals from a promising idea to a project ready for students.",
                ),
                "Your project community, from the first brief to the final handover.",
            ),
            "02 — PROJECTS",
        ),
        rx.el.div(
            rx.el.label(
                rx.icon("search", class_name="h-4 w-4 text-[#839281]"),
                rx.el.input(
                    placeholder="Search title, brief or sponsor…",
                    default_value=S.search,
                    on_change=S.set_search.debounce(400),
                    class_name="flex-1 min-w-0 bg-transparent text-sm text-[#26444a] outline-hidden",
                ),
                class_name="flex gap-3 items-center border border-[#cfd5c7] bg-[#fffef8] px-4 py-3 flex-1",
            ),
            rx.el.input(
                placeholder="Filter by skill",
                aria_label="Filter by skill",
                default_value=S.skill_filter,
                on_change=S.set_skill_filter.debounce(400),
                class_name="border border-[#cfd5c7] bg-[#fffef8] px-4 py-3 text-sm text-[#26444a] w-full sm:w-56 outline-hidden focus:border-teal-700",
            ),
            class_name="flex flex-col sm:flex-row gap-3 mb-6",
        ),
        rx.cond(
            S.can_propose & (S.section_name == "projects"),
            rx.el.div(
                disclosure("＋ New sponsor proposal", proposal_form()),
                class_name="mb-6",
            ),
        ),
        project_grid(),
    )


def preferences_page() -> rx.Component:
    return rx.el.div(
        page_header(
            "Find your fit",
            "Tell us what you bring, when you’re available, and where you want to contribute.",
            "03 — PREFERENCES",
        ),
        rx.el.div(
            rx.el.section(
                rx.el.h2(
                    "Your ranked shortlist",
                    class_name="font-serif text-2xl text-[#24434c]",
                ),
                rx.el.p(
                    S.round_info["name"],
                    " · ",
                    S.round_info["closes"],
                    class_name="text-xs text-[#768976] mt-2 mb-6",
                ),
                rx.cond(
                    S.preferences.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            S.preferences,
                            lambda p: rx.el.div(
                                rx.el.span(
                                    p["rank"],
                                    class_name="font-serif text-2xl text-[#64816b] w-8",
                                ),
                                rx.el.span(
                                    p["title"],
                                    class_name="flex-1 text-sm text-[#324e4e]",
                                ),
                                rx.el.button(
                                    rx.icon("arrow-up", class_name="h-4 w-4"),
                                    aria_label="Move preference up",
                                    on_click=S.save(
                                        {"action": "up", "target": p["id"]}
                                    ),
                                    class_name=SECONDARY,
                                ),
                                rx.el.button(
                                    rx.icon("arrow-down", class_name="h-4 w-4"),
                                    aria_label="Move preference down",
                                    on_click=S.save(
                                        {"action": "down", "target": p["id"]}
                                    ),
                                    class_name=SECONDARY,
                                ),
                                rx.el.button(
                                    rx.icon("x", class_name="h-4 w-4"),
                                    aria_label="Remove preference",
                                    on_click=S.save(
                                        {"action": "remove", "target": p["id"]}
                                    ),
                                    class_name=SECONDARY,
                                ),
                                class_name="flex gap-2 items-center border-b border-[#d9dece] py-4",
                            ),
                        )
                    ),
                    empty(
                        "Your shortlist starts here",
                        "Open a project in the marketplace and add it to your preferences. Rank your choices before the round closes.",
                    ),
                ),
                rx.el.a(
                    "Explore the marketplace →",
                    href="/studio/marketplace",
                    class_name="inline-block text-sm font-medium text-teal-800 mt-6",
                ),
                class_name=PANEL,
            ),
            rx.el.section(
                form(
                    "Your skills & availability",
                    "profile",
                    field("Display name", "name", S.profile["name"]),
                    area("About you", "biography", S.profile["biography"]),
                    field(
                        "Skills · comma separated",
                        "skills",
                        S.profile["skills"],
                    ),
                    field(
                        "Maximum hours per week",
                        "hours",
                        S.profile["hours"],
                        "number",
                    ),
                    area(
                        "Weekly availability · UTC",
                        "availability",
                        S.profile["availability"],
                        "0 09:00 12:00\n2 14:00 17:00",
                    ),
                    rx.el.p(
                        "One window per line: weekday (Monday = 0, Sunday = 6), start, end. Use 24-hour UTC times. Unknown availability receives no schedule bonus.",
                        class_name="text-xs text-[#7c8879] leading-5",
                    ),
                    submit="Save my profile",
                ),
                class_name=PANEL,
            ),
            class_name="grid lg:grid-cols-2 gap-6",
        ),
    )


def assignments_page() -> rx.Component:
    return rx.el.div(
        page_header(
            "Build the right teams",
            "Transparent matching, reviewed by people. Preview first; publish when the preference window closes.",
            "04 — ASSIGNMENTS",
        ),
        rx.el.div(
            rx.el.section(
                rx.el.div(
                    chip("Current round"),
                    rx.el.h2(
                        S.round_info["name"],
                        class_name="font-serif text-2xl text-[#24434c] mt-3",
                    ),
                    rx.el.p(
                        S.round_info["closes"],
                        class_name="text-sm text-[#738272] mt-1",
                    ),
                ),
                rx.el.p(
                    "Deterministic weighted matching uses ranked choices, skill overlap, known schedule overlap, and capacity. Only feasible teams are proposed; students are never assigned to two active teams.",
                    class_name="text-sm text-[#798574] leading-6 mt-5",
                ),
                rx.el.div(
                    rx.el.button(
                        "Generate preview",
                        rx.icon("git-branch", class_name="h-4 w-4"),
                        on_click=S.save({"action": "preview"}),
                        disabled=S.round_info["id"] == "",
                        class_name=BUTTON,
                    ),
                    rx.el.button(
                        "Publish assignments",
                        on_click=S.request_action(
                            "publish",
                            "",
                            "Publish these teams? Students will be notified and the preference round will close.",
                        ),
                        disabled=S.preview.length() == 0,
                        class_name=SECONDARY,
                    ),
                    class_name="flex flex-wrap gap-3 mt-5",
                ),
                class_name=PANEL,
            ),
            rx.el.section(
                disclosure(
                    "Open a preference round & configure weights",
                    form(
                        "New preference round",
                        "round",
                        field("Round name", "name", required=True),
                        field(
                            "Preferences close · UTC",
                            "deadline",
                            kind="datetime-local",
                            required=True,
                        ),
                        rx.el.div(
                            field(
                                "Preference weight", "preference", "5", "number"
                            ),
                            field(
                                "Skill overlap weight", "skill", "3", "number"
                            ),
                            field("Schedule weight", "schedule", "1", "number"),
                            field("Capacity weight", "capacity", "1", "number"),
                            class_name="grid grid-cols-2 gap-4",
                        ),
                        submit="Open round",
                    ),
                ),
                disclosure(
                    "Manual assignment override",
                    form(
                        "Move a student",
                        "override",
                        select_field("Student", "student", S.students),
                        select_field(
                            "Destination project",
                            "project",
                            S.projects,
                            "id",
                            "title",
                        ),
                        area("Reason · required for audit history", "reason"),
                        rx.el.p(
                            "Team minimum and maximum sizes still apply. The previous team assignments remain in the history.",
                            class_name="text-xs text-[#7c8879]",
                        ),
                        submit="Review override",
                    ),
                ),
                class_name=PANEL,
            ),
            class_name="grid lg:grid-cols-2 gap-6 mb-7",
        ),
        rx.el.h2(
            "Assignment preview",
            class_name="font-serif text-2xl text-[#24434c] mb-4",
        ),
        rx.cond(
            S.preview.length() > 0,
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.el.th("Student", class_name="p-4 text-left"),
                            rx.el.th("Project", class_name="p-4 text-left"),
                            rx.el.th("Score", class_name="p-4 text-left"),
                            rx.el.th(
                                "Why this match", class_name="p-4 text-left"
                            ),
                        ),
                        class_name="bg-[#e9eee0] text-xs text-[#536e5d]",
                    ),
                    rx.el.tbody(
                        rx.foreach(
                            S.preview,
                            lambda r: rx.el.tr(
                                rx.el.td(r["student"], class_name="p-4"),
                                rx.el.td(r["project"], class_name="p-4"),
                                rx.el.td(
                                    r["score"], class_name="p-4 font-mono"
                                ),
                                rx.el.td(
                                    r["explanation"],
                                    class_name="p-4 text-xs text-[#72806e]",
                                ),
                                class_name="border-t border-[#dbe0d0] even:bg-[#f2f4e9] hover:bg-[#eaf0e2]",
                            ),
                        )
                    ),
                    class_name="table-auto w-full text-sm text-[#324e4e]",
                ),
                class_name="overflow-x-auto border border-[#d9dece]",
            ),
            empty(
                "No assignments proposed yet",
                "Generate a preview after students rank their choices. Projects without enough eligible students remain unstaffed rather than forming undersized teams.",
            ),
        ),
    )


def templates_page() -> rx.Component:
    return rx.el.div(
        page_header(
            "A framework for progress",
            "Reusable milestone sequences keep expectations consistent without rewriting project history.",
            "05 — TEMPLATES",
        ),
        rx.el.div(
            rx.el.section(
                form(
                    "Create a milestone template",
                    "template",
                    field("Template name", "name", required=True),
                    area("Description", "description"),
                    area(
                        "Milestones · Title | days after start | acceptance criteria",
                        "items",
                        placeholder="Project brief | 7 | Agreed objectives and scope\nInterim review | 35 | Demonstrate progress\nFinal handover | 70 | Deliver documentation and outcomes",
                    ),
                    submit="Create template",
                ),
                class_name=PANEL,
            ),
            rx.el.section(
                rx.cond(
                    S.templates.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            S.templates,
                            lambda t: rx.el.div(
                                rx.icon(
                                    "files", class_name="h-5 w-5 text-[#7f9a79]"
                                ),
                                rx.el.div(
                                    rx.el.h3(
                                        t["name"],
                                        class_name="font-serif text-xl text-[#294c4e]",
                                    ),
                                    rx.el.p(
                                        t["description"],
                                        class_name="text-sm text-[#7b8877] mt-2",
                                    ),
                                ),
                                class_name="flex gap-4 border-b border-[#d8dfce] py-5",
                            ),
                        )
                    ),
                    empty(
                        "A blank page, ready for structure",
                        "Create a template, then apply it from a project workspace with a start date.",
                    ),
                ),
                class_name=PANEL,
            ),
            class_name="grid lg:grid-cols-2 gap-6",
        ),
    )


def notifications_page() -> rx.Component:
    return rx.el.div(
        page_header(
            "Keep the conversation moving",
            "Decisions, feedback, and deadlines—all in one place.",
            "06 — NOTIFICATIONS",
        ),
        rx.el.div(
            rx.el.p(f"{S.unread} unread", class_name="text-sm text-[#64816c]"),
            rx.el.button(
                "Mark all as read",
                on_click=S.save({"action": "read_all"}),
                class_name=SECONDARY,
            ),
            class_name="flex justify-between items-center mb-5",
        ),
        rx.cond(
            S.notifications.length() > 0,
            rx.el.div(
                rx.foreach(
                    S.notifications,
                    lambda n: rx.el.div(
                        rx.icon(
                            "bell", class_name="h-5 w-5 text-[#6f927d] mt-1"
                        ),
                        rx.el.div(
                            rx.el.p(
                                n["title"],
                                class_name="text-sm font-semibold text-[#2c4c4c]",
                            ),
                            rx.el.p(
                                n["date"],
                                class_name="text-xs text-[#81917d] mt-2",
                            ),
                            class_name="flex-1",
                        ),
                        rx.cond(
                            n["read"] == "unread",
                            rx.el.button(
                                "Mark read",
                                on_click=S.save(
                                    {"action": "read", "target": n["id"]}
                                ),
                                class_name=SECONDARY,
                            ),
                            chip("Read"),
                        ),
                        class_name="flex items-start gap-4 border-b border-[#dce1d1] bg-[#f7f8ee] px-5 py-5",
                    ),
                )
            ),
            empty(
                "You’re all caught up",
                "New approvals, team assignments, and project feedback will appear here.",
            ),
        ),
        rx.cond(
            S.is_admin,
            rx.el.div(
                rx.el.h3(
                    "Deadline notification queue",
                    class_name="font-serif text-xl text-[#294c4e]",
                ),
                rx.el.p(
                    "Scan active projects for milestones due within three days or already overdue. Repeated scans do not duplicate deadline notices.",
                    class_name="text-sm text-[#7c8879] mt-2 mb-4",
                ),
                rx.el.button(
                    rx.cond(S.scanning, "Scanning…", "Scan deadlines now"),
                    on_click=S.start_scan,
                    disabled=S.scanning,
                    class_name=BUTTON,
                ),
                rx.el.p(
                    S.queue_status,
                    role="status",
                    class_name="text-xs text-[#668670] mt-4",
                ),
                class_name="mt-8 border border-[#d6deca] bg-[#eef2e4] p-6",
            ),
        ),
    )


def reports_page() -> rx.Component:
    return rx.el.div(
        page_header(
            "Evidence for better decisions",
            "Live operational reports from your studio. No sample records, no invented outcomes.",
            "07 — REPORTS",
        ),
        rx.el.div(
            stat(
                "Behind schedule",
                S.stats["late"],
                "clock",
                "Projects with overdue milestones",
            ),
            stat(
                "Missing submissions",
                S.stats["missing"],
                "file-clock",
                "Student–milestone obligations",
            ),
            stat(
                "Top-three choice",
                S.stats["choice"],
                "list-checks",
                "Current team assignments",
            ),
            stat(
                "Unstaffed projects",
                S.stats["unstaffed"],
                "users",
                "Excludes closed projects",
            ),
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-7",
        ),
        rx.el.section(
            rx.el.h2(
                "Faculty supervision load",
                class_name="font-serif text-2xl text-[#24434c] mb-4",
            ),
            rx.cond(
                S.faculty.length() > 0,
                reflex_xy.chart(
                    reflex_xy.bar("advisor", "projects", color="#477f70"),
                    reflex_xy.x_axis(label="Faculty advisor"),
                    reflex_xy.y_axis(label="Open projects"),
                    reflex_xy.modebar(False),
                    reflex_xy.interaction_config(navigation=False),
                    data=S.faculty_data,
                    height="300px",
                    class_name="w-full min-w-[300px]",
                ),
                empty(
                    "No faculty assignments yet",
                    "Grant faculty advisor roles and assign advisors to projects to see supervision load.",
                ),
            ),
            class_name="border border-[#d9dece] bg-[#fafaf3] p-5 w-full mb-7 overflow-x-auto",
        ),
        rx.el.div(
            rx.el.input(
                placeholder="Filter by project, advisor, schedule or staffing…",
                aria_label="Filter report",
                default_value=S.search,
                on_change=S.set_search.debounce(400),
                class_name=INPUT,
            ),
            rx.el.button(
                rx.icon("download", class_name="h-4 w-4"),
                "Export CSV",
                on_click=S.export,
                class_name=SECONDARY,
            ),
            class_name="flex gap-3 mb-4",
        ),
        rx.cond(
            S.filtered_reports.length() > 0,
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.foreach(
                                [
                                    "Project",
                                    "Lifecycle",
                                    "Schedule",
                                    "Missing",
                                    "Advisor",
                                    "Members",
                                    "Staffing",
                                ],
                                lambda col: rx.el.th(
                                    rx.el.div(
                                        rx.icon(
                                            "minus",
                                            class_name="h-3 w-3 text-[#8ea285]",
                                        ),
                                        col,
                                        class_name="flex gap-2 items-center",
                                    ),
                                    class_name="p-4 text-left whitespace-nowrap",
                                ),
                            )
                        ),
                        class_name="text-xs text-[#57715d] bg-[#e9eee0]",
                    ),
                    rx.el.tbody(
                        rx.foreach(
                            S.filtered_reports,
                            lambda r: rx.el.tr(
                                rx.foreach(
                                    [
                                        "project",
                                        "lifecycle",
                                        "schedule",
                                        "missing",
                                        "advisor",
                                        "members",
                                        "staffing",
                                    ],
                                    lambda key: rx.el.td(
                                        r[key], class_name="p-4"
                                    ),
                                ),
                                class_name="border-t border-[#dbe0d0] even:bg-[#f2f4e9] hover:bg-[#eaf0e2]",
                            ),
                        )
                    ),
                    class_name="table-auto w-full text-xs text-[#36524e]",
                ),
                class_name="overflow-x-auto border border-[#d9dece] rounded-sm",
            ),
            empty(
                "No matching report rows",
                "Projects and milestone activity will populate this report. Try clearing the filter.",
            ),
        ),
        rx.el.p(
            "Missing submissions counts each current student’s obligation for an overdue milestone with no team submission. Top-three rate uses preferences from the assignment’s original round; manual overrides without a ranked choice count outside the top three.",
            class_name="text-xs text-[#8b9482] mt-5 leading-5",
        ),
    )


def users_page() -> rx.Component:
    return rx.el.div(
        page_header(
            "The people behind the work",
            "Grant responsibilities intentionally. Role changes take effect on the next server action.",
            "08 — ADMINISTRATION",
        ),
        rx.el.div(
            rx.el.section(
                rx.el.div(
                    rx.foreach(
                        S.people,
                        lambda u: rx.el.div(
                            rx.el.div(
                                rx.el.p(
                                    u["name"],
                                    class_name="font-medium text-sm text-[#30504d]",
                                ),
                                rx.el.p(
                                    u["email"],
                                    class_name="text-xs text-[#809079] mt-1",
                                ),
                            ),
                            rx.el.p(
                                u["roles"].replace("_", " "),
                                class_name="text-xs text-[#63836a] mt-3",
                            ),
                            class_name="border-b border-[#dbe1d0] py-5",
                        ),
                    )
                ),
                class_name=PANEL,
            ),
            rx.el.section(
                form(
                    "Manage a user role",
                    "role",
                    select_field("User", "user", S.people),
                    choice(
                        "Role",
                        "role",
                        [
                            "student",
                            "sponsor",
                            "faculty_advisor",
                            "program_administrator",
                            "system_administrator",
                        ],
                    ),
                    choice("Operation", "operation", ["grant", "revoke"]),
                    rx.el.p(
                        "The final active system administrator cannot be revoked. Role changes are retained in the audit history.",
                        class_name="text-xs text-[#7c8879] leading-5",
                    ),
                    submit="Review role change",
                ),
                class_name=PANEL,
            ),
            class_name="grid lg:grid-cols-2 gap-6",
        ),
    )


def workspace_tools() -> rx.Component:
    return rx.el.div(
        rx.cond(
            S.selected["editable"] == "yes",
            disclosure("Edit project proposal", proposal_form(True)),
        ),
        rx.cond(
            S.can_propose,
            disclosure(
                "Lifecycle decision",
                form(
                    "Move the project forward",
                    "transition",
                    hidden("version", S.selected["version"]),
                    choice(
                        "Next state",
                        "state",
                        [
                            "submitted",
                            "under_review",
                            "approved",
                            "rejected",
                            "changes_requested",
                            "matching",
                            "active",
                            "completed",
                            "archived",
                        ],
                    ),
                    area("Decision / reason", "reason"),
                    rx.el.p(
                        "Only valid lifecycle transitions are accepted. Opening matching makes the project available for student preferences.",
                        class_name="text-xs text-[#7c8879]",
                    ),
                    submit="Review transition",
                ),
            ),
        ),
        rx.cond(
            S.is_admin,
            rx.el.div(
                disclosure(
                    "Advisor, health & status",
                    form(
                        "Project configuration",
                        "configure",
                        hidden("version", S.selected["version"]),
                        select_field("Faculty advisor", "advisor", S.advisors),
                        choice(
                            "Health",
                            "health",
                            ["on_track", "at_risk", "off_track", "unknown"],
                        ),
                        choice(
                            "Status",
                            "status",
                            ["not_started", "in_progress", "on_hold"],
                        ),
                        submit="Save configuration",
                    ),
                ),
                disclosure(
                    "Apply a milestone template",
                    form(
                        "Set the project’s milestones",
                        "instantiate",
                        select_field("Template", "template", S.templates),
                        field(
                            "Project start · UTC",
                            "start",
                            kind="datetime-local",
                            required=True,
                        ),
                        submit="Create milestones",
                    ),
                ),
            ),
        ),
    )


def milestone_item(item) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h4(
                    item["title"],
                    class_name="font-medium text-sm text-[#32534e]",
                ),
                rx.el.p(item["due"], class_name="text-xs text-[#7b8b73] mt-1"),
                rx.el.p(
                    item["criteria"], class_name="text-xs text-[#7b8b73] mt-2"
                ),
            ),
            chip(item["state"]),
            class_name="flex justify-between items-start gap-3",
        ),
        rx.cond(
            S.is_admin,
            disclosure(
                "Change deadline",
                form(
                    "Reschedule milestone",
                    "deadline",
                    hidden("milestone", item["id"]),
                    hidden("version", item["version"]),
                    field(
                        "New due date · UTC",
                        "due",
                        kind="datetime-local",
                        required=True,
                    ),
                    area("Reason", "reason"),
                    submit="Save deadline",
                ),
            ),
        ),
        class_name="border-b border-[#dce2d0] py-4",
    )


def work_records() -> rx.Component:
    return rx.el.div(
        rx.el.section(
            rx.el.h3(
                "Milestones & deliverables",
                class_name="font-serif text-2xl text-[#294a4c] mb-4",
            ),
            rx.cond(
                S.milestones.length() > 0,
                rx.el.div(rx.foreach(S.milestones, milestone_item)),
                rx.el.p(
                    "No milestones yet. An administrator can apply a template below.",
                    class_name="text-sm text-[#7d8b78] py-5",
                ),
            ),
            rx.cond(
                S.is_student,
                disclosure(
                    "Submit a deliverable",
                    form(
                        "Create an immutable submission version",
                        "submission",
                        select_field(
                            "Milestone",
                            "milestone",
                            S.milestones,
                            "id",
                            "title",
                        ),
                        area("Submission notes", "notes"),
                        rx.el.p(
                            "Use the document uploader first. Each submission creates a new version; earlier files and notes are retained.",
                            class_name="text-xs text-[#7c8879] leading-5",
                        ),
                        rx.foreach(
                            S.staged_files,
                            lambda f: rx.el.p(
                                f["name"], class_name="text-xs text-teal-700"
                            ),
                        ),
                        submit="Submit new version",
                    ),
                ),
            ),
            rx.el.h3(
                "Submission history",
                class_name="font-serif text-xl text-[#294a4c] mt-7 mb-3",
            ),
            rx.cond(
                S.submissions.length() > 0,
                rx.el.div(
                    rx.foreach(
                        S.submissions,
                        lambda sub: rx.el.div(
                            rx.el.h4(
                                sub["title"],
                                class_name="text-sm font-medium text-[#34534e]",
                            ),
                            rx.el.p(
                                sub["notes"],
                                class_name="text-sm text-[#7b8875] mt-2 whitespace-pre-wrap",
                            ),
                            rx.el.p(
                                sub["files"],
                                class_name="text-xs text-[#80917a] mt-2",
                            ),
                            rx.el.div(
                                rx.el.span(
                                    sub["date"],
                                    class_name="text-[10px] text-[#92a087]",
                                ),
                                rx.el.button(
                                    "Download files",
                                    on_click=S.download_submission(sub["id"]),
                                    class_name="text-xs text-teal-800 underline underline-offset-4",
                                ),
                                class_name="flex justify-between gap-2 mt-3",
                            ),
                            class_name="border border-[#dde3d1] bg-[#f3f6ea] p-4 mb-3",
                        ),
                    )
                ),
                rx.el.p(
                    "No submissions yet.", class_name="text-sm text-[#7d8b78]"
                ),
            ),
            rx.cond(
                S.is_admin | S.roles.contains("faculty_advisor"),
                disclosure(
                    "Evaluate a submission",
                    form(
                        "Advisor evaluation",
                        "evaluate",
                        select_field(
                            "Submission version",
                            "submission",
                            S.submissions,
                            "id",
                            "title",
                        ),
                        field(
                            "Score out of 100",
                            "score",
                            kind="number",
                            required=True,
                        ),
                        choice(
                            "Decision",
                            "decision",
                            ["accepted", "changes_requested"],
                        ),
                        area("Feedback", "notes"),
                        submit="Save evaluation",
                    ),
                ),
            ),
            class_name=PANEL,
        ),
        rx.el.section(
            rx.el.h3(
                "People & conversations",
                class_name="font-serif text-2xl text-[#294a4c] mb-5",
            ),
            rx.el.p(
                "SPONSOR",
                class_name="text-[9px] text-[#7e957c] tracking-widest",
            ),
            rx.el.p(
                S.selected["sponsor"],
                class_name="text-sm text-[#355750] mt-1 mb-4",
            ),
            rx.el.p(
                "FACULTY ADVISOR",
                class_name="text-[9px] text-[#7e957c] tracking-widest",
            ),
            rx.el.p(
                S.selected["advisor"],
                class_name="text-sm text-[#355750] mt-1 mb-4",
            ),
            rx.el.p(
                "TEAM",
                class_name="text-[9px] text-[#7e957c] tracking-widest mb-2",
            ),
            rx.cond(
                S.roster.length() > 0,
                rx.el.div(
                    rx.foreach(
                        S.roster,
                        lambda person: rx.el.p(
                            person["name"],
                            class_name="text-sm text-[#355750] py-1",
                        ),
                    )
                ),
                rx.el.p(
                    "Team not assigned yet", class_name="text-sm text-[#89967e]"
                ),
            ),
            rx.el.h3(
                "Feedback",
                class_name="font-serif text-xl text-[#294a4c] mt-7 mb-3",
            ),
            rx.foreach(
                S.feedback,
                lambda f: rx.el.div(
                    rx.el.p(
                        f["title"],
                        " · ",
                        f["score"],
                        class_name="text-xs font-semibold text-[#60816c]",
                    ),
                    rx.el.p(
                        f["notes"],
                        class_name="text-sm text-[#7a8875] mt-2 whitespace-pre-wrap",
                    ),
                    class_name="border-b border-[#dce3d0] py-4",
                ),
            ),
            rx.cond(
                S.can_propose,
                disclosure(
                    "Add sponsor feedback",
                    form(
                        "Sponsor feedback",
                        "feedback",
                        area("Comments", "notes"),
                        submit="Post feedback",
                    ),
                ),
            ),
            rx.el.h3(
                "Meeting records",
                class_name="font-serif text-xl text-[#294a4c] mt-7 mb-3",
            ),
            rx.foreach(
                S.meetings,
                lambda meeting: rx.el.div(
                    rx.el.h4(
                        meeting["title"],
                        class_name="text-sm text-[#35564f] font-medium",
                    ),
                    rx.el.p(
                        meeting["date"],
                        " · ",
                        meeting["location"],
                        class_name="text-xs text-[#8c9b80] mt-1",
                    ),
                    rx.el.p(
                        meeting["notes"],
                        class_name="text-sm text-[#788873] mt-2 whitespace-pre-wrap",
                    ),
                    class_name="border-b border-[#dce3d0] py-4",
                ),
            ),
            disclosure(
                "Record a meeting",
                form(
                    "Meeting & attendee notes",
                    "meeting",
                    field("Meeting title", "title", required=True),
                    rx.el.div(
                        field(
                            "Starts · UTC",
                            "start",
                            kind="datetime-local",
                            required=True,
                        ),
                        field(
                            "Ends · UTC",
                            "end",
                            kind="datetime-local",
                            required=True,
                        ),
                        class_name="grid sm:grid-cols-2 gap-3",
                    ),
                    field("Location / meeting link", "location"),
                    area("Minutes and attendee notes", "notes"),
                    submit="Save meeting",
                ),
            ),
            class_name=PANEL,
        ),
        class_name="grid xl:grid-cols-2 gap-5 mt-6",
    )


def risks_timeline() -> rx.Component:
    return rx.el.div(
        rx.el.section(
            rx.el.h3(
                "Risks & issues",
                class_name="font-serif text-2xl text-[#294a4c] mb-5",
            ),
            rx.foreach(
                S.risks,
                lambda r: rx.el.div(
                    rx.el.div(
                        rx.el.h4(
                            r["title"],
                            class_name="text-sm font-medium text-[#3f594e]",
                        ),
                        chip(r["state"]),
                        class_name="flex justify-between gap-3",
                    ),
                    rx.el.p(
                        r["severity"],
                        " · ",
                        r["owner"],
                        " · ",
                        r["due"],
                        class_name="text-xs text-[#8a9477] mt-2",
                    ),
                    rx.el.p(
                        r["notes"], class_name="text-sm text-[#819075] mt-2"
                    ),
                    disclosure(
                        "Resolve",
                        form(
                            "Resolution",
                            "resolve",
                            hidden("risk", r["id"]),
                            area("Resolution notes", "notes"),
                            submit="Resolve issue",
                        ),
                    ),
                    class_name="border-b border-[#dde3d0] py-4",
                ),
            ),
            disclosure(
                "Record a risk or issue",
                form(
                    "New risk / issue",
                    "risk",
                    field("Title", "title", required=True),
                    choice("Type", "kind", ["risk", "issue"]),
                    choice(
                        "Severity",
                        "severity",
                        ["low", "medium", "high", "critical"],
                    ),
                    select_field(
                        "Owner · current team member", "owner", S.roster
                    ),
                    field("Due date · UTC", "due", kind="datetime-local"),
                    area("Description & mitigation", "notes"),
                    submit="Save risk / issue",
                ),
            ),
            class_name=PANEL,
        ),
        rx.el.section(
            rx.el.h3(
                "Studio activity",
                class_name="font-serif text-2xl text-[#294a4c] mb-5",
            ),
            rx.foreach(
                S.timeline,
                lambda a: rx.el.div(
                    rx.el.div(
                        class_name="size-2 shrink-0 rounded-full bg-[#8bab82] mt-1.5"
                    ),
                    rx.el.div(
                        rx.el.p(
                            a["title"],
                            class_name="text-xs font-medium text-[#557659]",
                        ),
                        rx.el.p(
                            a["notes"], class_name="text-xs text-[#7e8d75] mt-1"
                        ),
                        rx.el.p(
                            a["date"],
                            " · ",
                            a["actor"],
                            class_name="text-[10px] text-[#99a48b] mt-2",
                        ),
                    ),
                    class_name="flex gap-3 border-l border-[#d7e0cb] pl-4 pb-6",
                ),
            ),
            class_name=PANEL,
        ),
        class_name="grid xl:grid-cols-2 gap-5 mt-5",
    )


def project_detail() -> rx.Component:
    return rx.el.div(
        rx.el.section(
            rx.el.div(
                rx.el.p(
                    "PROJECT STUDIO / WORKSPACE",
                    class_name="text-[9px] tracking-[0.2em] text-[#809079]",
                ),
                rx.el.button(
                    rx.icon("x", class_name="h-5 w-5"),
                    on_click=S.close_project,
                    aria_label="Close workspace",
                    class_name=SECONDARY,
                ),
                class_name="flex justify-between items-center",
            ),
            rx.el.h2(
                S.selected["title"],
                class_name="font-serif text-3xl md:text-4xl text-[#23474c] my-5",
            ),
            rx.el.div(
                chip(S.selected["lifecycle"]),
                chip(S.selected["health"]),
                chip(S.selected["status"]),
                class_name="flex flex-wrap gap-2 mb-5",
            ),
            ribbon(),
            rx.el.p(
                S.selected["summary"],
                class_name="text-base text-[#627e6b] leading-7 mt-6",
            ),
            rx.el.p(
                S.selected["description"],
                class_name="text-sm text-[#7e8b78] leading-6 whitespace-pre-wrap mt-4",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.h3(
                        "Objectives",
                        class_name="font-serif text-xl text-[#3b6053]",
                    ),
                    rx.el.p(
                        S.selected["objectives"],
                        class_name="whitespace-pre-wrap text-sm text-[#7e8e76] leading-7 mt-3",
                    ),
                ),
                rx.el.div(
                    rx.el.h3(
                        "Skills & team",
                        class_name="font-serif text-xl text-[#3b6053]",
                    ),
                    rx.el.p(
                        S.selected["skills"],
                        class_name="text-sm text-[#7e8e76] mt-3",
                    ),
                    rx.el.p(
                        S.selected["min"],
                        "–",
                        S.selected["max"],
                        " students",
                        class_name="text-sm text-[#7e8e76] mt-2",
                    ),
                ),
                class_name="grid md:grid-cols-2 gap-6 mt-6 mb-5",
            ),
            rx.cond(
                S.selected["review"] != "",
                rx.el.div(
                    rx.el.p(
                        "Review notes",
                        class_name="font-semibold text-xs text-[#668573]",
                    ),
                    rx.el.p(
                        S.selected["review"],
                        class_name="text-sm text-[#7e8e76] mt-2",
                    ),
                    class_name="bg-[#edf2e2] border border-[#dbe3cd] p-4 mb-5",
                ),
            ),
            rx.cond(
                S.is_student & (S.selected["lifecycle"] == "matching"),
                rx.el.button(
                    "Add to my preferences",
                    rx.icon("list-plus", class_name="h-4 w-4"),
                    on_click=S.save(
                        {"action": "preference", "target": S.selected["id"]}
                    ),
                    class_name=BUTTON,
                ),
            ),
            rx.el.h3(
                "Supporting documents",
                class_name="font-serif text-xl text-[#3b6053] mt-6 mb-4",
            ),
            rx.foreach(
                S.documents,
                lambda f: rx.el.a(
                    rx.icon("file-text", class_name="h-4 w-4"),
                    f["name"],
                    href=rx.get_upload_url(f["key"]),
                    target="_blank",
                    class_name="flex gap-2 text-xs text-teal-800 py-2 underline underline-offset-4",
                ),
            ),
            disclosure(
                "Upload documents",
                rx.el.p(
                    "PDF, DOCX, TXT or CSV · up to 5 files, 10 MB each. Only upload documents appropriate for sharing with project participants.",
                    class_name="text-xs text-[#7c8879] mb-3",
                ),
                rx.upload.root(
                    rx.el.div(
                        rx.icon("upload", class_name="h-6 w-6 text-[#8da384]"),
                        rx.el.p(
                            "Choose documents or drop them here",
                            class_name="text-sm text-[#658169]",
                        ),
                        class_name="flex flex-col items-center justify-center gap-3 py-7",
                    ),
                    id="documents",
                    multiple=True,
                    max_files=5,
                    class_name="border border-dashed border-[#b7c9ac] bg-[#eff4e5] rounded-sm cursor-pointer",
                ),
                rx.foreach(
                    rx.selected_files("documents"),
                    lambda filename: rx.el.p(
                        filename, class_name="text-xs text-[#7d8e74] mt-2"
                    ),
                ),
                rx.el.button(
                    "Upload selected files",
                    on_click=S.upload(rx.upload_files(upload_id="documents")),
                    class_name=BUTTON,
                ),
                rx.el.p(
                    "For student deliverables, upload first and then submit a new version below.",
                    class_name="text-xs text-[#7c8879] mt-3",
                ),
            ),
            workspace_tools(),
            work_records(),
            risks_timeline(),
            class_name="w-full max-w-[1300px] mx-auto bg-[#fafbf1] p-5 md:p-8 min-h-full border-x border-[#d9e1cb]",
        ),
        role="dialog",
        aria_modal=True,
        aria_label="Project workspace",
        class_name="fixed inset-0 z-40 overflow-y-auto bg-[#f0f3e5] text-[#24484c]",
    )


def confirmation() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("clipboard-check", class_name="h-8 w-8 text-[#62846a]"),
            rx.el.h2(
                "Confirm your decision",
                class_name="font-serif text-2xl text-[#254a4a] mt-4",
            ),
            rx.el.p(
                S.pending_label,
                class_name="text-sm text-[#7b8c75] leading-6 mt-3",
            ),
            rx.el.div(
                rx.el.button(
                    "Cancel", on_click=S.cancel_action, class_name=SECONDARY
                ),
                rx.el.button(
                    "Confirm change",
                    on_click=S.confirm_action,
                    class_name=BUTTON,
                ),
                class_name="flex gap-3 justify-end mt-7",
            ),
            role="alertdialog",
            aria_modal=True,
            aria_label="Confirm your decision",
            class_name="w-full max-w-md border border-[#cbd8be] bg-[#fafbf1] p-7 rounded-sm",
        ),
        class_name="fixed inset-0 z-50 flex items-center justify-center p-5 bg-[#112e3c]/70",
    )


def shell() -> rx.Component:
    return rx.el.div(
        masthead(),
        rx.el.div(
            navigation(),
            rx.el.main(
                rx.cond(
                    S.error != "",
                    rx.el.div(
                        rx.icon("circle-alert", class_name="h-4 w-4 shrink-0"),
                        rx.el.p(S.error),
                        role="alert",
                        class_name="flex gap-3 border border-red-200 bg-red-50 text-red-700 p-4 mb-5 text-sm",
                    ),
                ),
                rx.match(
                    S.section_name,
                    ("dashboard", dashboard()),
                    ("marketplace", project_page()),
                    ("projects", project_page()),
                    ("reviews", project_page()),
                    ("preferences", preferences_page()),
                    ("assignments", assignments_page()),
                    ("templates", templates_page()),
                    ("notifications", notifications_page()),
                    ("reports", reports_page()),
                    ("users", users_page()),
                    dashboard(),
                ),
                rx.el.footer(
                    "UniFlow / University project studio",
                    class_name="mt-12 pt-5 border-t border-[#d9ddce] text-[10px] tracking-wide text-[#9ba18e]",
                ),
                class_name="flex-1 w-full min-w-0 min-h-0 overflow-y-auto px-5 py-7 lg:p-9 bg-[#f8f7ef]",
            ),
            class_name="flex flex-col md:flex-row flex-1 min-h-0",
        ),
        rx.cond(S.selected["id"] != "", project_detail()),
        rx.cond(S.pending_action != "", confirmation()),
        rx.cond(
            (S.error != "") & (S.selected["id"] != ""),
            rx.el.div(
                rx.el.p(S.error),
                rx.el.button(
                    "Dismiss", on_click=S.load, class_name="underline"
                ),
                role="alert",
                class_name="fixed bottom-5 left-5 right-5 z-[60] flex justify-between gap-4 p-4 border border-red-200 bg-red-50 text-red-700 text-sm",
            ),
        ),
        class_name="font-['Inter'] flex flex-col h-dvh w-full overflow-hidden bg-[#f8f7ef] text-[#29474b]",
    )
