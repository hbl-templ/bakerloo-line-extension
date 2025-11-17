"""
Bakerloo Line Extension Equalities Impact Assessment Dashboard
Streamlit application for visualizing demographic data across different stations.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from config.station_config import STATIONS, COMPARISON_AREAS, NOMIS_DATASETS

# Page configuration
st.set_page_config(
    page_title="Bakerloo Line Extension EqIA",
    page_icon="🚇",
    layout="wide"
)

# Global area display order used across tables
# Note: This is now generated dynamically based on station selection
def get_area_order(station_name):
    """Get the area order for comparison based on station's parent borough."""
    parent_borough = STATIONS.get(station_name, {}).get("parent_borough", "Southwark")
    return ["Local Study Area", parent_borough, "London", "England"]

# Cache the NOMIS API data fetching
@st.cache_data
def fetch_nomis_data(dataset_id, geography_code, variables=None, measures="20100,20301"):
    """Fetch data from NOMIS API for a given dataset and geography code."""
    base_url = f"https://www.nomisweb.co.uk/api/v01/dataset/{dataset_id}.jsonstat.json"
    params = {
        "geography": geography_code,
        "date": "latest",
        "measures": measures
    }
    if variables:
        params.update(variables)

    # Simple retry for transient server/rate-limit errors
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(base_url, params=params, timeout=30)
        except requests.exceptions.RequestException as e:
            st.error(f"Network error when fetching NOMIS data: {e}")
            return None

        # If rate limited or server error, retry
        if response.status_code in (429, 502, 503, 504) and attempt < max_retries:
            st.warning(f"NOMIS API responded {response.status_code}; retrying ({attempt+1}/{max_retries})...")
            import time
            time.sleep(1 + attempt * 2)
            continue

        # If non-2xx, show informative error including the request URL
        if not response.ok:
            # Try to include server message if available
            text_snippet = response.text[:500] if response.text else "(no response body)"
            url = getattr(response, 'url', '(unknown url)')
            st.error(f"NOMIS API error: {response.status_code} for URL: {url}. Response snippet: {text_snippet}")
            return None

        # If body empty, return None with message (include URL)
        if not response.text or response.text.strip() == "":
            url = getattr(response, 'url', '(unknown url)')
            st.error(f"NOMIS API returned an empty response body for URL: {url}")
            return None

        # Try to parse JSON, but handle non-JSON bodies gracefully
        try:
            return response.json()
        except ValueError as e:
            snippet = response.text[:1000]
            url = getattr(response, 'url', '(unknown url)')
            st.error(f"Error parsing NOMIS response as JSON for URL: {url}. Error: {e}. Response snippet: {snippet}")
            return None


def _extract_nomis_percentages(values, n_groups):
    """Return a list of n_groups percentages from raw NOMIS 'value' output.

    Handles both formats: [count1, pct1, count2, pct2, ...] and [pct1, pct2, ...].
    Returns None if values is None or too short.
    """
    if values is None:
        return None
    vals = list(values)
    # If looks like count+percentage pairs
    if len(vals) >= 2 * n_groups:
        try:
            pct = [float(vals[i]) for i in range(1, 2 * n_groups, 2)]
            return pct[:n_groups]
        except Exception:
            return None
    # If length matches or exceeds n_groups, assume values are percentages
    if len(vals) >= n_groups:
        try:
            return [float(x) for x in vals[:n_groups]]
        except Exception:
            return None
    return None

def calculate_lsa_average(station_name, dataset_id, variables=None):
    """Calculate the Local Study Area average for a given dataset across ward codes."""
    if station_name not in STATIONS:
        return None
    
    ward_codes = [ward["nomis_code"] for ward in STATIONS[station_name]["wards"]]
    all_ward_data = []
    
    for ward_code in ward_codes:
        ward_data = fetch_nomis_data(dataset_id, ward_code, variables)
        if ward_data and "value" in ward_data:
            all_ward_data.append(ward_data["value"])
    
    if not all_ward_data:
        return None
    
    # Calculate simple mean (Option B as specified)
    return [sum(values) / len(values) for values in zip(*all_ward_data)]

