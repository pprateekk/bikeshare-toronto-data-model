#create tables
create_stations_table = """CREATE TABLE IF NOT EXISTS stations (station_id INT PRIMARY KEY, 
                                                                station_name VARCHAR(100) NOT NULL, 
                                                                latitude DECIMAL(10,8),
                                                                longitude DECIMAL(11,8),
                                                                capacity INT
);
"""


create_bikes_table = """CREATE TABLE IF NOT EXISTS bikes (bike_id INT PRIMARY KEY,
                                                          bike_model TEXT NOT NULL
                                                            CHECK (bike_model IN ('ICONIC', 'EFIT', 'EFIT G5')) 
);
"""

create_trips_table = """CREATE TABLE IF NOT EXISTS trips (trip_id BIGINT PRIMARY KEY,
                                                          start_time TIMESTAMP NOT NULL,
                                                          end_time TIMESTAMP NOT NULL,
                                                          trip_duration_sec INT NOT NULL
                                                            CHECK (trip_duration_sec > 0),
                                                          start_station_id INT NOT NULL,
                                                          end_station_id INT NOT NULL,
                                                          bike_id INT NOT NULL,
                                                          user_type TEXT NOT NULL CHECK (user_type IN ('Member', 'Casual'))

                                                          FOREIGN KEY (start_station_id) REFERENCES stations(station_id),
                                                          FOREIGN KEY (end_station_id) REFERENCES stations(station_id),
                                                          FOREIGN KEY (bike_id) REFERENCES bikes(bike_id)
);
"""

create_rejected_table = """CREATE TABLE IF NOT EXISTS rejected_trips (trip_id TEXT,
                                                                      start_time TEXT,
                                                                      end_time TEXT,
                                                                      trip_duration_sec TEXT,
                                                                      start_station_id TEXT,
                                                                      end_station_id TEXT,
                                                                      bike_id TEXT,
                                                                      user_type TEXT,
                                                                      reject_reason TEXT
);
"""

#drop tables
drop_trips_table = "DROP TABLE IF EXISTS trips CASCADE;"
drop_stations_table = "DROP TABLE IF EXISTS stations CASCADE;"
drop_bikes_table = "DROP TABLE IF EXISTS bikes CASCADE;"
drop_rejected_table = "DROP TABLE IF EXISTS rejected_trips;"
