from dash import Input, Output, dcc, html

from dashboard.components.common import (
    dropdown_control,
    format_timestamp,
    page_shell,
    section_heading,
    stat_card,
)
from dashboard.figures import (
    PLOT_CONFIG,
    academic_period,
    borough_comparison_figure,
    labour_market_figure,
    youth_transition_figure,
)


def _definition_map(bundle):
    return {
        row["kpi_code"]: row
        for row in bundle.datasets[
            "kpi_definitions"
        ]
    }


def _indicator_options(bundle):
    definitions = bundle.datasets[
        "kpi_definitions"
    ]

    return [
        {
            "label": row["kpi_name"],
            "value": row["kpi_code"],
        }
        for row in sorted(
            definitions,
            key=lambda row: (
                row["domain_name"],
                row["kpi_name"],
            ),
        )
    ]


def layout(
    store,
):
    bundle = store.get_bundle()

    status = store.status()

    current = bundle.datasets[
        "borough_current"
    ]

    definitions = bundle.datasets[
        "kpi_definitions"
    ]

    apprenticeship_period = (
        academic_period(
            current[0].get(
                "apprenticeship_period"
            )
        )
        if current
        else "Unavailable"
    )

    gateway_count = max(
        (
            row.get(
                "mbacc_gateway_count"
            )
            or 0
        )
        for row in current
    )

    hero = html.Section(
        className="hero",
        children=[
            html.Div(
                className="hero-content",
                children=[
                    html.Span(
                        "Greater Manchester",
                        className="eyebrow",
                    ),
                    html.H1(
                        
                            "Connecting skills supply "
                            "with economic opportunity"
                        
                    ),
                    html.P(
                        
                            "Explore apprenticeships, "
                            "youth transitions, "
                            "qualifications and "
                            "labour-market outcomes "
                            "across Greater "
                            "Manchester's ten boroughs."
                        
                    ),
                    html.Div(
                        id="hero-refresh",
                        className="hero-meta",
                        children=(
                            "Public data refreshed "
                            + format_timestamp(
                                bundle.published_at_utc
                            )
                        ),
                    ),
                ],
            )
        ],
    )

    stats = html.Div(
        className="stat-grid",
        children=[
            stat_card(
                "Greater Manchester",
                str(len(current)),
                "boroughs",
            ),
            stat_card(
                "Current KPI layer",
                str(len(definitions)),
                "governed indicators",
            ),
            stat_card(
                "MBacc framework",
                str(gateway_count),
                "analytical gateways",
            ),
            stat_card(
                "Latest apprenticeships",
                apprenticeship_period,
                "academic year",
            ),
        ],
    )

    selector = dropdown_control(
        label="Indicator",
        component_id="overview-kpi",
        options=_indicator_options(
            bundle
        ),
        value="EMPLOYMENT_RATE",
    )

    comparison = html.Section(
        children=[
            section_heading(
                "Current position",
                (
                    "Compare Greater "
                    "Manchester boroughs"
                ),
                (
                    "Choose an indicator to "
                    "compare the latest available "
                    "observation for each borough."
                ),
                selector,
            ),
            html.Div(
                className="panel chart-card",
                children=[
                    dcc.Graph(
                        id=(
                            "overview-comparison-chart"
                        ),
                        config=PLOT_CONFIG,
                    ),
                    html.Div(
                        id="overview-period",
                        className="chart-note",
                    ),
                ],
            ),
        ],
    )

    supporting = html.Div(
        className="analysis-grid",
        children=[
            html.Section(
                className="panel chart-card",
                children=[
                    html.Div(
                        className="panel-heading",
                        children=[
                            html.Span(
                                "Youth transition",
                                className="eyebrow",
                            ),
                            html.H3(
                                
                                    "NEET and education "
                                    "participation"
                                
                            ),
                        ],
                    ),
                    dcc.Graph(
                        id="overview-youth-chart",
                        config=PLOT_CONFIG,
                    ),
                ],
            ),
            html.Section(
                className="panel chart-card",
                children=[
                    html.Div(
                        className="panel-heading",
                        children=[
                            html.Span(
                                "Labour market",
                                className="eyebrow",
                            ),
                            html.H3(
                                
                                    "Employment and "
                                    "inactivity"
                                
                            ),
                        ],
                    ),
                    dcc.Graph(
                        id="overview-labour-chart",
                        config=PLOT_CONFIG,
                    ),
                ],
            ),
        ],
    )


    technology = html.Section(
        className="panel technology-overview-panel",
        children=[
            html.Div(
                className="technology-overview-heading",
                children=[
                    html.Div(
                        children=[
                            html.Span(
                                "Technology behind GM SkillsFlow",
                                className="eyebrow",
                            ),
                            html.H2(
                                "Built as a data platform, not only a dashboard"
                            ),
                        ],
                    ),
                    html.P(
                        (
                            "GM SkillsFlow combines multi-source ingestion, "
                            "Microsoft Fabric data engineering, dimensional "
                            "modelling, secure Azure serving and automated "
                            "production workflows."
                        )
                    ),
                ],
            ),

            html.Div(
                className="technology-overview-grid",
                children=[
                    html.Article(
                        className="technology-overview-card",
                        children=[
                            html.Span("Microsoft Fabric"),
                            html.H3("Data platform"),
                            html.P(
                                "Data Factory • Lakehouse • OneLake • "
                                "Fabric Warehouse • Bronze / Silver / Gold"
                            ),
                        ],
                    ),
                    html.Article(
                        className="technology-overview-card",
                        children=[
                            html.Span("Data Engineering"),
                            html.H3("Engineering layer"),
                            html.P(
                                "Python • PySpark • SQL • "
                                "Multi-source ETL / ELT • Data Quality"
                            ),
                        ],
                    ),
                    html.Article(
                        className="technology-overview-card",
                        children=[
                            html.Span("Warehouse Modelling"),
                            html.H3("Historical intelligence"),
                            html.P(
                                "Dimensions • Fact Tables • "
                                "SCD Type 2 • SCD Type 4"
                            ),
                        ],
                    ),
                    html.Article(
                        className="technology-overview-card",
                        children=[
                            html.Span("Microsoft Azure"),
                            html.H3("Cloud serving"),
                            html.P(
                                "Private Blob Storage • Azure App Service • "
                                "Managed Identity"
                            ),
                        ],
                    ),
                    html.Article(
                        className="technology-overview-card",
                        children=[
                            html.Span("Automation & Security"),
                            html.H3("Production workflow"),
                            html.P(
                                "GitHub Actions • OIDC • Entra ID • "
                                "Automated Refresh • Health Checks"
                            ),
                        ],
                    ),
                ],
            ),

            html.Div(
                className="technology-flow",
                children=[
                    html.Span(
                        "DfE + Nomis + Reference Data",
                        className="technology-flow-step",
                    ),
                    html.Span(
                        "→",
                        className="technology-flow-arrow",
                    ),
                    html.Span(
                        "Microsoft Fabric",
                        className="technology-flow-step",
                    ),
                    html.Span(
                        "→",
                        className="technology-flow-arrow",
                    ),
                    html.Span(
                        "Bronze → Silver → Gold",
                        className="technology-flow-step",
                    ),
                    html.Span(
                        "→",
                        className="technology-flow-arrow",
                    ),
                    html.Span(
                        "Azure Serving",
                        className="technology-flow-step",
                    ),
                    html.Span(
                        "→",
                        className="technology-flow-arrow",
                    ),
                    html.Span(
                        "GM SkillsFlow",
                        className="technology-flow-step",
                    ),
                ],
            ),

            html.A(
                "Explore the full architecture, data sources and methodology →",
                href="/methodology",
                className="technology-more-link",
            ),
        ],
    )

    content = [
        hero,
        html.Div(
            className="content",
            children=[
                stats,
                technology,
                comparison,
                supporting,
            ],
        ),
    ]

    return page_shell(
        active_page="overview",
        status=status,
        children=content,
    )


