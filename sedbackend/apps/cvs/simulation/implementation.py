from fastapi import HTTPException, UploadFile
from starlette import status
import tempfile

from typing import List, Optional

from sedbackend.apps.cvs.simulation import models, storage

from sedbackend.apps.core.authentication import exceptions as auth_ex
from sedbackend.apps.core.db import get_connection
from sedbackend.apps.cvs.project import exceptions as project_exceptions
from sedbackend.apps.cvs.simulation.exceptions import DSMFileNotFoundException, FormulaEvalException, NegativeTimeException, ProcessNotFoundException, RateWrongOrderException
from sedbackend.apps.cvs.vcs import exceptions as vcs_exceptions
from sedbackend.apps.cvs.market_input import exceptions as market_input_exceptions


def run_simulation(vcs_id: int, flow_time: float, flow_rate: float, 
                    flow_process_id: int, simulation_runtime: float, discount_rate: float, 
                    non_tech_add: models.NonTechCost, design_ids: List[int], 
                    normalized_npv: bool, user_id: int) -> List[models.Simulation]:
    try:
        with get_connection() as con:
            result = storage.run_simulation(con, vcs_id, flow_time, flow_rate, flow_process_id, 
                                simulation_runtime, discount_rate, non_tech_add, design_ids, normalized_npv, user_id)
            return result
    except auth_ex.UnauthorizedOperationException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Unauthorized user.',
        )
    except vcs_exceptions.VCSNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find vcs with id={vcs_id}.',
        )
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project.',
        )
    except market_input_exceptions.MarketInputNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find market input',
        )
    except ProcessNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find process',
        )
    except FormulaEvalException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Could not evaluate formulas of process with id: {e.process_id}'
        )
    except RateWrongOrderException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Wrong order of rate of entities. Per project assigned after per product'
        )
    except NegativeTimeException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Formula at process with id: {e.process_id} evaluated to negative time'
        )


def run_csv_simulation(vcs_id: int, flow_time: float, flow_rate: float, 
                        flow_process_id: int, simulation_runtime: float, discount_rate: float, 
                        non_tech_add: models.NonTechCost, dsm_csv: UploadFile, design_ids: List[int], 
                        normalized_npv: bool, user_id: int) -> List[models.Simulation]:
    try: 
        with get_connection() as con:
            res = storage.run_sim_with_csv_dsm(con, vcs_id, flow_time, flow_rate, flow_process_id, 
                                simulation_runtime, discount_rate, non_tech_add, dsm_csv, design_ids, 
                                normalized_npv, user_id)
            return res
    except auth_ex.UnauthorizedOperationException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Unauthorized user.',
        )
    except vcs_exceptions.VCSNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find vcs with id={vcs_id}.',
        )
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project.',
        )
    except market_input_exceptions.MarketInputNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find market input',
        )
    except ProcessNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find process',
        )
    except DSMFileNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not read uploaded file'
        )
    except FormulaEvalException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Could not evaluate formulas of process with id: {e.process_id}'
        )
    except RateWrongOrderException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Wrong order of rate of entities. Per project assigned after per product'
        )
    except NegativeTimeException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Formula at process with id: {e.process_id} evaluated to negative time'
        )

def run_xlsx_simulation(vcs_id: int, flow_time: float, flow_rate: float, flow_process_id: int, 
                        simulation_runtime: float, discount_rate: float, non_tech_add: models.NonTechCost, 
                        dsm_xlsx: UploadFile, design_ids: List[int], normalized_npv: bool, 
                        user_id: int) -> List[models.Simulation]:
    try: 
        with get_connection() as con:
            res = storage.run_sim_with_xlsx_dsm(con, vcs_id, flow_time, flow_rate, flow_process_id, 
                            simulation_runtime, discount_rate, non_tech_add, dsm_xlsx, design_ids, normalized_npv, user_id)
            return res
    except auth_ex.UnauthorizedOperationException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Unauthorized user.',
        )
    except vcs_exceptions.VCSNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find vcs with id={vcs_id}.',
        )
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project.',
        )
    except market_input_exceptions.MarketInputNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find market input',
        )
    except ProcessNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find process',
        )
    except DSMFileNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not read uploaded file'
        )
    except FormulaEvalException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Could not evaluate formulas of process with id: {e.process_id}'
        )
    except RateWrongOrderException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Wrong order of rate of entities. Per project assigned after per product'
        )
    except NegativeTimeException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Formula at process with id: {e.process_id} evaluated to negative time'
        )

def run_sim_monte_carlo(vcs_id: int, flow_time: float, flow_rate: float, 
                    flow_process_id: int, simulation_runtime: float, discount_rate: float, 
                    non_tech_add: models.NonTechCost, design_ids: List[int], 
                    runs: int, normalized_npv: bool, 
                    user_id: int = None) -> List[models.SimulationMonteCarlo]:
    try: 
        with get_connection() as con:
            result = storage.run_sim_monte_carlo(con, vcs_id, flow_time, flow_rate, flow_process_id, 
                                simulation_runtime, discount_rate, non_tech_add, design_ids, runs, 
                                normalized_npv, user_id)
            return result
    except vcs_exceptions.GenericDatabaseException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Fel'
        )
    except FormulaEvalException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Could not evaluate formulas of process with id: {e.process_id}'
        )
    except RateWrongOrderException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Wrong order of rate of entities. Per project assigned after per product'
        )
    except NegativeTimeException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Formula at process with id: {e.process_id} evaluated to negative time'
        )
