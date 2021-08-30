import argparse
import json
import os
import logging.handlers
import re
import sys

import requests
import yaml
from loguru import logger

config = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), os.pardir, "conf/config.yaml")))

parser = argparse.ArgumentParser()
parser.add_argument('-payload', '--queuePayload', required=True)
parser.add_argument('-logLevel', '--logLevel', required=True)
parser.add_argument('-apiKey', '--apiKey', required=True)
parser.add_argument('-opsgenieUrl', '--opsgenieUrl', required=True)

@logger.catch
def set_log_level(log_level):
    if log_level == "DEBUG":
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level>  | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    else:
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level>  | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    # Remove default logger
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


@logger.catch
def parse_sitename(description):
    sitename_pattern = re.compile("Group:\s*(?P<sitename>.*)\n")

    sitename_match = sitename_pattern.search(description)

    if sitename_match:
        return sitename_match.group("sitename").strip()
    return None


@logger.catch
def parse_location(description):
    location_pattern = re.compile("Location:\s*(?P<location>.*)\n")
    location_match = location_pattern.search(description)

    if location_match:
        location_match.group("location").strip()
    return None


@logger.catch
def update_alert_description(id, description):
    url = "https://api.opsgenie.com/v2/alerts/" + id + "/description"
    headers = config["opsgenie"]["alertApi"]["headers"]
    params = config["opsgenie"]["alertApi"]["params"]

    payload = {
        "description": description
    }

    logger.info("POSTing alert api to update description.")
    request = requests.post(url, json=payload, headers=headers, params=params)

    request.raise_for_status()
    return request.status_code


@logger.catch
def add_alert_details(id, details):
    url = "https://api.opsgenie.com/v2/alerts/" + id + "/details"
    headers = config["opsgenie"]["alertApi"]["headers"]
    params = config["opsgenie"]["alertApi"]["params"]

    payload = {
        "details": details
    }

    logger.info("POSTing alert api to update details")
    request = requests.post(url, json=payload, headers=headers, params=params)

    request.raise_for_status()
    return request.status_code


@logger.catch
def close_alert(id):
    url = "https://api.opsgenie.com/v2/alerts/" + id + "/close"
    headers = config["opsgenie"]["alertApi"]["headers"]
    params = config["opsgenie"]["alertApi"]["params"]

    payload = {}

    logger.info("POSTing alert api to close alert")
    request = requests.post(url, json=payload, headers=headers, params=params)

    request.raise_for_status()
    return request.status_code


@logger.catch
def check_site(site_name):
    url = "http://power-api.quokka.ninja/checkSite"
    params = {
        "siteName": site_name
    }

    logger.info("GETting site " + site_name + " power status.")
    request = requests.get(url, params=params)
    return request.json()


@logger.catch
def main():
    set_log_level(config["logger"]["logLevel"])
    args = vars(parser.parse_args())
    raw_message = args['queuePayload']
    raw_message = raw_message.strip()
    payload = json.loads(raw_message)

    alert = payload["entity"]
    alert_id = alert[config["opsgenie"]["alertApi"]["params"]["identifierType"]]

    site_name = parse_sitename(alert["description"])

    # get outage status
    response = check_site(site_name)

    if response:
        if "PowerStatus" in response:
            # build string response, update and close alert
            # str_response = ""
            # for key, item in response.items():
            #     str_response += key + ": " + str(item) + "\n"
            # update_status_code = update_alert_description(alert_id, alert["description"] + "\n" + str_response)
            # if update_status_code == 202:
            post_details_status_code = add_alert_details(alert_id, response)
            if post_details_status_code == 202:
                close_status_code = close_alert(alert_id)
                if close_status_code == 202:
                    logger.info("Successfully closed and updated alert!")
                else:
                    logger.error("Could not update or close the alert.")
            else:
                logger.error("Could not add details, no further actions taken.")
        else:
            logger.error("Cannot parse outage status.")
    else:
        logger.error("Unable to retrieve outage status, no further actions taken.")


if __name__ == "__main__":
    main()
