from dash import Input, Output, dcc, html

from dashboard.components.common import (
    dropdown_control,
    page_hero,
    page_shell,
)
from dashboard.figures import (
    PLOT_CONFIG,
    academic_period,
    mbacc_pathway_figure,
)


def _borough_names(bundle):
    return sorted(
        {
            row["borough_name"]
            for row in bundle.datasets[
                "mbacc_pathways"
            ]
        }
    )


def _rows(
    bundle,
    borough_name,
):
    return [
        row
        for row in bundle.datasets[
            "mbacc_pathways"
        ]
        if (
            row["borough_name"]
            == borough_name
            and row.get(
                "is_latest_period",
                1,
            )
            == 1
        )
    ]


def _disclosure_note(
    rows,
):
    starts_suppressed = [
        row
        for row in rows
        if row.get(
            "apprenticeship_starts"
        )
        is None
    ]

    achievements_suppressed = [
        row
        for row in rows
        if row.get(
            "apprenticeship_achievements"
        )
        is None
    ]

    if (
        starts_suppressed
        or achievements_suppressed
    ):
        return (
            "Suppressed or partially "
            "reportable gateway aggregates "
            "remain unavailable rather than "
            "being reconstructed."
        )

    return (
        "All currently displayed gateway "
        "aggregates are reportable."
    )


def _period_note(
    rows,
):
    if not rows:
        return ""

    period = academic_period(
        rows[0].get(
            "time_period"
        )
    )

    return (
        f"Reporting period: {period}."
    )


def layout(
    store,
):
    bundle = store.get_bundle()

    names = _borough_names(
        bundle
    )

    default = (
        "Stockport"
        if "Stockport" in names
        else (
            "Manchester"
            if "Manchester" in names
            else names[0]
        )
    )

    rows = _rows(
        bundle,
        default,
    )

    selector = dropdown_control(
        label="Borough",
        component_id=(
            "pathway-borough-select"
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
            eyebrow="MBacc Pathways",
            title=(
                "Apprenticeship supply across "
                "Greater Manchester's "
                "MBacc gateways"
            ),
            description=(
                "Explore apprenticeship starts "
                "and achievements using the "
                "governed analytical "
                "SSA-to-MBacc mapping."
            ),
        ),
        html.Div(
            className="content",
            children=[
                html.Div(
                    selector,
                    className="toolbar",
                ),
                html.Section(
                    className=(
                        "panel chart-card "
                        "mbacc-chart-panel"
                    ),
                    children=[
                        dcc.Graph(
                            id="pathway-chart",
                            figure=(
                                mbacc_pathway_figure(
                                    rows
                                )
                            ),
                            config=PLOT_CONFIG,
                        ),
                        html.Div(
                            id="pathway-period-note",
                            className=(
                                "chart-note"
                            ),
                            children=(
                                _period_note(
                                    rows
                                )
                            ),
                        ),
                        html.Div(
                            id=(
                                "pathway-"
                                "disclosure-note"
                            ),
                            className=(
                                "chart-note "
                                "disclosure-note"
                            ),
                            children=(
                                _disclosure_note(
                                    rows
                                )
                            ),
                        ),
                    ],
                ),
            ],
        ),
    ]

    return page_shell(
        active_page="mbacc",
        status=store.status(),
        children=children,
    )


def register_callbacks(
    app,
    store,
):
    @app.callback(
        Output(
            "pathway-chart",
            "figure",
        ),
        Output(
            "pathway-period-note",
            "children",
        ),
        Output(
            "pathway-disclosure-note",
            "children",
        ),
        Input(
            "pathway-borough-select",
            "value",
        ),
        Input(
            "snapshot-version",
            "data",
        ),
    )
    def update_pathways(
        borough_name,
        _snapshot_version,
    ):
        bundle = store.get_bundle()

        rows = _rows(
            bundle,
            borough_name,
        )

        return (
            mbacc_pathway_figure(
                rows
            ),
            _period_note(
                rows
            ),
            _disclosure_note(
                rows
            ),
        )
