from typing import List
from fastapi import Depends, APIRouter
from sedbackend.apps.core.authentication.utils import get_current_active_user
from sedbackend.apps.core.projects.dependencies import SubProjectAccessChecker
from sedbackend.apps.core.projects.models import AccessLevel
from sedbackend.apps.core.users.models import User
from sedbackend.apps.cvs.design.router import router
from sedbackend.apps.cvs.project.router import CVS_APP_SID
from sedbackend.apps.cvs.vcs.models import ValueDriver
from sedbackend.libs.datastructures.pagination import ListChunk
from sedbackend.apps.cvs.vcs import models, implementation, implementation as vcs_impl

router = APIRouter()


# ======================================================================================================================
# VCS
# ======================================================================================================================


@router.get(
    '/project/{native_project_id}/vcs/all',
    summary='Returns all of VCSs of a project',
    response_model=ListChunk[models.VCS],
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))]
)
async def get_all_vcs(native_project_id: int) -> ListChunk[models.VCS]:
    return implementation.get_all_vcs(native_project_id)


@router.get(
    '/project/{native_project_id}/vcs/{vcs_id}',
    summary='Returns a VCS',
    response_model=models.VCS,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))]
)
async def get_vcs(native_project_id: int, vcs_id: int) -> models.VCS:
    return implementation.get_vcs(native_project_id, vcs_id)


@router.post(
    '/project/{native_project_id}/vcs',
    summary='Creates a new VCS in a project',
    response_model=models.VCS,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_edit(), CVS_APP_SID))]
)
async def create_vcs(native_project_id: int, vcs_post: models.VCSPost) -> models.VCS:
    return implementation.create_vcs(native_project_id, vcs_post)


@router.put(
    '/project/{native_project_id}/vcs/{vcs_id}',
    summary='Edits a VCS',
    response_model=models.VCS,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_edit(), CVS_APP_SID))]
)
async def edit_vcs(native_project_id: int, vcs_id: int, vcs_post: models.VCSPost) -> models.VCS:
    return implementation.edit_vcs(native_project_id, vcs_id, vcs_post)


@router.delete(
    '/project/{native_project_id}/vcs/{vcs_id}',
    summary='Deletes a VCS based on id',
    response_model=bool,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_edit(), CVS_APP_SID))]
)
async def delete_vcs(native_project_id: int, vcs_id: int) -> bool:
    return implementation.delete_vcs(native_project_id, vcs_id)


# ======================================================================================================================
# VCS Table
# ======================================================================================================================


@router.get(
    '/project/{native_project_id}/vcs/{vcs_id}/table',
    summary='Returns the table of a a VCS',
    response_model=List[models.VcsRow],
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))]
)
async def get_vcs_table(native_project_id: int, vcs_id: int) -> List[models.VcsRow]:
    return implementation.get_vcs_table(native_project_id, vcs_id)


@router.put(
    '/project/{native_project_id}/vcs/{vcs_id}/table',
    summary='Edits rows of the vcs table',
    response_model=bool,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_edit(), CVS_APP_SID))]
)
async def edit_vcs_table(native_project_id: int, vcs_id: int, updated_table: List[models.VcsRowPost]) -> bool:
    return implementation.edit_vcs_table(native_project_id, vcs_id, updated_table)


# ======================================================================================================================
# VCS Value driver
# ======================================================================================================================


@router.get(
    '/value-driver/all',
    summary='Returns all of value drivers',
    response_model=List[models.ValueDriver],
)
async def get_all_value_driver(user: User = Depends(get_current_active_user)) -> List[models.ValueDriver]:
    return implementation.get_all_value_driver(user.id)


@router.get(
    '/project/{native_project_id}/vcs/{vcs_id}/value-driver/all',
    summary='Fetch all value drivers in a vcs',
    response_model=List[ValueDriver],
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))]
)
async def get_all_value_driver_vcs(native_project_id: int, vcs_id: int) -> List[ValueDriver]:
    return vcs_impl.get_all_value_driver_vcs(native_project_id, vcs_id)


