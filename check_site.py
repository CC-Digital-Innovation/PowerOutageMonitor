import datetime
import json
from loguru import logger
import logging
import logging.handlers
import pytz
import requests
import yaml
from site_data import SiteData, Providers
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

@logger.catch
def convert_epoch_to_datetime(epoch):
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

    converted_datetime = datetime.datetime.fromtimestamp(epoch, datetime.datetime.now().astimezone().tzinfo)
    if config["date-time"]["timezone"]:
        return converted_datetime.astimezone(pytz.timezone(config["date-time"]["timezone"]))
    return converted_datetime

@logger.catch
def get_gis_power_status(site):
    """checks the power status of a site using CalOES's Power Outage Incident API.
    (more at: https://gis.data.ca.gov/datasets/CalEMA::power-outage-incidents/about)

    Parameters
    ----------
    site : SiteData

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

    response_content = json.loads(response.content)

    # get list of outages
    try:
        statuses = response_content['features']
    except KeyError:
        logger.error(response_content)
        return None

    if len(statuses) == 1:
        site_status = statuses[0]["attributes"]
        
        # convert epoch to formatted datetime
        if "StartDate" in site_status:
            site_status["StartDate"] = convert_epoch_to_datetime(site_status["StartDate"]//(10**3)).strftime(config["date-time"]["timeFormat"])
        if "EstimatedRestoreDate" in site_status:
            site_status["EstimatedRestoreDate"] = convert_epoch_to_datetime(site_status["EstimatedRestoreDate"]//(10**3)).strftime(config["date-time"]["timeFormat"])

        return site_status
    else:
        site_status = site
        site_status["OutageStatus"] = "Restored"
        return site_status

@logger.catch
def get_pge_power_status(site):
    """checks the power status of a site using PG&E's API

    Parameters
    ----------
    site : SiteData

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

    response_content = json.loads(response.content)

    # get list of outages based on region
    outage_regions = response_content['outagesRegions']

    for outage_region in outage_regions:
        # parse for matching region
        if site['Region'] == outage_region['regionName']:
            for outage in outage_region['outages']:
                # parse for matching longitude and latitude
                # note that PG&E uses (longitude, latitude) vs. Google Map's (latitude, longitude)
                if site['Long'] == outage['longitude'] and site['Lat'] == outage['latitude']:
                    # convert epoch to formatted datetime
                    if "autoEtor" in outage:
                        outage["autoEtor"] = convert_epoch_to_datetime(int(outage["autoEtor"])).strftime(config["date-time"]["timeFormat"])
                    if "crewEta" in outage:
                        outage["crewEta"] = convert_epoch_to_datetime(int(outage["crewEta"])).strftime(config["date-time"]["timeFormat"])
                    if "currentEtor" in outage:
                        outage["currentEtor"] = convert_epoch_to_datetime(int(outage["currentEtor"])).strftime(config["date-time"]["timeFormat"])
                    if "lastUpdateTime" in outage:
                        outage["lastUpdateTime"] = convert_epoch_to_datetime(int(outage["lastUpdateTime"])).strftime(config["date-time"]["timeFormat"])
                    if "outageStartTime" in outage:
                        outage["outageStartTime"] = convert_epoch_to_datetime(int(outage["outageStartTime"])).strftime(config["date-time"]["timeFormat"])
                    return outage
    site_status = site
    site_status["OutageStatus"] = "Restored"
    return site_status

#TODO functions for other APIs, get list of specific power providers

#function to redirect which function API to call
@logger.catch
def check_which_api_to_call(site, provider_name):
    if provider_name == Providers.GIS:
        logger.info("GIS API USED")
        logger.info(json.dumps(get_gis_power_status(site), indent=4, sort_keys=True))
        return json.dumps(get_gis_power_status(site), sort_keys=True)
    elif provider_name == Providers.PGE:
        logger.info("PGE API USED")
        logger.info(json.dumps(get_pge_power_status(site), indent=4, sort_keys=True))
        return json.dumps(get_pge_power_status(site), sort_keys=True)



# @logger.catch

def callCSV():
    # set_log_level(config["logger"]["logLevel"])
    site_data_obj = SiteData(Providers.GIS)
    site_data_obj.read_json(site_data_obj.read_from_csv('site.csv'))
    for site in site_data_obj.site_list:
        print(site)
        # check_which_api_to_call(site_data_obj.get_site_data(site) , site_data_obj.service_provider_tag)


def callJSON():
    site_data_obj = SiteData(Providers.PGE)
    site_data_obj.read_json_from_file('site.json')
    jsonoutput = []
    for site in site_data_obj.site_list:
        print(site)
        # jsonoutput.append(check_which_api_to_call(site_data_obj.get_site_data(site), site_data_obj.service_provider_tag))
    return  jsonoutput




if __name__ == "__main__":
    callCSV()