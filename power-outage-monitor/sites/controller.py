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
    con.execute("DROP TABLE sites")
    con.execute("""CREATE TABLE sites
                    (name TEXT PRIMARY KEY,
                     street TEXT,
                     city TEXT,
                     county TEXT,
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
                site_list.append((row["name"], row["street"], row["city"], row["county"], row["state"], row["longitude"], row["latitude"]))
        con = sqlite3.connect(config["sqlite3"]["dbName"])
        con.executemany("INSERT INTO sites(name, street, city, county, state, longitude, latitude) VALUES (?, ?, ?, ?, ?, ?, ?)", site_list)
        con.commit()
        con.close()
        logger.info("Successfully populated sites.")
    elif extension == ".json":
        with open(file_name) as json_file:
            data = json.load(json_file)
            site_list = []
            for site in data:
                site_list.append((site["siteName"], site["street"], site["city"], site["county"], site["state"], site["longitude"], site["latitude"]))
        con = sqlite3.connect(config["sqlite3"]["dbName"])
        con.executemany("INSERT INTO sites(name, street, city, county, state, longitude, latitude) VALUES (?, ?, ?, ?, ?, ?, ?)", site_list)
        con.commit()
        con.close()
        logger.info("Successfully populated sites.")
    else:
        logger.error("File not supported.")


@logger.catch
def add_site(site_name, street, city, county, state, longitude, latitude):
    con = sqlite3.connect(config["sqlite3"]["dbName"])
    logger.info("Adding site " + site_name + " to db.")
    try:
        with con:
            con.execute("INSERT INTO sites(name, street, city, county, state, longitude, latitude) VALUES (?, ?, ?, ?, ?, ?, ?)", (site_name, street, city, county, state, longitude, latitude))
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
    con.row_factory = sqlite3.Row
    query = dict(con.execute("SELECT * FROM sites WHERE name=? COLLATE NOCASE", (site_name,)).fetchone())
    con.close()
    query["siteName"] = query.pop("name")
    return query


@logger.catch
def get_all():
    con = sqlite3.connect(config["sqlite3"]["dbName"])
    logger.info("Getting all sites from db.")
    con.row_factory = sqlite3.Row
    query = [dict(row) for row in con.execute("SELECT * FROM sites").fetchall()]
    con.close()
    for row in query:
        row["siteName"] = row.pop("name") 
    return query


def main():
    init_db()
    populate_site(os.path.join(os.path.dirname(__file__), "site.json"))


if __name__ == "__main__":
    main()