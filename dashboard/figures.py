from typing import Any

import plotly.graph_objects as go

BLUE = "#0f80bd"
CYAN = "#00a6c7"
TEAL = "#1d8f78"
AMBER = "#d68c1f"
RED = "#c85151"
PURPLE = "#7062d9"
INK = "#152536"
MUTED = "#667788"
GRID = "#e7edf2"


PLOT_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}


def format_value(
    value,
    unit: str | None = None,
) -> str:
    if value is None:
        return "Not available"

    if unit == "percent":
        return f"{float(value):.1f}%"

    if unit in {
        "count",
        "number",
    }:
        return f"{float(value):,.0f}"

    number = float(value)

    if number.is_integer():
        return f"{number:,.0f}"

    return f"{number:,.1f}"


def academic_period(
    value: str | None,
) -> str:
    if not value:
        return "Unavailable"

    value = str(value)

    if (
        len(value) == 6
        and value.isdigit()
    ):
        return (
            f"{value[:4]}/"
            f"{value[4:]}"
        )

    return value


def base_layout(
    *,
    height: int = 430,
):
    return dict(
        height=height,
        margin=dict(
            l=30,
            r=25,
            t=25,
            b=45,
        ),
        paper_bgcolor=(
            "rgba(0,0,0,0)"
        ),
        plot_bgcolor=(
            "rgba(0,0,0,0)"
        ),
        font=dict(
            family=(
                "Inter, Segoe UI, sans-serif"
            ),
            color=INK,
            size=12,
        ),
        hoverlabel=dict(
            bgcolor="white",
            font=dict(
                color=INK,
            ),
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="left",
            x=0,
        ),
    )


def empty_figure(
    message: str,
    *,
    height: int = 430,
):
    figure = go.Figure()

    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(
            color=MUTED,
            size=14,
        ),
    )

    figure.update_layout(
        **base_layout(
            height=height
        )
    )

    figure.update_xaxes(
        visible=False
    )

    figure.update_yaxes(
        visible=False
    )

    return figure


def borough_comparison_figure(
    rows: list[dict[str, Any]],
    definition: dict[str, Any],
):
    rows = [
        row
        for row in rows
        if row.get("kpi_value")
        is not None
    ]

    rows.sort(
        key=lambda row: float(
            row["kpi_value"]
        ),
        reverse=True,
    )

    if not rows:
        return empty_figure(
            "No reportable values available."
        )

    unit = definition.get(
        "unit_name"
    )

    values = [
        float(row["kpi_value"])
        for row in rows
    ]

    labels = [
        format_value(
            value,
            unit,
        )
        for value in values
    ]

    figure = go.Figure(
        go.Bar(
            x=values,
            y=[
                row["borough_name"]
                for row in rows
            ],
            orientation="h",
            marker_color=BLUE,
            text=labels,
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "%{text}"
                "<extra></extra>"
            ),
        )
    )

    layout = base_layout(
        height=475
    )

    layout.update(
        showlegend=False,
    )

    figure.update_layout(
        **layout
    )

    figure.update_xaxes(
        title=(
            "Percent"
            if unit == "percent"
            else definition.get(
                "unit_name",
                "",
            ).title()
        ),
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
    )

    figure.update_yaxes(
        title=None,
        autorange="reversed",
        showgrid=False,
    )

    return figure


def youth_transition_figure(
    current_rows: list[
        dict[str, Any]
    ],
):
    rows = [
        row
        for row in current_rows
        if (
            row.get(
                "neet_percent"
            )
            is not None
            and row.get(
                "education_training_percent"
            )
            is not None
        )
    ]

    rows.sort(
        key=lambda row: float(
            row[
                "education_training_percent"
            ]
        ),
        reverse=True,
    )

    names = [
        row["borough_name"]
        for row in rows
    ]

    figure = go.Figure()

    figure.add_bar(
        name="NEET",
        x=names,
        y=[
            row["neet_percent"]
            for row in rows
        ],
        marker_color=RED,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "NEET: %{y:.1f}%"
            "<extra></extra>"
        ),
    )

    figure.add_bar(
        name="Education / training",
        x=names,
        y=[
            row[
                "education_training_percent"
            ]
            for row in rows
        ],
        marker_color=TEAL,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Education / training: "
            "%{y:.1f}%"
            "<extra></extra>"
        ),
    )

    layout = base_layout(
        height=420
    )

    layout.update(
        barmode="group"
    )

    figure.update_layout(
        **layout
    )

    figure.update_yaxes(
        title="Percent",
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
    )

    figure.update_xaxes(
        title=None,
        tickangle=-35,
        showgrid=False,
    )

    return figure


def labour_market_figure(
    current_rows: list[
        dict[str, Any]
    ],
):
    rows = [
        row
        for row in current_rows
        if (
            row.get(
                "employment_rate"
            )
            is not None
            and row.get(
                "economic_inactivity_rate"
            )
            is not None
        )
    ]

    rows.sort(
        key=lambda row: float(
            row["employment_rate"]
        ),
        reverse=True,
    )

    names = [
        row["borough_name"]
        for row in rows
    ]

    figure = go.Figure()

    figure.add_bar(
        name="Employment",
        x=names,
        y=[
            row["employment_rate"]
            for row in rows
        ],
        marker_color=BLUE,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Employment: %{y:.1f}%"
            "<extra></extra>"
        ),
    )

    figure.add_bar(
        name="Economic inactivity",
        x=names,
        y=[
            row[
                "economic_inactivity_rate"
            ]
            for row in rows
        ],
        marker_color=AMBER,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Economic inactivity: "
            "%{y:.1f}%"
            "<extra></extra>"
        ),
    )

    layout = base_layout(
        height=420
    )

    layout.update(
        barmode="group"
    )

    figure.update_layout(
        **layout
    )

    figure.update_yaxes(
        title="Percent",
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
    )

    figure.update_xaxes(
        title=None,
        tickangle=-35,
        showgrid=False,
    )

    return figure


