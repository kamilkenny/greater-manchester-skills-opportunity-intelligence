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


    technology_stack = [
        (
            "01",
            "Data Sources",
            [
                "Department for Education",
                "Nomis Annual Population Survey",
                "Reference & MBacc mappings",
            ],
        ),
        (
            "02",
            "Data Engineering",
            [
                "Python",
                "PySpark",
                "SQL",
                "ETL / ELT",
                "Data quality validation",
            ],
        ),
        (
            "03",
            "Microsoft Fabric",
            [
                "Data Factory",
                "Lakehouse",
                "OneLake",
                "Fabric Warehouse",
                "Bronze / Silver / Gold",
            ],
        ),
        (
            "04",
            "Warehouse Modelling",
            [
                "Dimensional modelling",
                "Shared dimensions",
                "Fact tables",
                "SCD Type 2",
                "SCD Type 4",
            ],
        ),
        (
            "05",
            "Microsoft Azure",
            [
                "Private Blob Storage",
                "Azure App Service",
                "Managed Identity",
                "Two-slot publication",
            ],
        ),
        (
            "06",
            "Application",
            [
                "Plotly Dash",
                "Python",
                "Validated JSON serving",
                "Five-page intelligence interface",
            ],
        ),
        (
            "07",
            "DevOps & Automation",
            [
                "Git",
                "GitHub Actions",
                "Scheduled production refresh",
                "NO_CHANGE detection",
                "Health validation",
            ],
        ),
        (
            "08",
            "Security",
            [
                "Microsoft Entra ID",
                "OIDC federation",
                "Managed Identity",
                "Least-privilege access",
            ],
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
                    className="panel technology-detail-panel",
                    children=[
                        html.Span(
                            "Technology & Platform Stack",
                            className="eyebrow",
                        ),
                        html.H2(
                            "Engineering behind GM SkillsFlow"
                        ),
                        html.P(
                            (
                                "GM SkillsFlow is an end-to-end cloud data "
                                "platform. Public datasets are ingested and "
                                "transformed in Microsoft Fabric, modelled in "
                                "a governed analytical warehouse, exported "
                                "through a controlled serving layer and "
                                "delivered through Microsoft Azure."
                            ),
                            className="technology-detail-intro",
                        ),
                        html.Div(
                            [
                                html.Article(
                                    className="technology-detail-card",
                                    children=[
                                        html.Div(
                                            number,
                                            className=(
                                                "technology-detail-number"
                                            ),
                                        ),
                                        html.H3(title),
                                        html.Div(
                                            [
                                                html.Span(
                                                    item,
                                                    className="technology-pill",
                                                )
                                                for item in items
                                            ],
                                            className="technology-pill-row",
                                        ),
                                    ],
                                )
                                for number, title, items
                                in technology_stack
                            ],
                            className="technology-detail-grid",
                        ),
                    ],
                ),

                html.Section(
                    className="panel technology-architecture-panel",
                    children=[
                        html.Span(
                            "Platform architecture",
                            className="eyebrow",
                        ),
                        html.H2(
                            "From public source data to live intelligence"
                        ),
                        html.P(
                            (
                                "The serving application is intentionally "
                                "separated from the analytical warehouse. "
                                "Only validated analytical outputs cross "
                                "the public serving boundary."
                            ),
                            className="technology-detail-intro",
                        ),
                        html.Div(
                            className="technology-architecture-flow",
                            children=[
                                html.Div(
                                    "DfE + Nomis + Reference Data",
                                    className="technology-architecture-node",
                                ),
                                html.Div(
                                    "↓",
                                    className="technology-architecture-arrow",
                                ),
                                html.Div(
                                    "Microsoft Fabric Data Factory",
                                    className="technology-architecture-node",
                                ),
                                html.Div(
                                    "↓",
                                    className="technology-architecture-arrow",
                                ),
                                html.Div(
                                    [
                                        html.Strong(
                                            "Bronze → Silver → Gold"
                                        ),
                                        html.Span(
                                            "Preserve • Clean • Govern"
                                        ),
                                    ],
                                    className="technology-architecture-node",
                                ),
                                html.Div(
                                    "↓",
                                    className="technology-architecture-arrow",
                                ),
                                html.Div(
                                    [
                                        html.Strong(
                                            "Fabric Warehouse"
                                        ),
                                        html.Span(
                                            (
                                                "Dimensions • Facts • "
                                                "SCD Type 2 • SCD Type 4"
                                            )
                                        ),
                                    ],
                                    className="technology-architecture-node",
                                ),
                                html.Div(
                                    "↓",
                                    className="technology-architecture-arrow",
                                ),
                                html.Div(
                                    [
                                        html.Strong(
                                            "Validated JSON"
                                        ),
                                        html.Span(
                                            "Governed public serving bundle"
                                        ),
                                    ],
                                    className="technology-architecture-node",
                                ),
                                html.Div(
                                    "↓",
                                    className="technology-architecture-arrow",
                                ),
                                html.Div(
                                    [
                                        html.Strong(
                                            "Private Azure Blob Storage"
                                        ),
                                        html.Span(
                                            (
                                                "Two-slot publication • "
                                                "NO_CHANGE detection"
                                            )
                                        ),
                                    ],
                                    className="technology-architecture-node",
                                ),
                                html.Div(
                                    "↓",
                                    className="technology-architecture-arrow",
                                ),
                                html.Div(
                                    [
                                        html.Strong(
                                            "Azure App Service"
                                        ),
                                        html.Span(
                                            "Managed Identity • Plotly Dash"
                                        ),
                                    ],
                                    className="technology-architecture-node",
                                ),
                                html.Div(
                                    "↓",
                                    className="technology-architecture-arrow",
                                ),
                                html.Div(
                                    "GM SkillsFlow",
                                    className=(
                                        "technology-architecture-node "
                                        "technology-architecture-node-final"
                                    ),
                                ),
                            ],
                        ),
                    ],
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
