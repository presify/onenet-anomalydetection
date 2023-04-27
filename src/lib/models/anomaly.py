from pyod.models.hbos import HBOS
from sklearn.covariance import EllipticEnvelope
from sklearn.neighbors import LocalOutlierFactor
import numpy as np
import pandas as pd
from tensorflow import keras
from keras import layers
from sklearn.preprocessing import MinMaxScaler
import warnings
from datetime import datetime
from src.helpers.external.utiliy import lag_creator, dummy_creator
warnings.filterwarnings("ignore")

def lof(df,n_neigh):
  X = [[i] for i in df['value'].values.tolist()]
  clf = LocalOutlierFactor(n_neighbors=n_neigh, novelty=True, metric="l1")
  clf.fit(X)
  pred_list = list()
  for data,val,idx in zip(X,df['value'].values.tolist(),df.index.tolist()):
    result = clf.predict([data])[0]
    if result == -1:
      pred_list.append(idx)
  return pred_list

def three_sigma_rule(df,param):
  mean = df['value'].mean()
  std = df['value'].std()
  pred_list = list()
  for idx,row in df.iterrows():
    if abs(mean-row['value']) > param*std:
      pred_list.append(idx)
  return pred_list

#"10YDE-ENBW-----N"
def hbos(df,n_bins,contamination):
  X = [[i] for i in df['value'].values.tolist()]
  idx_list = [i for i in df.index.tolist()]
  hbos = HBOS(n_bins=n_bins, contamination=contamination)
  hbos.fit(X)
  y_train_pred = hbos.predict(X)
  l  = [x*y for x,y in zip(y_train_pred,idx_list)]
  return list(filter(lambda num: num !=0,l))

def robust_covariance(df,contamination):
  X = [[i] for i in df['value'].values.tolist()]
  idx_list = df.index.tolist()
  detector = EllipticEnvelope(contamination=contamination, random_state=0)
  is_outlier = detector.fit(X).predict(X)
  pred_list = list()
  for i,idx in zip(is_outlier,idx_list):
    if i == -1:
      pred_list.append(idx)
  return pred_list

def deep_anomaly_detector(df, freq):
    scaler = MinMaxScaler()
    scaler2 = MinMaxScaler()
    dataset = df
    scale = dataset.shape[0]//24
    dataset = dataset[-24*scale:]
    dataset2 = pd.DataFrame(scaler.fit_transform(dataset), columns = ["value"] , index = dataset.index)
    dataset2 = lag_creator(dataset2, 25 if freq == "hourly" else 96)
    dataset3 = pd.DataFrame(scaler.inverse_transform(np.array(dataset2.value).reshape(-1,1)),index=dataset2.index,columns=["value"])
    #dataset2 = dataset2.sample(frac=1)
    #dataset2 = pd.DataFrame(scaler.fit_transform(dataset2), index=dataset2.index, columns=dataset2.columns)
    dataset2 = dummy_creator(dataset2)
    x_train = dataset2
    x_train = scaler2.fit_transform(dataset2)            
    x_train = np.array(x_train)#.reshape(-1,24, 24 if freq == "hourly" else 96,1)
    y_train = np.array(dataset2.value)
    
    inputs = keras.Input(shape=(np.shape(x_train)[1]))
    
    x1 = layers.Dense(32, kernel_initializer='lecun_uniform')
    x1_out = x1(inputs)
    #x2 = layers.Dropout(0.5)
    #x2_out = x2(x1_out, training=False)
    x3 = layers.Dense(16,kernel_initializer='lecun_uniform')
    x3_out = x3(x1_out)
    #x4 = layers.Dropout(0.5)
    #x4_out = x4(x3_out, training=False)
    x5 = layers.Dense(8,   kernel_initializer='lecun_uniform')
    x5_out = x5(x3_out)
    #x6 = layers.Dropout(0.5)
    #x6_out = x6(x5_out, training=False)
    outputs = layers.Dense(1, kernel_initializer='lecun_uniform')
    outputs_out = outputs(x5_out)
    model_nn1 = keras.Model(inputs, outputs_out, name="demand")
    #cost_function = fe.custom_loss_function_yedas if con_config.company == 'yedas' else fe.custom_loss_function_adm if con_config.company == 'adm' else fe.custom_loss_function_gdz
    cost_function = keras.losses.MeanSquaredError()
    opt = keras.optimizers.Adam(learning_rate=0.001, beta_1=0.9, beta_2=0.999, amsgrad=True)
    model_nn1.compile(optimizer=opt,
                      loss= cost_function,
                      metrics=['mse'])
    #es = keras.callbacks.EarlyStopping(monitor='val_loss', mode='min', verbose=0, patience=10)
    
    preds=[]
    
    for i in range(0,5):
        history = model_nn1.fit(
            x_train,
            y_train,
            epochs=50,
            batch_size=64,
            validation_split=0.2,
            callbacks=[
               keras.callbacks.EarlyStopping(monitor="val_loss", patience=20, mode="min")
            ],
        )
    

        x_pred = pd.DataFrame(model_nn1.predict(x_train).reshape(-1,1),index=dataset2.index, columns=["values"])
        x_pred["values"][x_pred["values"]<0] = 0
        preds.append(x_pred)
        #abs_error.append(np.mean(np.abs(x_pred - dataset), axis=1))
    preds=pd.concat(preds,1)
    preds2 = pd.DataFrame(scaler.inverse_transform(np.array(preds.mean(1).sort_index()).reshape(-1,1)), index=dataset2.sort_index().index, columns =["value"])
    res = dataset3.merge(preds2, right_index=True, left_index= True)
    std=preds.std(1)
    diffs = np.abs(res[res.columns[0]]-res[res.columns[1]])
    """
    diffs_all=[]
    for i in range(5):
        compare_dataset = pd.concat([dataset2.value,preds.iloc[:,i]],1)
        diffs = np.abs(compare_dataset["value"]-compare_dataset["values"])
        diffs_all.append(diffs.mean())
    compare_dataset = pd.concat([dataset2.value,preds.iloc[:,np.argmin(diffs_all)]],1)
    diffs = np.abs(compare_dataset["value"]-compare_dataset["values"])
    """
    pred_list = dataset3.value.iloc[np.where(diffs>diffs.std()*6)[0]]
    pred_list = pd.DataFrame(pred_list.sort_index())      
    return pred_list.index



