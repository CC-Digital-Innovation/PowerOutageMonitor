import re

from loguru import logger

import check_outage

def check(site_name, alert_id, action_name, prtg_api, opsgenie_api):
    # payload to post for alert extra properties
    details = {"SiteName":site_name}

    # get gis outage status
    gis_response = check_outage.get_site_status(site_name)
    if gis_response:
        if "PowerStatus" in gis_response:
            if gis_response["PowerStatus"] == "Active":
                details["Power_SitePower"] = "Up"
            elif gis_response["PowerStatus"] == "Inactive":
                # prefix keys
                prefixed = {}
                for key, val in gis_response.items():
                    prefixed["Power_" + key] = val
                details.update(prefixed)
                del details["Power_PowerStatus"]
                details["Power_SitePower"] = "Down"
            else:
                logger.error("PowerStatus '" + gis_response["PowerStatus"] + "' is not a valid response.")
                details["Power_SitePower"] = "Unknown"
        else:
            logger.error("Cannot parse outage status.")
            details["Power_SitePower"] = "Unknown"
    else:
        logger.error("Unable to retrieve outage status.")
        details["Power_SitePower"] = "Unknown"

    # get pi status
    pi_response = prtg_api.get_sensors_by_name('Ping', 'PI - LTE', site_name)
    pi_is_up = None
    if "sensors" in pi_response:
        if len(pi_response["sensors"]) == 1:
            if "status" in pi_response["sensors"][0]:
                details["PRTG_PiStatus"] = pi_response["sensors"][0]["status"]
                if re.match("Up|Unusual|Warning",  details["PRTG_PiStatus"]):
                    pi_is_up = True
                elif re.match("Down.*", details["PRTG_PiStatus"]):
                    pi_is_up = False
                # else pi is Paused|Unknown
            else:
                logger.error("Could not parse pi sensor status.")
        elif len(pi_response["sensors"]) > 1:
            logger.error("More than one pi sensor was found.")
        else:
            logger.error("Could not find pi sensor.")
    else:
        logger.error("Cannot parse pi sensors in payload.")

    # get probe status
    probe_response = prtg_api.get_sensors_by_name('Probe Health', site_name, 'Probe Device')
    probe_is_up = None
    if "sensors" in probe_response:
        if len(probe_response["sensors"]) == 1:
            if "status" in probe_response["sensors"][0]:
                details["PRTG_ProbeStatus"] = probe_response["sensors"][0]["status"]
                if re.match("Up|Unusual|Warning",  details["PRTG_ProbeStatus"]):
                    probe_is_up = True
                elif re.match("Down.*", details["PRTG_ProbeStatus"]):
                    probe_is_up = False
                # else pi is Paused|Unknown
            else:
                logger.error("Could not parse probe device status.")
        elif len(probe_response["sensors"]) > 1:
            logger.error("More than one probe device was found.")
        else:
            logger.error("Could not find probe device.")
    else:
        logger.error("Cannot parse probe devices in payload.")

    # Site power confidence level
    if details["Power_SitePower"] == "Up":
        if not pi_is_up and not probe_is_up:
            details["Power_SitePowerConfidence"] = "Low"
        else:
            details["Power_SitePowerConfidence"] = "High"
    elif details["Power_SitePower"] == "Down":
        if pi_is_up is None or probe_is_up is None:
            logger.warning('Could not check pi or probe status. Confidence default to low')
            details["Power_SitePowerConfidence"] = "Low"
        elif not pi_is_up and not probe_is_up:
            details["Power_SitePowerConfidence"] = "High"

            # add tag for site down
            add_tag_status_code = opsgenie_api.add_alert_tags(alert_id, ["SitePowerDown"], note=f"Automated action {action_name} detected site power is down with high confidence. Tag has been added.")
            if add_tag_status_code == 202:
                logger.info(f"Successfully added tags to alert {alert_id}.")
            else:
                logger.error(f"Could not add tags to alert {alert_id}")
        else:
            details["Power_SitePowerConfidence"] = "Low"

    # User input validity check
    details["PowerCheckValidation"] = ""

    # update alert with site, pi, and probe statuses
    note = f"Automated action {action_name} completed. Details of site, pi and probe statuses have been added as extra properties."

    post_details_status_code = opsgenie_api.add_alert_details(alert_id, details, note=note)
    if post_details_status_code == 202:
        logger.info(f"Successfully posted details to alert {alert_id}.")
    else:
        logger.error(f"Could not post details to alert {alert_id}")

    return details
