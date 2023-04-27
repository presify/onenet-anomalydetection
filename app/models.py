from pydantic import BaseModel

class Load(BaseModel):
  dataType: str
  startDate: str
  endDate: str
  outBiddingZoneDomain: str
  contamination: float = 0.05
  n_neigh: int = 12
  sigma: float = 2.4
  n_bins: int = 7
  threshold: int = 3

class Generation(BaseModel):
  dataType: str
  startDate: str
  endDate: str
  inDomain: str
  contamination: float = 0.05
  n_neigh: int = 12
  sigma: int = 2.4
  n_bins: int = 7
  threshold: int = 3

