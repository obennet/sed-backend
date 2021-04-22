from fastapi import HTTPException, status

from apps.core.projects.exceptions import ProjectNotFoundException
from apps.core.projects.storage import (db_get_projects, db_get_project, db_post_project, db_has_minimum_access)
from apps.core.db import get_connection
from apps.core.projects.models import Project, AccessLevel


def impl_get_projects(segment_length: int, index: int):
    try:
        with get_connection() as con:
            return db_get_projects(con, segment_length, index)
    except TypeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect argument type",
        )


def impl_get_project(project_id: int):
    try:
        with get_connection() as con:
            return db_get_project(con, project_id)
    except ProjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )


def impl_post_project(project: Project):
    with get_connection() as con:
        return db_post_project(con, project)


def impl_has_minimum_access(project_id: int, user_id, int, minimum_level: AccessLevel):
    """
    Check if a user has the necessary access level to perform an action in a project
    :param project_id:
    :param user_id:
    :param int:
    :param minimum_level:
    :return:
    """
    with get_connection() as con:
        return db_has_minimum_access(con, project_id, user_id, minimum_level)
