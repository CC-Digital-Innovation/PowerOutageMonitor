import csv
import json
import enum
from geocode import get_long_lat

class SiteData:

    def __init__(self,service_provider):
        self.site_list = {}
        self.service_provider_tag = service_provider

    def read_from_csv(self,filename):
        """
        Read data from a CSV File.

        Parameters
        ----------
        filename: Name of the CSV file.

        Returns
        -------
        Returns a JSON data packet converted from the file
        """
        data = []
        with open(filename, encoding='utf-8') as csvf:
            csvReader = csv.DictReader(csvf)
            for rows in csvReader:
                data.append(rows)
        return json.dumps(data, indent=4)
    
    def read_json(self,jsonData):
        """

        Read data from a JSON Payload and add it to the site list.
        This function takes a JSON payload as an argument and adds it to the site_list dictionary.
        Note this is a strictly typed function which requires certain keynames to match.

        Parameters
        ----------
        jsonData: JSON payload needs to be converted .

        Returns
        -------
        None, Addes the json values to the data_list

        """
        JSONResponses = json.loads(jsonData)
        for JSONResponse in JSONResponses:
            address = JSONResponse["Address"] + " " + JSONResponse["city"] + " " + JSONResponse["state"] + " " + JSONResponse["zipcode"]
            [long, lat] = get_long_lat(address)
            if long is not None and lat is not None:
                self.add_values_to_site_list(JSONResponse["Sitename"], address, JSONResponse["Region"], long, lat)
    def read_json_from_file(self,fileName):
        """
        Read data from a JSON file and add it to the site list.
        This function takes a JSON payload as an argument and adds it to the site_list dictionary.
        Note this is a strictly typed function which requires certain keynames to match.

        Parameters
        ----------
        fileName: JSON payload form a file needs to be converted .

        Returns
        -------
        None, Adds the json values to the data_list using a helper function.

        """
        jsonData = open(fileName,)
        JSONResponses = json.load(jsonData)
        for JSONResponse in JSONResponses:
            address = JSONResponse["Address"] + " " + JSONResponse["city"] + " " + JSONResponse["state"] + " " + JSONResponse["zipcode"]
            [long, lat] = get_long_lat(address)
            if long is not None and lat is not None:
                self.add_values_to_site_list(JSONResponse["Sitename"],address,JSONResponse["Region"],long,lat)

    def add_values_to_site_list(self,Sitename, Address, Region, Long, Lat):
        """
        Helper function to Add values to the Site_list dictionary.
        This function takes in five arguments that define a sitename.

        Parameters
        ----------
        Sitename: A string value and it will be the key in the site_list Dictionary
        Address: The address of the site, expected value STRING.
        Region: The address of the site, expected value STRING.
        Long: The address of the site, expected value STRING.
        Lat: The address of the site, expected value STRING.

        Returns
        -------
        None, Adds the json values to the data_list.

        """
        sites = {}
        sites["Sitename"] = Sitename
        sites["Address"] = Address
        sites["Region"] = Region
        sites["Long"] = Long
        sites["Lat"] = Lat
        self.site_list[Sitename] = sites
    
    def get_site_data(self,Sitename):
        """
        Takes the sitename as an argument which needs to be fetched
        Parameters
        ----------
        Sitename : Name of the site to be fetched

        Returns
        -------
        Returns sitedata for a specific site

        """
        if Sitename in self.site_list:
            return self.site_list[Sitename]

    def return_vals(self):
       """

       Returns
       -------
        Site_list data LIST
       """
       return self.site_list



    

class Providers(enum.Enum):
    """
    A enum to see which provider has to be used.
    """
    GIS = 1
    PGE = 2

