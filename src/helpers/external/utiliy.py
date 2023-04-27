from datetime import datetime, timedelta
import pandas as pd

def datetime_checker(start_period,end_period):
  total_days = datetime.strptime(end_period, '%Y-%m-%d %H:%M')-datetime.strptime(start_period, '%Y-%m-%d %H:%M')
  total_days = int(total_days/timedelta(days=1))
  return False if total_days>366 else True


def data_type_mapping(data_type):
  if data_type in ['Biomass Actual', 'Fossil Brown coal/Lignite Actual', 'Fossil Coal-derived gas Actual',
                                  'Fossil Gas Actual', 'Fossil Hard coal Actual', 'Hydro Run-of-river and poundage Actual',
                                  'Hydro Water Reservoir Actual', 'Nuclear Actual', 'Other Actual', 'Other renewable Actual',
                                  'Waste Actual', 'Wind Onshore Actual']:
    return "acGenPerProdType"
  elif data_type =="Aggregated_Generation_Forecast":
    return "dayAhAggGenFor"
  elif data_type ==   "Solar_Generation_Forecast":
    return "dayAhSolGenFor"
  elif data_type == "Load_Actual":
    return "actLoad"
  elif data_type == "Load_Forecast":
    return "dayAhLoadFor"
  elif data_type == "Week_Load_Forecast":
    return "weekAhLoadFor"

def lag_creator(data, lag):
  lags = []
  for i in range(1, lag):
    lagged = data.shift(i)
    lagged.columns = ["value_" + str(i)]
    lags.append(lagged)
  lags = pd.concat(lags, 1)
  return pd.concat([data, lags], 1).dropna()

def dummy_creator(df):
        hours = pd.get_dummies(pd.DatetimeIndex(df.index).hour, drop_first=False )\
        .set_index(pd.DatetimeIndex(df.index))
        df = pd.concat([df, hours], 1)
        months = pd.get_dummies(pd.DatetimeIndex(df.index).month, drop_first=False )\
        .set_index(pd.DatetimeIndex(df.index))
        #df = pd.concat([df, months], 1)
        #season = [(month % 12 + 3) // 3 for month in pd.DatetimeIndex(df.index).month]
        season_dum = pd.get_dummies([(month % 12 + 3) // 3 for month in pd.DatetimeIndex(df.index).month],  drop_first=False).set_index(pd.DatetimeIndex(df.index))
        ##season_sin = pd.DataFrame(np.sin([math.degrees(i) for i in season]), index=data.index)
        #data = pd.concat([data, season_sin], 1)
        #df = pd.concat([df, season_dum], 1)

        return df

