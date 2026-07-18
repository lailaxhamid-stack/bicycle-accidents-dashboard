"""
Bicycle Accidents in Great Britain (1979-2018) - Interactive Dashboard
Run with: python dashboard.py
Then open the URL shown in the terminal (usually http://127.0.0.1:8050)
"""

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

# ------------------------------------------------------------------
# 1. LOAD DATA
# ------------------------------------------------------------------
DATA_PATH = "cleaned_bicycle_accidents.csv"
df = pd.read_csv(DATA_PATH, parse_dates=["Date_parsed"])

# Make sure expected helper columns exist even if not saved from notebook
if "Year" not in df.columns:
    df["Year"] = df["Date_parsed"].dt.year
if "Month" not in df.columns:
    df["Month"] = df["Date_parsed"].dt.month

MIN_YEAR, MAX_YEAR = int(df["Year"].min()), int(df["Year"].max())
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

SEVERITY_ORDER = ["Slight", "Serious", "Fatal"]
SEVERITY_COLORS = {"Slight": "#4C9AFF", "Serious": "#FFAB00", "Fatal": "#DE350B"}

# ------------------------------------------------------------------
# 2. APP SETUP
# ------------------------------------------------------------------
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "GB Bicycle Accidents Dashboard (1979-2018)"

# ------------------------------------------------------------------
# 3. LAYOUT
# ------------------------------------------------------------------
filters = dbc.Card(
    dbc.CardBody([
        html.H5("Filters", className="card-title"),

        html.Label("Year Range"),
        dcc.RangeSlider(
            id="year-slider",
            min=MIN_YEAR, max=MAX_YEAR, value=[MIN_YEAR, MAX_YEAR],
            marks={y: str(y) for y in range(MIN_YEAR, MAX_YEAR + 1, 5)},
            tooltip={"placement": "bottom", "always_visible": False},
        ),
        html.Br(),

        html.Label("Gender"),
        dcc.Checklist(
            id="gender-filter",
            options=[{"label": g, "value": g} for g in sorted(df["Gender"].dropna().unique())],
            value=sorted(df["Gender"].dropna().unique()),
            inline=True,
            inputStyle={"margin-right": "5px", "margin-left": "10px"},
        ),
        html.Br(),

        html.Label("Severity"),
        dcc.Checklist(
            id="severity-filter",
            options=[{"label": s, "value": s} for s in SEVERITY_ORDER],
            value=SEVERITY_ORDER,
            inline=True,
            inputStyle={"margin-right": "5px", "margin-left": "10px"},
        ),
        html.Br(),

        html.Label("Road Type"),
        dcc.Dropdown(
            id="roadtype-filter",
            options=[{"label": r, "value": r} for r in sorted(df["Road_type"].dropna().unique())],
            value=sorted(df["Road_type"].dropna().unique()),
            multi=True,
        ),
    ]),
    className="mb-4",
)

kpi_row = dbc.Row(id="kpi-row", className="mb-4")

trend_row = dbc.Row([
    dbc.Col(dcc.Graph(id="yearly-trend"), width=8),
    dbc.Col(dcc.Graph(id="monthly-pattern"), width=4),
], className="mb-4")

conditions_row = dbc.Row([
    dbc.Col(dcc.Graph(id="road-weather-severity"), width=6),
    dbc.Col(dcc.Graph(id="roadtype-count"), width=6),
], className="mb-4")

demo_row = dbc.Row([
    dbc.Col(dcc.Graph(id="age-gender-severity"), width=8),
    dbc.Col(dcc.Graph(id="gender-pie"), width=4),
], className="mb-4")

speed_row = dbc.Row([
    dbc.Col(dcc.Graph(id="speed-severity"), width=6),
    dbc.Col(dcc.Graph(id="light-severity"), width=6),
], className="mb-4")

