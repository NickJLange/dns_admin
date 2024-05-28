#!/usr/bin/env python3 
import requests
import urllib3
import json

import logging
from http.client import HTTPConnection  # py3

HTTPConnection.debuglevel = 1
# Enable debug-level logging for the requests library
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

# Disable SSL verification and suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

device_ip = "192.168.100.1"


# Replace these placeholders with your API endpoints and credentials
login_url = f"https://{ device_ip }/api/auth/login"
base_api_url = f"https://{ device_ip }/proxy/network/api"
base_api_v2_url = f"https://{ device_ip }/proxy/network/v2/api"

mac_block_url = f"{base_api_url}/s/default/cmd/stamgr"
client_list_url = (
    f"{base_api_v2_url}/site/default/clients/active?includeTrafficUsage=false"
)
# https://192.168.100.1/proxy/network/v2/api/site/default/clients/active?includeTrafficUsage=true

username = "overlord"
password = "0veroveroveR"

# Initial login to obtain session cookies
login_data = {
    "username": username,
    "password": password,
    "rememberMe": False,
    "token": "",
}
session = requests.Session()
resp = session.post(login_url, json=login_data, verify=False)
if resp.status_code != 200:
    print("Uh oh")

other_token = resp.headers["X-CSRF-Token"]
print(other_token)
token = resp.cookies if "TOKEN" in resp.cookies else None

session.headers["X-CSRF-Token"] = other_token
# print(token)

# resp2 = session.get(client_list_url, verify=False)

## block sta

# --data-raw '{"mac":"cc:d2:81:7e:b2:b0","cmd":"block-sta"}'

block_sta = {"cmd": "unblock-sta", "mac": "cc:d2:81:7e:b2:b0"}

resp2 = session.post(mac_block_url, json=block_sta, verify=False)

print(resp2.text)

# https://192.168.100.1/proxy/network/v2/api/site/default/client/a0:ce:c8:33:f6:7a/24hr-activity?mac=a0:ce:c8:33:f6:7a
# post - login
# post - https://api/auth/logout

###
# curl 'https://192.168.100.1/api/auth/login' -X POST  -H 'Content-Type: application/json' --data-raw '{"username":"overlord","password":"0veroveroveR","token":"","rememberMe":false}'


# -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/114.0'
# -H 'Accept: */*'
# -H 'Accept-Language: en-US,en;q=0.5'
# -H 'Accept-Encoding: gzip, deflate, br'
# -H 'Referer: https://192.168.100.1/login?redirect=%2F'
#  -H 'X-CSRF-Token: bd014c3a-833b-4fad-adce-9a2d72f780d6'
# -H 'Origin: https://192.168.100.1'
# -H 'DNT: 1'
# -H 'Connection: keep-alive'
# -H 'Sec-Fetch-Dest: empty'
# -H 'Sec-Fetch-Mode: cors'
# -H 'Sec-Fetch-Site: same-origin'
# -H 'TE: trailers'

# TOKEN == TOKEN	"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI5NjA5OGMyZC04NzJkLTQ4NGQtOTNhMS0wNGFiZTNmNGVmY2UiLCJjc3JmVG9rZW4iOiIzMzA4YjZjZC1mZDBjLTQzZTktOWNlMy1jMWE4ZTkwZjZiM2QiLCJqdGkiOiI0NDQ2MzllZS0yZjlhLTQwYzMtYTBiNC03MGFiMWNjZjQzNmMiLCJwYXNzd29yZFJldmlzaW9uIjoxNjg3MTQ4NTMxLCJpYXQiOjE2ODcxNDg3ODYsImV4cCI6MTY4NzE1MjM4Nn0.kj_1H96n3ULW8zFSOgCoM_3OwxEOAPty9g-SZxq81Y0"
###
# curl 'https://192.168.100.1/' --data-raw '{"mac":"cc:d2:81:7e:b2:b0","cmd":"block-sta"}'


# curl -k -b TOKEN='' 'https://192.168.100.1/proxy/network/api/s/default/cmd/stamgr' -X POST --data-raw '{"mac":"cc:d2:81:7e:b2:b0","cmd":"unblock-sta"}'

### c
# curl 'https://192.168.100.1/proxy/network/api/s/default/cmd/stamgr' -X POST -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/114.0' -H 'Accept: application/json, text/plain, */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://192.168.100.1/network/default/clients/properties/cc:d2:81:7e:b2:b0/settings' -H 'Content-Type: application/json' -H 'X-CSRF-Token: 3308b6cd-fd0c-43e9-9ce3-c1a8e90f6b3d' -H 'Origin: https://192.168.100.1' -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Cookie: TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI5NjA5OGMyZC04NzJkLTQ4NGQtOTNhMS0wNGFiZTNmNGVmY2UiLCJjc3JmVG9rZW4iOiIzMzA4YjZjZC1mZDBjLTQzZTktOWNlMy1jMWE4ZTkwZjZiM2QiLCJqdGkiOiI0NDQ2MzllZS0yZjlhLTQwYzMtYTBiNC03MGFiMWNjZjQzNmMiLCJwYXNzd29yZFJldmlzaW9uIjoxNjg3MTQ4NTMxLCJpYXQiOjE2ODcxNDkxMzksImV4cCI6MTY4NzE1MjczOX0.sIxton82RF0XqmomadFJIZ2aT1ps8SBqIbZksPLidHQ' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-origin' -H 'TE: trailers'
# --data-raw '{"mac":"cc:d2:81:7e:b2:b0","cmd":"unblock-sta"}'

# GET https://192.168.100.1/proxy/network/v2/api/


##Referer: https://192.168.100.1/network/default/clients/properties/cc:d2:81:7e:b2:b0/settings
