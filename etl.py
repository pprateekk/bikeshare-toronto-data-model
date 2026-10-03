import pandas as pd
import numpy as np
import json
from pathlib import Path
import psycopg
from ddl_queries import (create_stations_table, create_bikes_table, create_trips_table, create_rejected_table, drop_trips_table, drop_stations_table, drop_bikes_table, drop_rejected_table)

import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

#load data
def extract_data():
    trips_raw = pd.read_csv(Path('data/raw/bikeshare_ridership-2024.csv'))

    with open(Path('data/raw/station_information.json')) as f:
        stations_raw = pd.json_normalize(json.load(f)["data"]["stations"])
    
    stations_raw["station_id"] = stations_raw["station_id"].astype("int64") #convert station_id from string to int
    trips_raw.columns = trips_raw.columns.str.lower()

    return trips_raw, stations_raw

#transform data

def transform_trips(trips_raw):
    df = trips_raw.rename(columns={"trip_duration": "duration_sec"})
    df["start_time"] = pd.to_datetime(df["start_time"], format = "%Y-%m-%d %H:%M:%S")
    df["end_time"] = pd.to_datetime(df["end_time"], format = "%Y-%m-%d %H:%M:%S")
    df["end_station_id"] = df["end_station_id"].astype("Int64")

    #filter out "invalid" trips
    #a valid trip = has an end station, has an end time and has trip_duration > 0
    no_end_station = df["end_station_id"].isna()
    no_end_time = df["end_time"].isna()
    invalid_duration = df["duration_sec"] <= 0

    df["reject_reason"] = np.select(
        [no_end_station & no_end_time, 
         no_end_station,
         no_end_time,
         invalid_duration
        ], 
        ["no end station and no end time", 
         "no end station", 
         "no end time", 
         "zero duration"
        ], default=""
    )

    is_valid = df["reject_reason"] == ""

    #select all valid trips
    trips = df.loc[is_valid, ["trip_id", "start_time", "end_time", "duration_sec", "start_station_id", "end_station_id", "bike_id", "user_type"]]

    #all rejected trips w reason for rejection
    rejected_trips = df.loc[~is_valid, ["trip_id", "start_time", "end_time", "duration_sec", "start_station_id", "end_station_id", "bike_id", "user_type", "reject_reason"]]

    return trips, rejected_trips

def build_stations(trips_raw, stations_raw):
    start_stations = trips_raw[["start_station_id", "start_station_name"]].rename(columns={"start_station_id": "station_id", "start_station_name": "station_name"})
    end_stations = trips_raw[["end_station_id", "end_station_name"]].rename(columns={"end_station_id": "station_id", "end_station_name": "station_name"})
    
    stations = pd.concat([start_stations, end_stations]).drop_duplicates(subset=["station_id"])

    #get every station in 2024 and merge w station info from station_information.json
    stations = stations.merge(stations_raw[["station_id", "lat", "lon", "capacity"]], on="station_id", how="left")

    stations = stations.rename(columns={"lat": "latitude", "lon": "longitude"})
    
    stations["capacity"] = stations["capacity"].astype("Int64")

    return stations

def build_bikes(trips_raw):
    bikes = trips_raw[["bike_id", "bike_model"]].drop_duplicates(subset=["bike_id"])
    return bikes

#load

def create_tables(conn):
    statement = [drop_rejected_table, drop_trips_table, drop_stations_table, drop_bikes_table, create_stations_table, create_bikes_table, create_trips_table, create_rejected_table]

    with conn.cursor() as cur:
        for s in statement:
            cur.execute(s)
        conn.commit()

def load_data(conn, df, table, chunk_size=500_000):
    columns = ', '.join(df.columns)

    #using COPY for faster loading (6.9M records), much faster than using INSERT INTO or to_sql()
    sql = f"COPY {table} ({columns}) FROM STDIN WITH (FORMAT csv)" 

    with conn.cursor() as cur:
        with cur.copy(sql) as copy:
            for i in range(0, len(df), chunk_size):
                chunk = df.iloc[i:i+chunk_size]
                csv_data = chunk.to_csv(index=False, header=False)
                copy.write(csv_data)
    
    conn.commit()

    print(f"loaded {len(df)} rows into {table} table")


#main
def main():
    #extract
    trips_raw, stations_raw = extract_data()

    #transform
    trips, rejected_trips = transform_trips(trips_raw)
    stations = build_stations(trips_raw, stations_raw)
    bikes = build_bikes(trips_raw)

    print(f"raw trips: {len(trips_raw)}")
    print(f"valid trips: {len(trips)}")
    print(f"rejected trips: {len(rejected_trips)}")
    print(f"stations: {len(stations)}")
    print(f"bikes: {len(bikes)}")

    #load
    #connect to db and create tables
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            create_tables(conn)

            #load data into tables
            load_data(conn, stations, "stations")
            load_data(conn, bikes, "bikes")
            load_data(conn, trips, "trips")
            load_data(conn, rejected_trips, "rejected_trips")
    except Exception as e:
        print(f"ETL failed: {e}")
        raise e

if __name__ == "__main__":
    main()

