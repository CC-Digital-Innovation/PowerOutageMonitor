from typing import Optional

from fastapi import FastAPI, HTTPException
from loguru import logger

import geocode
from check_site import get_site_status
from config import config
from sites import controller

app = FastAPI()

@app.get("/checkSite")
def check_site(siteName: str, token: str, provider: Optional[str] = None):
    if token != config["web"]["token"]:
        raise HTTPException(status_code=401, detail='Unauthorized request.')
    site = controller.get_site(siteName)
    if site:
        logger.info("Found site '" + siteName + ".' Getting power status...")
        return get_site_status(site, provider)
    logger.info("Could not find site '" + siteName + "'")
    raise HTTPException(status_code=404, detail="Could not find site '" + siteName + "'")


@app.get("/sites/{siteName}")
def get_site(siteName: str, token: str):
    if token != config["web"]["token"]:
        raise HTTPException(status_code=401, detail='Unauthorized request.')
    site = controller.get_site(siteName)
    if site:
        logger.info("Found site '" + siteName + ".' Sending response...")
        return site
    logger.info("Could not find site '" + siteName + "'")
    raise HTTPException(status_code=404, detail="Could not find site '" + siteName + "'")


@app.get("/sites")
def get_all_sites(token: str):
    if token != config["web"]["token"]:
        raise HTTPException(status_code=401, detail='Unauthorized request.')
    return controller.get_all()


@app.post("/sites")
def add_site(siteName: str, street: str, city: str, state: str, token: str, longitude: Optional[str] = None, latitude: Optional[str] = None):
    if token != config["web"]["token"]:
        raise HTTPException(status_code=401, detail='Unauthorized request.')
    if not longitude or not latitude:
        longitude, latitude = geocode.get_long_lat(",".join((street, city, state)))
    if longitude and latitude:
        return controller.add_site(siteName, street, city, state, longitude, latitude)
    logger.error("Could not get longitude and latitude, cannot add to db.")
    raise HTTPException(status_code=422, detail="Could not find longitude or latitude based on address. Check street, city, and state inputs.")
