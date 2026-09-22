"""
CDC Provisional Natality Dashboard (2025)
=========================================
An interactive Streamlit application designed for undergraduate business analytics students
to explore geographic, monthly, and sex-based patterns in provisional 2025 U.S. birth counts.

Author: Business Analytics Development Team
Technologies: Python, Streamlit, pandas, Plotly, openpyxl
"""

from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==============================================================================
# 1. CONSTANTS & CONFIGURATION
# ==============================================================================

# Reliable 2-letter postal abbreviation mapping for all 50 states + DC
STATE_TO_ABBR: Dict[str, str] = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME",
    "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM",
    "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}

# Strict chronological calendar month ordering
MONTH_ORDER: List[str] = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

REQUIRED_COLUMNS: List[str] = [
    "State of Residence", "Month", "Month Code", "Year Code", "Sex of Infant", "Births"
]


# ==============================================================================
# 2. DATA INGESTION & VALIDATION
# ==============================================================================

@st.cache_data(show_spinner="Loading provisional natality dataset...")
def load_data() -> pd.DataFrame:
    """
    Loads and cleans the provisional natality dataset from Excel using openpyxl.
    Uses relative path resolution compatible with both local runs and Streamlit Cloud.
    """
    # Dynamic path resolution ensures portability
    data_path = Path(__file__).parent / "data" / "Provisional_Natality_2025_CDC.xlsx"

    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at expected location: {data_path.resolve()}.\n"
            "Please ensure 'Provisional_Natality_2025_CDC.xlsx' is inside the 'data/' folder."
        )

    # Read the designated worksheet
    df = pd.read_excel(
        data_path,
        sheet_name="Provisional Natality, 2023 thro",
        engine="openpyxl"
    )

    # Validate structural integrity
    validate_data(df)

    # Standardize column data types
    df["State of Residence"] = df["State of Residence"].astype(str).str.strip()
    df["Month"] = pd.Categorical(df["Month"].astype(str).str.strip(), categories=MONTH_ORDER, ordered=True)
    df["Month Code"] = pd.to_numeric(df["Month Code"], errors="raise").astype(int)
    df["Year Code"] = pd.to_numeric(df["Year Code"], errors="raise").astype(int)
    df["Sex of Infant"] = df["Sex of Infant"].astype(str).str.strip()
    df["Births"] = pd.to_numeric(df["Births"], errors="raise").astype(int)

    # Add state abbreviation column for mapping
    df["State Abbr"] = df["State of Residence"].map(STATE_TO_ABBR)

    return df


def validate_data(df: pd.DataFrame) -> None:
    """
    Conducts sanity checks on the raw dataframe to ensure data governance and quality.
    """
    # Check for missing required columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset is missing required columns: {missing_cols}")

    # Check for non-empty dataframe
    if len(df) == 0:
        raise ValueError("The loaded dataset contains zero rows.")

    # Check for missing values in core fields
    null_counts = df[REQUIRED_COLUMNS].isnull().sum()
    if null_counts.sum() > 0:
        raise ValueError(f"Unexpected null values detected in raw data:\n{null_counts[null_counts > 0]}")

    # Verify that all births are non-negative
    if (df["Births"] < 0).any():
        raise ValueError("Negative birth counts found in dataset.")


# ==============================================================================
# 3. UI: HEADER & EDUCATIONAL CALLOUTS
# ==============================================================================

