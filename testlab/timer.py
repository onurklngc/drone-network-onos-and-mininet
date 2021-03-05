import requests
import time

start = time.time()
for i in range(1):
    url = "http://localhost:8181/onos/v1/paths/of%3A0000000000000014/of%3A0000000000000001"
    payload = {}
    headers = {
      'Authorization': 'Basic b25vczpyb2Nrcw=='
    }
    requests.request("GET", url, headers=headers, data = payload)
end = time.time()
print(end-start)