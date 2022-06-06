from typing import List

from fastapi import HTTPException
from starlette import status

import sedbackend.apps.cvs.vcs.exceptions as vcs_exceptions
import sedbackend.apps.cvs.project.exceptions as project_exceptions
from sedbackend.apps.core.authentication import exceptions as auth_ex
from sedbackend.apps.core.db import get_connection
from sedbackend.libs.datastructures.pagination import ListChunk
from sedbackend.apps.cvs.design import models, storage, exceptions


# ======================================================================================================================
# CVS Design
# ======================================================================================================================


def create_cvs_design(design_post: models.DesignPost, vcs_id: int, project_id: int, user_id: int) -> models.Design:
    try:
        with get_connection() as con:
            result = storage.create_design(con, design_post, vcs_id, project_id, user_id)
            con.commit()
            return result
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}.',
        )
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


def get_all_design(project_id: int, vcs_id: int, user_id: int) -> ListChunk[models.Design]:
    try:
        with get_connection() as con:
            return storage.get_all_designs(con, project_id, vcs_id, user_id)
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}.',
        )
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


def get_design(design_id: int, vcs_id: int, project_id: int, user_id: int) -> models.Design:
    try:
        with get_connection() as con:
            result = storage.get_design(con, design_id, project_id, vcs_id, user_id)
            con.commit()
            return result
    except project_exceptions.CVSProjectFailedDeletionException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}.',
        )
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}.',
        )
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
    except exceptions.DesignNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find design with id={design_id}.',
        )


def delete_design(design_id: int, vcs_id: int, project_id: int, user_id: int) -> bool:
    try:
        with get_connection() as con:
            res = storage.delete_design(con, design_id, project_id, vcs_id, user_id)
            con.commit()
            return res
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}'
        )
    except exceptions.DesignNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find design with id={design_id}.',
        )
    except vcs_exceptions.VCSNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find vcs with id={vcs_id}.',
        )


def edit_design(design_id: int, project_id: int, vcs_id: int, user_id: int,
                updated_design: models.DesignPost) -> models.Design:
    try:
        with get_connection() as con:
            result = storage.edit_design(con, design_id, project_id, vcs_id, user_id, updated_design)
            con.commit()
            return result
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}'
        )
    except exceptions.DesignNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find design with id={design_id}.',
        )
    except vcs_exceptions.VCSNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find vcs with id={vcs_id}.',
        )


# ======================================================================================================================
# Quantified Objectives
# ======================================================================================================================


def get_all_quantified_objectives(design_id: int, project_id: int, vcs_id: int,
                                  user_id: int) -> List[models.QuantifiedObjective]:
    try:
        with get_connection() as con:
            res = storage.get_all_quantified_objectives(con, design_id, project_id, vcs_id, user_id)
            con.commit()
            return res
    except exceptions.QuantifiedObjectiveNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find quantified objective'
        )
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}'
        )
    except exceptions.DesignNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find design with id={design_id}.',
        )
    except vcs_exceptions.VCSNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find vcs with id={vcs_id}.',
        )


def get_quantified_objective(quantified_objective_id: int, design_id: int, value_driver_id: int,
                             project_id: int, vcs_id: int, user_id: int) -> models.QuantifiedObjective:
    try:
        with get_connection() as con:
            res = storage.get_quantified_objective(con, quantified_objective_id, design_id, value_driver_id, project_id,
                                                   vcs_id, user_id)
            con.commit()
            return res
    except exceptions.QuantifiedObjectiveNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find quantified objective with id={quantified_objective_id}'
        )
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}'
        )
    except exceptions.DesignNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find design with id={design_id}.',
        )
    except vcs_exceptions.VCSNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find vcs with id={vcs_id}.',
        )
    except vcs_exceptions.ValueDriverNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Could not find value driver with id={value_driver_id}.',
        )


def create_quantified_objective(design_id: int, value_driver_id: int,
                                quantified_objective_post: models.QuantifiedObjectivePost, project_id: int, vcs_id: int,
                                user_id: int) -> models.QuantifiedObjective:
    try:
        with get_connection() as con:
            res = storage.create_quantified_objective(con, design_id, value_driver_id, quantified_objective_post,
                                                      project_id, vcs_id, user_id)
            con.commit()
            return res
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}'
        )
    except vcs_exceptions.ValueDriverNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Could not find value driver with id={value_driver_id}.',
        )


def delete_quantified_objective(quantified_objective_id: int, value_driver_id: int, design_id: int, project_id: int,
                                vcs_id: int, user_id: int) -> bool:
    try:
        with get_connection() as con:
            res = storage.delete_quantified_objective(con, quantified_objective_id, value_driver_id, design_id,
                                                      project_id, vcs_id, user_id)
            con.commit()
            return res
    except auth_ex.UnauthorizedOperationException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized operation'
        )
    except exceptions.QuantifiedObjectiveNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Could not find quantified objective'
        )
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}'
        )
    except exceptions.DesignNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find design with id={design_id}.',
        )
    except vcs_exceptions.VCSNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find vcs with id={vcs_id}.',
        )
    except vcs_exceptions.ValueDriverNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Could not find value driver with id={value_driver_id}.',
        )


def edit_quantified_objective(quantified_objective_id: int, design_id: int, value_driver_id: int, project_id: int,
                              vcs_id: int, updated_qo: models.QuantifiedObjectivePost,
                              user_id: int) -> models.QuantifiedObjective:
    try:
        with get_connection() as con:
            res = storage.edit_quantified_objective(con, quantified_objective_id, design_id, value_driver_id,
                                                    updated_qo, user_id, project_id, vcs_id)
            con.commit()
            return res
    except exceptions.QuantifiedObjectiveNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find quantified objective with id={quantified_objective_id}'
        )
    except project_exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}'
        )
    except exceptions.DesignNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find design with id={design_id}.',
        )
    except vcs_exceptions.VCSNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find vcs with id={vcs_id}.',
        )
