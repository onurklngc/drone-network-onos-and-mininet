import logging

import requests

# ONOS_ADDRESS = "http://192.168.31.11:30120"
ONOS_ADDRESS = "http://localhost:8181"
APPLICATIONS_TO_REFRESH = {
    "org.boun.trafficobserver": "/home/onur/MS/trafficobserver/app/target/trafficobserver-app-1.0.0-SNAPSHOT.oar"}

APPLICATION_REST_PATH = "/onos/v1/applications"
HEADERS_GENERIC = {
    "Authorization": "Basic b25vczpyb2Nrcw==",
}
HEADERS_UPLOAD = {
    "Authorization": "Basic b25vczpyb2Nrcw==",
    "Content-Type": "application/octet-stream",
    "Accept": "application/json, text/plain, */*",
}


def debug_http_requests():
    try:
        import http.client as http_client
    except ImportError:
        # Python 2
        import httplib as http_client
    http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def delete_application(application):
    response = requests.request("DELETE", "{}{}/{}/active".format(ONOS_ADDRESS, APPLICATION_REST_PATH, application),
                                headers=HEADERS_GENERIC)
    print("DEACTIVATE %s result: %s" % (application, response.status_code))
    response = requests.request("DELETE", "{}{}/{}".format(ONOS_ADDRESS, APPLICATION_REST_PATH, application),
                                headers=HEADERS_GENERIC)
    print("DELETE %s result: %s" % (application, response.status_code))


def upload_application(application_id, application_file):
    with open(application_file, 'rb') as f:
        data = f.read()
        response = requests.request("POST",
                                    "{}{}?activate=true".format(ONOS_ADDRESS, APPLICATION_REST_PATH),
                                    headers=HEADERS_UPLOAD, data=data)
        print("UPLOAD %s result: %s" % (application_id, response.status_code))


# Activate apps first
def refresh_applications():
    for application_id in APPLICATIONS_TO_REFRESH:
        delete_application(application_id)
    for application_id, application_file in APPLICATIONS_TO_REFRESH.items():
        upload_application(application_id, application_file)


if __name__ == '__main__':
    refresh_applications()
    print("Finished")
