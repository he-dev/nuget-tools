import time
import json
import requests

from pprint import pprint
# from reusable import log_elapsed

DELETE_DELAY_IN_SECONDS = 0.25
NUGET_API_VERSION = "3"
SERVICE_INDEX_URL = f"https://api.nuget.org/v{NUGET_API_VERSION}/index.json"


def load_config():
    with open("..\\blackhole\\settings\\python\\nuget-tools.json", "r") as f:
        return json.load(f)


class NugGetClient:

    def __init__(self, api_key):
        self.__apiKey = api_key

    def __enter__(self):
        # http://docs.python-requests.org/en/master/api/
        self.nuGet_session = requests.Session()
        self.nuGet_session.headers.update({"X-NuGet-ApiKey": self.__apiKey})
        return self

    def get_search_url(self):
        response = self.nuGet_session.get(SERVICE_INDEX_URL)
        if response.status_code == requests.codes.ok:
            resources = response.json()["resources"]
            return self.get_resource_url(resources, "SearchQueryService")
        else:
            raise Exception("Could not reach service index.")

    @staticmethod
    def get_resource_url(resources, type):
        return [x for x in resources if x["@type"] == type][0]["@id"]

    def find_my_packages(self, search_url):
        query = "author:he-dev&take=100"
        # GET {@id}?q={QUERY}&skip={SKIP}&take={TAKE}&prerelease={PRERELEASE}&semVerLevel={SEMVERLEVEL}"
        response = self.nuGet_session.get(f"{search_url}?q={query}")
        if response.status_code == requests.codes.ok:
            # https://docs.microsoft.com/en-us/nuget/api/search-query-service-resource
            return response.json()["data"]
        else:
            raise Exception("Could not search for packages.")

    @staticmethod
    def get_obsolete_packages(data):
        versions_to_unlist = [{"id": x["id"], "previous": [v["version"] for v in x["versions"][:-1]]} for x in data]
        return versions_to_unlist

    def unlist_packages(self, packages_to_unlist, list_only=True):
        for unlist in packages_to_unlist:
            package_id = unlist["id"]
            pprint(package_id)
            for version in unlist["previous"]:
                url = f"https://www.nuget.org/api/v2/package/{package_id}/{version}"
                if list_only:
                    print(f"\t{url} - this is just a test")
                else:
                    # we don't want to remove them too fast
                    time.sleep(DELETE_DELAY_IN_SECONDS)
                    response = self.nuGet_session.delete(url)
                    print(f"\t{url} - {response.status_code}")
                    if response.status_code > 200:
                        message = json.loads(response.content)["message"]
                        print(f"\t{message}")
                        return

    def __exit__(self, exc_type, exc_value, traceback):
        self.nuGet_session.close()


# --- --- ---

# @log_elapsed
def main():
    config = load_config()

    with NugGetClient(config["apiKey"]) as nuGet:
        search_url = nuGet.get_search_url()
        my_packages = nuGet.find_my_packages(search_url)
        obsolete_packages = nuGet.get_obsolete_packages(my_packages)
        nuGet.unlist_packages(obsolete_packages, list_only=False)


if __name__ == '__main__':
    main()
