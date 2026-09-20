from dash import Input, Output, dcc, html

from dashboard.components.common import (
    dropdown_control,
    page_hero,
    page_shell,
)
from dashboard.figures import (
    PLOT_CONFIG,
    academic_period,
    multi_line_figure,
)

DOMAINS = (
    (
        "apprenticeships",
        "Apprenticeships",
    ),
    (
        "youth",
        "Youth Transition",
    ),
    (
        "labour",
        "Labour Market",
    ),
    (
        "qualifications",
        "Qualifications",
    ),
)


def _borough_names(bundle):
    return sorted(
        {
            row["borough_name"]
            for row in bundle.datasets[
                "borough_current"
            ]
        }
    )


def _apprenticeship_series(
    bundle,
    borough_name,
):
    rows = [
        row
        for row in bundle.datasets[
            "skills_supply"
        ]
        if row["borough_name"]
        == borough_name
    ]

    rows.sort(
        key=lambda row: str(
            row["time_period"]
        )
    )

    x_values = [
        academic_period(
            row["time_period"]
        )
        for row in rows
    ]

    return (
        [
            {
                "name": (
                    "Apprenticeship starts"
                ),
                "x": x_values,
                "y": [
                    row.get(
                        "apprenticeship_starts"
                    )
                    for row in rows
                ],
            },
            {
                "name": (
                    "Apprenticeship "
                    "achievements"
                ),
                "x": x_values,
                "y": [
                    row.get(
                        "apprenticeship_achievements"
                    )
                    for row in rows
                ],
            },
            {
                "name": (
                    "Apprenticeship "
                    "participation"
                ),
                "x": x_values,
                "y": [
                    row.get(
                        "apprenticeship_participation"
                    )
                    for row in rows
                ],
            },
        ],
        (
            "Academic-year apprenticeship "
            "supply and participation."
        ),
        "Apprenticeships",
    )


def _youth_series(
    bundle,
    borough_name,
):
    rows = [
        row
        for row in bundle.datasets[
            "youth_transition"
        ]
        if row["borough_name"]
        == borough_name
    ]

    rows.sort(
        key=lambda row: str(
            row["time_period"]
        )
    )

    x_values = [
        row["time_period"]
        for row in rows
    ]

    return (
        [
            {
                "name": "NEET",
                "x": x_values,
                "y": [
                    row.get(
                        "neet_percent"
                    )
                    for row in rows
                ],
            },
            {
                "name": (
                    "NEET or not known"
                ),
                "x": x_values,
                "y": [
                    row.get(
                        "neet_or_not_known_percent"
                    )
                    for row in rows
                ],
            },
            {
                "name": (
                    "Education / training"
                ),
                "x": x_values,
                "y": [
                    row.get(
                        "education_training_percent"
                    )
                    for row in rows
                ],
            },
        ],
        (
            "Calendar-year transition "
            "outcomes for young people."
        ),
        "Percent",
    )


def _labour_series(
    bundle,
    borough_name,
):
    rows = [
        row
        for row in bundle.datasets[
            "borough_opportunity"
        ]
        if (
            row["borough_name"]
            == borough_name
            and (
                row.get(
                    "employment_rate"
                )
                is not None
                or row.get(
                    "unemployment_rate"
                )
                is not None
                or row.get(
                    "economic_inactivity_rate"
                )
                is not None
            )
        )
    ]

    rows.sort(
        key=lambda row: str(
            row["date"]
        )
    )

    x_values = [
        row.get(
            "date_name"
        )
        or row["date"]
        for row in rows
    ]

    return (
        [
            {
                "name": "Employment",
                "x": x_values,
                "y": [
                    row.get(
                        "employment_rate"
                    )
                    for row in rows
                ],
            },
            {
                "name": "Unemployment",
                "x": x_values,
                "y": [
                    row.get(
                        "unemployment_rate"
                    )
                    for row in rows
                ],
            },
            {
                "name": (
                    "Economic inactivity"
                ),
                "x": x_values,
                "y": [
                    row.get(
                        "economic_inactivity_rate"
                    )
                    for row in rows
                ],
            },
        ],
        (
            "ONS APS labour-market rates. "
            "Each observation retains its "
            "original reporting period."
        ),
        "Percent",
    )


