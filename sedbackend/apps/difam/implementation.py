from fastapi import HTTPException, status

import sedbackend.apps.core.individuals.exceptions as ind_ex
import sedbackend.apps.core.individuals.storage as ind_storage
import sedbackend.apps.core.authentication.exceptions as auth_ex
import sedbackend.apps.difam.exceptions as ex
import sedbackend.apps.difam.storage as storage
import sedbackend.apps.difam.models as models
import sedbackend.apps.difam.algorithms as algs
from sedbackend.apps.core.db import get_connection
from sedbackend.libs.datastructures.pagination import ListChunk


def impl_delete_project(difam_project_id: int, current_user_id: int):
    try:
        with get_connection() as con:
            res = storage.db_delete_project(con, difam_project_id, current_user_id)
            con.commit()
            return res
    except ex.DifamProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No such project"
        )
    except ex.DifamProjectDeleteException:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove the project"
        )
    except auth_ex.UnauthorizedOperationException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No."
        )


def impl_get_difam_projects(segment_length: int, index: int, current_user_id: int) -> ListChunk[models.DifamProject]:
    with get_connection() as con:
        return storage.db_get_difam_projects(con, segment_length, index, current_user_id)


def impl_post_difam_project(difam_project: models.DifamProjectPost, current_user_id: int) -> models.DifamProject:
    try:
        with get_connection() as con:
            res = storage.db_post_difam_project(con, difam_project, current_user_id)
            con.commit()
            return res
    except ind_ex.IndividualNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No such archetype with ID = {difam_project.individual_archetype_id}"
        )


def impl_get_difam_project(difam_project_id: int) -> models.DifamProject:
    try:
        with get_connection() as con:
            return storage.db_get_difam_project(con, difam_project_id)
    except ex.DifamProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No DIFAM project with ID = {difam_project_id} could be found."
        )


def impl_put_project_archetype(difam_project_id: int, individual_archetype_id: int) -> models.DifamProject:
    try:
        with get_connection() as con:
            res = storage.db_put_project_archetype(con, difam_project_id, individual_archetype_id)
            con.commit()
            return res
    except ex.DifamProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No DIFAM project with ID = {difam_project_id} could be found."
        )
    except ind_ex.IndividualNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No such archetype with ID = {individual_archetype_id}"
        )


def impl_post_generate_individuals(individual_archetype_id: int, doe_generation_request: models.DOEGenerationRequest,
                                   current_user_id: int):
    try:
        with get_connection() as con:
            if doe_generation_request.doe_type == 0:

                parameters_id_list = []
                for range_param in doe_generation_request.range_parameters:
                    parameters_id_list.append(range_param.parameter_id)

                parameters_dict = ind_storage.db_get_parameters(con, parameters_id_list)
                hypercube = algs.create_hypercube_doe(doe_generation_request, parameters_dict)
                res = storage.db_post_generate_individuals(con, individual_archetype_id, parameters_id_list, hypercube,
                                                           current_user_id)
            else:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED
                )

            con.commit()
            return res
    except ind_ex.IndividualNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No such archetype with ID = {individual_archetype_id}"
        )