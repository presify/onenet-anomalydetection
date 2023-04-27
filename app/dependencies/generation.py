from app.models import Generation
from fastapi import Depends
from src.helpers.external.utiliy import datetime_checker,data_type_mapping
from src.lib.preprocess.dataset_construction import *
from src.lib.models.anomaly import lof,hbos,robust_covariance,three_sigma_rule,deep_anomaly_detector
import pandas as pd

def data(generation: Generation = Depends(Generation)):
  if datetime_checker(generation.startDate,generation.endDate) == False:
    return {"status":False,"warning":["Your date range has exceeded 365 days. Try shorter range."],"data":[]}
  generation_data = get_generation_data(data_type_mapping(generation.dataType), generation.startDate, generation.endDate, generation.inDomain).get("df")
  print(generation_data, "asdasdasdasd")
  if generation_data.shape[0] == 0:
    return {"status":False,"warning":["There is no data in given range."],"data":[]}
  return {"status":True,"data":generation_data,"warning":[]}



def aggregate_solar(data: data = Depends(data),generation: Generation = Depends(Generation)):
  if generation.dataType not in ["Aggregated_Generation_Forecast","Solar_Generation_Forecast"]:
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
  df['lof'],df['hbo'],df['rob_cov'],df['sigma_rule'], df['autoencoder'], df['ensemble'] = 0,0,0,0,0,0
  for month in range(1,13):
    for hour in range(9,16):
      df_ = df[df['date'].dt.month==month]
      df_ = df_[df_['date'].dt.hour == hour]
      if df_.shape[0] > generation.n_neigh:
        lof_score = lof(df_,generation.n_neigh)
        hbo_score = hbos(df_,generation.n_bins,generation.contamination)
        sigma_rules_score = three_sigma_rule(df_,generation.sigma)
        rob_cov_score = robust_covariance(df_,generation.contamination)
        df.loc[hbo_score, 'hbo'] = 1
        df.loc[lof_score, 'lof'] = 1
        df.loc[rob_cov_score, 'rob_cov'] = 1
        df.loc[sigma_rules_score, 'sigma_rule'] = 1
  df = df.set_index(df.date)
  df.loc[autoencoder_results, 'autoencoder'] = 1
  df['total'] = df['lof'] + df['rob_cov'] + df['sigma_rule'] + df['hbo'] + df['autoencoder']
  df.loc[df['total']>=generation.threshold, ['ensemble']] = 1
  df.drop(['total'],axis=1,inplace=True)
  df.to_excel("/Users/omeraynur/Downloads/solarrr.xlsx",index=False)
  return {"data":df.to_dict(orient='records'),"message":""}


def actual_generation_prod_type(data: data = Depends(data),generation: Generation = Depends(Generation)):
  if generation.dataType not in  ['Biomass Actual', 'Fossil Brown coal/Lignite Actual', 'Fossil Coal-derived gas Actual',
                                  'Fossil Gas Actual', 'Fossil Hard coal Actual', 'Hydro Run-of-river and poundage Actual',
                                  'Hydro Water Reservoir Actual', 'Nuclear Actual', 'Other Actual', 'Other renewable Actual',
                                  'Waste Actual', 'Wind Onshore Actual']:
    return {}
  if len(data.get("warning")) !=0:
    return data
  df = data.get("data")
  key = generation.dataType.split(" Actual")[0]
  if key in ["Fossil Oil","Hydro Pumped Storage","Solar"]:
    return {}
  df['value'] = df['value'].astype(float)
  df['date'] = pd.to_datetime(df['date'])
  freq = "other" if len(df['date'].dt.minute.unique()) > 1 else "hourly"
  df1 = df[df['type']==key].copy()
  df1 = df1.set_index(df1.date)
  df1.drop(columns = ['date'],inplace= True)
  autoencoder_results = deep_anomaly_detector(df1[['value']],freq)
  df['lof'],df['hbo'],df['rob_cov'],df['sigma_rule'], df['autoencoder'], df['ensemble'] = 0,0,0,0,0,0
  df__ = df[df['type']==key][["date","value", "type", "lof", "hbo", "rob_cov", "sigma_rule","autoencoder","ensemble"]]
  for month in range(1, 13):
    df_ = df__[df__['date'].dt.month == month]
    if df_.shape[0] > 0:
      lof_score = lof(df_, generation.n_neigh)
      hbo_score = hbos(df_, generation.n_bins,generation.contamination)
      sigma_rules_score = three_sigma_rule(df_, generation.sigma)
      rob_cov_score = robust_covariance(df_, generation.contamination)
      df__.loc[hbo_score, 'hbo'] = 1 if len(hbo_score) > 0 else 0
      df__.loc[lof_score, 'lof'] = 1 if len(lof_score) > 0 else 0
      df__.loc[rob_cov_score, 'rob_cov'] = 1 if len(rob_cov_score) > 0 else 0
      df__.loc[sigma_rules_score, 'sigma_rule'] = 1 if len(sigma_rules_score) > 0 else 0
  df__ = df__.set_index(df__.date)
  df__.loc[autoencoder_results, 'autoencoder'] = 1
  df__['total'] = df__['lof'] + df__['rob_cov'] + df__['sigma_rule'] + df__['hbo'] + df__['autoencoder']
  df__.loc[df__['total'] >= generation.threshold, ['ensemble']] = 1
  df__.drop(['total','type'], axis=1, inplace=True)
  df__.to_excel("/Users/omeraynur/Downloads/wind.xlsx",index=False)
  return {"data":df__.to_dict(orient='records'),"message":""}


def generation(agg_solar: aggregate_solar = Depends(aggregate_solar),actual_prod: actual_generation_prod_type = Depends(actual_generation_prod_type)):
  obj = {**agg_solar,**actual_prod}
  return obj if obj !={} else {"data":[],"message":"Your dataType parameter is not appropriate."}
