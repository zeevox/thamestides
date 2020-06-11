import sqlite3
from time import time, sleep

import pla

DB_NAME = "tides.db"
VERBOSE = False


def init(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        if VERBOSE:
            print("Connection to SQLite DB successful")
    except sqlite3.Error as e:
        print(e)
    return connection


def init_gauge(conn, gauge_name):
    sql_init_tide_gauge = (
        f"CREATE TABLE IF NOT EXISTS {gauge_name} "
        f"(time integer PRIMARY KEY, observed_cd integer NOT NULL, predicted_cd integer NOT NULL);"
    )
    conn.cursor().execute(sql_init_tide_gauge)
    conn.commit()
    if VERBOSE:
        print(f"Creation of table for gauge at {gauge_name} successful")


def update(conn, gauge_name, timestamp, observed_cd, predicted_cd):
    conn.cursor().execute(
        f"INSERT INTO {gauge_name} VALUES(?,?,?)",
        (timestamp, observed_cd, predicted_cd),
    )
    conn.commit()
    if VERBOSE:
        print(
            f"Saved new values for {gauge_name} as of {timestamp}: {observed_cd}, {predicted_cd}"
        )


if __name__ == "__main__":
    DB_CONN = init(DB_NAME)

    START = time()
    if DB_CONN is not None:
        try:
            while True:
                print(f"tick {int(time())}")
                DATA = pla.fetch()
                if DATA is not None:
                    for tide_gauge in DATA.keys():
                        init_gauge(DB_CONN, tide_gauge)
                        update(
                            DB_CONN,
                            tide_gauge,
                            int(DATA[tide_gauge]["time"]),
                            int(
                                DATA[tide_gauge]["observed_cd"] * 100
                            ),  # store values in cm to keep them as ints
                            int(DATA[tide_gauge]["predicted_cd"] * 100),
                        )
                sleep(60.0 - ((time() - START) % 60.0))  # tide gauges update every 60s
        except (KeyboardInterrupt, SystemExit, Exception):
            pass
        finally:
            DB_CONN.commit()
            DB_CONN.close()
    else:
        print(
            "An error occurred initialising the connection to the database. Please try again."
        )
