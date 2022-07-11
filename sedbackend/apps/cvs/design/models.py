from typing import Optional, List

from pydantic import BaseModel

from sedbackend.apps.cvs.vcs.models import VCS, ValueDriver, VcsRow

# ======================================================================================================================
# CVS Design Quantified Objectives
# ======================================================================================================================


class QuantifiedObjective(BaseModel):
    design_group: int
    value_driver: ValueDriver
    name: str
    unit: Optional[str] = None


class QuantifiedObjectivePost(BaseModel):
    name: str
    unit: Optional[str] = None


# ======================================================================================================================
# CVS Design Quantified Objectives
# ======================================================================================================================


class QuantifiedObjectiveValue(BaseModel):
    design_id: int  # PRIMARY KEY(`design`, `value_driver`, `design_group`)
    qo: QuantifiedObjective
    value: float


class QuantifiedObjectiveValuePost(BaseModel):
    value: float


# ======================================================================================================================
# CVS Design
# ======================================================================================================================


class DesignGroup(BaseModel):
    id: int
    vcs: int
    name: str
    qo_list: Optional[List[QuantifiedObjective]]


class DesignGroupPost(BaseModel):
    name: str
    qo_list: Optional[List[int]]


class DesignGroupPut(BaseModel):
    name: str
    qo_list: Optional[List[QuantifiedObjective]]


# ======================================================================================================================
# CVS Design Row
# ======================================================================================================================


class Design(BaseModel):
    id: int
    design_group: int
    name: str
    qo_values: List[QuantifiedObjectiveValue]


class DesignPost(BaseModel):
    name: str
    qo_values: List[int]


