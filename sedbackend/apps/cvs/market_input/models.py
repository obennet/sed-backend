from pydantic import BaseModel
from sedbackend.apps.cvs.vcs import models as vcs_models


class MarketInputGet(BaseModel):
    vcs: int
    vcs_row: vcs_models.VcsRow
    time: float
    cost: float
    revenue: float


class MarketInputPost(BaseModel):
    time: float
    cost: float
    revenue: float