def register_callbacks(
    app,
    store,
):
    @app.callback(
        Output(
            "overview-comparison-chart",
            "figure",
        ),
        Output(
            "overview-period",
            "children",
        ),
        Output(
            "overview-youth-chart",
            "figure",
        ),
        Output(
            "overview-labour-chart",
            "figure",
        ),
        Output(
            "hero-refresh",
            "children",
        ),
        Input(
            "overview-kpi",
            "value",
        ),
        Input(
            "snapshot-version",
            "data",
        ),
    )
    def update_overview(
        kpi_code,
        _snapshot_version,
    ):
        bundle = store.get_bundle()

        definitions = (
            _definition_map(
                bundle
            )
        )

        definition = definitions.get(
            kpi_code
        )

        if definition is None:
            definition = definitions[
                "EMPLOYMENT_RATE"
            ]

            kpi_code = (
                "EMPLOYMENT_RATE"
            )

        rows = [
            row
            for row in bundle.datasets[
                "borough_kpis"
            ]
            if row["kpi_code"]
            == kpi_code
        ]

        comparison_figure = (
            borough_comparison_figure(
                rows,
                definition,
            )
        )

        periods = sorted(
            {
                row.get(
                    "period_name"
                )
                for row in rows
                if row.get(
                    "period_name"
                )
            }
        )

        period = (
            periods[0]
            if len(periods) == 1
            else ", ".join(periods)
        )

        note = (
            f"{definition['kpi_name']}. "
            f"Reporting period: {period}."
        )

        current = bundle.datasets[
            "borough_current"
        ]

        refreshed = (
            "Public data refreshed "
            + format_timestamp(
                bundle.published_at_utc
            )
        )

        return (
            comparison_figure,
            note,
            youth_transition_figure(
                current
            ),
            labour_market_figure(
                current
            ),
            refreshed,
        )
