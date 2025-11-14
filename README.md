# Bakerloo Line Extension Equalities Impact Assessment

An interactive Streamlit dashboard for assessing the equalities impact of the proposed Bakerloo Line Extension across nine station sites in South London. The application visualizes demographic, socioeconomic, and crime data to support equalities impact assessment analysis.

## Overview

This dashboard provides comprehensive demographic analysis for each proposed station along the Bakerloo Line Extension, comparing Local Study Area (LSA) data against Southwark, London, and England benchmarks. The tool combines Census 2021 data from the NOMIS API with local datasets on deprivation, homelessness, crime, and population projections.

## Features

The application provides eight interactive data visualization tabs:

1. **Age Distribution** - Census 2021 age band data with detailed and broad age categories
2. **Gender** - Gender distribution comparisons across geographic areas
3. **Ethnicity** - Ethnic group breakdowns with percentage comparisons
4. **Religion** - Religious affiliation data from Census 2021
5. **Deprivation** - IMD 2025 data showing deprivation quintiles and domain-level analysis for LSOAs
6. **Homelessness** - GLA CHAIN data (2023-2025) showing trends across target boroughs
7. **Crime** - Metropolitan Police crime statistics by borough and offense type
8. **Population Growth** - GLA population projections by age category and borough

### Station Coverage

The dashboard covers nine proposed station sites:
- Lambeth North
- London Road
- Elephant & Castle
- Burgess Park
- Old Kent Road
- New Cross Gate
- Lewisham Way Shaft
- Lewisham
- Wearside Road

### Geographic Coverage

**Target Boroughs:** Lambeth, Southwark, Lewisham, Greenwich  
**Comparison Areas:** Local Study Area (ward-aggregated), Southwark, London, England

## Project Structure

```
bakerloo-line-extension/
├── src/
│   ├── streamlit_app.py        # Main Streamlit application
│   ├── config/
│   │   ├── __init__.py
│   │   └── station_config.py   # Station and ward configurations, NOMIS dataset IDs
│   ├── data_handlers/
│   │   ├── __init__.py
│   │   ├── census_data.py      # Census data processing functions
│   │   └── nomis_api.py        # NOMIS API interaction utilities
│   ├── utils/
│   │   ├── __init__.py
│   │   └── data_processing.py  # Data transformation utilities
│   └── visualization/
│       ├── __init__.py
│       └── charts.py           # Visualization helper functions
├── data/
│   ├── station_areas.json      # Geographic station metadata
│   └── ward_mappings.csv       # Ward to LSOA mappings
├── tests/
│   └── __init__.py
├── API to ONS Codes Complete.csv
├── BLE_Boroughs_Crime_Data.csv
├── BLE_Population Projections Data.csv
├── GLA Homelessness Data 23-25.csv
├── Housing Affordability Ratios.csv
├── IMD 2025.csv
├── LSOA to WD to LA Lookup.csv
├── requirements.txt
└── README.md
```

## Dependencies

The application requires the following Python packages (see `requirements.txt`):

- **streamlit** (1.29.0) - Web application framework
- **pandas** (2.1.3) - Data manipulation and analysis
- **plotly** (5.18.0) - Interactive visualizations
- **requests** (2.31.0) - HTTP library for NOMIS API calls
- **numpy** (1.26.2) - Numerical computing
- **matplotlib** (3.8.2) - Additional plotting capabilities
- **seaborn** (0.13.0) - Statistical data visualization
- **xarray** (2023.11.0) - Multi-dimensional data arrays

## How It Works

### Data Sources

1. **NOMIS API (Census 2021)**
   - Age distribution (TS007A - NM_2018_1)
   - Gender (TS008 - NM_2023_1)
   - Ethnicity (TS021 - NM_2041_1)
   - Religion (TS030 - NM_2049_1)
   - Fetched dynamically with caching and retry logic

2. **Local CSV Files**
   - `IMD 2025.csv` - Index of Multiple Deprivation data
   - `GLA Homelessness Data 23-25.csv` - CHAIN homelessness statistics
   - `BLE_Boroughs_Crime_Data.csv` - Metropolitan Police crime data
   - `BLE_Population Projections Data.csv` - GLA population forecasts
   - `LSOA to WD to LA Lookup.csv` - Geographic lookup tables

### Data Processing

1. **Local Study Area Calculation**
   - Ward-level data is fetched for each station's constituent wards (defined in `station_config.py`)
   - Values are averaged across wards to create LSA aggregates
   - Comparison areas (Southwark, London, England) are fetched separately

2. **Caching Strategy**
   - All NOMIS API calls use `@st.cache_data` to minimize API requests
   - CSV data loading is cached for performance
   - Retry logic handles transient API failures (429, 502, 503, 504 errors)

3. **Visualization**
   - Plotly bar charts and line graphs with consistent color scheme
   - Red/blue palette for area comparisons
   - Interactive hover details and responsive layouts
   - Pivot tables for detailed data exploration

### Key Functions

- `fetch_nomis_data()` - Retrieves data from NOMIS API with error handling
- `calculate_lsa_average()` - Aggregates ward data for Local Study Area
- `display_*_data()` - Individual functions for each data tab (age, gender, ethnicity, etc.)
- `_extract_nomis_percentages()` - Parses NOMIS API response formats

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd bakerloo-line-extension
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Mac/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ensure data files are present:**
   - Verify all CSV files are in the project root directory
   - Check that `data/station_areas.json` and `data/ward_mappings.csv` exist

5. **Run the Streamlit application:**
   ```bash
   streamlit run src/streamlit_app.py
   ```

6. **Access the dashboard:**
   - The application will open automatically in your default browser
   - Default URL: `http://localhost:8501`

## Usage

1. **Select a Station** - Use the sidebar dropdown to choose a station site
2. **View Ward Information** - The header displays constituent wards for the selected Local Study Area
3. **Navigate Tabs** - Click through the eight data tabs to explore different demographic dimensions
4. **Interact with Charts** - Hover for details, zoom, and download charts using Plotly controls
5. **Review Tables** - Detailed data tables appear below each visualization

## Configuration

Station and ward configurations are managed in `src/config/station_config.py`:

- `STATIONS` - Dictionary mapping station names to ward lists with NOMIS codes
- `COMPARISON_AREAS` - NOMIS geography codes for comparison regions
- `NOMIS_DATASETS` - Dataset IDs for different Census tables

To add new stations or modify ward boundaries, update the `STATIONS` dictionary with appropriate ward names and NOMIS geography codes.

## Troubleshooting

**NOMIS API Errors:**
- The application includes retry logic for rate limiting and server errors
- Check your internet connection if data fails to load
- NOMIS API documentation: https://www.nomisweb.co.uk/api/v01/help

**Missing Data Files:**
- Ensure all CSV files are in the correct directory (project root)
- Verify file names match exactly (case-sensitive)

**Performance Issues:**
- Clear Streamlit cache: Click "Clear cache" in the hamburger menu
- First load may be slow due to API calls; subsequent loads use cached data

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Open a Pull Request

## License

[Specify license information]

## Contact

[Add contact information or project maintainer details]