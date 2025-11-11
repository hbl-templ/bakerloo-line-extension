from flask import Flask, render_template, request
from data_handlers.census_data import fetch_census_data
from data_handlers.nomis_api import fetch_nomis_data
from config.station_config import STATION_CONFIG

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<station_name>')
def station(station_name):
    if station_name not in STATION_CONFIG:
        return "Station not found", 404

    local_study_area = STATION_CONFIG[station_name]['local_study_area']
    census_data = fetch_census_data(local_study_area)
    nomis_data = fetch_nomis_data(local_study_area)

    return render_template('station.html', 
                           station=station_name, 
                           census_data=census_data, 
                           nomis_data=nomis_data)

if __name__ == '__main__':
    app.run(debug=True)