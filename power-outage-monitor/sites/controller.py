import csv
import json
import os
import sqlite3

import yaml
from loguru import logger

with open(os.path.join(os.path.dirname(__file__), os.pardir, "config.yaml")) as config_stream:
    config = yaml.safe_load(config_stream)

@logger.catch
def init_db():
    con = sqlite3.connect(config["sqlite3"]["dbName"])
    con.execute("""CREATE TABLE sites
                    (name TEXT PRIMARY KEY,
                     street TEXT,
                     city TEXT,
                     state TEXT,
                     longitude REAL,
                     latitude REAL)""")
    con.close()
    logger.info("Successfully created site table.")


@logger.catch
def populate_site(file_name):
    extension = os.path.splitext(file_name)[1]
    if extension == ".csv":
        with open(file_name) as csv_file:
            reader = csv.DictReader(csv_file)
            site_list = []
            for row in reader:
                site_list.append((row["name"], row["street"], row["city"], row["state"], row["longitude"], row["latitude"]))
        con = sqlite3.connect(config["sqlite3"]["dbName"])
        con.executemany("INSERT INTO sites(name, street, city, state, longitude, latitude) VALUES (?, ?, ?, ?, ?, ?)", site_list)
        con.commit()
        con.close()
        logger.info("Successfully populated sites.")
    elif extension == ".json":
        with open(file_name) as json_file:
            data = json.load(json_file)
            site_list = []
            for site in data:
                site_list.append((site["name"], site["street"], site["city"], site["state"], site["longitude"], site["latitude"]))
        con = sqlite3.connect(config["sqlite3"]["dbName"])
        con.executemany("INSERT INTO sites(name, street, city, state, longitude, latitude) VALUES (?, ?, ?, ?, ?, ?)", site_list)
        con.commit()
        con.close()
        logger.info("Successfully populated sites.")
    else:
        logger.error("File not yet supported.")


@logger.catch
def query_to_site(query):
    if query:
        return {
            "siteName": query[0],
            "street": query[1],
            "city": query[2],
            "state": query[3],
            "longitude": query[4],
            "latitude": query[5]
        }
    return None


@logger.catch
def add_site(site_name, street, city, state, longitude, latitude):
    con = sqlite3.connect(config["sqlite3"]["dbName"])
    logger.info("Adding site " + site_name + " to db.")
    try:
        with con:
            con.execute("INSERT INTO sites(name, street, city, state, longitude, latitude) VALUES (?, ?, ?, ?, ?, ?)", (site_name, street, city, state, longitude, latitude))
    except sqlite3.IntegrityError:
        logger.error("Site '" + site_name + "' already exists.")
        return None
    finally:
        con.close()
    logger.info("Successfully added " + site_name + " to db.")
    return get_site(site_name)


@logger.catch
def get_site(site_name):
    con = sqlite3.connect(config["sqlite3"]["dbName"])
    logger.info("Getting site " + site_name + " from db.")
    query = con.execute("SELECT * FROM sites WHERE name=?", (site_name,)).fetchone()
    con.close()
    return query_to_site(query)


@logger.catch
def get_all():
    con = sqlite3.connect(config["sqlite3"]["dbName"])
    logger.info("Getting all sites from db.")
    query = con.execute("SELECT * FROM sites").fetchall()
    con.close()
    return [query_to_site(row) for row in query]


def main():
    init_db()
    populate_site("site.json")


if __name__ == "__main__":
    main()
