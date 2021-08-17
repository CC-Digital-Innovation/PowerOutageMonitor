from flask import Flask
from check_site import callJSON
from flask import jsonify


app = Flask(__name__)

@app.route('/<string:siteName>/')
def welcome(siteName):

    return jsonify(callJSON())
if __name__ == '__main__':
    app.run()