def borough_labour_figure(
    row: dict[str, Any] | None,
):
    if not row:
        return empty_figure(
            "No labour-market data available."
        )

    labels = (
        "Employment",
        "Unemployment",
        "Economic inactivity",
    )

    values = (
        row.get("employment_rate"),
        row.get("unemployment_rate"),
        row.get(
            "economic_inactivity_rate"
        ),
    )

    colours = (
        BLUE,
        RED,
        AMBER,
    )

    figure = go.Figure(
        go.Bar(
            x=list(labels),
            y=list(values),
            marker_color=list(colours),
            text=[
                (
                    f"{float(value):.1f}%"
                    if value is not None
                    else ""
                )
                for value in values
            ],
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "%{y:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    layout = base_layout(
        height=390
    )

    layout.update(
        showlegend=False,
    )

    figure.update_layout(
        **layout
    )

    figure.update_yaxes(
        title="Percent",
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        rangemode="tozero",
    )

    figure.update_xaxes(
        title=None,
        showgrid=False,
    )

    return figure


def borough_qualification_figure(
    row: dict[str, Any] | None,
):
    if not row:
        return empty_figure(
            "No qualification data available."
        )

    labels = (
        "RQF3+",
        "RQF4+",
    )

    values = (
        row.get("rqf3_plus_rate"),
        row.get("rqf4_plus_rate"),
    )

    figure = go.Figure(
        go.Bar(
            x=list(labels),
            y=list(values),
            marker_color=[
                CYAN,
                TEAL,
            ],
            text=[
                (
                    f"{float(value):.1f}%"
                    if value is not None
                    else ""
                )
                for value in values
            ],
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "%{y:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    layout = base_layout(
        height=390
    )

    layout.update(
        showlegend=False,
    )

    figure.update_layout(
        **layout
    )

    figure.update_yaxes(
        title="Percent",
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        rangemode="tozero",
    )

    figure.update_xaxes(
        title=None,
        showgrid=False,
    )

    return figure


def mbacc_pathway_figure(
    rows: list[dict[str, Any]],
):
    rows = sorted(
        rows,
        key=lambda row: row[
            "gateway_code"
        ],
        reverse=True,
    )

    if not rows:
        return empty_figure(
            "No MBacc pathway data available.",
            height=520,
        )

    gateway_names = [
        row["gateway_name"]
        for row in rows
    ]

    starts = [
        row.get(
            "apprenticeship_starts"
        )
        for row in rows
    ]

    achievements = [
        row.get(
            "apprenticeship_achievements"
        )
        for row in rows
    ]

    starts_status = [
        row.get(
            "apprenticeship_starts_status",
            "unavailable",
        )
        for row in rows
    ]

    achievement_status = [
        row.get(
            "apprenticeship_achievements_status",
            "unavailable",
        )
        for row in rows
    ]

    figure = go.Figure()

    figure.add_bar(
        name="Starts",
        x=starts,
        y=gateway_names,
        orientation="h",
        marker_color=TEAL,
        customdata=starts_status,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Starts: %{x:,.0f}<br>"
            "Status: %{customdata}"
            "<extra></extra>"
        ),
    )

    figure.add_bar(
        name="Achievements",
        x=achievements,
        y=gateway_names,
        orientation="h",
        marker_color=BLUE,
        customdata=achievement_status,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Achievements: %{x:,.0f}<br>"
            "Status: %{customdata}"
            "<extra></extra>"
        ),
    )

    layout = base_layout(
        height=540
    )

    layout.update(
        barmode="group",
    )

    figure.update_layout(
        **layout
    )

    figure.update_xaxes(
        title="Apprenticeships",
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
    )

    figure.update_yaxes(
        title=None,
        showgrid=False,
        automargin=True,
    )

    return figure


def multi_line_figure(
    series: list[dict[str, Any]],
    *,
    y_title: str,
    height: int = 500,
):
    if not series:
        return empty_figure(
            "No historical data available.",
            height=height,
        )

    figure = go.Figure()

    colours = (
        BLUE,
        TEAL,
        AMBER,
        PURPLE,
        RED,
        CYAN,
    )

    for index, item in enumerate(series):
        x_values = item.get("x", [])
        y_values = item.get("y", [])

        figure.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="lines+markers",
                name=item["name"],
                connectgaps=False,
                line=dict(
                    width=3,
                    color=colours[
                        index
                        % len(colours)
                    ],
                ),
                marker=dict(
                    size=7,
                ),
                hovertemplate=(
                    "<b>%{fullData.name}</b>"
                    "<br>%{x}"
                    "<br>%{y:.1f}"
                    "<extra></extra>"
                ),
            )
        )

    layout = base_layout(
        height=height
    )

    layout.update(
        hovermode="x unified",
    )

    figure.update_layout(
        **layout
    )

    figure.update_xaxes(
        title=None,
        showgrid=False,
    )

    figure.update_yaxes(
        title=y_title,
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
    )

    return figure
