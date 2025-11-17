# File: /bakerloo-line-extension/bakerloo-line-extension/src/config/station_config.py

# Configuration settings for the Bakerloo Line Extension Equalities Impact Assessment project

# Station configurations with ward NOMIS API codes
STATIONS = {
    "Lambeth North": {
        "parent_borough": "Lambeth",
        "wards": [
            {"name": "Waterloo and South Bank", "nomis_code": "641735110"},
            {"name": "Borough and Bankside", "nomis_code": "641732386"},
            {"name": "Kennington", "nomis_code": "641735097"},
            {"name": "St George's", "nomis_code": "641732405"},
            {"name": "Chaucer", "nomis_code": "641732389"},
            {"name": "North Walworth", "nomis_code": "641732396"}
        ]
    },
    "London Road": {
        "parent_borough": "Southwark",
        "wards": [
            {"name": "Waterloo and South Bank", "nomis_code": "641735110"},
            {"name": "St George's", "nomis_code": "641732405"},
            {"name": "Borough and Bankside", "nomis_code": "641732386"},
            {"name": "Kennington", "nomis_code": "641735097"}
        ]
    },
    "Elephant & Castle": {
        "parent_borough": "Southwark",
        "wards": [
            {"name": "St George's", "nomis_code": "641732405"},
            {"name": "Kennington", "nomis_code": "641735097"},
            {"name": "Newington", "nomis_code": "641732396"},
            {"name": "North Walworth", "nomis_code": "641732396"},
            {"name": "Chaucer", "nomis_code": "641732389"},
            {"name": "Borough and Bankside", "nomis_code": "641732386"}
        ]
    },
    "Burgess Park": {
        "parent_borough": "Southwark",
        "wards": [
            {"name": "North Walworth", "nomis_code": "641732396"},
            {"name": "Faraday", "nomis_code": "641732393"},
            {"name": "Old Kent Road", "nomis_code": "641732399"},
            {"name": "South Bermondsey", "nomis_code": "641732407"},
            {"name": "London Bridge & West Bermondsey", "nomis_code": "641732395"}
        ]
    },
    "Old Kent Road": {
        "parent_borough": "Southwark",
        "wards": [
            {"name": "Old Kent Road", "nomis_code": "641732399"},
            {"name": "Peckham", "nomis_code": "641732400"},
            {"name": "Nunhead & Queen's Road", "nomis_code": "641732398"},
            {"name": "Telegraph Hill", "nomis_code": "641734724"}
        ]
    },
    "New Cross Gate": {
        "parent_borough": "Lewisham",
        "wards": [
            {"name": "New Cross", "nomis_code": "641734720"},
            {"name": "Telegraph Hill", "nomis_code": "641734724"},
            {"name": "Brockley", "nomis_code": "641734708"},
            {"name": "Deptford", "nomis_code": "641734711"}
        ]
    },
    "Lewisham Way Shaft": {
        "parent_borough": "Lewisham",
        "wards": [
            {"name": "Brockley", "nomis_code": "641734708"},
            {"name": "Deptford", "nomis_code": "641734711"},
            {"name": "Lewisham", "nomis_code": "641734716"}
        ]
    },
    "Lewisham": {
        "parent_borough": "Lewisham",
        "wards": [
            {"name": "Ladywell", "nomis_code": "641734716"},
            {"name": "Lewisham Central", "nomis_code": "641734719"},
            {"name": "Greenwich Park", "nomis_code": "641735073"},
            {"name": "Blackheath", "nomis_code": "641735074"}
        ]
    },
    "Wearside Road": {
        "parent_borough": "Lewisham",
        "wards": [
            {"name": "Ladywell", "nomis_code": "641734716"},
            {"name": "Lewisham Central", "nomis_code": "641734719"},
            {"name": "Lee Green", "nomis_code": "641734718"}
        ]
    }
}

# Comparison area NOMIS codes
COMPARISON_AREAS = {
    "Lambeth": "1778385156",
    "Southwark": "1778385187",
    "Lewisham": "1778385154",
    "Greenwich": "1778385144",
    "London": "2013265927",
    "England": "2092957699"
}

# NOMIS Dataset IDs
NOMIS_DATASETS = {
    'age': 'NM_2018_1',
    'gender': 'NM_2028_1',
    'ethnicity': 'NM_2041_1',
    'religion': 'NM_2049_1',
    'sexual_orientation': 'NM_2086_1',
    'languages': 'NM_2043_1'
}