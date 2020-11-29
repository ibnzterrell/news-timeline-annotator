import requests
import json
import pandas as pd
import numpy as np
from scipy import signal, stats
from flask import Flask, request, g
from flask_cors import CORS, cross_origin
from io import BytesIO
import sqlalchemy as sa
import re

app = Flask(__name__)
CORS(app)


def db_connect():
    db = getattr(g, '_database', None)
    articlesTable = getattr(g, '_articlesTable', None)
    engine = getattr(g, '_engine', None)

    if engine is None:
        engine = g._engine = sa.create_engine(
            "[DATABASE ENGINE]", echo=True)

    if db is None:
        db = g._database = engine.connect()

    if articlesTable is None:
        md = sa.MetaData()
        md.reflect(bind=engine)
        articlesTable = g.__articlesTable = md.tables["articles"]

    return (db, articlesTable)


def findPeaks(df):
    # Use median absolute deviation instead of standard deviation for robustness
    mad = stats.median_absolute_deviation(df["screentime"])
    peak_indices = signal.find_peaks(df["screentime"], threshold=mad)
    return df.iloc[peak_indices[0]]


def getPersonScreentime(name):
    rawData = requests.get(
        f"https://tvnews.stanford.edu/search?aggregate=month&detailed=false&end_date=2020-12-31&query=%5B%22name%22%2C%22{name}%22%5D&start_date=2010-01-01")
    data = json.loads(rawData.content)
    df = pd.DataFrame.from_dict(data, orient="index")
    df.rename(columns={df.columns[0]: "screentime"}, inplace=True)
    return df


def legalize(name):
    # Convert common name to legal name for NYT lookup
    return {
        "joe biden": "Joseph R Jr Biden",
        "bernie sanders": "Bernard Sanders",
        "jack welch": "John F Jr Welch"
    }.get(name, name)  # Return name if not found


def convertNameForNYT(name):
    name = legalize(name)

    # Convert name from Cable TV format (first middle last) to NYT format (last, first middle)
    results = re.search("(.*) (.*)", name).groups()
    return f"{results[1]}, {results[0]}"


def findEvents(name, dates):
    name = convertNameForNYT(name)
    df = []

    (db_conn, articlesTable) = db_connect()

    # Tags are ordered by relevance, only select articles where they are first person listed
    sqlQuery = sa.sql.select([articlesTable]).where(
        articlesTable.c.people.ilike(f"[\'{name}%"))
    # NOTE While fairly limiting, we use SQLAlchemy selectables instead of raw queries to prevent SQL injection

    # TODO Make more efficient by doing processing ahead of time to offload date filtering to DB
    # TODO Make more accurate using Heideltime NLP to temporalize events
    df = pd.read_sql_query(sql=sqlQuery, con=db_conn)

    # Cut ISO dates to year-month e.g. 2020-11 for string-based date matching
    df['month_date'] = df['pub_date'].str.slice(0, 7)
    # NOTE efficient but not as accurate
    dates = dates.str.slice(0, 7)
    df = df[df["month_date"].isin(dates)]

    # If multiple articles keep most recent one - most likely to have most information
    # NOTE NLP temporal / volume-based event detection should help with which article to use later on
    df = df.drop_duplicates(subset=["month_date"], keep="last")

    return df


@app.route("/person/<name>/screentime", methods=["GET"])
@cross_origin()
def personScreentimeRoute(name):
    df = getPersonScreentime(name)
    return df.to_csv(None, index_label="date")


@app.route("/person/<name>/events", methods=["GET"])
@cross_origin()
def personEventsRoute(name):
    df = getPersonScreentime(name)
    df = findPeaks(df)
    df = findEvents(name, df.index)
    return df.to_csv(None)


@app.route("/warmup", methods=["GET"])
@cross_origin()
def warmupRoute(name):
    db_connect()
    return "OK"

# @app.route("/utility/findPeaks", methods=["POST"])
# def findPeaksUtilityRoute():
#     print(request.data)
#     df = pd.read_csv(BytesIO(request.data))
#     df = findPeaks(df)
#     return df.to_csv(None, index=False)

# Close database on shutdown
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run(port=3000)