def _qualification_series(
    bundle,
    borough_name,
):
    rows = [
        row
        for row in bundle.datasets[
            "borough_opportunity"
        ]
        if (
            row["borough_name"]
            == borough_name
            and (
                row.get(
                    "rqf3_plus_rate"
                )
                is not None
                or row.get(
                    "rqf4_plus_rate"
                )
                is not None
            )
        )
    ]

    rows.sort(
        key=lambda row: str(
            row["date"]
        )
    )

    x_values = [
        row.get(
            "date_name"
        )
        or row["date"]
        for row in rows
    ]

    return (
        [
            {
                "name": "RQF3+",
                "x": x_values,
                "y": [
                    row.get(
                        "rqf3_plus_rate"
                    )
                    for row in rows
                ],
            },
            {
                "name": "RQF4+",
                "x": x_values,
                "y": [
                    row.get(
                        "rqf4_plus_rate"
                    )
                    for row in rows
                ],
            },
        ],
        (
            "Qualification attainment "
            "from the Annual Population "
            "Survey."
        ),
        "Percent",
    )


def _trend(
    bundle,
    borough_name,
    domain,
):
    if domain == "youth":
        return _youth_series(
            bundle,
            borough_name,
        )

    if domain == "labour":
        return _labour_series(
            bundle,
            borough_name,
        )

    if domain == "qualifications":
        return _qualification_series(
            bundle,
            borough_name,
        )

    return _apprenticeship_series(
        bundle,
        borough_name,
    )


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

    series, note, y_title = (
        _trend(
            bundle,
            default,
            "apprenticeships",
        )
    )

    controls = html.Div(
        className="toolbar",
        children=[
            dropdown_control(
                label="Borough",
                component_id=(
                    "trend-borough-select"
                ),
                options=[
                    {
                        "label": name,
                        "value": name,
                    }
                    for name in names
                ],
                value=default,
            ),
            dropdown_control(
                label="Indicator group",
                component_id=(
                    "trend-domain-select"
                ),
                options=[
                    {
                        "label": label,
                        "value": value,
                    }
                    for value, label
                    in DOMAINS
                ],
                value="apprenticeships",
            ),
        ],
    )

    children = [
        page_hero(
            eyebrow="Trends",
            title=(
                "How skills and opportunity "
                "are changing over time"
            ),
            description=(
                "Follow historical movement "
                "within each statistical "
                "reporting cycle without "
                "mixing incompatible periods."
            ),
        ),
        html.Div(
            className="content",
            children=[
                controls,
                html.Section(
                    className=(
                        "panel chart-card "
                        "trend-chart-panel"
                    ),
                    children=[
                        dcc.Graph(
                            id="trend-chart",
                            figure=(
                                multi_line_figure(
                                    series,
                                    y_title=(
                                        y_title
                                    ),
                                    height=520,
                                )
                            ),
                            config=PLOT_CONFIG,
                        ),
                        html.Div(
                            id="trend-note",
                            className=(
                                "chart-note"
                            ),
                            children=note,
                        ),
                    ],
                ),
            ],
        ),
    ]

    return page_shell(
        active_page="trends",
        status=store.status(),
        children=children,
    )


def register_callbacks(
    app,
    store,
):
    @app.callback(
        Output(
            "trend-chart",
            "figure",
        ),
        Output(
            "trend-note",
            "children",
        ),
        Input(
            "trend-borough-select",
            "value",
        ),
        Input(
            "trend-domain-select",
            "value",
        ),
        Input(
            "snapshot-version",
            "data",
        ),
    )
    def update_trend(
        borough_name,
        domain,
        _snapshot_version,
    ):
        bundle = store.get_bundle()

        series, note, y_title = (
            _trend(
                bundle,
                borough_name,
                domain,
            )
        )

        return (
            multi_line_figure(
                series,
                y_title=y_title,
                height=520,
            ),
            note,
        )
