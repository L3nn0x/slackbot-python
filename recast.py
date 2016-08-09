import requests

class Recast:
    def __init__(self, token):
        self.token = token
        self.url = "https://api.recast.ai/v1/request"

    def getIntent(self, request):
        headers = {
                "Authorization" : "Token " + self.token
                }
        data = {
                "text" : request
                }
        r = requests.post(self.url, headers=headers, data=data)
        return r.text
