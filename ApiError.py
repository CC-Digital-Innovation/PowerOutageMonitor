import json


class ApiError:
    def __init__(self, errorCode,errorMessage):
        self.errorCode = errorCode
        self.errorMessage = errorMessage

    def returnJson(self):
        error = {"Code": self.errorCode,"Message": self.errorMessage}
        return json.dumps(error, indent= 4)