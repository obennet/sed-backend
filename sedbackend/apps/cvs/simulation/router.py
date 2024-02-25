from fastapi import Depends, APIRouter
from typing import List, Optional
from sedbackend.apps.core.authentication.utils import get_current_active_user
from sedbackend.apps.core.projects.dependencies import SubProjectAccessChecker
from sedbackend.apps.core.projects.models import AccessLevel
from sedbackend.apps.cvs.project.router import CVS_APP_SID
from sedbackend.apps.core.users.models import User
from sedbackend.apps.cvs.simulation import implementation, models
from sedbackend.apps.cvs.simulation.models import SimulationResult


router = APIRouter()


@router.post(
    '/project/{native_project_id}/simulation/run',
    summary='Run simulation',
    response_model=models.SimulationFetch,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))]
)
async def run_simulation(sim_settings: models.EditSimSettings, native_project_id: int, vcs_ids: List[int],
                         design_group_ids: List[int], normalized_npv: Optional[bool] = False,
                         user: User = Depends(get_current_active_user)) -> models.SimulationFetch:
    return implementation.run_simulation(sim_settings, native_project_id, vcs_ids, design_group_ids, user.id,
                                         normalized_npv)


# Temporary disabled
''' 
@router.post(
    '/project/{native_project_id}/sim/upload-dsm',
    summary='Run simulation with DSM predefined in Excel or CSV file',
    response_model=List[models.Simulation],
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))]
)
async def run_dsm_file_simulation(native_project_id: int, sim_params: models.FileParams = Depends(),
                                  dsm_file: UploadFile = File(default=None),
                                  user: User = Depends(get_current_active_user)) -> List[models.Simulation]:
    if dsm_file.content_type != 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and \
            dsm_file.content_type != 'text/csv':
        print("Content-type: ", dsm_file.content_type)
        raise HTTPException(400, detail="Invalid file type")
    return implementation.run_dsm_file_simulation(user.id, native_project_id, sim_params, dsm_file)
'''


@router.post(
    '/project/{native_project_id}/simulation/run-multiprocessing',
    summary='Run monte carlo simulation with multiprocessing',
    response_model=models.SimulationFetch,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))]
)
async def run_multiprocessing(sim_settings: models.EditSimSettings, native_project_id: int, vcs_ids: List[int],
                              design_group_ids: List[int], normalized_npv: Optional[bool] = False,
                              user: User = Depends(get_current_active_user)) -> models.SimulationFetch:
    return implementation.run_simulation(sim_settings, native_project_id, vcs_ids, design_group_ids, user.id,
                                         normalized_npv, True)


@router.get(
    '/project/{native_project_id}/simulation/settings',
    summary='Get settings for project',
    response_model=models.SimSettings,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))]
)
async def get_sim_settings(native_project_id: int) -> models.SimSettings:
    return implementation.get_sim_settings(native_project_id)


@router.get(
    '/project/{native_project_id}/simulation/all',
    summary='Get simulations for project',
    response_model=List[models.SimulationFetch],
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))]
)
async def get_simulations(native_project_id: int) -> List[models.SimulationFetch]:
    return implementation.get_simulations(native_project_id)


@router.delete(
    '/project/{native_project_id}/simulation/all',
    summary='Remove all simulation files',
    response_model= bool,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))]
)
async def remove_simulation_files(native_project_id: int, user: User = Depends(get_current_active_user)) -> bool:
    return implementation.remove_simulation_files(native_project_id, user.id)

@router.put(
    '/project/{native_project_id}/simulation/settings',
    summary='Create or update simulation settings',
    response_model=bool,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_edit(), CVS_APP_SID))]
)
async def put_sim_settings(native_project_id: int, sim_settings: models.EditSimSettings,
                           user: User = Depends(get_current_active_user)) -> bool:
    return implementation.edit_sim_settings(native_project_id, sim_settings, user.id)


@router.get(
   '/project/{native_project_id}/simulation/file/{file_id}',
    summary='Get simulation file',
    response_model=models.SimulationResult,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))]
)
async def get_simulation_file_content(native_project_id,file_id: int, user: User = Depends(get_current_active_user)) -> models.SimulationResult:
    return implementation.get_simulation_file_content(user.id, file_id)

@router.delete(
   '/project/{native_project_id}/simulation/file/{file_id}',
    summary='Remove simulation file',
    response_model=bool,
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))]
)
async def get_simulation_file_content(native_project_id,file_id: int, user: User = Depends(get_current_active_user)) -> bool:
    return implementation.remove_simulation_file(native_project_id, user.id, file_id)

@router.get(
   '/project/{native_project_id}/simulation/surrogate',
    summary='Get surrogate model for simulation',
    dependencies=[Depends(SubProjectAccessChecker(AccessLevel.list_can_read(), CVS_APP_SID))]
)
async def get_surrogate_model(file_id: int, user: User = Depends(get_current_active_user)):
    return implementation.get_surrogate_model(user.id, file_id)