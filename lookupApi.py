from ApiError import ApiError
from site_data import SiteData, Providers
from check_site import check_which_api_to_call

def apiLookupRun(sitename, address):
    if sitename is not None and address is not None:
        sitedata = SiteData(Providers.GIS)

        if sitedata.get_site_data(sitename) is not None:
            site = sitedata.checkandAddforAddressExist(sitedata.get_site_data(sitename),address,None)
            if site is None:
                apiErrorObj = ApiError("404", "The requested resource was not found.")
                return apiErrorObj.returnJson()
            return check_which_api_to_call( site, sitedata.service_provider_tag)
        else:
            apiErrorObj = ApiError("404", "The requested resource was not found.")
            return apiErrorObj.returnJson()

    else:
        apiErrorObj = ApiError("400","The request was invalid.")
        return apiErrorObj.returnJson()