def render_header() -> None:
    """
    Renders dashboard title, CDC source attribution, provisional status warning,
    and the essential 'counts vs. birth rates' business analytics disclaimer.
    """
    st.title("👶 CDC Provisional Natality Dashboard (2025)")
    st.markdown(
        "**Exploratory Analytics Platform for Undergraduate Business Analytics Students**  \n"
        "Analyze geographic distributions, seasonal fluctuations, and sex-based patterns in U.S. live birth counts."
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.info(
            "📌 **Data Source & Status:**  \n"
            "• **Source:** Centers for Disease Control and Prevention (CDC) / NCHS — *Provisional Natality Data (2025)*  \n"
            "• **Notice:** These figures are **provisional** and subject to continuous reporting updates."
        )

    with col2:
        st.warning(
            "⚠️ **Analytical Guidance: Counts vs. Birth Rates:**  \n"
            "All metrics shown are **raw birth counts** (total number of live births), **not standardized birth rates**. "
            "Because this dataset does not contain population denominators, differences between states primarily reflect "
            "overall population scale rather than fertility propensity."
        )

    st.markdown("---")


# ==============================================================================
# 4. UI: SIDEBAR FILTERS & INTERACTION CONTROLS
# ==============================================================================

def render_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs sidebar controls for Geography, Month, and Infant Sex,
    with Select All, Clear, and Reset Filters functionality.
    """
    all_states: List[str] = sorted(df["State of Residence"].unique().tolist())
    all_months: List[str] = [m for m in MONTH_ORDER if m in df["Month"].cat.categories]
    all_sexes: List[str] = ["All (Female & Male)", "Female", "Male"]

    # Initialize session state for filters if not present
    if "states_multiselect" not in st.session_state:
        st.session_state["states_multiselect"] = all_states
    if "months_multiselect" not in st.session_state:
        st.session_state["months_multiselect"] = all_months
    if "sex_radio" not in st.session_state:
        st.session_state["sex_radio"] = "All (Female & Male)"

    st.sidebar.header("🔍 Filter Selection")

    # Reset Filters Button
    if st.sidebar.button("🔄 Reset All Filters", use_container_width=True, type="secondary"):
        st.session_state["states_multiselect"] = all_states
        st.session_state["months_multiselect"] = all_months
        st.session_state["sex_radio"] = "All (Female & Male)"
        st.rerun()

    st.sidebar.markdown("---")

    # 1. Geography Filter
    st.sidebar.subheader("📍 Geographies")
    col_st1, col_st2 = st.sidebar.columns(2)
    if col_st1.button("Select All", key="btn_all_states", use_container_width=True):
        st.session_state["states_multiselect"] = all_states
        st.rerun()
    if col_st2.button("Clear", key="btn_clear_states", use_container_width=True):
        st.session_state["states_multiselect"] = []
        st.rerun()

    selected_states = st.sidebar.multiselect(
        "Select States / Geographies:",
        options=all_states,
        key="states_multiselect"
    )

    # 2. Month Filter
    st.sidebar.subheader("📅 Calendar Months")
    col_m1, col_m2 = st.sidebar.columns(2)
    if col_m1.button("Select All", key="btn_all_months", use_container_width=True):
        st.session_state["months_multiselect"] = all_months
        st.rerun()
    if col_m2.button("Clear", key="btn_clear_months", use_container_width=True):
        st.session_state["months_multiselect"] = []
        st.rerun()

    selected_months = st.sidebar.multiselect(
        "Select Months (Chronological):",
        options=all_months,
        key="months_multiselect"
    )

    # 3. Infant Sex Filter
    st.sidebar.subheader("👶 Infant Biological Sex")
    selected_sex = st.sidebar.radio(
        "Filter by Sex of Infant:",
        options=all_sexes,
        key="sex_radio"
    )

    # Apply filters to dataframe
    filtered_df = df[
        (df["State of Residence"].isin(selected_states)) &
        (df["Month"].isin(selected_months))
    ].copy()

    if selected_sex != "All (Female & Male)":
        filtered_df = filtered_df[filtered_df["Sex of Infant"] == selected_sex]

    # Active Filters Summary in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Active Filter Summary")
    pct_total = (len(filtered_df) / len(df) * 100) if len(df) > 0 else 0
    st.sidebar.markdown(
        f"• **Geographies:** {len(selected_states)} of {len(all_states)}  \n"
        f"• **Months:** {len(selected_months)} of {len(all_months)}  \n"
        f"• **Sex Filter:** `{selected_sex}`  \n"
        f"• **Observations:** {len(filtered_df):,} / {len(df):,} ({pct_total:.1f}% of data)"
    )

    return filtered_df


# ==============================================================================
# 5. UI: KPI CARDS
# ==============================================================================

def render_kpi_cards(filtered_df: pd.DataFrame, total_rows_original: int) -> None:
    """
    Renders 5 top-level KPI cards with thousands separators and safe handling
    for empty filter combinations.
    """
    if len(filtered_df) == 0:
        st.warning(
            "⚠️ **No observations match the current filter selection.** "
            "Please select at least one geography and one month in the sidebar, or click 'Reset All Filters'."
        )
        return

    # KPI 1: Total Births
    total_births = int(filtered_df["Births"].sum())

    # KPI 2: Number of Selected Geographies
    selected_geos_count = filtered_df["State of Residence"].nunique()

    # KPI 3: Average Births per Selected Month
    selected_months_count = filtered_df["Month"].nunique()
    avg_births_per_month = total_births / selected_months_count if selected_months_count > 0 else 0

    # KPI 4: Geography with the Highest Birth Count in Selection
    geo_totals = filtered_df.groupby("State of Residence", as_index=False)["Births"].sum()
    top_geo_row = geo_totals.sort_values(by="Births", ascending=False).iloc[0]
    top_geo_name = top_geo_row["State of Residence"]
    top_geo_val = int(top_geo_row["Births"])

    # KPI 5: Month with the Highest Birth Count in Selection
    month_totals = filtered_df.groupby("Month", as_index=False, observed=True)["Births"].sum()
    top_month_row = month_totals.sort_values(by="Births", ascending=False).iloc[0]
    top_month_name = str(top_month_row["Month"])
    top_month_val = int(top_month_row["Births"])

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Selected Births", f"{total_births:,}")
    with col2:
        st.metric("Geographies Selected", f"{selected_geos_count} of 51")
    with col3:
        st.metric("Avg Births / Month", f"{avg_births_per_month:,.0f}")
    with col4:
        st.metric("Top Geography", f"{top_geo_name}", delta=f"{top_geo_val:,} births", delta_color="off")
    with col5:
        st.metric("Peak Month", f"{top_month_name}", delta=f"{top_month_val:,} births", delta_color="off")

    st.markdown("---")


# ==============================================================================
# 6. TAB 1: OVERVIEW
# ==============================================================================

def render_overview_tab(filtered_df: pd.DataFrame) -> None:
    """
    Renders high-level monthly trajectory, sex distribution breakdown,
    and a top-5 vs bottom-5 geography comparison.
    """
    st.subheader("📈 High-Level Birth Volume & Distribution Overview")

    if len(filtered_df) == 0:
        st.info("Select filters to view the overview charts.")
        return

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("#### Chronological Monthly Birth Trend")
        # Aggregate births chronologically by month
        monthly_trend = (
            filtered_df.groupby("Month", as_index=False, observed=True)["Births"]
            .sum()
        )
        fig_trend = px.line(
            monthly_trend,
            x="Month",
            y="Births",
            markers=True,
            title="Total Recorded Live Births by Month (2025)",
            labels={"Births": "Total Births", "Month": "Calendar Month"},
            color_discrete_sequence=["#1f77b4"]
        )
        fig_trend.update_layout(
            hovermode="x unified",
            yaxis=dict(rangemode="tozero", tickformat=","),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        fig_trend.update_traces(
            hovertemplate="<b>%{x}</b><br>Recorded Births: %{y:,}<extra></extra>",
            line=dict(width=3),
            marker=dict(size=8)
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with col2:
        st.markdown("#### Infant Sex Distribution")
        sex_summary = filtered_df.groupby("Sex of Infant", as_index=False)["Births"].sum()
        total_in_selection = sex_summary["Births"].sum()
        sex_summary["Percentage"] = (sex_summary["Births"] / total_in_selection * 100).round(2)

        fig_sex = px.pie(
            sex_summary,
            names="Sex of Infant",
            values="Births",
            hole=0.45,
            title="Distribution by Infant Sex",
            color="Sex of Infant",
            color_discrete_map={"Female": "#e377c2", "Male": "#17becf"}
        )
        fig_sex.update_traces(
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Births: %{value:,}<br>Share: %{percent}<extra></extra>"
        )
        fig_sex.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_sex, use_container_width=True)

    st.markdown("---")

    # Top 5 and Bottom 5 Geography Comparison Snapshot
    st.markdown("#### 🏆 Geographic Distribution: Highest vs. Lowest Volume Geographies")
    geo_totals = (
        filtered_df.groupby("State of Residence", as_index=False)["Births"]
        .sum()
        .sort_values(by="Births", ascending=False)
    )

    if len(geo_totals) >= 2:
        col_top, col_bot = st.columns(2)
        top_n = min(5, len(geo_totals))
        top_df = geo_totals.head(top_n).sort_values(by="Births", ascending=True)
        bot_df = geo_totals.tail(top_n).sort_values(by="Births", ascending=True)

        with col_top:
            fig_top = px.bar(
                top_df,
                x="Births",
                y="State of Residence",
                orientation="h",
                title=f"Top {top_n} Geographies by Birth Count",
                color_discrete_sequence=["#2ca02c"],
                labels={"Births": "Births", "State of Residence": "Geography"}
            )
            fig_top.update_layout(
                xaxis=dict(rangemode="tozero", tickformat=","),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            fig_top.update_traces(hovertemplate="<b>%{y}</b>: %{x:,} births<extra></extra>")
            st.plotly_chart(fig_top, use_container_width=True)

        with col_bot:
            fig_bot = px.bar(
                bot_df,
                x="Births",
                y="State of Residence",
                orientation="h",
                title=f"Bottom {top_n} Geographies by Birth Count",
                color_discrete_sequence=["#d62728"],
                labels={"Births": "Births", "State of Residence": "Geography"}
            )
            fig_bot.update_layout(
                xaxis=dict(rangemode="tozero", tickformat=","),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            fig_bot.update_traces(hovertemplate="<b>%{y}</b>: %{x:,} births<extra></extra>")
            st.plotly_chart(fig_bot, use_container_width=True)
    else:
        st.write(geo_totals)


# ==============================================================================
# 7. TAB 2: GEOGRAPHIC ANALYSIS
# ==============================================================================

def render_geographic_tab(filtered_df: pd.DataFrame) -> None:
    """
    Renders an interactive US State choropleth map, a full state ranking chart,
    and an analytical deep-dive into state scale vs. birth volumes.
    """
    st.subheader("🗺️ Geographic Distribution & State Comparisons")

    if len(filtered_df) == 0:
        st.info("Please adjust filters to display geographic analysis.")
        return

    # Aggregate births by State
    state_df = (
        filtered_df.groupby(["State of Residence", "State Abbr"], as_index=False)["Births"]
        .sum()
        .sort_values(by="Births", ascending=False)
    )

    # 1. Interactive US Choropleth Map
    st.markdown("#### U.S. State Choropleth Map")
    st.caption("Color intensity reflects total recorded birth count in the current selection.")

    fig_map = px.choropleth(
        state_df,
        locations="State Abbr",
        locationmode="USA-states",
        color="Births",
        scope="usa",
        hover_name="State of Residence",
        hover_data={"State Abbr": False, "Births": ":,"},
        color_continuous_scale="Blues",
        labels={"Births": "Births"}
    )
    fig_map.update_layout(
        geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="rgb(255, 255, 255)"),
        margin=dict(l=0, r=0, t=20, b=0),
        coloraxis_colorbar=dict(title="Births", tickformat=",")
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns([3, 2])

    with col1:
        # 2. State Ranking Chart (Sorted horizontal bar)
        st.markdown("#### State Rankings by Total Selected Births")
        # Ensure non-truncated axis starting at zero
        fig_rank = px.bar(
            state_df.sort_values(by="Births", ascending=True),
            x="Births",
            y="State of Residence",
            orientation="h",
            height=max(450, len(state_df) * 18),
            title="Geographic Ranking (Sorted Descending)",
            labels={"Births": "Total Births", "State of Residence": "Geography"},
            color="Births",
            color_continuous_scale="Viridis"
        )
        fig_rank.update_layout(
            xaxis=dict(rangemode="tozero", tickformat=","),
            yaxis=dict(autorange="reversed"),
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        fig_rank.update_traces(hovertemplate="<b>%{y}</b><br>Births: %{x:,}<extra></extra>")
        st.plotly_chart(fig_rank, use_container_width=True)

    with col2:
        # 3. Top vs Bottom Geography Deep Dive Table
        st.markdown("#### 🔍 Scale Comparison: High vs. Low Volume States")
        st.caption(
            "Comparing the largest vs. smallest geographies reinforces why counts cannot be interpreted as rates."
        )

        n_compare = min(10, len(state_df))
        display_df = state_df[["State of Residence", "Births"]].copy()
        display_df["% of Selected"] = (display_df["Births"] / display_df["Births"].sum() * 100).round(2)
        display_df["Births"] = display_df["Births"].apply(lambda v: f"{v:,}")
        display_df["% of Selected"] = display_df["% of Selected"].apply(lambda v: f"{v:.2f}%")

        st.markdown("**Highest Volume Geographies:**")
        st.dataframe(display_df.head(n_compare), use_container_width=True, hide_index=True)

        if len(state_df) > n_compare:
            st.markdown("**Lowest Volume Geographies:**")
            st.dataframe(display_df.tail(n_compare), use_container_width=True, hide_index=True)


# ==============================================================================
# 8. TAB 3: MONTHLY & SEX ANALYSIS
# ==============================================================================

def render_monthly_sex_tab(filtered_df: pd.DataFrame) -> None:
    """
    Renders state-by-month heatmap, chronological month-by-sex comparisons,
    and seasonal birth volume metrics.
    """
    st.subheader("📅 Monthly Seasonality and Sex-Based Comparisons")

    if len(filtered_df) == 0:
        st.info("Please adjust filters to display monthly and sex analysis.")
        return

    # 1. Female and Male Comparison by Month
    st.markdown("#### Monthly Comparison: Female vs. Male Births")
    st.caption("Investigate consistency of biological sex ratios across calendar months.")

    sex_month_df = (
        filtered_df.groupby(["Month", "Sex of Infant"], as_index=False, observed=True)["Births"]
        .sum()
    )

    fig_sex_month = px.bar(
        sex_month_df,
        x="Month",
        y="Births",
        color="Sex of Infant",
        barmode="group",
        title="Live Birth Counts by Month and Infant Sex",
        labels={"Births": "Birth Counts", "Month": "Calendar Month"},
        color_discrete_map={"Female": "#e377c2", "Male": "#1f77b4"}
    )
    fig_sex_month.update_layout(
        xaxis=dict(title="Month (Chronological)"),
        yaxis=dict(rangemode="tozero", tickformat=","),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    fig_sex_month.update_traces(hovertemplate="<b>%{data.name}</b>: %{y:,} births<extra></extra>")
    st.plotly_chart(fig_sex_month, use_container_width=True)

    st.markdown("---")

    # 2. State-by-Month Heatmap Matrix
    st.markdown("#### State-by-Month Birth Count Heatmap")
    st.caption("Visualizing seasonality across geographies. Darker shading indicates higher birth counts.")

    # Pivot table with months ordered chronologically
    pivot_df = (
        filtered_df.groupby(["State of Residence", "Month"], observed=True)["Births"]
        .sum()
        .unstack(level="Month", fill_value=0)
    )

    # Re-order columns strictly according to calendar month sequence
    ordered_cols = [m for m in MONTH_ORDER if m in pivot_df.columns]
    pivot_df = pivot_df[ordered_cols]

    # Calculate state totals to sort y-axis descending
    state_order = pivot_df.sum(axis=1).sort_values(ascending=True).index
    pivot_df = pivot_df.loc[state_order]

    fig_heat = px.imshow(
        pivot_df,
        labels=dict(x="Calendar Month", y="Geography", color="Birth Count"),
        x=pivot_df.columns.tolist(),
        y=pivot_df.index.tolist(),
        color_continuous_scale="Teal",
        aspect="auto"
    )
    fig_heat.update_layout(
        height=max(450, len(pivot_df) * 16),
        coloraxis_colorbar=dict(title="Births", tickformat=","),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    fig_heat.update_traces(hovertemplate="<b>%{y}</b> - %{x}<br>Births: %{z:,}<extra></extra>")
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("---")

    # 3. Monthly Summary Metrics Table
    st.markdown("#### Monthly Seasonal Share Table")
    monthly_summary = (
        filtered_df.groupby("Month", as_index=False, observed=True)["Births"]
        .sum()
    )
    total_sel = monthly_summary["Births"].sum()
    monthly_summary["Share of Selected Total"] = (
        (monthly_summary["Births"] / total_sel * 100).round(2).apply(lambda v: f"{v:.2f}%")
        if total_sel > 0 else "0.00%"
    )
    monthly_summary["Births"] = monthly_summary["Births"].apply(lambda v: f"{v:,}")

    st.dataframe(monthly_summary, use_container_width=True, hide_index=True)


# ==============================================================================
# 9. TAB 4: DATA TABLE & DOWNLOAD
# ==============================================================================

def render_data_table_tab(filtered_df: pd.DataFrame) -> None:
    """
    Renders a searchable, sortable data table of filtered records and enables
    direct CSV download of the active subset.
    """
    st.subheader("📋 Searchable Filtered Dataset & CSV Export")

    if len(filtered_df) == 0:
        st.info("No records match your filter criteria.")
        return

    st.markdown(
        f"Displaying **{len(filtered_df):,}** observation rows in the current filtered view."
    )

    # Search box for state filtering within the table view
    search_query = st.text_input(
        "🔎 Search table by state name or keyword:",
        placeholder="Type to filter (e.g. 'Texas', 'Male', 'July')..."
    )

    display_df = filtered_df[REQUIRED_COLUMNS].copy()

    if search_query:
        mask = display_df.astype(str).apply(
            lambda row: row.str.contains(search_query, case=False).any(), axis=1
        )
        display_df = display_df[mask]
        st.caption(f"Filtered by search query: `{search_query}` — {len(display_df):,} matching rows.")

    # Render formatted interactive table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Births": st.column_config.NumberColumn(
                "Births (Count)",
                help="Count of recorded live births",
                format="%d"
            ),
            "Month Code": st.column_config.NumberColumn("Month Code", format="%d"),
            "Year Code": st.column_config.NumberColumn("Year", format="%d"),
        }
    )

    # CSV Download Button
    csv_bytes = filtered_df[REQUIRED_COLUMNS].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv_bytes,
        file_name="cdc_provisional_births_filtered_2025.csv",
        mime="text/csv",
        use_container_width=False,
        type="primary"
    )


# ==============================================================================
# 10. TAB 5: ABOUT THE DATA & PEDAGOGICAL GUIDE
# ==============================================================================

def render_about_tab() -> None:
    """
    Provides data provenance, a comprehensive data dictionary, and an educational
    guide on business analytics principles (counts vs rates, provisional data).
    """
    st.subheader("📖 About the Dataset & Business Analytics Guide")

    st.markdown("""
    ### 1. Data Provenance & Description
    This dashboard visualizes **2025 provisional natality data** provided by the 
    **National Center for Health Statistics (NCHS)** at the **Centers for Disease Control and Prevention (CDC)**.
    
    * **Reporting Unit:** Aggregated count of registered live births by state of residence, calendar month, and infant sex.
    * **Coverage:** All 50 U.S. states and the District of Columbia ($N = 51$).
    * **Temporal Span:** Full calendar year 2025 (12 months: January through December).
    * **Panel Structure:** Perfectly balanced Cartesian product ($51 \text{ geographies} \times 12 \text{ months} \times 2 \text{ infant sexes} = 1,224 \text{ observations}$).

    ---

    ### 2. Data Dictionary

    | Column Name | Data Type | Permitted Values / Range | Description |
    | :--- | :--- | :--- | :--- |
    | `State of Residence` | Categorical (String) | 50 States + District of Columbia | The mother's primary geographic state of residence. |
    | `Month` | Categorical (String) | January – December | Full English calendar month name. |
    | `Month Code` | Integer | $1, 2, \dots, 12$ | Numeric calendar month index ($1 = \text{Jan}$, $12 = \text{Dec}$). |
    | `Year Code` | Integer | $2025$ | Four-digit calendar reporting year. |
    | `Sex of Infant` | Categorical (Binary) | `Female`, `Male` | Assigned biological sex of the infant at birth. |
    | `Births` | Continuous Integer | $177$ – $17,627$ | Count of live births recorded in that category. |

    ---

    ### 3. Core Business Analytics Concepts for Students

    #### 🎓 The "Denominator Trap": Birth Counts vs. Birth Rates
    * **Count Metric:** A count simply measures *how many times an event occurred*. In this dashboard, California registers significantly more births than Wyoming purely because California has ~39 million residents whereas Wyoming has ~580,000 residents.
    * **Rate Metric (Standardized):** A true birth rate divides event counts by a population denominator (e.g., $\text{Crude Birth Rate} = \frac{\text{Live Births}}{\text{Total Population}} \times 1,000$).
    * **Key Takeaway:** Ranking states by birth *counts* identifies where healthcare capacity, obstetric services, and infant product distribution need the greatest physical resources. It does **not** indicate which state has the highest propensity for childbirth.

    #### 🎓 Interpreting Provisional Health Statistics
    * Provisional data are published before vital registration systems close and undergo final auditing.
    * In provisional CDC datasets, minor adjustments may occur as delayed birth certificates from hospitals and vital records offices are reconciled.
    
    #### 🎓 The Biological Sex Ratio at Birth
    * Demographers and vital statistics researchers consistently observe a worldwide sex ratio at birth of approximately **104 to 106 males per 100 females** ($\approx 1.045$).
    * Exploring the **Infant Sex Distribution** in this dashboard confirms that male births slightly exceed female births across nearly every state and month, matching biological expectations.
    """)


# ==============================================================================
# 11. MAIN CONTROLLER
# ==============================================================================

def main() -> None:
    """
    Main application orchestration routine.
    """
    st.set_page_config(
        page_title="CDC Provisional Natality Dashboard (2025)",
        page_icon="👶",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 1. Load Data
    try:
        df = load_data()
    except Exception as exc:
        st.error(f"❌ **Failed to load dataset:** {exc}")
        st.stop()

    # 2. Render Header & Disclaimers
    render_header()

    # 3. Render Sidebar Controls & Filter Data
    filtered_df = render_sidebar_filters(df)

    # 4. Render High-Level KPI Summary Cards
    render_kpi_cards(filtered_df, total_rows_original=len(df))

    # 5. Render Navigation Tabs
    tab_overview, tab_geo, tab_monthly_sex, tab_table, tab_about = st.tabs([
        "📊 Overview",
        "🗺️ Geographic Analysis",
        "📅 Monthly & Sex Analysis",
        "📋 Data Table & Download",
        "📖 About the Data"
    ])

    with tab_overview:
        render_overview_tab(filtered_df)

    with tab_geo:
        render_geographic_tab(filtered_df)

    with tab_monthly_sex:
        render_monthly_sex_tab(filtered_df)

    with tab_table:
        render_data_table_tab(filtered_df)

    with tab_about:
        render_about_tab()


if __name__ == "__main__":
    main()