@router.get(
    '/value-driver/{value_driver_id}',
    summary='Returns a value driver',
    response_model=models.ValueDriver,
)
async def get_value_driver(value_driver_id: int) -> models.ValueDriver:
    return implementation.get_value_driver(value_driver_id)


@router.post(
    '/value-driver',
    summary='Creates a new value driver',
    response_model=models.ValueDriver,
)
async def create_value_driver(value_driver_post: models.ValueDriverPost,
                              user: User = Depends(get_current_active_user)) -> models.ValueDriver:
    return implementation.create_value_driver(user.id, value_driver_post)


@router.put(
    '/value-driver/{value_driver_id}',
    summary='Edits a value driver',
    response_model=models.ValueDriver,
)
async def edit_value_driver(value_driver_id: int, value_driver_post: models.ValueDriverPost) -> models.ValueDriver:
    return implementation.edit_value_driver(value_driver_id, value_driver_post)


@router.delete(
    '/value-driver/{value_driver_id}',
    summary='Deletes a value driver',
    response_model=bool,
)
async def delete_value_driver(value_driver_id: int) -> bool:
    return implementation.delete_value_driver(value_driver_id)


# ======================================================================================================================
# VCS ISO Processes
# ======================================================================================================================


@router.get(
    '/vcs/iso-processes/all',
    summary='Returns all ISO processes',
    response_model=List[models.VCSISOProcess],
)
async def get_all_iso_process() -> List[models.VCSISOProcess]:
    return implementation.get_all_iso_process()


# ======================================================================================================================
# VCS Subprocesses
# ======================================================================================================================


@router.get(
    '/project/{native_project_id}/vcs/{vcs_id}/subprocess/all',
    summary='Returns all subprocesses of a project',
    response_model=List[models.VCSSubprocess],
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))]
)
async def get_all_subprocess(native_project_id: int, vcs_id: int) -> List[models.VCSSubprocess]:
    return implementation.get_all_subprocess(native_project_id, vcs_id)


@router.get(
    '/project/{native_project_id}/subprocess/{subprocess_id}',
    summary='Returns a subprocess',
    response_model=models.VCSSubprocess,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))]
)
async def get_subprocess(native_project_id: int, subprocess_id: int) -> models.VCSSubprocess:
    return implementation.get_subprocess(native_project_id, subprocess_id)


@router.post(
    '/project/{native_project_id}/vcs/{vcs_id}/subprocess',
    summary='Creates a new subprocess',
    response_model=models.VCSSubprocess,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_edit(), CVS_APP_SID))]
)
async def create_subprocess(native_project_id: int, vcs_id: int,
                            subprocess_post: models.VCSSubprocessPost) -> models.VCSSubprocess:
    return implementation.create_subprocess(native_project_id, vcs_id, subprocess_post)


@router.put(
    '/project/{native_project_id}/subprocess/{subprocess_id}',
    summary='Edits a subprocess',
    response_model=bool,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_edit(), CVS_APP_SID))]
)
async def edit_subprocess(native_project_id: int, subprocess_id: int,
                          subprocess: models.VCSSubprocessPut) -> bool:
    return implementation.edit_subprocess(native_project_id, subprocess_id, subprocess)


@router.delete(
    '/project/{native_project_id}/subprocess/{subprocess_id}',
    summary='Deletes a subprocess',
    response_model=bool,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_edit(), CVS_APP_SID))]
)
async def delete_subprocess(native_project_id: int, subprocess_id: int) -> bool:
    return implementation.delete_subprocess(native_project_id, subprocess_id)


# ======================================================================================================================
# VCS Duplicate
# ======================================================================================================================

@router.post(
    '/project/{native_project_id}/vcs/{vcs_id}/duplicate/{n}',
    summary='Duplicate VCS n times',
    response_model=List[models.VCS],
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_edit(), CVS_APP_SID))]
)
async def duplicate_vcs(native_project_id: int, vcs_id: int, n: int) -> List[models.VCS]:
    return implementation.duplicate_vcs(native_project_id, vcs_id, n)
