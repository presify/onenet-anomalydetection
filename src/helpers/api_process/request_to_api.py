import requests
import os

def request(params,api_type):
  url = os.path.join("http://0.0.0.0:3000/api/presify-onenet",api_type)
  response = requests.get(url,params=params)
  if response.status_code !=200:
    return {"status":False,"data":[],"cause":"API Crash..."}
  elif response.status_code ==200:
    return {"status":True,"data":response.json().get("data"),"cause":""}


