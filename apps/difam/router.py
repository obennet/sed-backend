from typing import List

from fastapi import APIRouter, Security, Depends

import apps.difam.implementation as impl
import apps.difam.models as models
from apps.core.users.models import User
from apps.core.authentication.utils import get_current_active_user

router = APIRouter()


@router.get("/projects/",
            summary="List available DIFAM projects",)
async def get_difam_projects(segment_length: int, index: int, current_user: User = Depends(get_current_active_user)) \
        -> List[models.DifamProject]:
    current_user_id = current_user.id
    return impl.impl_get_difam_projects(segment_length, index, current_user_id)


@router.get("/projects/{native_project_id}",
            summary="Returns overview of DIFAM project",
            description="Returns overview of DIFAM project",)
async def get_difam_project(native_project_id: int) -> models.DifamProject:
    """
    Returns overview difam project information
    """
    return impl.impl_get_difam_project(native_project_id)

@router.post("/projects/",
             summary="Create new DIFAM project")
async def post_difam_project(difam_project_post: models.DifamProjectPost,
                             current_user: User = Depends(get_current_active_user)) -> models.DifamProject:
    current_user_id = current_user.id
    return impl.impl_post_difam_project(difam_project_post, current_user_id)