app.layout = dbc.Container([
    html.H1("Bicycle Accidents in Great Britain, 1979-2018", className="mt-4"),
    html.P("Interactive exploration of 827,861 recorded bicycle accidents. "
           "Use the filters below to drill into specific years, demographics, and conditions.",
           className="text-muted"),
    html.Hr(),

    dbc.Row([
        dbc.Col(filters, width=3),
        dbc.Col([
            kpi_row,
            trend_row,
            conditions_row,
            demo_row,
            speed_row,
        ], width=9),
    ]),

    html.Hr(),
    html.P("Data source: Kaggle - Bicycle Accidents in Great Britain 1979-2018",
           className="text-muted text-center small"),
], fluid=True)


# ------------------------------------------------------------------
# 4. HELPER: apply filters
# ------------------------------------------------------------------
def filter_df(year_range, genders, severities, road_types):
    d = df[
        (df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1]) &
        (df["Gender"].isin(genders)) &
        (df["Severity"].isin(severities)) &
        (df["Road_type"].isin(road_types))
    ]
    return d


# ------------------------------------------------------------------
# 5. CALLBACKS
# ------------------------------------------------------------------
@app.callback(
    Output("kpi-row", "children"),
    Input("year-slider", "value"),
    Input("gender-filter", "value"),
    Input("severity-filter", "value"),
    Input("roadtype-filter", "value"),
)
def update_kpis(year_range, genders, severities, road_types):
    d = filter_df(year_range, genders, severities, road_types)

    total = len(d)
    fatal = (d["Severity"] == "Fatal").sum()
    fatal_pct = round(fatal / total * 100, 2) if total else 0
    avg_per_year = round(total / max(1, (year_range[1] - year_range[0] + 1)))

    def card(title, value, color):
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.H6(title, className="text-muted"),
            html.H3(value, style={"color": color}),
        ])), width=3)

    return [
        card("Total Accidents (filtered)", f"{total:,}", "#2C3E50"),
        card("Fatal Accidents", f"{fatal:,}", "#DE350B"),
        card("Fatal Rate", f"{fatal_pct}%", "#DE350B"),
        card("Avg. Accidents / Year", f"{avg_per_year:,}", "#2C3E50"),
    ]


@app.callback(
    Output("yearly-trend", "figure"),
    Input("year-slider", "value"),
    Input("gender-filter", "value"),
    Input("severity-filter", "value"),
    Input("roadtype-filter", "value"),
)
def update_yearly_trend(year_range, genders, severities, road_types):
    d = filter_df(year_range, genders, severities, road_types)
    yearly = d.groupby("Year").size().reset_index(name="Accidents")
    fig = px.line(yearly, x="Year", y="Accidents", markers=True,
                  title="Accidents Over Time")
    fig.update_layout(margin=dict(t=40, b=20))
    return fig


@app.callback(
    Output("monthly-pattern", "figure"),
    Input("year-slider", "value"),
    Input("gender-filter", "value"),
    Input("severity-filter", "value"),
    Input("roadtype-filter", "value"),
)
def update_monthly(year_range, genders, severities, road_types):
    d = filter_df(year_range, genders, severities, road_types)
    monthly = d.groupby("Month").size().reindex(range(1, 13), fill_value=0)
    fig = px.bar(x=MONTH_NAMES, y=monthly.values, title="Seasonal Pattern (All Years Combined)",
                 labels={"x": "Month", "y": "Accidents"})
    fig.update_layout(margin=dict(t=40, b=20))
    return fig


@app.callback(
    Output("road-weather-severity", "figure"),
    Input("year-slider", "value"),
    Input("gender-filter", "value"),
    Input("severity-filter", "value"),
    Input("roadtype-filter", "value"),
)
def update_weather(year_range, genders, severities, road_types):
    d = filter_df(year_range, genders, severities, road_types)
    rate = d.groupby("Weather_conditions")["Severity"].apply(
        lambda x: (x.isin(["Serious", "Fatal"])).mean() * 100
    ).round(2).sort_values(ascending=False)
    fig = px.bar(x=rate.values, y=rate.index, orientation="h",
                 title="Serious/Fatal Rate (%) by Weather Condition",
                 labels={"x": "Serious/Fatal Rate (%)", "y": ""})
    fig.update_layout(margin=dict(t=40, b=20))
    return fig


