import json
from loguru import logger
import requests
import yaml

config = yaml.safe_load(open("config.yaml"))

@logger.catch
def get_long_lat(address):
    """Uses ArcGIS's REST API 'findAddressCandidates' to find the longitude and latitude of a given address.
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
        if address could not be found or too many results.
    """

    url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
    headers = config["geocode"]["headers"]
    params = config["geocode"]["params"]

    params["SingleLine"] = address

    response = requests.get(url, headers=headers, params=params)

    jsonResponse = json.loads(response.content)

    if len(jsonResponse["candidates"]) > 1:
        logger.error("Address '" + address + "' is not specific enough.")
        return None
    elif len(jsonResponse["candidates"]) <= 0:
        logger.error("Could not find address '" + address + "'.")
        return None
    else:
        point = jsonResponse["candidates"][0]["location"]
        return point["x"], point["y"]

@logger.catch
def main():
    #Test with multiple addresses
    logger.info(get_long_lat("1600 Pennsylvania Ave NW, DC"))

if __name__ == "__main__":
    main()