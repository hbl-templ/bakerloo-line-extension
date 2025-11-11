def fetch_nomis_data(nomis_code):
    """Fetch demographic data from the NOMIS API for a given NOMIS code."""
    if not nomis_code:
        return None

    base_url = "https://www.nomisweb.co.uk/api/v01/dataset/NM_2021_1.jsonstat.json"
    params = {
        "date": "latest",
        "geography": nomis_code,
        "c2021_restype_3": "0",
        "measures": "20100"
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data for NOMIS code {nomis_code}: {e}")
        return None


def get_demographic_data(nomis_codes):
    """Retrieve demographic data for a list of NOMIS codes."""
    demographic_data = {}
    for code in nomis_codes:
        data = fetch_nomis_data(code)
        if data:
            demographic_data[code] = data
    return demographic_data


def parse_nomis_response(response):
    """Parse the response from the NOMIS API to extract relevant demographic information."""
    if not response:
        return {}

    # Extract relevant data from the response
    # This will depend on the structure of the response
    # Example: Extracting population data
    try:
        population_data = response['value']
        return {
            "population": population_data
        }
    except KeyError:
        print("Error parsing response data.")
        return {}


def fetch_and_process_nomis_data(nomis_codes):
    """Fetch and process NOMIS data for the specified NOMIS codes."""
    raw_data = get_demographic_data(nomis_codes)
    processed_data = {}
    
    for code, response in raw_data.items():
        processed_data[code] = parse_nomis_response(response)
    
    return processed_data