# Bakerloo Line Extension Equalities Impact Assessment

This project aims to assess the equalities impact of the Bakerloo Line Extension by generating comparative data tables and visualizations for nine different sites along the Bakerloo line in London. The analysis includes data from various areas, including the Local Study Area, Southwark, London, and England.

## Project Structure

```
bakerloo-line-extension
├── src
│   ├── app.py                  # Main entry point of the application
│   ├── data_handlers
│   │   ├── __init__.py         # Initializes the data_handlers module
│   │   ├── census_data.py      # Functions to fetch and process ONS Census data
│   │   └── nomis_api.py        # Functions to interact with the NOMIS API
│   ├── visualization
│   │   ├── __init__.py         # Initializes the visualization module
│   │   └── charts.py           # Functions to create visualizations based on census data
│   ├── config
│   │   ├── __init__.py         # Initializes the config module
│   │   └── station_config.py    # Configuration settings for each of the 9 stations
│   └── utils
│       ├── __init__.py         # Initializes the utils module
│       └── data_processing.py   # Utility functions for data processing
├── data
│   ├── ward_mappings.csv       # Mappings of NOMIS ward areas to local study areas
│   └── station_areas.json      # Geographical and demographic information for each station
├── tests
│   └── __init__.py             # Initializes the tests module
├── requirements.txt             # Lists project dependencies
└── README.md                    # Project documentation
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd bakerloo-line-extension
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python src/app.py
   ```

## Usage Guidelines

- Access the application through your web browser to view the comparative data tables and visualizations for each of the nine sites.
- The application provides insights into demographic data and equalities impact assessments based on the latest ONS Census data.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.