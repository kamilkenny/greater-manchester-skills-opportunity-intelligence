from dash import Input, Output, dcc, html

from dashboard.components.common import (
    dropdown_control,
    page_hero,
    page_shell,
)
from dashboard.figures import (
    PLOT_CONFIG,
    borough_labour_figure,
    borough_qualification_figure,
    format_value,
)

KPI_CODES = (
    "APP_STARTS",
    "NEET_RATE",
    "EDU_TRAINING_RATE",
    "EMPLOYMENT_RATE",
    "UNEMPLOYMENT_RATE",
    "INACTIVITY_RATE",
    "RQF3_PLUS_RATE",
    "RQF4_PLUS_RATE",
)


def _definitions(bundle):
    return {
        row["kpi_code"]: row
        for row in bundle.datasets[
            "kpi_definitions"
        ]
    }


def _borough_names(bundle):
    return sorted(
        {
            row["borough_name"]
            for row in bundle.datasets[
                "borough_current"
            ]
        }
    )


def _period_label(row):
    if not row:
        return "Period unavailable"

    value = row.get(
        "period_name"
    )

    if value:
        code = str(
            row.get(
                "period_code",
                "",
            )
        )

        if (
            value.startswith(
                "Academic year "
            )
            and len(code) == 6
            and code.isdigit()
        ):
            return (
                "Academic year "
                f"{code[:4]}/{code[4:]}"
            )

        return value

    return "Period unavailable"


def _current_row(
    bundle,
    borough_name,
):
    return next(
        (
            row
            for row in bundle.datasets[
                "borough_current"
            ]
            if row[
                "borough_name"
            ]
            == borough_name
        ),
        None,
    )


def _kpi_rows(
    bundle,
    borough_name,
):
    return {
        row["kpi_code"]: row
        for row in bundle.datasets[
            "borough_kpis"
        ]
        if row[
            "borough_name"
        ]
        == borough_name
    }


def _kpi_cards(
    bundle,
    borough_name,
):
    definitions = _definitions(
        bundle
    )

    rows = _kpi_rows(
        bundle,
        borough_name,
    )

    cards = []

    for code in KPI_CODES:
        definition = definitions[
            code
        ]

        row = rows.get(
            code
        )

        value = (
            row.get(
                "kpi_value"
            )
            if row
            else None
        )

        status = (
            row.get(
                "value_status",
                "unavailable",
            )
            if row
            else "unavailable"
        )

        unit = definition.get(
            "unit_name"
        )

        cards.append(
            html.Article(
                className="kpi-card",
                children=[
                    html.Div(
                        definition[
                            "domain_name"
                        ],
                        className=(
                            "kpi-domain"
                        ),
                    ),
                    html.Div(
                        definition[
                            "kpi_name"
                        ],
                        className=(
                            "kpi-name"
                        ),
                    ),
                    html.Div(
                        format_value(
                            value,
                            unit,
                        ),
                        className=(
                            "kpi-value"
                        ),
                    ),
                    html.Div(
                        _period_label(
                            row
                        ),
                        className=(
                            "kpi-period"
                        ),
                    ),
                    html.Div(
                        status.replace(
                            "_",
                            " ",
                        ),
                        className=(
                            "kpi-status "
                            f"status-{status}"
                        ),
                    ),
                ],
            )
        )

    return cards


def layout(
    store,
):
    bundle = store.get_bundle()

    names = _borough_names(
        bundle
    )

    default = (
        "Manchester"
        if "Manchester" in names
        else names[0]
    )

    row = _current_row(
        bundle,
        default,
    )

    selector = dropdown_control(
        label="Borough",
        component_id=(
            "borough-select"
        ),
        options=[
            {
                "label": name,
                "value": name,
            }
            for name in names
        ],
        value=default,
    )

    children = [
        page_hero(
            eyebrow="Borough Explorer",
            title=(
                "One borough. Multiple "
                "dimensions of opportunity."
            ),
            description=(
                "Examine the latest skills, "
                "youth, labour-market and "
                "qualification indicators."
            ),
        ),
        html.Div(
            className="content",
            children=[
                html.Div(
                    selector,
                    className=(
                        "toolbar "
                        "borough-toolbar"
                    ),
                ),
                html.Div(
                    id="borough-kpi-grid",
                    className="kpi-grid",
                    children=_kpi_cards(
                        bundle,
                        default,
                    ),
                ),
                html.Div(
                    className=(
                        "analysis-grid "
                        "borough-analysis-grid"
                    ),
                    children=[
                        html.Section(
                            className=(
                                "panel chart-card"
                            ),
                            children=[
                                html.Div(
                                    className=(
                                        "panel-heading"
                                    ),
                                    children=[
                                        html.Span(
                                            (
                                                "Labour "
                                                "market"
                                            ),
                                            className=(
                                                "eyebrow"
                                            ),
                                        ),
                                        html.H3(
                                            
                                                "Current "
                                                "labour-market "
                                                "profile"
                                            
                                        ),
                                    ],
                                ),
                                dcc.Graph(
                                    id=(
                                        "borough-"
                                        "labour-chart"
                                    ),
                                    figure=(
                                        borough_labour_figure(
                                            row
                                        )
                                    ),
                                    config=(
                                        PLOT_CONFIG
                                    ),
                                ),
                            ],
                        ),
                        html.Section(
                            className=(
                                "panel chart-card"
                            ),
                            children=[
                                html.Div(
                                    className=(
                                        "panel-heading"
                                    ),
                                    children=[
                                        html.Span(
                                            "Qualifications",
                                            className=(
                                                "eyebrow"
                                            ),
                                        ),
                                        html.H3(
                                            
                                                "RQF "
                                                "attainment"
                                            
                                        ),
                                    ],
                                ),
                                dcc.Graph(
                                    id=(
                                        "borough-"
                                        "qualification-chart"
                                    ),
                                    figure=(
                                        borough_qualification_figure(
                                            row
                                        )
                                    ),
                                    config=(
                                        PLOT_CONFIG
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ]

    return page_shell(
        active_page="borough",
        status=store.status(),
        children=children,
    )


def register_callbacks(
    app,
    store,
):
    @app.callback(
        Output(
            "borough-kpi-grid",
            "children",
        ),
        Output(
            "borough-labour-chart",
            "figure",
        ),
        Output(
            "borough-qualification-chart",
            "figure",
        ),
        Input(
            "borough-select",
            "value",
        ),
        Input(
            "snapshot-version",
            "data",
        ),
    )
    def update_borough(
        borough_name,
        _snapshot_version,
    ):
        bundle = store.get_bundle()

        row = _current_row(
            bundle,
            borough_name,
        )

        return (
            _kpi_cards(
                bundle,
                borough_name,
            ),
            borough_labour_figure(
                row
            ),
            borough_qualification_figure(
                row
            ),
        )
