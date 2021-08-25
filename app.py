import logging.handlers
import sys
from typing import Optional

import uvicorn
import yaml
from fastapi import FastAPI, Response, status, HTTPException
from loguru import logger

import controller
import geocode
from check_site import get_site_status

config = yaml.safe_load(open("config.yaml"))

@logger.catch
def set_log_level(log_level):
    if log_level == "DEBUG":
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level>  | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    else:
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level>  | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    # Log to console
    # logger.add(sys.stderr, colorize=True, format=log_format, level=log_level)

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


set_log_level("DEBUG")
app = FastAPI()


@logger.catch
@app.get("/checkSite")
def check_site(siteName: str, response: Response, provider: Optional[str] = None):
    site = controller.get_site(siteName)
    if site:
        return get_site_status(site, provider)
    response.status_code = status.HTTP_404_NOT_FOUND
    return None


@logger.catch
@app.get("/sites/{siteName}")
def get_site(siteName: str):
    return controller.get_site(siteName)


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
    return None


def main():
    set_log_level("DEBUG")
    uvicorn.run(app, host="0.0.0.0", port=config["web"]["port"])


if __name__ == "__main__":
    main()