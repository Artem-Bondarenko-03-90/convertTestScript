import shutil
from datetime import datetime
import json
import requests
from pytz import timezone

class originalOscFile(object):
    def __init__(self, name, parts, suf):
        self.name = name
        self.suf = suf
        self.parts = parts
        self.parts_in_client = []
        self.createdTimestamp = None
        self.inSSNTItimestamp = None
        self.convertedTimestamp = None
        self.clientId = None

    def copyOriginalOscInClient(self, client_dir):
        for part in self.parts:
            self.parts_in_client.append(shutil.copy(part, client_dir))
        tz = timezone('Europe/Moscow')
        self.createdTimestamp = datetime.now(tz)

    def requestFilesFromClient(self, addressSSNTI, token):
        headers = {'accept': 'application/json', 'Authorization': token, 'Content-Type': 'application/json-patch+json'}
        j = {"ssntiClientId": [str(self.clientId)], "pageNumber": 1}
        j1 = json.dumps(j)
        response = requests.post(url=str(addressSSNTI) + 'api/ssnti/client-files/clients-files/fetch-page' , data=j1, headers=headers)
        #print(response.content)
        if response.status_code == 200:
            return json.loads(response.content)