def display_age_data(station_name):
    """Display age distribution data for the selected station."""
    st.subheader("Age Distribution")
    
    variables = {"c2021_age_12a": "0...11"}  # Age bands 0 to 85+
    
    # Get dynamic area order based on station
    area_order = get_area_order(station_name)
    parent_borough = area_order[1]  # The borough comparison area
    
    # Get data for Local Study Area
    lsa_data = calculate_lsa_average(station_name, NOMIS_DATASETS["age"], variables)
    
    # Get data for comparison areas
    comparison_data = {}
    for area_name in [parent_borough, "London", "England"]:
        if area_name in COMPARISON_AREAS:
            area_code = COMPARISON_AREAS[area_name]
            area_data = fetch_nomis_data(NOMIS_DATASETS["age"], area_code, variables)
            if area_data:
                comparison_data[area_name] = area_data["value"]
    
    if lsa_data and comparison_data:
        # Create DataFrame for visualization with ordered age bands
        age_bands = [
            "Total", 
            "0-4", "5-9", "10-15", "16-19", "20-24", "25-34",
            "35-49", "50-64", "65-74", "75-84", "85+"
        ]
        
        data = []
        # Add LSA data
        for i, value in enumerate(lsa_data[::2]):  # Skip every other value (percentages)
            data.append({
                "Area": "Local Study Area",
                "Age Band": age_bands[i],
                "Percentage": lsa_data[i*2 + 1]  # Get percentage value
            })
        
        # Add comparison area data in the specified order
        for area_name in [parent_borough, "London", "England"]:
            if area_name in comparison_data:
                values = comparison_data[area_name]
                for i, value in enumerate(values[::2]):
                    data.append({
                        "Area": area_name,
                        "Age Band": age_bands[i],
                        "Percentage": values[i*2 + 1]
                    })
        
        df = pd.DataFrame(data)
        
        # Filter out 'Total' row
        df = df[df["Age Band"] != "Total"]
        
        # Ensure the Age Bands are in the correct order
        df["Age Band"] = pd.Categorical(df["Age Band"], categories=age_bands[1:], ordered=True)
        # Ensure areas are in the correct order
        df["Area"] = pd.Categorical(df["Area"], categories=area_order, ordered=True)
        
        # Create visualization
        fig = px.bar(
            df,
            x="Age Band",
            y="Percentage",
            color="Area",
            barmode="group",
            title=f"Age Distribution - {station_name}",
            labels={"Percentage": "Percentage (%)", "Age Band": "Age Group"},
            color_discrete_sequence=["#DE2110", "#0009AB", "#FF6B6B", "#4B4BFF"]
        )
        
        fig.update_layout(
            legend_title="Area",
            xaxis_title="Age Group",
            yaxis_title="Percentage (%)",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
                linecolor="rgba(128,128,128,0.2)"
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
                linecolor="rgba(128,128,128,0.2)"
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display detailed age bands table
        st.subheader("Detailed Age Distribution")
        st.dataframe(
            df.pivot(index="Age Band", columns="Area", values="Percentage").round(1),
            use_container_width=True
        )
        
        # Create broad age categories table (0-15, 16-64, 65+)
        st.subheader("Broad Age Categories")
        
        # Define the groupings
        age_groupings = {
            "0-15": ["0-4", "5-9", "10-15"],
            "16-64": ["16-19", "20-24", "25-34", "35-49", "50-64"],
            "65+": ["65-74", "75-84", "85+"]
        }
        
        # Calculate sums for each group and area
        grouped_data = []
        pivot_df = df.pivot(index="Age Band", columns="Area", values="Percentage")
        
        for group_name, age_bands in age_groupings.items():
            group_data = {"Age Band": group_name}
            for area in area_order:
                if area in pivot_df.columns:
                    group_data[area] = pivot_df.loc[age_bands, area].sum()
            grouped_data.append(group_data)
            
        # Create and display the grouped DataFrame
        grouped_df = pd.DataFrame(grouped_data)
        grouped_df.set_index("Age Band", inplace=True)
        
        st.dataframe(grouped_df.round(1), use_container_width=True)

def display_ethnicity_data(station_name):
    """Display ethnicity distribution data for the selected station."""
    st.subheader("Ethnicity Distribution")
    
    variables = {"c2021_eth_20": "0,1001...1005"}
    
    # Get dynamic area order based on station
    area_order = get_area_order(station_name)
    parent_borough = area_order[1]
    
    # Get raw data for Local Study Area (may be counts+percent or just percent)
    lsa_raw = calculate_lsa_average(station_name, NOMIS_DATASETS["ethnicity"], variables)

    # Get raw data for comparison areas
    comparison_raw = {}
    for area_name in [parent_borough, "London", "England"]:
        if area_name in COMPARISON_AREAS:
            area_code = COMPARISON_AREAS[area_name]
            area_resp = fetch_nomis_data(NOMIS_DATASETS["ethnicity"], area_code, variables)
            if area_resp and "value" in area_resp:
                comparison_raw[area_name] = area_resp["value"]

    # Expected groups (ordered as NOMIS returns)
    ethnic_groups = [
        "Total",
        "Asian, Asian British or Asian Welsh",
        "Black, Black British, Black Welsh, Caribbean or African",
        "Mixed or Multiple ethnic groups",
        "White",
        "Other ethnic group"
    ]

    def _extract_percentages(values, n_groups):
        """Return a list of n_groups percentages from raw NOMIS values.

        NOMIS sometimes returns [count1, pct1, count2, pct2, ...] or just [pct1, pct2, ...].
        This helper handles both formats and will return None if values are shorter than expected.
        """
        if values is None:
            return None
        vals = list(values)
        # If looks like count+percentage pairs (length at least 2*n_groups)
        if len(vals) >= 2 * n_groups:
            # take odd indices as percentages
            pct = [float(vals[i]) for i in range(1, 2 * n_groups, 2)]
            return pct[:n_groups]
        # If length matches n_groups or longer, assume values are percentages
        if len(vals) >= n_groups:
            try:
                return [float(x) for x in vals[:n_groups]]
            except Exception:
                return None
        return None

    lsa_perc = _extract_percentages(lsa_raw, len(ethnic_groups))
    comp_perc = {k: _extract_percentages(v, len(ethnic_groups)) for k, v in comparison_raw.items()}

    if lsa_perc is None or not any(comp_perc.values()):
        st.warning("Ethnicity data not available for this area yet.")
        return
    
    # Build dataframe rows excluding the Total row
    rows = []
    for idx, group in enumerate(ethnic_groups):
        if group == "Total":
            continue
        # Local Study Area first
        rows.append({
            "Area": "Local Study Area",
            "Ethnic Group": group,
            "Percentage": lsa_perc[idx] if idx < len(lsa_perc) else None
        })
        # Then add comparison areas in the specified order
        for area_name in [parent_borough, "London", "England"]:
            if area_name in comp_perc:
                pct_list = comp_perc[area_name]
                rows.append({
                    "Area": area_name,
                    "Ethnic Group": group,
                    "Percentage": pct_list[idx] if pct_list and idx < len(pct_list) else None
                })

    df = pd.DataFrame(rows)
        
    # Create visualization
    fig = px.bar(
        df,
        x="Ethnic Group",
        y="Percentage",
        color="Area",
        barmode="group",
        title=f"Ethnicity Distribution - {station_name}",
        labels={"Percentage": "Percentage (%)", "Ethnic Group": "Ethnic Group"},
        color_discrete_sequence=["#DE2110", "#0009AB", "#FF6B6B", "#4B4BFF"]
    )

    fig.update_layout(
        legend_title="Area",
        xaxis_title="Ethnic Group",
        yaxis_title="Percentage (%)",
        xaxis_tickangle=-45,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(128,128,128,0.2)",
            linecolor="rgba(128,128,128,0.2)"
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(128,128,128,0.2)",
            linecolor="rgba(128,128,128,0.2)"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # Create pivot table with enforced column order
    pivot_df = df.pivot(index="Ethnic Group", columns="Area", values="Percentage")
    # Reorder columns to match area_order
    pivot_df = pivot_df[area_order]
    
    # Display data table
    st.dataframe(pivot_df.round(1), use_container_width=True)

def display_gender_data(station_name):
    """Display gender distribution data for the selected station."""
    st.subheader("Gender Distribution")
    
    # Get dynamic area order based on station
    area_order = get_area_order(station_name)
    parent_borough = area_order[1]
    
    # Use c_sex variable with 0...2 to get Total, Male, Female
    # Use only measure 20301 (percent) to avoid getting counts mixed in
    variables = {"c_sex": "0...2"}
    
    # Helper function to fetch gender data with percentage-only measure
    def fetch_gender_data(geography_code):
        return fetch_nomis_data(NOMIS_DATASETS["gender"], geography_code, variables, measures="20301")
    
    # Get raw data for Local Study Area (averaged across wards)
    ward_codes = [ward["nomis_code"] for ward in STATIONS[station_name]["wards"]]
    all_ward_data = []
    
    for ward_code in ward_codes:
        ward_data = fetch_gender_data(ward_code)
        if ward_data and "value" in ward_data:
            all_ward_data.append(ward_data["value"])
    
    lsa_raw = None
    if all_ward_data:
        # Calculate simple mean across wards
        lsa_raw = [sum(values) / len(values) for values in zip(*all_ward_data)]

    # Get raw data for comparison areas
    comparison_raw = {}
    for area_name in [parent_borough, "London", "England"]:
        if area_name in COMPARISON_AREAS:
            area_code = COMPARISON_AREAS[area_name]
            area_resp = fetch_gender_data(area_code)
            if area_resp and "value" in area_resp:
                comparison_raw[area_name] = area_resp["value"]
    
    if not lsa_raw or not comparison_raw:
        st.warning("Gender data not available for this area yet.")
        return
    
    # Build data rows - NOMIS returns [total_pct, male_pct, female_pct]
    # We use indices 1 (Male) and 2 (Female)
    rows = []
    
    # Extract LSA percentages (indices 1 and 2 for Male and Female percentages)
    if lsa_raw and len(lsa_raw) >= 3:
        male_pct = lsa_raw[1]    # Male percentage
        female_pct = lsa_raw[2]  # Female percentage
        
        rows.append({
            "Area": "Local Study Area",
            "Gender": "Male",
            "Percentage": male_pct
        })
        rows.append({
            "Area": "Local Study Area",
            "Gender": "Female",
            "Percentage": female_pct
        })
    
    # Extract comparison area percentages
    for area_name in area_order[1:]:
        if area_name in comparison_raw:
            vals = comparison_raw[area_name]
            if vals and len(vals) >= 3:
                rows.append({
                    "Area": area_name,
                    "Gender": "Male",
                    "Percentage": vals[1]  # Male percentage
                })
                rows.append({
                    "Area": area_name,
                    "Gender": "Female",
                    "Percentage": vals[2]  # Female percentage
                })
    
    df = pd.DataFrame(rows)
    
    # Verify data looks correct before plotting
    if df.empty:
        st.warning("No gender data available.")
        return
    
    # Create pie charts for each area in a grid layout
    st.markdown("**Gender Distribution by Area**")
    
    # Create 2x2 grid for pie charts
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    cols = [col1, col2, col3, col4]
    
    for idx, area_name in enumerate(area_order):
        area_data = df[df["Area"] == area_name]
        
        if not area_data.empty:
            with cols[idx]:
                fig = px.pie(
                    area_data,
                    values="Percentage",
                    names="Gender",
                    title=area_name,
                    color="Gender",
                    color_discrete_map={"Male": "#0009AB", "Female": "#DE2110"},
                    hole=0.3  # Create a donut chart
                )
                
                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>%{value:.1f}%<extra></extra>'
                )
                
                fig.update_layout(
                    showlegend=True,
                    height=300,
                    margin=dict(t=40, b=20, l=20, r=20),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    # Display data table
    st.markdown("**Detailed Gender Breakdown**")
    pivot_df = df.pivot(index="Gender", columns="Area", values="Percentage")
    # Reorder columns to match area_order
    cols = [c for c in area_order if c in pivot_df.columns]
    pivot_df = pivot_df[cols]
    st.dataframe(pivot_df.round(1), use_container_width=True)

def display_sexual_orientation_data(station_name):
    """Display sexual orientation distribution data for borough and London only."""
    st.subheader("Sexual Orientation")
    
    st.info("📊 Sexual orientation data is only available at borough and London level (not ward level).")
    
    # Get dynamic area order based on station
    area_order = get_area_order(station_name)
    parent_borough = area_order[1]
    
    # Fetch sexual orientation data (TS077 - NM_2086_1 with c2021_sexor_9 dimension)
    # Categories: 0=Total, 1=Straight/Heterosexual, 2=Gay/Lesbian, 3=Bisexual, 
    # 4=Pansexual, 5=Asexual, 6=Queer, 7=Other, 8=Not answered
    
    dataset_id = NOMIS_DATASETS['sexual_orientation']
    sexual_orientation_data = {}
    
    for area_name in [parent_borough, "London"]:
        area_code = COMPARISON_AREAS[area_name]
        
        # Fetch data using jsonstat format
        url = f"https://www.nomisweb.co.uk/api/v01/dataset/{dataset_id}/geography/{area_code}.jsonstat.json"
        params = {
            'date': 'latest',
            'measures': '20301'  # Percentage only
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.ok:
                data = response.json()
                if 'value' in data:
                    values = data['value']
                    # Extract main categories (indices 1-8, skip 0 which is total)
                    sexual_orientation_data[area_name] = {
                        'Straight or Heterosexual': values[1],
                        'Gay or Lesbian': values[2],
                        'Bisexual': values[3],
                        'Pansexual': values[4],
                        'Asexual': values[5],
                        'Queer': values[6],
                        'Other sexual orientations': values[7],
                        'Not answered': values[8]
                    }
        except Exception as e:
            st.error(f"Error fetching data for {area_name}: {str(e)}")
    
    if not sexual_orientation_data:
        st.warning("No data available for this station.")
        return
    
    # Create comparison bar chart
    categories = list(next(iter(sexual_orientation_data.values())).keys())
    
    fig = go.Figure()
    
    for area_name in [parent_borough, "London"]:
        if area_name in sexual_orientation_data:
            values = [sexual_orientation_data[area_name][cat] for cat in categories]
            fig.add_trace(go.Bar(
                name=area_name,
                x=categories,
                y=values,
                text=[f"{v:.1f}%" for v in values],
                textposition='outside'
            ))
    
    fig.update_layout(
        title="Sexual Orientation Comparison (%)",
        xaxis_title="Sexual Orientation",
        yaxis_title="Percentage (%)",
        barmode='group',
        height=600,
        xaxis={'tickangle': -45}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display data table
    with st.expander("📊 View Sexual Orientation Data Table"):
        df = pd.DataFrame(sexual_orientation_data).T
        df = df.round(1)
        st.dataframe(df, use_container_width=True)

def display_languages_data(station_name):
    """Display main language distribution data for BLE boroughs."""
    st.subheader("Main Languages Spoken")
    
    st.info("📊 Language data shown at borough level for Lambeth, Lewisham, Greenwich, and Southwark")
    
    # Dataset: NM_2043_1 - TS024 Main language (detailed) with 106 categories
    # We'll focus on top languages
    dataset_id = NOMIS_DATASETS['languages']
    
    # Define the 4 BLE boroughs
    ble_boroughs = {
        'Lambeth': COMPARISON_AREAS['Lambeth'],
        'Lewisham': COMPARISON_AREAS['Lewisham'],
        'Greenwich': COMPARISON_AREAS['Greenwich'],
        'Southwark': COMPARISON_AREAS['Southwark']
    }
    
    # Fetch language data for all boroughs
    all_languages_data = {}
    
    for borough_name, area_code in ble_boroughs.items():
        url = f"https://www.nomisweb.co.uk/api/v01/dataset/{dataset_id}/geography/{area_code}.jsonstat.json"
        params = {'date': 'latest', 'measures': '20301'}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.ok:
                data = response.json()
                if 'value' in data:
                    all_languages_data[borough_name] = data['value']
        except Exception as e:
            st.error(f"Error fetching language data for {borough_name}: {str(e)}")
    
    if not all_languages_data:
        st.warning("No language data available.")
        return
    
    # Language categories (simplified top languages based on index positions)
    # Index 0 = Total, 1 = English, then other languages
    language_categories = [
        'English (English or Welsh in Wales)',
        'French',
        'Portuguese', 
        'Spanish',
        'Polish',
        'Italian',
        'German',
        'Romanian',
        'Arabic',
        'Bengali',
        'Urdu',
        'Tamil',
        'Punjabi',
        'Gujarati',
        'Turkish',
        'Somali',
        'Chinese (All Chinese)',
        'Yoruba',
        'Akan',
        'Other language'
    ]
    
    # Map indices to language names (simplified version with main categories)
    # Based on TS024 structure: 0=Total, 1=English, 13=French, 14=Portuguese, 15=Spanish, etc.
    language_indices = {
        'English (English or Welsh in Wales)': 1,
        'French': 13,
        'Portuguese': 14,
        'Spanish': 15,
        'Polish': 19,
        'Italian': 17,
        'German': 18,
        'Romanian': 22,
        'Arabic': 46,
        'Bengali': 69,
        'Urdu': 68,
        'Tamil': 65,
        'Punjabi': 67,
        'Gujarati': 71,
        'Turkish': 61,
        'Somali': 56,
        'Chinese (All Chinese)': 86,
        'Yoruba': 55,
        'Akan': 51,
        'Other language': 105
    }
    
    # Extract data for each borough
    borough_language_data = {}
    for borough_name, values in all_languages_data.items():
        borough_language_data[borough_name] = {}
        for lang_name, idx in language_indices.items():
            if idx < len(values):
                borough_language_data[borough_name][lang_name] = values[idx]
    
    # Create summary table
    st.markdown("### Language Distribution by Borough")
    
    # Build table data - show top 10 languages across all boroughs
    summary_rows = []
    for lang_name in language_indices.keys():
        row = {'Language': lang_name}
        for borough in ['Lambeth', 'Lewisham', 'Greenwich', 'Southwark']:
            if borough in borough_language_data and lang_name in borough_language_data[borough]:
                row[borough] = f"{borough_language_data[borough][lang_name]:.1f}%"
        summary_rows.append(row)
    
    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(summary_df, use_container_width=True, hide_index=True, height=600)
    
    # Visualization: Comparison bar chart for top 10 languages
    st.markdown("---")
    st.markdown("### Top 10 Most Spoken Languages (Excluding English)")
    
    # Calculate average percentage across boroughs for each language (excluding English)
    lang_averages = {}
    for lang_name, idx in language_indices.items():
        if lang_name != 'English (English or Welsh in Wales)':
            avg = sum(borough_language_data[b].get(lang_name, 0) for b in ble_boroughs.keys()) / len(ble_boroughs)
            lang_averages[lang_name] = avg
    
    # Get top 10 languages
    top_languages = sorted(lang_averages.items(), key=lambda x: x[1], reverse=True)[:10]
    top_lang_names = [lang[0] for lang in top_languages]
    
    # Create grouped bar chart
    fig = go.Figure()
    
    for borough in ['Lambeth', 'Lewisham', 'Greenwich', 'Southwark']:
        values = [borough_language_data[borough].get(lang, 0) for lang in top_lang_names]
        fig.add_trace(go.Bar(
            name=borough,
            x=top_lang_names,
            y=values,
            text=[f"{v:.1f}%" for v in values],
            textposition='outside'
        ))
    
    fig.update_layout(
        title="Top 10 Most Spoken Languages (Excluding English)",
        xaxis_title="Language",
        yaxis_title="Percentage (%)",
        barmode='group',
        height=500,
        xaxis={'tickangle': -45},
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # English language proficiency comparison
    st.markdown("---")
    st.markdown("### English Language Speakers")
    
    english_data = []
    for borough in ['Lambeth', 'Lewisham', 'Greenwich', 'Southwark']:
        english_pct = borough_language_data[borough].get('English (English or Welsh in Wales)', 0)
        english_data.append({'Borough': borough, 'English Speakers (%)': english_pct})
    
    english_df = pd.DataFrame(english_data)
    
    fig_english = px.bar(
        english_df,
        x='Borough',
        y='English Speakers (%)',
        title='Percentage of Residents with English as Main Language',
        text='English Speakers (%)',
        height=400
    )
    
    fig_english.update_traces(
        texttemplate='%{text:.1f}%',
        textposition='outside',
        marker_color='#2E86AB'
    )
    
    fig_english.update_layout(
        showlegend=False,
        yaxis=dict(range=[0, 100])
    )
    
    st.plotly_chart(fig_english, use_container_width=True)

def display_religion_data(station_name):
    """Display religion distribution data for the selected station."""
    st.subheader("Religion Distribution")
    
    variables = {"c2021_religion_10": "0...9"}
    
    # Get dynamic area order based on station
    area_order = get_area_order(station_name)
    parent_borough = area_order[1]
    
    # Get raw data for Local Study Area
    lsa_raw = calculate_lsa_average(station_name, NOMIS_DATASETS["religion"], variables)

    # Get raw data for comparison areas
    comparison_raw = {}
    for area_name in [parent_borough, "London", "England"]:
        if area_name in COMPARISON_AREAS:
            area_code = COMPARISON_AREAS[area_name]
            area_resp = fetch_nomis_data(NOMIS_DATASETS["religion"], area_code, variables)
            if area_resp and "value" in area_resp:
                comparison_raw[area_name] = area_resp["value"]

    religion_groups = [
        "Total",
        "No religion",
        "Christian",
        "Buddhist",
        "Hindu",
        "Jewish",
        "Muslim",
        "Sikh",
        "Other religion",
        "Not answered"
    ]

    lsa_perc = _extract_nomis_percentages(lsa_raw, len(religion_groups))
    comp_perc = {k: _extract_nomis_percentages(v, len(religion_groups)) for k, v in comparison_raw.items()}

    if lsa_perc is None or not any(comp_perc.values()):
        st.warning("Religion data not available for this area yet.")
        return
    
    rows = []
    for idx, group in enumerate(religion_groups):
        if group == "Total":
            continue
        # Local Study Area first
        rows.append({
            "Area": "Local Study Area",
            "Religion": group,
            "Percentage": lsa_perc[idx] if idx < len(lsa_perc) else None
        })
        # Then add comparison areas in the specified order
        for area_name in [parent_borough, "London", "England"]:
            if area_name in comp_perc:
                pct_list = comp_perc[area_name]
                rows.append({
                    "Area": area_name,
                    "Religion": group,
                    "Percentage": pct_list[idx] if pct_list and idx < len(pct_list) else None
                })

    df = pd.DataFrame(rows)

    # Create visualization
    fig = px.bar(
        df,
        x="Religion",
        y="Percentage",
        color="Area",
        barmode="group",
        title=f"Religion Distribution - {station_name}",
        labels={"Percentage": "Percentage (%)", "Religion": "Religion"},
        color_discrete_sequence=["#DE2110", "#0009AB", "#FF6B6B", "#4B4BFF"]
    )

    fig.update_layout(
        legend_title="Area",
        xaxis_title="Religion",
        yaxis_title="Percentage (%)",
        xaxis_tickangle=-45,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(128,128,128,0.2)",
            linecolor="rgba(128,128,128,0.2)"
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(128,128,128,0.2)",
            linecolor="rgba(128,128,128,0.2)"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # Create pivot table with enforced column order
    pivot_df = df.pivot(index="Religion", columns="Area", values="Percentage")
    # Reorder columns to match area_order
    pivot_df = pivot_df[area_order]
    
    # Display data table
    st.dataframe(pivot_df.round(1), use_container_width=True)


def display_deprivation_data(station_name):
    """Display IMD 2025 deprivation data for the LSOAs that align to the station's wards.

    Process:
    - Use `LSOA to WD to LA Lookup.csv` to find LSOAs for each ward in the Local Study Area.
    - Load `IMD 2025.csv` and extract the overall IMD and the seven domain deciles.
    - Display a table unique to the station showing each LSOA and the deciles.
    """
    st.subheader("Deprivation (IMD 2025)")

    # Paths to data files (workspace root) - go up one level from src/
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lsoa_lookup_path = os.path.join(project_root, "LSOA to WD to LA Lookup.csv")
    imd_path = os.path.join(project_root, "IMD 2025.csv")

    @st.cache_data
    def _load_lsoa_lookup(path):
        try:
            df = pd.read_csv(path, dtype=str)
            # Ensure expected columns exist
            expect = [c for c in df.columns]
            return df
        except Exception as e:
            st.error(f"Could not load LSOA lookup CSV at {path}: {e}")
            return None

    @st.cache_data
    def _load_imd(path):
        try:
            df = pd.read_csv(path, dtype=str)
            return df
        except Exception as e:
            st.error(f"Could not load IMD CSV at {path}: {e}")
            return None

    lookup_df = _load_lsoa_lookup(lsoa_lookup_path)
    imd_df = _load_imd(imd_path)

    if lookup_df is None or imd_df is None:
        st.warning("Deprivation data files not available in the workspace.")
        return

    # Helper to normalise ward names for fuzzy matching
    def _norm_name(s):
        if pd.isna(s):
            return ""
        s2 = str(s).lower()
        s2 = s2.replace("&", "and")
        s2 = s2.replace("'", "")
        s2 = s2.replace("\u2019", "")
        s2 = "".join(ch for ch in s2 if ch.isalnum() or ch.isspace())
        s2 = " ".join(s2.split())
        return s2

    # Build mapping from normalised ward name -> list of LSOAs
    lookup_df["_ward_norm"] = lookup_df["WD22NM"].apply(_norm_name)
    lookup_df["LSOA21CD"] = lookup_df["LSOA21CD"]
    lookup_df["LSOA21NM"] = lookup_df.get("LSOA21NM", lookup_df["LSOA21CD"]) 

    station_wards = [w.get("name") for w in STATIONS[station_name]["wards"]]
    ward_norms = {_norm_name(w): w for w in station_wards}

    # Select LSOAs whose ward normalised name matches any of the station ward normals
    matched = lookup_df[lookup_df["_ward_norm"].isin(list(ward_norms.keys()))]

    if matched.empty:
        # Try matching by partial (contains) for robustness
        masks = pd.Series(False, index=lookup_df.index)
        for wn in ward_norms.keys():
            masks = masks | lookup_df["_ward_norm"].str.contains(wn, na=False)
        matched = lookup_df[masks]

    if matched.empty:
        st.warning("No LSOAs found for the Local Study Area wards (name matching failed). See ward list in header and the LSOA lookup file.")
        return

    # Unique LSOAs for this station
    lsoas = matched[["LSOA21CD", "LSOA21NM"]].drop_duplicates().rename(columns={"LSOA21CD": "LSOA Code", "LSOA21NM": "LSOA Name"})

    # Identify IMD columns (case-insensitive contains)
    col_map = {}
    cols = list(imd_df.columns)
    def find_col(keyword_list):
        for k in keyword_list:
            for c in cols:
                if k.lower() in c.lower():
                    return c
        return None

    col_map["IMD Rank"] = find_col(["Index of Multiple Deprivation (IMD) Rank", "imd rank"])
    col_map["IMD Decile"] = find_col(["Index of Multiple Deprivation (IMD) Decile", "imd decile"])
    col_map["Income Decile"] = find_col(["Income Decile"])
    col_map["Employment Decile"] = find_col(["Employment Decile"])
    col_map["Education Decile"] = find_col(["Education, Skills and Training Decile", "Education Decile"])
    col_map["Health Decile"] = find_col(["Health Deprivation and Disability Decile", "Health Decile"])
    col_map["Crime Decile"] = find_col(["Crime Decile"])
    col_map["Barriers Decile"] = find_col(["Barriers to Housing and Services Decile", "Barriers Decile"])
    col_map["Living Environment Decile"] = find_col(["Living Environment Decile"])

    # Ensure we have at least the IMD decile column
    if col_map["IMD Decile"] is None:
        st.error("Could not find IMD Decile column in IMD CSV. Columns found: " + ", ".join(cols[:10]))
        return

    # Subset IMD dataframe to the LSOAs we found
    imd_df_ = imd_df[[c for c in cols if c is not None]]
    imd_df_ = imd_df_.rename(columns={col_map.get(k): k for k in col_map if col_map.get(k)})

    # The IMD file uses 'LSOA code (2021)' header - normalise name if present
    lsoa_code_col = None
    for candidate in ["LSOA code (2021)", "LSOA21CD", "LSOA21CD", "LSOA code"]:
        if candidate in imd_df_.columns:
            lsoa_code_col = candidate
            break
    # If not present, try to find a column that looks like LSOA code
    if lsoa_code_col is None:
        for c in imd_df_.columns:
            if c.lower().startswith("e01") or "lsoa" in c.lower():
                lsoa_code_col = c
                break

    if lsoa_code_col is None:
        st.error("Could not find LSOA code column in IMD CSV")
        return

    # Normalise imd df LSOA code column name to 'LSOA Code' for merge
    imd_df_ = imd_df_.rename(columns={lsoa_code_col: "LSOA Code"})

    # Merge to get IMD data for our LSOAs
    merged = pd.merge(lsoas, imd_df_, on="LSOA Code", how="left")

    # Select and reorder columns for display: LSOA Code, LSOA Name, IMD Decile + 7 domains
    display_cols = ["LSOA Code", "LSOA Name"]
    for k in ["IMD Decile", "Income Decile", "Employment Decile", "Education Decile", "Health Decile", "Crime Decile", "Barriers Decile", "Living Environment Decile"]:
        if k in merged.columns:
            display_cols.append(k)

    # If the IMD Rank exists, include it and sort by it (most deprived first)
    if "IMD Rank" in merged.columns:
        merged["IMD Rank"] = pd.to_numeric(merged["IMD Rank"], errors="coerce")
        merged = merged.sort_values(by="IMD Rank")

    # Convert deciles to numeric where possible
    for c in display_cols:
        if c not in ["LSOA Code", "LSOA Name"]:
            merged[c] = pd.to_numeric(merged[c], errors="coerce")

    # Add summary statistics about IMD decile distribution
    st.markdown(f"**Found {len(merged)} unique LSOAs for this Local Study Area.**")
    
    if "IMD Decile" in merged.columns:
        # Convert deciles to quintiles (1-2 → 1, 3-4 → 2, etc.)
        merged["IMD Quintile"] = ((merged["IMD Decile"].astype(float) + 1) // 2).fillna(0).astype(int)
        
        # Calculate percentage in each quintile
        total_lsoas = len(merged)
        quintile_counts = merged["IMD Quintile"].value_counts().sort_index()
        quintile_pcts = (quintile_counts / total_lsoas * 100).round(1)
        
        # Display key statistics as callouts in columns
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Helper for consistent callout formatting
        def format_quintile_callout(quintile, pct):
            labels = ["Most Deprived 20%", "More Deprived 20%", "Middle 20%", "Less Deprived 20%", "Least Deprived 20%"]
            if quintile < 1 or quintile > 5:
                return ""
            return f"**{labels[quintile-1]}**\n\n{pct:.1f}% of LSA"
        
        # Show callouts for each quintile
        with col1:
            st.markdown(format_quintile_callout(1, quintile_pcts.get(1, 0.0)))
        with col2:
            st.markdown(format_quintile_callout(2, quintile_pcts.get(2, 0.0)))
        with col3:
            st.markdown(format_quintile_callout(3, quintile_pcts.get(3, 0.0)))
        with col4:
            st.markdown(format_quintile_callout(4, quintile_pcts.get(4, 0.0)))
        with col5:
            st.markdown(format_quintile_callout(5, quintile_pcts.get(5, 0.0)))
        
        # Create a visual representation
        st.subheader("Distribution of Deprivation in Local Study Area")
        
        # Prepare data for the chart
        chart_data = pd.DataFrame({
            "Quintile": ["Most Deprived 20%", "More Deprived 20%", "Middle 20%", 
                        "Less Deprived 20%", "Least Deprived 20%"],
            "Percentage": [quintile_pcts.get(1, 0.0), quintile_pcts.get(2, 0.0),
                         quintile_pcts.get(3, 0.0), quintile_pcts.get(4, 0.0),
                         quintile_pcts.get(5, 0.0)]
        })
        
        # Create a horizontal bar chart
        fig = px.bar(
            chart_data,
            x="Percentage",
            y="Quintile",
            orientation='h',
            title="Distribution of IMD Quintiles",
            labels={"Percentage": "Percentage of Local Study Area LSOAs", "Quintile": ""},
            # Use a sequential color scheme from red (most deprived) to blue (least deprived)
            color_discrete_sequence=["#DE2110", "#FF6B6B", "#CCCCCC", "#4B4BFF", "#0009AB"][::-1]
        )
        
        # Update layout for consistency with other charts
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
                linecolor="rgba(128,128,128,0.2)",
                range=[0, max(100, chart_data["Percentage"].max() + 5)]  # Ensure we see up to 100%
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
                linecolor="rgba(128,128,128,0.2)"
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Display the detailed LSOA table
    st.subheader("LSOA Level Deprivation Data")
    st.dataframe(merged[display_cols].reset_index(drop=True), use_container_width=True)

    # Mark todo item as complete in the internal todo list (update)
    try:
        # Use the manage_todo_list function if available in the environment
        pass
    except Exception:
        pass


def display_homelessness_data(station_name):
    """Display homelessness data for boroughs in the Local Study Area using GLA CHAIN data."""
    st.subheader("Homelessness")
    
    # Load the homelessness data
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    homelessness_path = os.path.join(project_root, "GLA Homelessness Data 23-25.csv")
    
    @st.cache_data
    def _load_homelessness_data(path):
        try:
            # Read CSV and skip metadata rows at the bottom
            df = pd.read_csv(path)
            # Remove rows where Area is NaN or contains metadata
            df = df[df['Area'].notna()].copy()
            # Remove rows that don't have numeric data (metadata rows)
            df = df[~df['Area'].str.contains('Source|Email|Downloaded|Explanatory|Date|Note', case=False, na=False)]
            return df
        except Exception as e:
            st.error(f"Could not load homelessness data at {path}: {e}")
            return None
    
    homelessness_df = _load_homelessness_data(homelessness_path)
    
    if homelessness_df is None:
        st.warning("Homelessness data file not available in the workspace.")
        return
    
    # Define target boroughs for analysis
    target_boroughs = ["Lambeth", "Southwark", "Lewisham", "Greenwich"]
    
    # Extract quarters from column names (format: YYYY-YY Q#)
    quarters = [col for col in homelessness_df.columns if 'Q' in col]
    
    # Prepare data for visualization
    # 1. Local Study Area boroughs
    lsa_data = homelessness_df[homelessness_df['Area'].isin(target_boroughs)].copy()
    
    # Reshape for plotting (area-specific graph)
    lsa_for_plot = []
    for _, row in lsa_data.iterrows():
        for quarter in quarters:
            try:
                value = pd.to_numeric(row[quarter], errors='coerce')
                if pd.notna(value):
                    lsa_for_plot.append({
                        'Borough': row['Area'],
                        'Quarter': quarter,
                        'Number of People': value
                    })
            except:
                pass
    
    lsa_plot_df = pd.DataFrame(lsa_for_plot)
    
    # 2. Greater London Authority data
    gla_data = homelessness_df[homelessness_df['Area'] == 'Greater London Authority'].copy()
    
    gla_for_plot = []
    if not gla_data.empty:
        row = gla_data.iloc[0]
        for quarter in quarters:
            try:
                value = pd.to_numeric(row[quarter], errors='coerce')
                if pd.notna(value):
                    gla_for_plot.append({
                        'Quarter': quarter,
                        'Number of People': value
                    })
            except:
                pass
    
    gla_plot_df = pd.DataFrame(gla_for_plot)
    
    # Display charts in two columns
    col1, col2 = st.columns(2)
    
    # Local Study Area boroughs chart
    with col1:
        st.markdown("**Local Study Area Boroughs**")
        if not lsa_plot_df.empty:
            fig_lsa = px.line(
                lsa_plot_df,
                x='Quarter',
                y='Number of People',
                color='Borough',
                markers=True,
                title='Homelessness Trends (2023-2026)',
                labels={'Number of People': 'Number of People Seen', 'Quarter': 'Quarter'},
                height=400
            )
            fig_lsa.update_layout(
                showlegend=True,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor="rgba(128,128,128,0.2)",
                    linecolor="rgba(128,128,128,0.2)"
                ),
                yaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor="rgba(128,128,128,0.2)",
                    linecolor="rgba(128,128,128,0.2)"
                ),
                hovermode='x unified'
            )
            st.plotly_chart(fig_lsa, use_container_width=True)
            
            # Summary statistics for LSA boroughs
            st.markdown("**Summary Statistics (LSA Boroughs)**")
            summary_stats = lsa_plot_df.groupby('Borough')['Number of People'].agg(['mean', 'min', 'max']).round(1)
            summary_stats.columns = ['Average', 'Minimum', 'Maximum']
            st.dataframe(summary_stats, use_container_width=True)
        else:
            st.warning("No homelessness data available for selected boroughs.")
    
    # Greater London Authority chart
    with col2:
        st.markdown("**Greater London Authority**")
        if not gla_plot_df.empty:
            fig_gla = px.line(
                gla_plot_df,
                x='Quarter',
                y='Number of People',
                markers=True,
                title='GLA Homelessness Trends (2023-2026)',
                labels={'Number of People': 'Number of People Seen', 'Quarter': 'Quarter'},
                height=400
            )
            fig_gla.update_traces(line=dict(color='#1f77b4'), marker=dict(size=8))
            fig_gla.update_layout(
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor="rgba(128,128,128,0.2)",
                    linecolor="rgba(128,128,128,0.2)"
                ),
                yaxis=dict(
                    showgrid=True,
                    gridwidth=1,
                    gridcolor="rgba(128,128,128,0.2)",
                    linecolor="rgba(128,128,128,0.2)"
                ),
                hovermode='x unified'
            )
            st.plotly_chart(fig_gla, use_container_width=True)
            
            # Summary statistics for GLA
            st.markdown("**Summary Statistics (GLA)**")
            gla_summary = {
                'Average': gla_plot_df['Number of People'].mean(),
                'Minimum': gla_plot_df['Number of People'].min(),
                'Maximum': gla_plot_df['Number of People'].max()
            }
            gla_summary_df = pd.DataFrame([gla_summary]).round(1)
            st.dataframe(gla_summary_df, use_container_width=True)
        else:
            st.warning("No GLA-wide homelessness data available.")


def display_crime_data(station_name):
    """Display crime data dashboard for relevant boroughs using Metropolitan Police data."""
    st.subheader("Crime")
    
    # Load crime data
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    crime_path = os.path.join(project_root, "BLE_Boroughs_Crime_Data.csv")
    
    @st.cache_data
    def _load_crime_data(path):
        try:
            df = pd.read_csv(path)
            return df
        except Exception as e:
            st.error(f"Could not load crime data at {path}: {e}")
            return None
    
    crime_df = _load_crime_data(crime_path)
    
    if crime_df is None:
        st.warning("Crime data file not available in the workspace.")
        return
    
    # Define target boroughs
    target_boroughs = ["Southwark", "Lambeth", "Lewisham", "Greenwich"]
    
    # Filter to target boroughs only
    crime_df_filtered = crime_df[crime_df['Borough_SNT'].isin(target_boroughs)].copy()
    
    if crime_df_filtered.empty:
        st.warning("No crime data available for the selected boroughs.")
        return
    
    # Get unique boroughs and sort alphabetically
    available_boroughs = sorted(crime_df_filtered['Borough_SNT'].unique())
    
    # Borough selector
    st.markdown("**Select a Borough to View Details:**")
    selected_borough = st.segmented_control(
        "Borough",
        options=available_boroughs,
        default=available_boroughs[0],
        label_visibility="collapsed"
    )
    
    # Filter data for selected borough
    borough_data = crime_df_filtered[crime_df_filtered['Borough_SNT'] == selected_borough].copy()
    
    # Get most recent time period in the data
    borough_data['Month_Year'] = pd.to_datetime(borough_data['Month_Year'], format='%d/%m/%Y')
    latest_month = borough_data['Month_Year'].max()
    latest_month_str = latest_month.strftime('%B %Y')
    
    # Aggregate data by offence group
    offence_group_totals = borough_data.groupby('Offence Group')['Count'].sum().sort_values(ascending=False)
    
    # Calculate total offences
    total_offences = offence_group_totals.sum()
    
    # Display top metric cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Offences",
            value=f"{int(total_offences):,}",
            delta=None
        )
    
    with col2:
        # Calculate percentage breakdown - most common offence
        top_offence = offence_group_totals.index[0]
        top_offence_count = offence_group_totals.iloc[0]
        top_pct = (top_offence_count / total_offences) * 100
        st.metric(
            label=f"Top Offence Type",
            value=top_offence,
            delta=f"{top_pct:.1f}% of total"
        )
    
    with col3:
        # Show data refreshed date
        refresh_date = borough_data['Refresh Date'].iloc[0] if 'Refresh Date' in borough_data.columns else "Unknown"
        st.metric(
            label="Data Last Refreshed",
            value=latest_month_str,
            delta=refresh_date if refresh_date != "Unknown" else None
        )
    
    # Crime Summary Table
    st.markdown("---")
    st.markdown(f"### Crime Summary: {selected_borough}")
    st.markdown("*Study Area Level Crime Data*")
    
    # Create summary table with counts and percentages
    summary_data = []
    for offence_type in offence_group_totals.index:
        count = int(offence_group_totals[offence_type])
        percentage = (offence_group_totals[offence_type] / total_offences * 100)
        summary_data.append({
            'Type of Crime': offence_type.title(),
            'Number': f"{count:,}",
            'Percentage': f"{percentage:.1f}%"
        })
    
    # Add total row
    summary_data.append({
        'Type of Crime': 'Total',
        'Number': f"{int(total_offences):,}",
        'Percentage': '100.0%'
    })
    
    summary_df = pd.DataFrame(summary_data)
    
    # Display as styled table
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
        height=min(400, (len(summary_df) + 1) * 35 + 3)
    )
    
    # Create visualizations in two columns
    st.markdown("---")
    col_left, col_right = st.columns([0.6, 0.4])
    
    # Left column: Time series of offences
    with col_left:
        st.markdown("**How have the volume of offences changed?**")
        
        # Aggregate by month across all offence types
        ts_data = borough_data.groupby('Month_Year')['Count'].sum().reset_index()
        ts_data = ts_data.sort_values('Month_Year')
        ts_data.columns = ['Month', 'Offences']
        
        # Create time series chart
        fig_ts = px.line(
            ts_data,
            x='Month',
            y='Offences',
            markers=True,
            title=f'{selected_borough} - Offence Trends Over Time',
            labels={'Offences': 'Number of Offences', 'Month': 'Month'},
            height=400
        )
        
        fig_ts.update_traces(
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=6)
        )
        
        fig_ts.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
                linecolor="rgba(128,128,128,0.2)"
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
                linecolor="rgba(128,128,128,0.2)"
            ),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_ts, use_container_width=True)
    
    # Right column: Offence type breakdown (horizontal bar chart)
    with col_right:
        st.markdown("**What are the volumes by Offence Type?**")
        
        # Prepare data for bar chart - top 10 offence groups
        top_n = 10
        chart_data = offence_group_totals.head(top_n).reset_index()
        chart_data.columns = ['Offence Type', 'Count']
        chart_data = chart_data.sort_values('Count', ascending=True)  # Sort ascending for horizontal bar
        
        # Calculate percentages
        chart_data['Percentage'] = (chart_data['Count'] / total_offences * 100).round(1)
        chart_data['Label'] = chart_data['Percentage'].astype(str) + '%'
        
        fig_bar = px.bar(
            chart_data,
            y='Offence Type',
            x='Count',
            orientation='h',
            title=f'Top {top_n} Offence Types in {selected_borough}',
            labels={'Count': 'Number of Offences', 'Offence Type': ''},
            height=400,
            text='Label'
        )
        
        fig_bar.update_traces(
            marker_color='#0066cc',
            textposition='outside'
        )
        
        fig_bar.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
                linecolor="rgba(128,128,128,0.2)"
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
                linecolor="rgba(128,128,128,0.2)"
            ),
            hovermode='y unified'
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Detailed breakdown section
    st.markdown("---")
    st.markdown(f"**Detailed Crime Breakdown for {selected_borough}**")
    
    # Create expandable sections for each offence group
    offence_groups = borough_data['Offence Group'].unique()
    
    for offence_group in sorted(offence_groups):
        offence_data = borough_data[borough_data['Offence Group'] == offence_group]
        group_total = offence_data['Count'].sum()
        group_pct = (group_total / total_offences) * 100
        
        with st.expander(f"{offence_group} ({int(group_total)} offences, {group_pct:.1f}%)"):
            # Breakdown by subgroup
            subgroup_data = offence_data.groupby('Offence Subgroup')['Count'].sum().sort_values(ascending=False)
            
            # Create a table
            subgroup_df = pd.DataFrame({
                'Offence Subgroup': subgroup_data.index,
                'Count': subgroup_data.values,
                'Percentage': (subgroup_data.values / group_total * 100).round(1)
            })
            
            st.dataframe(subgroup_df, use_container_width=True, hide_index=True)
    
    # Summary statistics at the bottom
    st.markdown("---")
    st.markdown("**Summary Statistics**")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        avg_monthly = borough_data.groupby('Month_Year')['Count'].sum().mean()
        st.metric("Average Monthly Offences", f"{int(avg_monthly):,}")
    
    with summary_col2:
        monthly_totals = borough_data.groupby('Month_Year')['Count'].sum()
        max_month = monthly_totals.idxmax().strftime('%B %Y')
        max_count = int(monthly_totals.max())
        st.metric("Peak Month", max_month, delta=f"{max_count} offences")
    
    with summary_col3:
        min_month = monthly_totals.idxmin().strftime('%B %Y')
        min_count = int(monthly_totals.min())
        st.metric("Lowest Month", min_month, delta=f"{min_count} offences")


