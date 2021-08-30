import logging.handlers
import sys
from typing import Optional

import uvicorn
import yaml
from fastapi import FastAPI, Response, status, HTTPException
from loguru import logger

from sites import controller
import geocode
from check_site import get_site_status

config = yaml.safe_load(open("config.yaml"))


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


set_log_level(config["logger"]["logLevel"])
logger.info("test watchtower")
app = FastAPI()


@logger.catch
@app.get("/checkSite")
def check_site(siteName: str, response: Response, provider: Optional[str] = None):
    site = controller.get_site(siteName)
    if site:
        logger.info("Found site '" + siteName + ".' Getting power status...")
        return get_site_status(site, provider)
    logger.info("Could not find site '" + siteName + "'")
    response.status_code = status.HTTP_404_NOT_FOUND
    return {"error": {"details": "Could not find site '" + siteName + "'"}}


@logger.catch
@app.get("/sites/{siteName}")
def get_site(siteName: str):
    site = controller.get_site(siteName)
    if site:
        logger.info("Found site '" + siteName + ".' Sending response...")
        return site
    logger.info("Could not find site '" + siteName + "'")
    response.status_code = status.HTTP_404_NOT_FOUND
    return {"error": {"details": "Could not find site '" + siteName + "'"}}


@logger.catch
@app.get("/sites")
def get_all_sites():
    return controller.get_all()


@logger.catch
@app.post("/sites")
def add_site(siteName: str, street: str, city: str, state: str, response: Response, longitude: Optional[str] = None, latitude: Optional[str] = None):
    if not longitude or not latitude:
        longitude, latitude = geocode.get_long_lat(",".join((street, city, state)))
    if longitude and latitude:
        return controller.add_site(siteName, street, city, state, longitude, latitude)
    logger.error("Could not get longitude and latitude, cannot add to db.")
    response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    return {"error": {"details": "Could not find longitude or latitude based on address. Check street, city, and state inputs."}}
