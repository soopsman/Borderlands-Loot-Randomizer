from unrealsdk import Log
from . import options
import json, sys, os, threading

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

import requests

GithubGistApi = "https://api.github.com/gists"

def update(seed, content) -> None:
    if options.GithubToken.CurrentValue == '':
        return

        def executeRequest():
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {options.GithubToken.CurrentValue}",
                "X-GitHub-Api-Version": "2022-11-28"
            }

        Log(f"Last seed updated {options.LastSeed.CurrentValue}")

        if options.LastSeed.CurrentValue == seed:
            data = {
                "description": f"Tracker for {seed}",
                "files": {
                    f"{seed}": {
                        "content": f"{content}"
                    }
                }
            }
        elif len(options.LastSeed.CurrentValue) > 0 and len(options.GistId.CurrentValue) > 0:
            data = {
                "description": f"Tracker for {seed}",
                "files": {
                    f"{seed}": {
                        "content": f"{content}"
                    },
                    f"{options.LastSeed.CurrentValue}": {
                        "content": ""
                    }
                }
            }
        else:
            data = {
                "description": f"Tracker for {seed}",
                "public": True,
                "files": {
                    f"{seed}": {
                        "content": f"{content}"
                    }
                }
            }

        if len(options.GistId.CurrentValue) == 0:
            method = "POST"
            url = GithubGistApi
        else:
            method = "PATCH"
            url = f"{GithubGistApi}/{options.GistId.CurrentValue}"

        Log(f"About to {method} to {url} for seed {seed}")
        
        dataString = json.dumps(data, indent=4)
            try:
            response = requests.request(method, url, headers=headers, data=dataString)
            options.LastSeed.CurrentValue = seed
            options.SaveSettings()
            except Exception as inst:
                Log(f"Got exception {type(inst)}: {inst}")

        Log(f"{method} response for seed {seed} was {response.status_code}")
        
            if response.status_code == 201:
                gist = json.loads(response.content)
                options.GistId.CurrentValue = gist["id"]
                options.GistUrl.CurrentValue = gist["html_url"]
                options.SaveSettings()
        
        #threading.Thread(target=executeRequest).start()
    executeRequest()