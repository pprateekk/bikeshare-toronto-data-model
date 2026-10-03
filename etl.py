import pandas as pd
import json
from pathlib import Path

#load data
def extract_data():
    trips_raw = pd.read_csv(Path('data/raw/bikeshare_ridership-2024.csv'))

    with open(Path('data/raw/station_information.json')) as f:
        stations_raw = pd.json_normalize(json.load(f)["data"]["stations"])
    
    stations_raw["station_id"] = stations_raw["station_id"].astype(int64) #convert station_id from string to int
    trips_raw.columns = trips_raw.columns.str.lower()

    return trips_raw, stations_raw

#transform data

def transform_trips(trips_raw):
    df = trips_raw.rename(columns={"trip_duration": "duration_sec"})
    df["start_time"] = pd.to_datetime(df["start_time"], format = "%Y-%m-%d %H:%M:%S")
    df["end_time"] = pd.to_datetime(df["end_time"], format = "%Y-%m-%d %H:%M:%S")
    df["end_station_id"] = df["end_station_id"].astype("Int64")

    #filter out "invalid" trips
    #a valid trip would be that has an end station, has an end time and has trip_duration > 0
