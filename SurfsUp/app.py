# Import the dependencies
from flask import Flask, jsonify
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import numpy as np
import datetime as dt

#################################################
# Database Setup
#################################################

# Create an engine to connect to the SQLite database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect the existing database into a new model
Base = automap_base()
Base.prepare(autoload_with=engine)

# Save references to the tables
Measurement = Base.classes.measurement
Station = Base.classes.station


#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

# 1. Homepage
@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"Available Routes:<br/>"
        f"<a href='/api/v1.0/precipitation'>Precipitation</a><br/>"
        f"<a href='/api/v1.0/stations'>Stations</a><br/>"
        f"<a href='/api/v1.0/tobs'>Tobs</a><br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
    )

# 2. /api/v1.0/precipitation
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the precipitation data for the last 12 months."""
    # Create a session to connect to the database
    session = Session(engine)
   
    # Get the last date in the dataset and calculate the date one year ago
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    last_date = dt.datetime.strptime(last_date, "%Y-%m-%d")
    one_year_ago = last_date - dt.timedelta(days=365)

    # Query the precipitation data for the last 12 months
    results = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_ago).all()
   
    # Close the session
    session.close()

    # Convert the query results to a dictionary
    precipitation_data = {date: prcp for date, prcp in results}
   
    return jsonify(precipitation_data)

# 3. /api/v1.0/stations
@app.route("/api/v1.0/stations")
def stations():
    """Return a list of all stations."""
    session = Session(engine)
   
    # Query all stations
    results = session.query(Station.station).all()
   
    session.close()

    # Convert list of tuples into normal list
    stations_list = list(np.ravel(results))
   
    return jsonify(stations_list)

# 4. /api/v1.0/tobs
@app.route("/api/v1.0/tobs")
def tobs():
    """Return temperature observations (TOBS) for the last year of the most active station."""
    session = Session(engine)
   
    # Find the most active station (the station with the most observations)
    most_active_station = session.query(Measurement.station).group_by(Measurement.station).\
                          order_by(func.count(Measurement.station).desc()).first()[0]

    # Get the last date and calculate one year back
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    last_date = dt.datetime.strptime(last_date, "%Y-%m-%d")
    one_year_ago = last_date - dt.timedelta(days=365)

    # Query the temperature observations for the most active station for the last year
    results = session.query(Measurement.date, Measurement.tobs).\
              filter(Measurement.station == most_active_station).\
              filter(Measurement.date >= one_year_ago).all()
   
    session.close()

    # Return the temperature observations as a JSON list
    tobs_data = list(np.ravel(results))
   
    return jsonify(tobs_data)

# 5. /api/v1.0/<start> and /api/v1.0/<start>/<end>
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_range(start, end=None):
    """Return the minimum, average, and maximum temperatures for a given start or start-end range."""
    session = Session(engine)

    if not end:
        # If no end date, calculate for dates greater than or equal to the start date
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
                  filter(Measurement.date >= start).all()
    else:
        # Calculate for dates between start and end
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
                  filter(Measurement.date >= start).filter(Measurement.date <= end).all()
   
    session.close()

    # Convert the query results to a dictionary
    temp_stats = {
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }
   
    return jsonify(temp_stats)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)