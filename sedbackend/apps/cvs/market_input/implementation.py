from typing import List

from fastapi import HTTPException
from starlette import status

from sedbackend.apps.core.authentication import exceptions as auth_ex
from sedbackend.apps.core.db import get_connection
from sedbackend.apps.cvs.project import exceptions as proj_exceptions
from sedbackend.apps.cvs.market_input import models, storage, exceptions
from sedbackend.apps.cvs.vcs import exceptions as vcs_exceptions

########################################################################################################################
# Market Inputs
########################################################################################################################


def get_all_market_inputs(project_id: int) -> List[models.MarketInputGet]:
    try:
        with get_connection() as con:
            db_result = storage.get_all_market_input(con, project_id)
            con.commit()
            return db_result
    except auth_ex.UnauthorizedOperationException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Unauthorized user.',
        )
    except proj_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}.',
        )
    except exceptions.MarketInputNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find market input',
        )


def get_market_input(project_id: int, market_input_id: int) -> models.MarketInputGet:
    try:
        with get_connection() as con:
            db_result = storage.get_market_input(con, project_id, market_input_id)
            con.commit()
            return db_result
    except auth_ex.UnauthorizedOperationException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Unauthorized user.',
        )
    except proj_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}.',
        )
    except exceptions.MarketInputNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find market input',
        )


def create_market_input(project_id: int, market_input: models.MarketInputPost) -> models.MarketInputGet:
    try:
        with get_connection() as con:
            db_result = storage.create_market_input(con, project_id, market_input)
            con.commit()
            return db_result
    except auth_ex.UnauthorizedOperationException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Unauthorized user.',
        )


def update_market_input(project_id: int, market_input_id: int, market_input: models.MarketInputPost) -> bool:
    try:
        with get_connection() as con:
            db_result = storage.update_market_input(con, project_id, market_input_id, market_input)
            con.commit()
            return db_result
    except auth_ex.UnauthorizedOperationException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Unauthorized user.',
        )
    except exceptions.MarketInputNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find market input with id={market_input_id}',
        )
    except proj_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}.',
        )
    except proj_exceptions.CVSProjectNoMatchException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Market input with id={market_input_id} is not a part from project with id={project_id}.',
        )


def delete_market_input(project_id: int, mi_id: int) -> bool:
    try:
        with get_connection() as con:
            res = storage.delete_market_input(con, project_id, mi_id)
            con.commit()
            return res
    except exceptions.MarketInputFailedDeletionException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not delete market input with id: {mi_id}'
        )
    except proj_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}.',
        )
    except proj_exceptions.CVSProjectNoMatchException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Market input with id={mi_id} is not a part from project with id={project_id}.',
        )


def get_all_formula_market_inputs(formulas_id: int) -> List[models.MarketInputGet]:
    try:
        with get_connection() as con:
            res = storage.get_all_formula_market_inputs(con, formulas_id)
            con.commit()
            return res
    except exceptions.MarketInputAlreadyExistException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find market inputs for formula with vcs_row id: {formulas_id}'
        )


########################################################################################################################
# Market Values
########################################################################################################################


def update_market_input_value(project_id: int, mi_value: models.MarketInputValue) -> bool:
    try:
        with get_connection() as con:
            res = storage.update_market_input_value(con, project_id, mi_value)
            con.commit()
            return res
    except exceptions.MarketInputNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find market input with id={mi_value.market_input_id}.',
        )
    except vcs_exceptions.VCSNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find vcs with id={mi_value.vcs_id}.',
        )
    except proj_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}.',
        )
    except proj_exceptions.CVSProjectNoMatchException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Market input with id={mi_value.market_input_id} is not a part from project with id={project_id}.',
        )


def update_market_input_values(project_id: int, mi_values: List[models.MarketInputValue]) -> bool:
    try:
        with get_connection() as con:
            res = storage.update_market_input_values(con, project_id, mi_values)
            con.commit()
            return res
    except exceptions.MarketInputNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Could not find market input',
        )
    except vcs_exceptions.VCSNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Could not find vcs',
        )
    except proj_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Could not find project with id={project_id}.',
        )


def get_all_market_values(project_id: int) -> List[models.MarketInputValue]:
    try:
        with get_connection() as con:
            res = storage.get_all_market_input_values(con, project_id)
            con.commit()
            return res
    except proj_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Could not find project with id={project_id}.',
        )


def delete_market_value(project_id: int, vcs_id: int, mi_id: int) -> bool:
    try:
        with get_connection() as con:
            res = storage.delete_market_value(con, project_id, vcs_id, mi_id)
            con.commit()
            return res
    except exceptions.MarketInputFailedDeletionException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Could not delete market input value with market input id: {mi_id} and vcs id: {vcs_id}'
        )
    except proj_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Could not find project with id={project_id}.',
        )
    except proj_exceptions.CVSProjectNoMatchException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Market input with id={mi_id} is not a part from project with id={project_id}.',
        )
