from typing import Optional, List

from pydantic import BaseModel

from sedbackend.apps.cvs.vcs.models import VCS, ValueDriver, VcsRow

# ======================================================================================================================
# CVS Design
# ======================================================================================================================


class Design(BaseModel):
    id: int
    vcs: VCS
    name: str
    description: Optional[str] = None


class DesignPost(BaseModel):
    name: str
    description: Optional[str] = None

# ======================================================================================================================
# CVS Design Quantified Objectives
# ======================================================================================================================


class QuantifiedObjective(BaseModel):
    id: int
    design: int
    value_driver: ValueDriver
    name: str
    property: float
    unit: str
    processes: List[VcsRow]


class QuantifiedObjectivePost(BaseModel):
    name: str
    property: float
    unit: str
