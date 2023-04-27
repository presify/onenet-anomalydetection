from src.helpers.api_process.request_to_api import request
import pandas as pd
from src.configs.schemas import *

def get_load_data(loadType,startPeriod,endPeriod,outBiddingZone_Domain):
  schema = load_schema
  schema['loadType']=loadType
  schema['periodStart'] = startPeriod
  schema['periodEnd'] = endPeriod
  schema['outBiddingZone_Domain'] = outBiddingZone_Domain
  resp = request(schema,"load")
  return {"df":pd.DataFrame(resp.get("data")),"cause":""} if resp.get("status") == True else {"df":pd.DataFrame([]),"cause":resp.get("cause")}


def get_generation_data(generationType,startPeriod,endPeriod,in_Domain):
  schema = generation_schema
  schema['generationType'] = generationType
  schema['periodStart'] = startPeriod
  schema['periodEnd'] = endPeriod
  schema['in_Domain'] = in_Domain
  resp = request(schema,"generation")
  if generationType in ["insCapPerType"]:
    return {"df": resp.get("data"), "cause": ""} if resp.get("status") == True else {
      "df": [], "cause": resp.get("cause")}
  else:
    return {"df":pd.DataFrame(resp.get("data")),"cause":""} if resp.get("status") == True else {"df":pd.DataFrame([]),"cause":resp.get("cause")}


def get_transmission_data(transmissionType,startPeriod,endPeriod,in_Domain,out_Domain):
  schema = transmission_schema
  schema['transmissionType'] = transmissionType
  schema['periodStart'] = startPeriod
  schema['periodEnd'] = endPeriod
  schema['in_Domain'] = in_Domain
  schema['out_Domain'] = out_Domain
  resp = request(schema,"transmission")
  return {"df":pd.DataFrame(resp.get("data")),"cause":""} if resp.get("status") == True else {"df":pd.DataFrame([]),"cause":resp.get("cause")}


def get_balancing_data(balancingType,startPeriod,endPeriod,controlArea_Domain):
  schema = balancing_schema
  schema['balancingType'] = balancingType
  schema['periodStart'] = startPeriod
  schema['periodEnd'] = endPeriod
  schema['controlArea_Domain'] = controlArea_Domain
  resp = request(schema,"balancing")
  return {"df":pd.DataFrame(resp.get("data")),"cause":""} if resp.get("status") == True else {"df":pd.DataFrame([]),"cause":resp.get("cause")}





