from app.models import Load
from fastapi import Depends
from src.helpers.external.utiliy import datetime_checker,data_type_mapping
from src.lib.preprocess.dataset_construction import *
from src.lib.models.anomaly import lof,hbos,robust_covariance,three_sigma_rule,deep_anomaly_detector
import pandas as pd

def data(load: Load = Depends(Load)):
  if datetime_checker(load.startDate,load.endDate) == False:
    return {"status":False,"warning":["Your date range has exceeded 365 days. Try shorter range."],"data":[]}
  load_data = get_load_data(data_type_mapping(load.dataType), load.startDate, load.endDate, load.outBiddingZoneDomain).get("df")
  if load_data.shape[0] == 0:
    return {"status":False,"warning":["There is no data in given range."],"data":[]}
  return {"status":True,"data":load_data,"warning":[]}


def actual_day(data: data = Depends(data),load: Load = Depends(Load)):
  if load.dataType not in  ['Load_Actual','Load_Forecast']:
    return {}
  if len(data.get("warning")) !=0:
    return data
  df = data.get("data")
  df['value'] = df['value'].astype(float)
  df['date'] = pd.to_datetime(df['date'])
  freq = "other" if len(df['date'].dt.minute.unique()) > 1 else "hourly"
  df1 = df.copy()
  df1 = df1.set_index(df1.date)
  df1.drop(columns = ['date'],inplace= True)
  autoencoder_results = deep_anomaly_detector(df1,freq)
  df['lof'], df['hbo'], df['rob_cov'], df['sigma_rule'], df['autoencoder'], df['ensemble'] = 0, 0, 0, 0, 0, 0
  for month in range(1,13):
    for hour in range(1,25):
      df_ = df[df['date'].dt.month==month]
      df_ = df_[df_['date'].dt.hour == hour]
      if df_.shape[0] > 0:
        lof_score = lof(df_,load.n_neigh)
        hbo_score = hbos(df_,load.n_bins,load.contamination)
        sigma_rules_score = three_sigma_rule(df_,load.sigma)
        rob_cov_score = robust_covariance(df_,load.contamination)
        df.loc[hbo_score, 'hbo'] = 1
        df.loc[lof_score, 'lof'] = 1
        df.loc[rob_cov_score, 'rob_cov'] = 1
        df.loc[sigma_rules_score, 'sigma_rule'] = 1
  df = df.set_index(df.date)
  df.loc[autoencoder_results, 'autoencoder'] = 1
  df['total'] = df['lof'] + df['rob_cov'] + df['sigma_rule'] + df['hbo'] + df['autoencoder']
  df.loc[df['total'] >= load.threshold, ['ensemble']] = 1
  df.drop(['total'],axis=1,inplace=True)
  return {"data":df.to_dict(orient='records'),"message":""}


def week(data: data = Depends(data),load: Load = Depends(Load)):
  if load.dataType != "Week_Load_Forecast":
    return {}
  if len(data.get("warning")) !=0:
    return data
  df = data.get("data")
  returning_obj = {"data":{},"message":""}
  df['min_value'] = df['min_value'].astype(float)
  df['max_value'] = df['max_value'].astype(float)
  df['date'] = pd.to_datetime(df['date'])
  df['lof'], df['hbo'], df['rob_cov'], df['sigma_rule'], df['ensemble'] = 0, 0, 0, 0, 0
  for key in ["min_value","max_value"]:
    df__ = df[["date",key,"lof","hbo","rob_cov","sigma_rule","ensemble"]]
    df__ = df__.rename(columns = {key:"value"})
    for month in range(1,13):
      df_ = df__[df__['date'].dt.month==month]
      if df_.shape[0] >load.n_neigh:
        lof_score = lof(df_,load.n_neigh)
        hbo_score = hbos(df_,load.n_bins,load.contamination)
        sigma_rules_score = three_sigma_rule(df_,load.sigma)
        rob_cov_score = robust_covariance(df_,load.contamination)
        df__.loc[hbo_score, 'hbo'] = 1 if len(hbo_score)>0 else 0
        df__.loc[lof_score, 'lof'] = 1 if len(lof_score)>0 else 0
        df__.loc[rob_cov_score, 'rob_cov'] = 1 if len(rob_cov_score)>0 else 0
        df__.loc[sigma_rules_score, 'sigma_rule'] = 1 if len(sigma_rules_score)>0 else 0
        df__['total'] = df__['lof'] + df__['rob_cov'] + df__['sigma_rule'] + df__['hbo']
        df__.loc[df__['total']>load.threshold, ['ensemble']] = 1
        df__.drop(['total'],axis=1,inplace=True)
    returning_obj["data"][key] = df__.to_dict(orient='records')
  return returning_obj


def load(actual_day_results: actual_day = Depends(actual_day),week_results: week = Depends(week)):
  obj = {**actual_day_results,**week_results}
  return obj if obj !={} else {"data":[],"message":"Your dataType parameter is not appropriate."}


