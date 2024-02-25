from fastapi import HTTPException, UploadFile
from starlette import status

from typing import List

from fastapi.logger import logger
from sedbackend.apps.cvs.simulation import models, storage

from sedbackend.apps.core.authentication import exceptions as auth_ex
from sedbackend.apps.core.db import get_connection
from sedbackend.apps.cvs.project import exceptions as project_exceptions
from sedbackend.apps.cvs.simulation.exceptions import (
    BadlyFormattedSettingsException,
    DSMFileNotFoundException,
    DesignIdsNotFoundException,
    FormulaEvalException,
    NegativeTimeException,
    ProcessNotFoundException,
    RateWrongOrderException,
    InvalidFlowSettingsException,
    SimulationFailedException,
    VcsFailedException,
    FlowProcessNotFoundException,
    SimSettingsNotFoundException,
    CouldNotFetchSimulationDataException,
    CouldNotFetchMarketInputValuesException,
    CouldNotFetchValueDriverDesignValuesException,
    NoTechnicalProcessException,
)
from sedbackend.apps.cvs.simulation.models import SimulationResult,SimulationFetch

from sedbackend.apps.cvs.vcs import exceptions as vcs_exceptions
from sedbackend.apps.cvs.market_input import exceptions as market_input_exceptions
from sedbackend.apps.core.files import exceptions as file_ex


def run_simulation(
    sim_settings: models.EditSimSettings,
    project_id: int,
    vcs_ids: List[int],
    design_group_ids: List[int],
    user_id: int,
    normalized_npv: bool = False,
    is_multiprocessing: bool = False,
) -> models.SimulationFetch:
    try:
        with get_connection() as con:
            result = storage.run_simulation(
                con,
                sim_settings,
                project_id,
                vcs_ids,
                design_group_ids,
                user_id,
                normalized_npv,
                is_multiprocessing,
            )
            con.commit()
            return result
    except auth_ex.UnauthorizedOperationException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized user.",
        )
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find project.",
        )
    except market_input_exceptions.ExternalFactorNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find market input",
        )
    except ProcessNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find process",
        )
    except FormulaEvalException as e:
        # TODO: Add vcs name and design group name. Have to update get_all_sim_data
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to evaluate formulas of process {e.name}. {e.message.capitalize()}.",
        )
    except RateWrongOrderException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Wrong order of rate of entities. Total sum cannot come after per product. Check your VCS table.",
        )
    except NegativeTimeException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Negative time for process {e.name}. Check your formulas.",
        )
    except DesignIdsNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No designs in chosen design group",
        )
    except VcsFailedException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid vcs ids"
        )
    except BadlyFormattedSettingsException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Settings are not correct: \n {e.message}",
        )
    except CouldNotFetchSimulationDataException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not fetch simulation data. Check your VCSs and Design Groups.",
        )
    except CouldNotFetchMarketInputValuesException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not fetch market input values",
        )
    except CouldNotFetchValueDriverDesignValuesException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not fetch value driver design values",
        )
    except NoTechnicalProcessException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No technical processes found",
        )
    except file_ex.FileNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Could not find DSM file"
        )
    except SimulationFailedException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message.capitalize()
        )


def run_dsm_file_simulation(
    user_id: int, project_id: int, sim_params: models.FileParams, dsm_file: UploadFile
) -> List[models.Simulation]:
    try:
        with get_connection() as con:
            res = storage.run_sim_with_dsm_file(
                con, user_id, project_id, sim_params, dsm_file
            )  # Wtf saknar xlsx file
            return res
    except auth_ex.UnauthorizedOperationException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized user.",
        )
    except vcs_exceptions.VCSNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not find vcs with id=.",
        )
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not find project.",
        )
    except market_input_exceptions.ExternalFactorNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not find market input",
        )
    except ProcessNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not find process",
        )
    except DSMFileNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file",
        )
    except FormulaEvalException as e:
        # TODO: Add vcs name and design group name. Have to update get_all_sim_data
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to evaluate formulas of process {e.name}. {e.message.capitalize()}.",
        )
    except RateWrongOrderException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Wrong order of rate of entities. Total sum cannot come after per product. Check your VCS table.",
        )
    except NegativeTimeException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formula at process with id: {e.process_id} evaluated to negative time",
        )
    except DesignIdsNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No designs in chosen design group",
        )


def get_sim_settings(project_id: int) -> models.SimSettings:
    try:
        with get_connection() as con:
            result = storage.get_simulation_settings(con, project_id)
            con.commit()
            return result
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Could not find project"
        )
    except SimSettingsNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find simulation settings",
        )
    except Exception as e:
        logger.debug(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not send simulation settings",
        )
        
def get_simulations(project_id: int) -> List[models.SimulationFetch]:
    try:
        with get_connection() as con:
            result = storage.get_simulation_files(con, project_id)
            con.commit()
            return result
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Could not find project"
        )
        
        
def remove_simulation_files(project_id: int, user_id: int) -> bool:
    try:
        with get_connection() as con:
            result = storage.delete_all_simulation_files(con, project_id, user_id)
            con.commit()
            return result
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Could not find project"
        )
    except Exception as e:
        logger.debug(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not send simulations",
        )
        
        
        
def get_simulation_file_content(user_id: int, file_id) -> SimulationResult:
    try:
        with get_connection() as con:
            result = storage.get_file_content(con, user_id, file_id)
            if result is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not find simulation file",
                )
            logger.debug('Successfully retrieved simulation file content')
            con.commit()
            return result
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find project"
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve simulation file content",
        )
        
        
        
def remove_simulation_file(project_id: int, user_id, file_id) -> bool:
    try:
        with get_connection() as con:
            result = storage.delete_simulation_file(con, project_id, file_id,user_id)
            con.commit()
            return result
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Could not find project"
        )
    except Exception as e:
        logger.debug(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not send simulations",
        )



def edit_sim_settings(
    project_id: int, sim_settings: models.EditSimSettings, user_id: int
) -> bool:
    try:
        with get_connection() as con:
            res = storage.edit_simulation_settings(
                con, project_id, sim_settings, user_id
            )
            con.commit()
            return res
    except InvalidFlowSettingsException:
        logger.debug("Invalid flow settings")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Both flow process and flow start time supplied or neither supplied",
        )
    except FlowProcessNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The supplied flow process can not be found in any vcs",
        )
    except Exception as e:
        logger.debug(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not update simulation settings",
        )

def get_surrogate_model(user_id: int, file_id) -> models.Design:
    try:
        with get_connection() as con:
            result = storage.get_surrogate_model(con, user_id, file_id)
            con.commit()
            return result
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not get surrogate model for simulation",
        )