def display_population_growth_data(station_name):
    """Display population projection charts and age-group breakdowns.

    Shows overall population growth lines for the four boroughs (All ages)
    and provides a borough selector that displays population for three
    age categories (0-15, 16-64, 65+) as both a table and a line chart.
    """
    st.subheader("Population Growth")

    # Load population projections data from project root
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pop_path = os.path.join(project_root, "BLE_Population Projections Data.csv")

    @st.cache_data
    def _load_pop_data(path):
        try:
            df = pd.read_csv(path, dtype=str)
            return df
        except Exception as e:
            st.error(f"Could not load population projections at {path}: {e}")
            return None

    pop_df = _load_pop_data(pop_path)
    if pop_df is None:
        st.warning("Population projections data file not available in the workspace.")
        return

    # Target boroughs
    target_boroughs = ["Lambeth", "Southwark", "Lewisham", "Greenwich"]

    # Determine year columns (numeric year headers)
    year_cols = [c for c in pop_df.columns if c.isdigit()]
    if not year_cols:
        st.error("No year columns found in population projections data.")
        return

    # Helper to parse AGE_GROUP into numeric where possible, treat '90 and over' as 90
    def parse_age_label(age_label):
        try:
            return int(age_label)
        except Exception:
            if isinstance(age_label, str) and '90' in age_label:
                return 90
            return None

    # ------------------------------------------------------------------
    # 1) Overall population growth chart for the 4 boroughs (All ages)
    overall_rows = pop_df[(pop_df['AREA_NAME'].isin(target_boroughs)) & (pop_df['AGE_GROUP'].str.strip().str.lower() == 'all ages')]
    if overall_rows.empty:
        st.warning("No 'All ages' rows found for target boroughs in population projections.")
    else:
        # Melt to long form for plotting
        overall_long = overall_rows.melt(id_vars=['AREA_CODE', 'AREA_NAME'], value_vars=year_cols, var_name='Year', value_name='Population')
        overall_long['Population'] = pd.to_numeric(overall_long['Population'], errors='coerce')
        overall_long = overall_long.dropna(subset=['Population'])

        fig_overall = px.line(
            overall_long,
            x='Year',
            y='Population',
            color='AREA_NAME',
            markers=True,
            title='Projected Total Population by Borough (All ages)'
        )
        fig_overall.update_layout(
            xaxis=dict(tickmode='array', tickvals=year_cols[::2]),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            legend_title_text='Borough'
        )
        st.plotly_chart(fig_overall, use_container_width=True)

    st.markdown('---')

    # ------------------------------------------------------------------
    # 2) Age-category breakdown for a selected borough
    st.markdown("**Borough-level age group projections**")
    available_boroughs = sorted(set(pop_df['AREA_NAME']).intersection(set(target_boroughs)))
    if not available_boroughs:
        st.warning("No target boroughs found in population projections data.")
        return

    # Borough selector (segmented control if available otherwise selectbox)
    try:
        selected_borough = st.segmented_control("Select borough", options=available_boroughs, label_visibility='collapsed')
    except Exception:
        selected_borough = st.selectbox("Select borough", options=available_boroughs)

    borough_rows = pop_df[pop_df['AREA_NAME'] == selected_borough].copy()

    # Exclude 'All ages' rows when computing age group sums
    age_rows = borough_rows[borough_rows['AGE_GROUP'].str.strip().str.lower() != 'all ages']

    # Map AGE_GROUP to numeric start age and create age-category column
    def age_category(age_label):
        parsed = parse_age_label(age_label)
        if parsed is None:
            return None
        if parsed <= 15:
            return '0-15'
        if 16 <= parsed <= 64:
            return '16-64'
        return '65+'

    age_rows['AGE_NUM'] = age_rows['AGE_GROUP'].apply(parse_age_label)
    age_rows['AGE_CAT'] = age_rows['AGE_GROUP'].apply(age_category)

    # Sum populations by age category and year
    age_cat_summaries = []
    for cat in ['0-15', '16-64', '65+']:
        subset = age_rows[age_rows['AGE_CAT'] == cat]
        if subset.empty:
            continue
        sums = subset[year_cols].apply(pd.to_numeric, errors='coerce').sum(axis=0)
        for year in year_cols:
            age_cat_summaries.append({'Age Category': cat, 'Year': year, 'Population': sums.get(year, pd.NA)})

    age_cat_df = pd.DataFrame(age_cat_summaries)
    if age_cat_df.empty:
        st.warning(f"No age-group data available for {selected_borough}.")
        return

    # Line chart for age categories
    fig_age = px.line(age_cat_df, x='Year', y='Population', color='Age Category', markers=True,
                      title=f'Population by Age Category - {selected_borough}')
    fig_age.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_age, use_container_width=True)

    # Table of age-category numbers (wide format)
    age_table = age_cat_df.pivot(index='Year', columns='Age Category', values='Population').reset_index()
    age_table[ ['0-15','16-64','65+'] ] = age_table[['0-15','16-64','65+']].apply(pd.to_numeric, errors='coerce')
    st.markdown(f"**Population numbers by age category for {selected_borough}**")
    st.dataframe(age_table.fillna(0).astype(int), use_container_width=True)

    # Simple summary statistics
    st.markdown('---')
    st.markdown('**Summary statistics (selected borough)**')
    avg_growth = overall_rows[overall_rows['AREA_NAME'] == selected_borough][year_cols].astype(float).T.pct_change().mean().mean() if not overall_rows.empty else None
    c1, c2 = st.columns(2)
    with c1:
        if avg_growth is not None:
            st.metric('Average yearly growth (approx)', f"{avg_growth*100:.2f}%")
        else:
            st.metric('Average yearly growth (approx)', 'N/A')
    with c2:
        latest_total = borough_rows[borough_rows['AGE_GROUP'].str.strip().str.lower() == 'all ages'][year_cols].apply(pd.to_numeric, errors='coerce').sum(axis=1).values
        latest_val = int(latest_total[0]) if len(latest_total) else 'N/A'
        st.metric('Latest projected total (All ages)', f"{latest_val:,}" if latest_val != 'N/A' else 'N/A')

