from pydantic import BaseModel
from enum import Enum
from typing import List, Optional

from sedbackend.apps.cvs.vcs import models as vcs_models
from sedbackend.apps.cvs.market_input import models as mi_models


class TimeFormat(str, Enum):
    """
    The time formats that can be chosen for a process. The values are the defaults for the
    simulation (years)
    """
    MINUTES:str = 'minutes'
    HOUR:str = 'hour'
    DAY:str = 'day'
    WEEK:str = 'week'
    MONTH:str = 'month'
    YEAR:str = 'year'


class Rate(Enum):
    PRODUCT = 'per_product'
    PROJECT = 'per_project'


class FormulaGet(BaseModel):
    vcs_row_id: int
    design_group_id: int
    time: str
    time_unit: TimeFormat
    cost: str
    revenue: str
    rate: Rate


class FormulaPost(BaseModel):
    time: str
    time_unit: TimeFormat
    cost: str
    revenue: str
    rate: Rate
    value_driver_ids: Optional[List[int]] = None
    market_input_ids: Optional[List[int]] = None


class FormulaRowGet(FormulaGet):
    value_drivers: List[vcs_models.ValueDriver]
    market_inputs: List[mi_models.MarketInputGet]


class VcsDgPairs(BaseModel):
    vcs: str
    vcs_id: int
    design_group: str
    design_group_id: int
    has_formulas: int
