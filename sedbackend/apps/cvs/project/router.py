from fastapi import Depends, APIRouter, UploadFile
from fastapi.logger import logger
from sedbackend.apps.core.authentication.utils import get_current_active_user
from sedbackend.apps.core.projects.dependencies import SubProjectAccessChecker
from sedbackend.apps.core.projects.models import AccessLevel
from sedbackend.apps.core.users.models import User
from sedbackend.libs.datastructures.pagination import ListChunk
from sedbackend.apps.cvs.project import models, implementation

router = APIRouter()
CVS_APP_SID = "MOD.CVS"


@router.get(
    "/project/all",
    summary="Returns all of the user's CVS projects",
    response_model=ListChunk[models.CVSProject],
)
async def get_all_cvs_project(
    user: User = Depends(get_current_active_user),
) -> ListChunk[models.CVSProject]:
    return implementation.get_all_cvs_project(user.id)


@router.get(
    "/project/{native_project_id}",
    summary="Returns a CVS project based on id",
    description="Returns a CVS project based on id",
    response_model=models.CVSProject,
    dependencies=[
        Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))
    ],
)
async def get_csv_project(
    native_project_id: int, user: User = Depends(get_current_active_user)
) -> models.CVSProject:
    return implementation.get_cvs_project(native_project_id, user.id)


@router.post(
    "/project",
    summary="Creates a new CVS project",
    response_model=models.CVSProject,
)
async def create_csv_project(
    project_post: models.CVSProjectPost,
    user: User = Depends(get_current_active_user),
) -> models.CVSProject:
    return implementation.create_cvs_project(project_post, user.id)


@router.post(
    "/project/{native_project_id}/image",
    summary="Uploads an image for a CVS project",
    response_model=models.CVSProject,
    dependencies=[
        Depends(SubProjectAccessChecker(AccessLevel.list_can_edit(), CVS_APP_SID))
    ],
)
async def upload_cvs_project_image(
    native_project_id: int,
    image: UploadFile,
    user: User = Depends(get_current_active_user),
) -> models.CVSProject:
    return implementation.upload_cvs_project_image(native_project_id, image, user.id)


@router.put(
    "/project/{native_project_id}",
    summary="Edits a CVS project",
    response_model=models.CVSProject,
    dependencies=[
        Depends(SubProjectAccessChecker(AccessLevel.list_can_edit(), CVS_APP_SID))
    ],
)
async def edit_csv_project(
    native_project_id: int,
    project_post: models.CVSProjectPost,
    user: User = Depends(get_current_active_user),
) -> models.CVSProject:
    return implementation.edit_cvs_project(
        project_id=native_project_id, project_post=project_post, user_id=user.id
    )


@router.delete(
    "/project/{native_project_id}",
    summary="Deletes a CVS project based on id",
    response_model=bool,
    dependencies=[
        Depends(SubProjectAccessChecker(AccessLevel.list_are_admins(), CVS_APP_SID))
    ],
)
async def delete_cvs_project(
    native_project_id: int, user: User = Depends(get_current_active_user)
) -> bool:
    return implementation.delete_cvs_project(native_project_id, user.id)
