import datetime
import json
from loguru import logger
import pytz
import requests
import yaml
from siteData import siteData,providers
import sys

config = yaml.safe_load(open("config.yaml"))

@logger.catch
def set_log_level(log_level):
    if log_level == "DEBUG":
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level>  | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    else:
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level>  | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    # Log to console
    logger.add(sys.stderr, colorize=True, format=log_format, level=log_level)

    # Log to log file
    # logger.add(config["logger"]["fileName"] +
    #            "\snowmail_{time:YYYY_MM_DD}.log", level=log_level, rotation="100 MB")
    
    # Log to syslog
    # handler = logging.handlers.SysLogHandler(
    #     address=(config["logger"]["sysLog"]["host"], config["logger"]["sysLog"]["port"]))
    # logger.add(handler)

    if log_level == "QUIET":
        logger.disable("")
    else:
        logger.enable("")

def convertEpochToDateTime(epoch):
    """convert epoch to datetime with config-specified timezone
    
    Parameters
    ----------
    epoch : int
        The timestamp to convert

    Returns
    -------
    datetime
        The converted time with config-specified timezone.
        If it is not specified, timezone defaults to local.
    """

    dateAndTime = datetime.datetime.fromtimestamp(epoch, datetime.datetime.now().astimezone().tzinfo)
    if config["date-time"]["timezone"]:
        return dateAndTime.astimezone(pytz.timezone(config["date-time"]["timezone"]))
    return dateAndTime

def getGisPowerStatus(site):
    """checks the power status of a site using CalOES's Power Outage Incident API.
    (more at: https://gis.data.ca.gov/datasets/CalEMA::power-outage-incidents/about)

    Parameters
    ----------
    site : siteData

    Returns
    -------
    dict
        A dictionary with outage status and outage information if it is active or
        simply site information if it is restored

    None
        If missing keys, missing key values, or incorrect longitude and latitude values.
    """

    # check argument
    try:
        if not site["Long"]:
            logger.error("Missing longitude value")
            return None
        if not site["Lat"]:
            logger.error("Missing latitude value")
            return None
    except KeyError as err:
        logger.exception("Argument is missing required key: " + err.args[0])
        return None
        
    url = config["gis-api"]["url"]
    headers = config["gis-api"]["headers"]
    params = config["gis-api"]["params"]

    params["geometry"] = str(site["Long"]) + "," + str(site["Lat"])

    response = requests.get(url, headers=headers, params=params)

    responseContent = json.loads(response.content)

    # get list of outages
    try:
        statuses = responseContent['features']
    except KeyError:
        logger.error(responseContent)
        return None

    if len(statuses) == 1:
        siteStatus = statuses[0]["attributes"]
        
        # convert epoch to formatted datetime
        if "StartDate" in siteStatus:
            siteStatus["StartDate"] = convertEpochToDateTime(siteStatus["StartDate"]//(10**3)).strftime(config["date-time"]["timeFormat"])
        if "EstimatedRestoreDate" in siteStatus:
            siteStatus["EstimatedRestoreDate"] = convertEpochToDateTime(siteStatus["EstimatedRestoreDate"]//(10**3)).strftime(config["date-time"]["timeFormat"])

        return siteStatus
    else:
        siteStatus = site
        siteStatus["OutageStatus"] = "Restored"
        return siteStatus

def getPgePowerStatus(site):
    """checks the power status of a site using PG&E's API

    Parameters
    ----------
    site : siteData

    Returns
    -------
    dict
        A dictionary with outage status and outage information if it is active or
        simply site information if it is restored

    None
        If missing keys, missing key values, or incorrect longitude and latitude values.
    """

    # check argument
    try:
        if not site["Region"]:
            logger.error("Missing region value.")
            return None
        if not site["Long"]:
            logger.error("Missing longitude value.")
            return None
        if not site["Lat"]:
            logger.error("Missing latitude value.")
            return None
    except KeyError as err:
        logger.exception("Argument is missing required key: " + err.args[0])
        return None

    url = config["pge-api"]["url"]
    headers = config["pge-api"]["headers"]
    params = config["pge-api"]["params"]

    response = requests.get(url, headers=headers, params=params)

    responseContent = json.loads(response.content)

    # get list of outages based on region
    outageRegions = responseContent['outagesRegions']

    for outageRegion in outageRegions:
        # parse for matching region
        if site['Region'] == outageRegion['regionName']:
            for outage in outageRegion['outages']:
                # parse for matching longitude and latitude
                # note that PG&E uses (longitude, latitude) vs. Google Map's (latitude, longitude)
                if site['Long'] == outage['longitude'] and site['Lat'] == outage['latitude']:
                    # convert epoch to formatted datetime
                    if "autoEtor" in outage:
                        outage["autoEtor"] = convertEpochToDateTime(int(outage["autoEtor"])).strftime(config["date-time"]["timeFormat"])
                    if "crewEta" in outage:
                        outage["crewEta"] = convertEpochToDateTime(int(outage["crewEta"])).strftime(config["date-time"]["timeFormat"])
                    if "currentEtor" in outage:
                        outage["currentEtor"] = convertEpochToDateTime(int(outage["currentEtor"])).strftime(config["date-time"]["timeFormat"])
                    if "lastUpdateTime" in outage:
                        outage["lastUpdateTime"] = convertEpochToDateTime(int(outage["lastUpdateTime"])).strftime(config["date-time"]["timeFormat"])
                    if "outageStartTime" in outage:
                        outage["outageStartTime"] = convertEpochToDateTime(int(outage["outageStartTime"])).strftime(config["date-time"]["timeFormat"])
                    return outage
    siteStatus = site
    siteStatus["OutageStatus"] = "Restored"
    return siteStatus

#TODO functions for other APIs, get list of specific power providers

#function to redirect which function API to call
def checkWhichApiToCall(site, providerName):
    if providerName == providers.GIS:
        logger.info("GIS API USED")
        logger.info(json.dumps(getGisPowerStatus(site), indent=4, sort_keys=True))
    elif providerName == providers.PGE:
        logger.info("PGE API USED")
        logger.info(json.dumps(getPgePowerStatus(site), indent=4, sort_keys=True))


def main():
    set_log_level(config["logger"]["logLevel"])
    siteDataObj = siteData(providers.GIS)
    siteDataObj.readJson(siteDataObj.readFromCSV('site.csv'))
    for site in siteDataObj.site_list:
        checkWhichApiToCall(siteDataObj.getSiteData(site) , siteDataObj.serviceProviderTag)

    siteDataObj = siteData(providers.PGE)
    siteDataObj.readJsonFromFile('site.json')
    for site in siteDataObj.site_list:
        checkWhichApiToCall(siteDataObj.getSiteData(site) , siteDataObj.serviceProviderTag)
    
if __name__ == "__main__":
    main()