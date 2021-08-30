import json
from loguru import logger
import requests
import yaml

config = yaml.safe_load(open("config.yaml"))

@logger.catch
def get_long_lat(address):
    """Uses ArcGIS's REST API 'findAddressCandidates' to find the longitude and latitude of a given address.
    If API returns multiple results, return the most accurate and acceptable, i.e. above minScore, address.
    (more at: https://developers.arcgis.com/rest/geocode/api-reference/geocoding-find-address-candidates.htm)
    
    Parameters
    ----------
    address : str
        The address to search.

    Returns
    -------
    2-tuple
        (longitude, latitude).

    None
        if address could not be found or score is below acceptable.
    """

    url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
    headers = config["geocode"]["headers"]
    params = config["geocode"]["params"]

    params["SingleLine"] = address

    response = requests.get(url, headers=headers, params=params)

    jsonResponse = json.loads(response.content)

    if len(jsonResponse["candidates"]) > 1:
        if jsonResponse["candidates"][0]["score"] >= config["geocode"]["minScore"]:
            logger.info("Address found: " + jsonResponse["candidates"][0]["address"] + " | Score: " + str(jsonResponse["candidates"][0]["score"]))
            point = jsonResponse["candidates"][0]["location"]
            return point["x"], point["y"]
        logger.error("Address '" + address + "' is not specific enough.")
        return None , None
    elif len(jsonResponse["candidates"]) <= 0:
        logger.error("Could not find address '" + address + "'.")
        return None , None
    else:
        logger.info("Address found: " + jsonResponse["candidates"][0]["address"] + " | Score: " + str(jsonResponse["candidates"][0]["score"]))
        point = jsonResponse["candidates"][0]["location"]
        return point["x"], point["y"]

@logger.catch
def main():
    #Test with multiple addresses
    logger.info(get_long_lat("5520 Lake Isabella Rd.  #G-1, Lake Isabella, CA"))

if __name__ == "__main__":
    main()