@app.callback(
    Output("roadtype-count", "figure"),
    Input("year-slider", "value"),
    Input("gender-filter", "value"),
    Input("severity-filter", "value"),
    Input("roadtype-filter", "value"),
)
def update_roadtype(year_range, genders, severities, road_types):
    d = filter_df(year_range, genders, severities, road_types)
    counts = d["Road_type"].value_counts()
    fig = px.bar(x=counts.values, y=counts.index, orientation="h",
                 title="Accident Count by Road Type",
                 labels={"x": "Accidents", "y": ""})
    fig.update_layout(margin=dict(t=40, b=20))
    return fig


@app.callback(
    Output("age-gender-severity", "figure"),
    Input("year-slider", "value"),
    Input("gender-filter", "value"),
    Input("severity-filter", "value"),
    Input("roadtype-filter", "value"),
)
def update_age_gender(year_range, genders, severities, road_types):
    d = filter_df(year_range, genders, severities, road_types)
    age_order = sorted(d["Age_Grp"].dropna().unique(), key=lambda x: int(str(x).split()[0]))
    fig = px.histogram(d, x="Age_Grp", color="Severity", barmode="group",
                        category_orders={"Age_Grp": age_order, "Severity": SEVERITY_ORDER},
                        color_discrete_map=SEVERITY_COLORS,
                        title="Severity by Age Group")
    fig.update_layout(margin=dict(t=40, b=20), xaxis_title="Age Group", yaxis_title="Count")
    return fig


@app.callback(
    Output("gender-pie", "figure"),
    Input("year-slider", "value"),
    Input("gender-filter", "value"),
    Input("severity-filter", "value"),
    Input("roadtype-filter", "value"),
)
def update_gender_pie(year_range, genders, severities, road_types):
    d = filter_df(year_range, genders, severities, road_types)
    counts = d["Gender"].value_counts()
    fig = px.pie(values=counts.values, names=counts.index, title="Accidents by Gender")
    fig.update_layout(margin=dict(t=40, b=20))
    return fig


@app.callback(
    Output("speed-severity", "figure"),
    Input("year-slider", "value"),
    Input("gender-filter", "value"),
    Input("severity-filter", "value"),
    Input("roadtype-filter", "value"),
)
def update_speed(year_range, genders, severities, road_types):
    d = filter_df(year_range, genders, severities, road_types)
    rate = d.groupby("Speed_limit")["Severity"].apply(
        lambda x: (x.isin(["Serious", "Fatal"])).mean() * 100
    ).round(2).sort_index()
    fig = px.bar(x=rate.index.astype(str), y=rate.values,
                 title="Serious/Fatal Rate (%) by Speed Limit",
                 labels={"x": "Speed Limit (mph)", "y": "Serious/Fatal Rate (%)"})
    fig.update_layout(margin=dict(t=40, b=20))
    return fig


@app.callback(
    Output("light-severity", "figure"),
    Input("year-slider", "value"),
    Input("gender-filter", "value"),
    Input("severity-filter", "value"),
    Input("roadtype-filter", "value"),
)
def update_light(year_range, genders, severities, road_types):
    d = filter_df(year_range, genders, severities, road_types)
    rate = d.groupby("Light_conditions")["Severity"].apply(
        lambda x: (x.isin(["Serious", "Fatal"])).mean() * 100
    ).round(2).sort_values(ascending=False)
    fig = px.bar(x=rate.values, y=rate.index, orientation="h",
                 title="Serious/Fatal Rate (%) by Light Condition",
                 labels={"x": "Serious/Fatal Rate (%)", "y": ""})
    fig.update_layout(margin=dict(t=40, b=20))
    return fig


# ------------------------------------------------------------------
# 6. RUN
# ------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
