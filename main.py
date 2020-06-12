import argparse
import logging
import sqlite3

from apscheduler.schedulers.background import BlockingScheduler

import jennings
import pla
import ukho
from constants import DB_NAME


def connect(path):
    database = None
    try:
        database = sqlite3.connect(path)
        logging.info(f"Connection to SQLite database {path} successful")
        database.set_trace_callback(logging.debug)
        logging.debug(f"Enabled logging of SQL queries for {path}")
    except sqlite3.Error as e:
        print(e)
    return database


# Fetch data from the PLA and save it to the databases
def update_pla():
    # initialise SQL database connection here, because SQLite objects
    # created in a thread can only be used in that same thread
    database = connect(DB_NAME)
    if database is None:
        logging.error("Could not initialise a connection to the database.")
        return

    pla_data = pla.fetch()
    if pla_data is not None:
        logging.info("Fetched PLA tide gauge readings")

        database.cursor().execute("CREATE TABLE IF NOT EXISTS readings (time integer PRIMARY KEY);")
        database.cursor().execute("CREATE TABLE IF NOT EXISTS predictions (time integer PRIMARY KEY);")

        for station_name in pla_data:
            try:
                database.cursor().execute(f"ALTER TABLE readings ADD COLUMN {station_name} real;")
                database.cursor().execute(f"ALTER TABLE predictions ADD COLUMN {station_name} real;")
            except sqlite3.OperationalError:  # thrown if the column exists already, simply ignore
                pass

            timestamp = int(pla_data[station_name]["time"])
            observed_cd = pla_data[station_name]["observed_cd"]
            predicted_cd = pla_data[station_name]["predicted_cd"]

            database.cursor().execute("INSERT OR IGNORE INTO readings(time) VALUES(?)", (int(timestamp),))
            database.cursor().execute(
                f"UPDATE readings SET {station_name} = ? WHERE time = ?",
                (observed_cd, timestamp),
            )

            database.cursor().execute("INSERT OR IGNORE INTO predictions(time) VALUES(?)", (int(timestamp),))
            database.cursor().execute(
                f"UPDATE predictions SET {station_name} = ? WHERE time = ?",
                (predicted_cd, timestamp),
            )

            database.commit()
            logging.debug(f"Saved new values for {station_name} as of {timestamp}: {observed_cd}, {predicted_cd}")

    # save our changes and close connection to the database
    database.commit()
    database.close()


def update_daily_predictions():
    database = connect(DB_NAME)
    if database is None:
        logging.error("Could not initialise a connection to the database.")
        return

    jennings_data = jennings.fetch()
    ukho_data = ukho.fetch()

    # in dictionaries later values will always override earlier ones (PEP 0448)
    # we prefer the accuracy of Richard Jennings' data over the UK Hydrographic Office
    fetched_data = {**ukho_data, **jennings_data}

    database.cursor().execute("CREATE TABLE IF NOT EXISTS predictions (time integer PRIMARY KEY);")

    for station_name in fetched_data:
        try:
            database.cursor().execute(f"ALTER TABLE predictions ADD COLUMN {station_name} real;")
        except sqlite3.OperationalError:  # thrown if the column exists already, simply ignore
            pass

        for turning_point in fetched_data[station_name]:
            timestamp, predicted_cd = turning_point
            database.cursor().execute("INSERT OR IGNORE INTO predictions(time) VALUES(?)", (int(timestamp),))
            database.cursor().execute(
                f"UPDATE predictions SET {station_name} = ? WHERE time = ?",
                (predicted_cd, int(timestamp))
            )

    database.commit()
    database.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Monitor the tidal stretch of the River Thames')
    parser.add_argument('-l', '--log', dest="loglevel", default="warning",
                        help="Set the logging level {DEBUG,INFO,WARNING,ERROR,CRITICAL}")
    parser.add_argument('-o', '--output', dest='logfile', help='Output to a log file')
    args = parser.parse_args()

    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {args.loglevel}')
    if args.logfile:
        logging.basicConfig(filename=args.logfile, level=numeric_level)
    else:
        logging.basicConfig(level=numeric_level)

    # one-off run because it is scheduled for once a day; otherwise it will not record today's values
    update_daily_predictions()

    scheduler = BlockingScheduler()

    scheduler.add_job(update_pla, 'cron', second=0)
    scheduler.add_job(update_daily_predictions, 'cron', hour=0)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit, Exception):
        logging.warning("Program shutting down")
