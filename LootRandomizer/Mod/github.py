from unrealsdk import Log
from . import options
import json, sys, os, threading

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

import requests

class Github:
    _url = "https://api.github.com/gists"

    def _create_gist(self, seed, content):
        Log(f"Creating gist for seed {seed} with content length {len(content)}")

        def executeRequest():
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {options.GithubToken.CurrentValue}",
                "X-GitHub-Api-Version": "2022-11-28"
            }

            postData = {
                "description": f"Tracker for {seed}",
                "public": True,
                "files": {
                    f"{seed}": {
                        "content": f"{content}"
                    }
                }
            }

            dataString = json.dumps(postData, indent=4)
            try:
                response = requests.post(self._url, headers=headers, data=dataString)
            except Exception as inst:
                Log(f"Got exception {type(inst)}: {inst}")

            Log(f"Response creating seed {seed} was {response.status_code}")
        
            if response.status_code == 201:
                gist = json.loads(response.content)
                options.GistId.CurrentValue = gist["id"]
                options.GistUrl.CurrentValue = gist["html_url"]
                options.SaveSettings()
            else:
                Log(f"Could not create gist, response code {response.status_code}")
        
        executeRequest()
        #threading.Thread(target=executeRequest).start()

    def update_gist(self, seed, content) -> None:
        if options.GithubToken.CurrentValue == '':
            return

        if options.GistId.CurrentValue == '':
            self._create_gist(seed, content)
        else:
            Log(f"Updating seed {seed} to gist {options.GistId.CurrentValue}")

            def executeRequest():
                headers = {
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {options.GithubToken.CurrentValue}",
                    "X-GitHub-Api-Version": "2022-11-28"
                }

                patchData = {
                    "description": f"Tracker for {seed}",
                    "files": {
                        f"{seed}": {
                            "content": f"{content}"
                        }
                    }
                }

                dataString = json.dumps(patchData, indent=4)

                response = None
                try:
                    response = requests.patch(f"{self._url}/{options.GistId.CurrentValue}", headers=headers, data=dataString)
                except:
                    Log("Unable to update gist")
                    self._create_gist(seed, content)

                if response != None:
                    Log(f"Response updating seed {seed} to gist {options.GistId.CurrentValue} was {response.status_code}")
                else:
                    Log(f"Response updating seed {seed} to gist {options.GistId.CurrentValue} was None")
            
            executeRequest()
            #threading.Thread(target=executeRequest).start()