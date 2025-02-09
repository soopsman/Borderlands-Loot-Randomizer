from . import options
import json, sys, os, threading
import unrealsdk

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

        dataString = json.dumps(data, indent=4)
        response = requests.request(method, url, headers=headers, data=dataString)
        options.LastSeed.CurrentValue = seed
        options.SaveSettings()
    
        if response.status_code == 201:
            gist = json.loads(response.content)
            options.GistId.CurrentValue = gist["id"]
            options.GistUrl.CurrentValue = gist["html_url"]
            options.SaveSettings()
        unrealsdk.RemoveHook("Engine.PlayerController.PlayerTick", "ModMenu.NetworkManager")
        
    threading.Thread(target=executeRequest).start()
    unrealsdk.RunHook("Engine.PlayerController.PlayerTick", "ModMenu.NetworkManager", _PlayerTick)

def _PlayerTick(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    return True