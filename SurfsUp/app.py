# Import the dependencies.
import numpy as np
import pandas as pd
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify



#################################################
# Database Setup
#################################################


# reflect an existing database into a new model
#database_path = Path("./Resources/hawaii.sqlite")

engine = create_engine(f"sqlite:///Resources/hawaii.sqlite")

# reflect the tables
Base = automap_base()
Base.prepare(autoload_with=engine)


# Save references to each table
station = Base.classes.station
measurement = Base.classes.measurement


#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Welcome. Here are the Available API Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&ltstart&gt<br/>"
        f"/api/v1.0/&ltstart&gt/&ltend&gt"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():

    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    # finding most recent date in dataset
    most_recent = session.query(measurement.date).order_by(measurement.date.desc()).limit(1).all()
    most_recent = np.ravel(most_recent)[0] # extracting only date string

    year, month, day = most_recent.split('-') # splitting into year, month, day

    # finding date a year before last date in dataset
    # converting year, month, day into integer to convert to datetime format
    # subtracting one year to get year before last date
    year_ago = dt.datetime(int(year),
                           int(month),
                           int(day)) - dt.timedelta(days=366)

    # querying for dates and precip measurements in last year of dataset
    last_year_precipitation = session.query(measurement.date, measurement.prcp).\
    filter(measurement.date <= dt.datetime(
        int(year),
        int(month),
        int(day)
    )).\
    filter(measurement.date >= year_ago).\
    all()

    # creating a list to hold dictionaries of date and precip info for all entries in last year of dataset
    all_precip = []
    for date, prcp in last_year_precipitation:
        one_precip = {} # creating dict for each entry
        one_precip['date'] = date # saving date
        one_precip['prcp'] = prcp # saving precipitation

        # adding date and precipitation dictionary to list
        all_precip.append(one_precip)

    # closing session
    session.close()

    return(jsonify(all_precip))



# find list of all station codes
@app.route("/api/v1.0/stations")
def stations():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # querying for list of distinct station codes
    all_stations = session.query(station.station).distinct().all()
    
    # changing from row to string type
    station_list = list(np.ravel(all_stations))

    # closing session
    session.close()

    return(jsonify(station_list))

@app.route("/api/v1.0/tobs")
def temp_obs():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # getting stations ordered descending by number of observations (limit to most active station)
    selection = [measurement.station,
             func.count(measurement.station)]
    most_active_station = session.query(*selection).\
    group_by(measurement.station).\
    order_by(func.count(measurement.station).desc()).limit(1).all()

    # getting only string code of most active station
    most_active_station = most_active_station[0][0]

    # selecting only date and temp observation
    selection = [measurement.date, measurement.tobs]
    # querying data from most active station
    active_station_info = session.query(*selection).\
    filter(measurement.station == most_active_station).all()

    # creating list to hold observations from most active station
    temp_list = []
    for date, tobs in active_station_info:
        one_obs = {} # creating dict for one observation
        one_obs['date'] = date # adding date
        one_obs['tobs'] = tobs # adding temperature
        temp_list.append(one_obs) # adding dict to list

    # closing session
    session.close()
    
    return(jsonify(temp_list))

@app.route("/api/v1.0/<start>/")
def temps_start(start):

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # getting string year, month, and day from api request
    year, month, day = start.split('-')

    # selecting, min, avg, and max
    selection = [func.min(measurement.prcp),
                 func.avg(measurement.prcp),
                 func.max(measurement.prcp)]
    # querying for all dates starting from start date
    start_year_precipitation = session.query(*selection).\
    filter(measurement.date >= dt.datetime(
        int(year),
        int(month),
        int(day)
    )).\
    all()

    # creating dict to hold min, avg, and max values
    # note: I wasn't sure what format was required,
    # so I made this a dict so users can reference the values by name instead of their position
    calcs_dict = {
            'TMIN' : start_year_precipitation[0][0],
            'TAVG' : start_year_precipitation[0][1],
            'TMAX' : start_year_precipitation[0][2]
    }
    
    # closing session
    session.close()
    return(jsonify(calcs_dict))

@app.route("/api/v1.0/<start>/<end>")
def temps_range(start, end):

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # getting string year, month, and day from api request start date
    start_year, start_month, start_day = start.split('-')

    # getting string year, month, and day from api request end date
    end_year, end_month, end_day = end.split('-')


    # selecting, min, avg, and max
    selection = [func.min(measurement.prcp),
                 func.avg(measurement.prcp),
                 func.max(measurement.prcp)]
    # querying for all dates starting from start date through end date
    range_precipitation = session.query(*selection).\
    filter(measurement.date >= dt.datetime(
        int(start_year),
        int(start_month),
        int(start_day)
    )).\
    filter(measurement.date <= dt.datetime(
        int(end_year),
        int(end_month),
        int(end_day)
    )).\
    all()

    # creating dict to hold min, avg, and max values
    # note: I wasn't sure what format was required,
    # so I made this a dict so users can reference the values by name instead of their position
    calcs_dict = {
            'TMIN' : range_precipitation[0][0],
            'TAVG' : range_precipitation[0][1],
            'TMAX' : range_precipitation[0][2]
    }
    
    # closing session
    session.close()
    return(jsonify(calcs_dict))


if __name__ == '__main__':
    app.run(debug=True)
    
    
