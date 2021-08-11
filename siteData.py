import csv
import json
import enum

class siteData:

    def __init__(self,serviceProvider):
        self.site_list = {}
        self.serviceProviderTag = serviceProvider

    def readFromCSV(self,filename):
        """ Read data from a CSV File.
         This function can takes csv filename as an argument and returns a JSON payload.
        """
        data = []
        with open(filename, encoding='utf-8') as csvf:
            csvReader = csv.DictReader(csvf)
            for rows in csvReader:
                data.append(rows)
        return json.dumps(data, indent=4)
    
    def readJson(self,jsonData):
        """ Read data from a JSON Payload and add it to thes site list.
        This function takes a JSON payload as an argument and adds it to the site_list dictionary.
        Note this is a strictly typed function which requires certain keynames to match.
        """
        JSONResponses = json.loads(jsonData)
        for JSONResponse in JSONResponses:
            self.addValuesToSiteList(JSONResponse["Sitename"],JSONResponse["Address"],JSONResponse["Region"],JSONResponse["Long"],JSONResponse["Lat"])

    def readJsonFromFile(self,fileName):
        """Read data from a JSON Payload and add it to thes site list.
        This function takes a JSON payload as an argument and adds it to the site_list dictionary.
        Note this is a strictly typed function which requires certain keynames to match.
        """
        jsonData = open(fileName,)
        JSONResponses = json.load(jsonData)
        for JSONResponse in JSONResponses:
            self.addValuesToSiteList(JSONResponse["Sitename"],JSONResponse["Address"],JSONResponse["Region"],JSONResponse["Long"],JSONResponse["Lat"])

    def addValuesToSiteList(self,Sitename, Address, Region, Long, Lat):
        """ Add values to the Site_list dictionary.
        This function takes in five arguments that define a sitename.
        Sitename: A string value and it will be the key in the site_list Dictionary
        Address: The address of the site, expected value STRING.
        Region: The address of the site, expected value STRING.
        Long: The address of the site, expected value STRING.
        Lat: The address of the site, expected value STRING.
        """
        sites = {}
        sites["Sitename"] = Sitename
        sites["Address"] = Address
        sites["Region"] = Region
        sites["Long"] = Long
        sites["Lat"] = Lat
        self.site_list[Sitename] = sites
    
    def getSiteData(self,Sitename):
        """Returns sitedata for a specific site 
        Takes the sitename as an argument which needs to be fetched 
        """
        if Sitename in self.site_list:
            return self.site_list[Sitename]

    def returnVals(self):
        # Returns the whole site_list dictionary 
        return self.site_list
    

class providers(enum.Enum):
    GIS = 1
    PGE = 2

