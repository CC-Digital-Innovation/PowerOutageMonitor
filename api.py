from flask import Flask
from flask import request
from lookupApi import apiLookupRun


app = Flask(__name__)

@app.route('/lookup/',methods =['GET'])
def welcome():

    sitename = request.args.get('sitename', None)
    address = request.args.get('address', None)
    return apiLookupRun(sitename,address)

if __name__ == '__main__':
    app.run()