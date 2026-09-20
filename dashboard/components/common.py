from datetime import datetime
from typing import Any

from dash import dcc, get_relative_path, html

NAV_ITEMS = (
    ("overview", "Overview", "/"),
    ("borough", "Borough Explorer", "/borough"),
    ("mbacc", "MBacc Pathways", "/mbacc"),
    ("trends", "Trends", "/trends"),
    ("methodology", "Data & Methodology", "/methodology"),
)


def format_timestamp(value: str | None) -> str:
    if not value:
        return "Unavailable"

    try:
        dt = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        return dt.strftime(
            "%d %b %Y, %H:%M UTC"
        )

    except ValueError:
        return value


def serving_label(
    status: dict[str, Any],
) -> tuple[str, str]:
    serving_status = status.get(
        "serving_status"
    )

    if serving_status == "current":
        return (
            "Live validated data",
            "status-live",
        )

    if serving_status == "last_known_good":
        return (
            "Last validated snapshot",
            "status-stale",
        )

    if serving_status == "bootstrap":
        return (
            "Bootstrap snapshot",
            "status-bootstrap",
        )

    return (
        "Data status unavailable",
        "status-unavailable",
    )


def header(
    active_page: str,
    status: dict[str, Any],
):
    label, status_class = serving_label(
        status
    )

    nav = [
        dcc.Link(
            text,
            href=get_relative_path(href),
            className=(
                "nav-link active"
                if page == active_page
                else "nav-link"
            ),
        )
        for page, text, href in NAV_ITEMS
    ]

    return html.Header(
        className="site-header",
        children=[
            html.Div(
                className="brand",
                children=[
                    html.Div(
                        "GM",
                        className="brand-mark",
                    ),
                    html.Div(
                        [
                            html.Div(
                                "GM SkillsFlow",
                                className="brand-name",
                            ),
                            html.Div(
                                (
                                    "Skills & Opportunity "
                                    "Intelligence"
                                ),
                                className=(
                                    "brand-subtitle"
                                ),
                            ),
                            html.Div(
                                "Designed and modelled by Kamil Ridwan",
                                className="designer-credit-header",
                            ),
                            html.Div(
                                (
                                    "Designed and modelled "
                                    "by Kamil Ridwan"
                                ),
                                className=(
                                    "designer-credit-header"
                                ),
                            ),
                        ]
                    ),
                ],
            ),
            html.Div(
                [
                    html.Div(
                        id="header-serving-status",
                        className=(
                            "header-serving-status "
                            f"{status_class}"
                        ),
                        children=label,
                    ),
                    html.Nav(
                        nav,
                        className="desktop-nav",
                    ),
                ],
                className="header-actions",
            ),
        ],
    )


def footer():
    return html.Footer(
        className="site-footer",
        children=[
            html.Div(
                [
                    html.Strong(
                        "GM SkillsFlow"
                    ),
                    html.Span(
                        
                            "Greater Manchester Skills "
                            "& Opportunity Intelligence"
                        
                    ),
                ],
                className="footer-brand",
            ),
            html.Div(
                (
                    "Public analytical prototype "
                    "using official statistics."
                ),
                className="footer-note",
            ),
        ],
    )


def page_shell(
    *,
    active_page: str,
    status: dict[str, Any],
    children,
):
    return html.Div(
        [
            header(
                active_page,
                status,
            ),
            html.Main(children),
            footer(),
        ],
        className="app-shell",
    )


def page_hero(
    *,
    eyebrow: str,
    title: str,
    description: str,
):
    return html.Section(
        className="page-hero",
        children=[
            html.Div(
                className="page-hero-inner",
                children=[
                    html.Span(
                        eyebrow,
                        className="eyebrow",
                    ),
                    html.H1(title),
                    html.P(description),
                ],
            )
        ],
    )


def stat_card(
    label: str,
    value: str,
    detail: str,
):
    return html.Article(
        className="stat-card",
        children=[
            html.Div(
                label,
                className="stat-label",
            ),
            html.Div(
                value,
                className="stat-value",
            ),
            html.Div(
                detail,
                className="stat-detail",
            ),
        ],
    )


def section_heading(
    eyebrow: str,
    title: str,
    description: str,
    control=None,
):
    children = [
        html.Div(
            [
                html.Span(
                    eyebrow,
                    className="eyebrow",
                ),
                html.H2(title),
                html.P(description),
            ]
        )
    ]

    if control is not None:
        children.append(control)

    return html.Div(
        children,
        className="section-heading",
    )


def dropdown_control(
    *,
    label: str,
    component_id: str,
    options,
    value,
):
    return html.Div(
        className="control",
        children=[
            html.Label(
                label,
                htmlFor=component_id,
            ),
            dcc.Dropdown(
                id=component_id,
                options=options,
                value=value,
                clearable=False,
                searchable=False,
                className="gm-dropdown",
            ),
        ],
    )
