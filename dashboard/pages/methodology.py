from dash import html

from dashboard.components.common import (
    page_hero,
    page_shell,
)
from dashboard.figures import (
    academic_period,
)


def _method_card(
    number,
    title,
    body,
):
    return html.Article(
        className="method-card",
        children=[
            html.Div(
                number,
                className=(
                    "method-number"
                ),
            ),
            html.H3(title),
            html.P(body),
        ],
    )


def layout(
    store,
):
    bundle = store.get_bundle()

    current = bundle.datasets[
        "borough_current"
    ]

    sample = (
        current[0]
        if current
        else {}
    )

    apprenticeship_period = (
        academic_period(
            sample.get(
                "apprenticeship_period"
            )
        )
    )

    youth_period = sample.get(
        "youth_transition_period",
        "Unavailable",
    )

    labour_period = sample.get(
        "labour_market_period_name",
        "Unavailable",
    )

    qualification_period = sample.get(
        "qualification_period_name",
        "Unavailable",
    )

    metadata = bundle.datasets[
        "metadata"
    ]

    cards = [
        _method_card(
            "01",
            "Official source data",
            (
                "The analytical platform "
                "combines Department for "
                "Education statistics, ONS "
                "Nomis Annual Population "
                "Survey data and governed "
                "Greater Manchester MBacc "
                "reference data."
            ),
        ),
        _method_card(
            "02",
            "Medallion architecture",
            (
                "Raw source history is "
                "preserved in Bronze, cleaned "
                "and conformed in Silver, then "
                "served through governed Gold "
                "dimensions, facts, marts and "
                "KPI views."
            ),
        ),
        _method_card(
            "03",
            "Governed KPI layer",
            (
                "Twelve business-facing KPIs "
                "are exposed at borough level "
                "with source, unit, period and "
                "interpretation metadata."
            ),
        ),
        _method_card(
            "04",
            "MBacc pathway mapping",
            (
                "Apprenticeship subject areas "
                "are mapped transparently to "
                "the seven Greater Manchester "
                "MBacc gateways using a "
                "version-controlled analytical "
                "crosswalk."
            ),
        ),
        _method_card(
            "05",
            "Reporting-period integrity",
            (
                "Indicators retain their "
                "actual statistical reporting "
                "period rather than being "
                "presented as though all "
                "sources refer to the same "
                "date."
            ),
        ),
        _method_card(
            "06",
            "Disclosure governance",
            (
                "Suppressed, low, missing and "
                "not-applicable values are "
                "retained as governed statuses. "
                "They are never silently "
                "converted to zero."
            ),
        ),
    ]

    period_rows = [
        (
            "Apprenticeships",
            apprenticeship_period,
        ),
        (
            "Youth transition",
            youth_period,
        ),
        (
            "Labour market",
            labour_period,
        ),
        (
            "Qualifications",
            qualification_period,
        ),
    ]

    children = [
        page_hero(
            eyebrow="Data & Methodology",
            title=(
                "Transparent by design"
            ),
            description=(
                "Understand the sources, "
                "reporting periods, modelling "
                "choices and disclosure rules "
                "behind GM SkillsFlow."
            ),
        ),
        html.Div(
            className="content",
            children=[
                html.Div(
                    cards,
                    className=(
                        "methodology-grid"
                    ),
                ),
                html.Section(
                    className=(
                        "panel period-panel"
                    ),
                    children=[
                        html.Span(
                            "Reporting periods",
                            className=(
                                "eyebrow"
                            ),
                        ),
                        html.H2(
                            
                                "Current source "
                                "period profile"
                            
                        ),
                        html.P(
                            
                                "The serving layer "
                                "keeps each source's "
                                "native statistical "
                                "cycle."
                            
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Strong(
                                            label
                                        ),
                                        html.Span(
                                            value
                                        ),
                                    ],
                                    className=(
                                        "period-row"
                                    ),
                                )
                                for label, value
                                in period_rows
                            ],
                            className=(
                                "period-list"
                            ),
                        ),
                    ],
                ),
                html.Section(
                    className=(
                        "panel governance-panel"
                    ),
                    children=[
                        html.Span(
                            "Serving governance",
                            className="eyebrow",
                        ),
                        html.H2(
                            
                                "Validated public "
                                "snapshot"
                            
                        ),
                        html.P(
                            metadata.get(
                                "reporting_period_policy",
                                "",
                            )
                        ),
                        html.P(
                            metadata.get(
                                "disclosure_policy",
                                "",
                            )
                        ),
                        html.Div(
                            (
                                "Snapshot ID: "
                                f"{bundle.snapshot_id}"
                            ),
                            className=(
                                "method-meta"
                            ),
                        ),
                    ],
                ),
            ],
        ),
    ]

    return page_shell(
        active_page="methodology",
        status=store.status(),
        children=children,
    )
