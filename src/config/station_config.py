# File: /bakerloo-line-extension/bakerloo-line-extension/src/config/station_config.py

# Configuration settings for the Bakerloo Line Extension Equalities Impact Assessment project

# Station configurations with ward NOMIS API codes
STATIONS = {
    "Lambeth North": {
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
        "wards": [
            {"name": "Waterloo and South Bank", "nomis_code": "641735110"},
            {"name": "St George's", "nomis_code": "641732405"},
            {"name": "Borough and Bankside", "nomis_code": "641732386"},
            {"name": "Kennington", "nomis_code": "641735097"}
        ]
    },
    "Elephant & Castle": {
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
        "wards": [
            {"name": "North Walworth", "nomis_code": "641732396"},
            {"name": "Faraday", "nomis_code": "641732393"},
            {"name": "Old Kent Road", "nomis_code": "641732399"},
            {"name": "South Bermondsey", "nomis_code": "641732407"},
            {"name": "London Bridge & West Bermondsey", "nomis_code": "641732395"}
        ]
    },
    "Old Kent Road": {
        "wards": [
            {"name": "Old Kent Road", "nomis_code": "641732399"},
            {"name": "Peckham", "nomis_code": "641732400"},
            {"name": "Nunhead & Queen's Road", "nomis_code": "641732398"},
            {"name": "Telegraph Hill", "nomis_code": "641734724"}
        ]
    },
    "New Cross Gate": {
        "wards": [
            {"name": "New Cross", "nomis_code": "641734720"},
            {"name": "Telegraph Hill", "nomis_code": "641734724"},
            {"name": "Brockley", "nomis_code": "641734708"},
            {"name": "Deptford", "nomis_code": "641734711"}
        ]
    },
    "Lewisham Way Shaft": {
        "wards": [
            {"name": "Brockley", "nomis_code": "641734708"},
            {"name": "Deptford", "nomis_code": "641734711"},
            {"name": "Lewisham", "nomis_code": "641734716"}
        ]
    },
    "Lewisham": {
        "wards": [
            {"name": "Ladywell", "nomis_code": "641734716"},
            {"name": "Lewisham Central", "nomis_code": "641734719"},
            {"name": "Greenwich Park", "nomis_code": "641735073"},
            {"name": "Blackheath", "nomis_code": "641735074"}
        ]
    },
    "Wearside Road": {
        "wards": [
            {"name": "Ladywell", "nomis_code": "641734716"},
            {"name": "Lewisham Central", "nomis_code": "641734719"},
            {"name": "Lee Green", "nomis_code": "641734718"}
        ]
    }
}

# Comparison area NOMIS codes
COMPARISON_AREAS = {
    "Southwark": "1778385187",
    "London": "2013265927",
    "England": "2092957699"
}

# NOMIS Dataset IDs
NOMIS_DATASETS = {
    "population": "NM_2021_1",
    "age": "NM_2018_1",
    "ethnicity": "NM_2041_1",
    "religion": "NM_2049_1",
    "disability": "C2021TS038",
    "gender": "NM_2023_1"  # Census 2021 Sex (TS008)
}