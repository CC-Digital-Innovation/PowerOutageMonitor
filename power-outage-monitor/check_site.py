import datetime
import json

import pytz
import requests
import yaml
from loguru import logger

config = yaml.safe_load(open("config.yaml"))

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
        if not site["longitude"]:
            logger.error("Missing longitude value")
            return None
        if not site["latitude"]:
            logger.error("Missing latitude value")
            return None
    except KeyError as err:
        logger.exception("Argument is missing required key: " + err.args[0])
        return None
        
    url = "https://services.arcgis.com/BLN4oKB0N1YSgvY8/arcgis/rest/services/Power_Outages_(View)/FeatureServer/0/query"
    headers = config["gis-api"]["headers"]
    params = config["gis-api"]["params"]

    params["geometry"] = str(site["longitude"]) + "," + str(site["latitude"])
    params["inSR"] = "4326"
    params["geometryType"] = "esriGeometryPoint"

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

        del site_status["OutageStatus"]
        site_status["PowerStatus"] = "Inactive"
        return site_status
    else:
        return {"PowerStatus": "Active"}

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
        if not site["city"]:
            logger.error("Missing region value.")
            return None
        if not site["longitude"]:
            logger.error("Missing longitude value.")
            return None
        if not site["latitude"]:
            logger.error("Missing latitude value.")
            return None
    except KeyError as err:
        logger.exception("Argument is missing required key: " + err.args[0])
        return None

    url = "https://apim.cloud.pge.com/cocoutage/outages/getOutagesRegions"
    headers = config["pge-api"]["headers"]
    params = config["pge-api"]["params"]

    response = requests.get(url, headers=headers, params=params)

    response_content = json.loads(response.content)

    # get list of outages based on region
    outage_regions = response_content['outagesRegions']

    for outage_region in outage_regions:
        # parse for matching region
        if site['city'] == outage_region['regionName']:
            for outage in outage_region['outages']:
                # parse for matching longitude and latitude
                # note that PG&E uses (longitude, latitude) vs. Google Map's (latitude, longitude)
                if site['longitude'] == outage['longitude'] and site['latitude'] == outage['latitude']:
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
                    del outage["outageStatus"]
                    outage["PowerStatus"] = "Inactive"
                    return outage
    return {"PowerStatus": "Active"}

#TODO functions for other APIs, get list of specific power providers

#function to redirect which function API to call
@logger.catch
def get_site_status(site, provider):
    if provider:
        if provider.lower() == "pge":
            logger.info("PGE API USED")
            logger.info(json.dumps(get_pge_power_status(site), indent=4, sort_keys=True))
            return get_pge_power_status(site)
    logger.info("GIS API USED")
    logger.info(json.dumps(get_gis_power_status(site), indent=4, sort_keys=True))
    return get_gis_power_status(site)
