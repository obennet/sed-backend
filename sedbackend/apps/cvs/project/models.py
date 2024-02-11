from datetime import datetime
from typing import Optional
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sedbackend.apps.core.projects.models import AccessLevel
from sedbackend.apps.core.users.models import User
import sedbackend.apps.core.projects.models as proj_models


class CVSProject(BaseModel):
    id: int
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=10)
    owner: User
    datetime_created: datetime
    my_access_right: int
    project: proj_models.Project = None
    subproject: proj_models.SubProject = None
    image: Optional[str] = None


class CVSProjectPost(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=10)
    participants_access: Optional[dict[int, AccessLevel]] = {}
