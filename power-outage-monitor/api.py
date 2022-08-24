from typing import Optional

from fastapi import FastAPI, HTTPException
from loguru import logger
from prtg import PrtgApi

import check_all
import geocode
from config import config
from opsgenie import OpsgenieApi
from snow import SnowApi
from sites import controller

TOKEN = config["web"]["token"]
try:
    PRTG_API = PrtgApi(config['prtg']['url'], config['prtg']['username'], config['prtg']['password'], is_passhash=config['prtg']['is_passhash'])
except KeyError:
    PRTG_API = PrtgApi(config['prtg']['url'], config['prtg']['username'], config['prtg']['password'])
try:
    OPSGENIE_API = OpsgenieApi(config['opsgenie']['api_key'], config['opsgenie']['identifier_type'])
except KeyError:
    OPSGENIE_API = OpsgenieApi(config['opsgenie']['api_key'])
SNOW_API = SnowApi(config['snow']['instance'], config['snow']['username'], config['snow']['password'])
SNOW_FILTER = config['snow']['filter']

app = FastAPI()

@app.get("/checkSite")
def check_site(siteName: str, alertId: str, actionName: str, token: str):
    if token != TOKEN:
        raise HTTPException(status_code=401, detail='Unauthorized request.')
    site = controller.get_site(siteName)
    if not site:
        logger.info("Could not find site '" + siteName + "'")
        raise HTTPException(status_code=404, detail="Could not find site '" + siteName + "'")
    logger.info("Found site '" + siteName + ".' Getting power status...")
    return check_all.check(siteName, alertId, actionName, PRTG_API, OPSGENIE_API, SNOW_API, SNOW_FILTER)


@app.get("/sites/{siteName}")
def get_site(siteName: str, token: str):
    if token != TOKEN:
        raise HTTPException(status_code=401, detail='Unauthorized request.')
    site = controller.get_site(siteName)
    if site:
        logger.info("Found site '" + siteName + ".' Sending response...")
        return site
    logger.info("Could not find site '" + siteName + "'")
    raise HTTPException(status_code=404, detail="Could not find site '" + siteName + "'")


@app.get("/sites")
def get_all_sites(token: str):
    if token != TOKEN:
        raise HTTPException(status_code=401, detail='Unauthorized request.')
    return controller.get_all()


@app.post("/sites")
def add_site(siteName: str, street: str, city: str, state: str, token: str, longitude: Optional[str] = None, latitude: Optional[str] = None):
    if token != TOKEN:
        raise HTTPException(status_code=401, detail='Unauthorized request.')
    if not longitude or not latitude:
        longitude, latitude = geocode.get_long_lat(",".join((street, city, state)))
    if longitude and latitude:
        return controller.add_site(siteName, street, city, state, longitude, latitude)
    logger.error("Could not get longitude and latitude, cannot add to db.")
    raise HTTPException(status_code=422, detail="Could not find longitude or latitude based on address. Check street, city, and state inputs.")