def main():
    """Main Streamlit application."""
    st.title("Bakerloo Line Extension")
    st.subheader("Equalities Impact Assessment Dashboard")
    
    # Station selector in sidebar
    station_name = st.sidebar.selectbox(
        "Select Station",
        list(STATIONS.keys())
    )
    
    if station_name:
        # Create two columns for the header section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header(f"{station_name} Demographics")
        
        with col2:
            # Display ward information in a more compact format
            st.markdown("**Local Study Area Wards:**")
            ward_names = [ward["name"] for ward in STATIONS[station_name]["wards"]]
            st.markdown(", ".join(ward_names))
        
        st.markdown("---")  # Add a separator
        
        # Display tabs for different demographic categories plus placeholders
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
            "Age Distribution",
            "Gender",
            "Ethnicity",
            "Religion",
            "Sexual Orientation",
            "Languages",
            "Deprivation",
            "Homelessness",
            "Crime",
            "Population Growth"
        ])
        
        with tab1:
            display_age_data(station_name)
            
        with tab2:
            display_gender_data(station_name)
        
        with tab3:
            display_ethnicity_data(station_name)
            
        with tab4:
            display_religion_data(station_name)

        with tab5:
            display_sexual_orientation_data(station_name)

        with tab6:
            display_languages_data(station_name)

        with tab7:
            display_deprivation_data(station_name)

        with tab8:
            display_homelessness_data(station_name)

        with tab9:
            display_crime_data(station_name)

        with tab10:
            display_population_growth_data(station_name)

if __name__ == "__main__":
    main()