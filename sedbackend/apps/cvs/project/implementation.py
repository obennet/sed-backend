from fastapi import HTTPException
from fastapi.logger import logger
from starlette import status
from sedbackend.apps.core.authentication import exceptions as auth_ex
from sedbackend.apps.core.db import get_connection
from sedbackend.apps.cvs.project import models, exceptions, storage
from sedbackend.libs.datastructures.pagination import ListChunk
from sedbackend.apps.core.files import exceptions as file_ex


def get_all_cvs_project(user_id: int) -> ListChunk[models.CVSProject]:
    with get_connection() as con:
        return storage.get_all_cvs_project(con, user_id)


def get_cvs_project(project_id: int, user_id: int) -> models.CVSProject:
    try:
        with get_connection() as con:
            return storage.get_cvs_project(con, project_id, user_id)
    except exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Could not find project with id={project_id}.',
        )
    except auth_ex.UnauthorizedOperationException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Unauthorized user.',
        )


def create_cvs_project(project_post: models.CVSProjectPost, user_id: int) -> models.CVSProject:
    try:
        with get_connection() as con:
            logger.debug(f'In create_cvs_proj: {user_id}, {project_post}')
            result = storage.create_cvs_project(con, project_post, user_id)
            con.commit()
            return result
    except exceptions.CVSProjectImageInvalidFormatException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid image format. Only PNG, JPG, JPEG, and GIF are allowed.',
        )
    except file_ex.FileSizeException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Image size is too large. Maximum allowed size is 5MB.',
        )


def upload_cvs_project_image(project_id: int, image: str, user_id: int) -> models.CVSProject:
    try:
        with get_connection() as con:
            result = storage.upload_cvs_project_image(con, project_id, image, user_id)
            con.commit()
            return result
    except exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}.',
        )
    except exceptions.CVSProjectImageInvalidFormatException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid image format. Only PNG, JPG, JPEG, and GIF are allowed.',
        )
    except file_ex.FileSizeException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Image size is too large. Maximum allowed size is 5MB.',
        )
    except auth_ex.UnauthorizedOperationException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Unauthorized user.',
        )


def edit_cvs_project(project_id: int, project_post: models.CVSProjectPost, user_id) -> models.CVSProject:
    try:
        with get_connection() as con:
            result = storage.edit_cvs_project(con, project_id, project_post, user_id)
            con.commit()
            return result
    except exceptions.CVSProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Could not find project with id={project_id}.',
        )
    except exceptions.CVSProjectFailedToUpdateException:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to edit project with id={project_id}.',
        )
    except auth_ex.UnauthorizedOperationException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Unauthorized user.',
        )


def delete_cvs_project(project_id: int, user_id: int) -> bool:
    try:
        with get_connection() as con:
            res = storage.delete_cvs_project(con, project_id, user_id)
            con.commit()
            return res
    except exceptions.CVSProjectFailedDeletionException:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to remove project with id={project_id}.',
        )
    except exceptions.SubProjectFailedDeletionException:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to remove sub-project with CVS native_project_id={project_id}'
        )
    except auth_ex.UnauthorizedOperationException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Unauthorized user.',
        )
