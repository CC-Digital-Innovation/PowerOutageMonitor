import logging.handlers
import os
import sys
from typing import Optional

import yaml
from fastapi import FastAPI, HTTPException
from loguru import logger

import geocode
from check_site import get_site_status
from sites import controller

with open(os.path.join(os.path.dirname(__file__), "config.yaml")) as config_stream:
    config = yaml.safe_load(config_stream)

LOG_LEVEL = config["logger"]["logLevel"]
TOKEN = config["web"]["token"]

@logger.catch
def set_log_level(log_level):
    if log_level == "DEBUG":
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level>  | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    else:
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level>  | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    # Remove default handler
    logger.remove()

    # Log to console
    logger.add(sys.stderr, colorize=True, format=log_format, level=log_level)

    # Log to log file
    # logger.add(config["logger"]["fileName"] +
    #            "\snowmail_{time:YYYY_MM_DD}.log", level=log_level, rotation="100 MB")
    
    # Log to syslog
    handler = logging.handlers.SysLogHandler(
        address=(config["logger"]["sysLog"]["host"], config["logger"]["sysLog"]["port"]))
    logger.add(handler)

    if log_level == "QUIET":
        logger.disable("")
    else:
        logger.enable("")


set_log_level(LOG_LEVEL)
logger.info("Starting up PowerCheckAPI...")
app = FastAPI()


@logger.catch
@app.get("/checkSite")
def check_site(siteName: str, token: str, provider: Optional[str] = None):
    if token != TOKEN:
        raise HTTPException(status_code=401, detail='Unauthorized request.')
    site = controller.get_site(siteName)
    if site:
        logger.info("Found site '" + siteName + ".' Getting power status...")
        return get_site_status(site, provider)
    logger.info("Could not find site '" + siteName + "'")
    raise HTTPException(status_code=404, detail="Could not find site '" + siteName + "'")


@logger.catch
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


@logger.catch
@app.get("/sites")
def get_all_sites(token: str):
    if token != TOKEN:
        raise HTTPException(status_code=401, detail='Unauthorized request.')
    return controller.get_all()


@logger.catch
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
