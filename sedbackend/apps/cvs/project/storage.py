from fastapi.logger import logger
from mysql.connector.pooling import PooledMySQLConnection

from sedbackend.apps.core.users.storage import db_get_user_safe_with_id
from sedbackend.apps.cvs.project import models as models, exceptions as exceptions
from sedbackend.libs.datastructures.pagination import ListChunk
from mysqlsb import MySQLStatementBuilder, Sort, FetchType
import sedbackend.apps.core.projects.models as proj_models
import sedbackend.apps.core.projects.storage as proj_storage
from sedbackend.apps.core.files import (
    models as file_models,
    storage as file_storage,
    exceptions as file_ex,
)
from sedbackend.apps.core.projects import storage as core_project_storage

CVS_APPLICATION_SID = "MOD.CVS"
CVS_PROJECT_TABLE = "cvs_projects"
CVS_PROJECT_COLUMNS = [
    "id",
    "name",
    "description",
    "currency",
    "owner_id",
    "datetime_created",
]

PROJECTS_SUBPROJECTS_TABLE = "projects_subprojects"
PROJECTS_SUBPROJECTS_COLUMNS = [
    "id",
    "name",
    "application_sid",
    "project_id",
    "native_project_id",
    "owner_id",
    "datetime_created",
]


def get_all_cvs_project(
    db_connection: PooledMySQLConnection, user_id: int
) -> ListChunk[models.CVSProject]:
    logger.debug(f"Fetching all CVS projects for user with id={user_id}.")

    # The issue is that cvs_project.id is not the same as

    query = f"SELECT DISTINCT p.*, COALESCE(pp.access_level, 4) AS my_access_right \
            FROM cvs_projects p \
            LEFT JOIN projects_subprojects ps ON p.id = ps.native_project_id \
            LEFT JOIN projects_participants pp ON ps.project_id = pp.project_id AND pp.user_id = %s \
            WHERE p.owner_id = %s OR ps.owner_id = %s OR pp.user_id = %s;"

    with db_connection.cursor(prepared=True, dictionary=True) as cursor:
        cursor.execute(query, [user_id, user_id, user_id, user_id])
        result = cursor.fetchall()

    cvs_project_list = []
    for res in result:
        subproject = proj_storage.db_get_subproject_native(
            db_connection, "MOD.CVS", res["id"]
        )
        project = None
        if subproject.project_id:
            project = proj_storage.db_get_project(db_connection, subproject.project_id)
        cvs_project_list.append(
            populate_cvs_project(db_connection, res, project, subproject)
        )

    return ListChunk[models.CVSProject](
        chunk=cvs_project_list, length_total=len(cvs_project_list)
    )


def get_cvs_project(
    db_connection: PooledMySQLConnection,
    project_id: int,
    user_id: int,
    project: proj_models.Project = None,
    subproject: proj_models.SubProject = None,
) -> models.CVSProject:
    logger.debug(f"Fetching CVS project with id={project_id} user={user_id}.")

    query = f"SELECT p.*, COALESCE(pp.access_level, 4) AS my_access_right \
            FROM cvs_projects p \
            LEFT JOIN projects_participants pp ON pp.project_id = %s AND pp.user_id = %s \
            WHERE p.id = %s;"

    with db_connection.cursor(prepared=True, dictionary=True) as cursor:
        cursor.execute(query, [project_id, user_id, project_id])
        result = cursor.fetchone()
    logger.debug(result)
    if result is None:
        raise exceptions.CVSProjectNotFoundException

    if not subproject:
        subproject = proj_storage.db_get_subproject_native(
            db_connection, "MOD.CVS", project_id
        )
    if not project and subproject and subproject.project_id:
        project = proj_storage.db_get_project(db_connection, subproject.project_id)

    return populate_cvs_project(db_connection, result, project, subproject)


def create_cvs_project(
    db_connection: PooledMySQLConnection,
    cvs_project: models.CVSProjectPost,
    user_id: int,
) -> models.CVSProject:
    logger.debug(f"Creating a CVS project for user with id={user_id}.")

    insert_statement = MySQLStatementBuilder(db_connection)
    insert_statement.insert(
        table=CVS_PROJECT_TABLE, columns=["name", "description", "currency", "owner_id"]
    ).set_values(
        [cvs_project.name, cvs_project.description, cvs_project.currency, user_id]
    ).execute(
        fetch_type=FetchType.FETCH_NONE
    )

    cvs_project_id = insert_statement.last_insert_id

    # Insert corresponding subproject row
    subproject_model = proj_models.SubProjectPost(
        name=cvs_project.name,
        application_sid=CVS_APPLICATION_SID,
        native_project_id=cvs_project_id,
    )
    project_model = proj_models.ProjectPost(
        name=cvs_project.name,
        participants=[user_id] + list(cvs_project.participants_access.keys()),
        participants_access={
            user_id: proj_models.AccessLevel.OWNER,
            **cvs_project.participants_access,
        },
    )
    project = proj_storage.db_post_project(db_connection, project_model, user_id)
    subproject = proj_storage.db_post_subproject(
        db_connection, subproject_model, user_id, project.id
    )

    return get_cvs_project(db_connection, cvs_project_id, user_id, project, subproject)


def upload_cvs_project_image(
    db_connection: PooledMySQLConnection, cvs_project_id: int, image: str, user_id: int
) -> models.CVSProject:
    logger.debug(f"Uploading image for CVS project with id={cvs_project_id}.")

    cvs_project = get_cvs_project(db_connection, cvs_project_id, user_id)

    fs = image.read()
    # if len(fs) > 5 * 1024 * 1024:
    #    raise file_ex.FileSizeException

    subproject = core_project_storage.db_get_subproject_native(
        db_connection, "MOD.CVS", cvs_project_id
    )
    model_file = file_models.StoredFilePost.import_fastapi_file(
        image, user_id, subproject.id
    )
    if model_file.extension not in [".png", ".jpg", ".jpeg", ".gif"]:
        raise exceptions.CVSProjectImageInvalidFormatException

    stored_file = file_storage.db_save_file(db_connection, model_file)

    insert_statement = MySQLStatementBuilder(db_connection)
    insert_statement.update(CVS_PROJECT_TABLE, "image_id = %s", [stored_file.id]).where(
        "id = %s", [cvs_project_id]
    ).execute(return_affected_rows=True)

    return get_cvs_project(db_connection, cvs_project_id, user_id)


def edit_cvs_project(
    db_connection: PooledMySQLConnection,
    cvs_project_id: int,
    new_project: models.CVSProjectPost,
    user_id: int,
) -> models.CVSProject:
    logger.debug(f"Editing CVS project with id={cvs_project_id}.")

    cvs_project = get_cvs_project(db_connection, cvs_project_id, user_id)

    # Updating
    update_statement = MySQLStatementBuilder(db_connection)
    update_statement.update(
        table=CVS_PROJECT_TABLE,
        set_statement="name = %s, description = %s, currency = %s",
        values=[new_project.name, new_project.description, new_project.currency],
    )
    update_statement.where("id = %s", [cvs_project_id])
    update_statement.execute(return_affected_rows=True)

    if cvs_project.project:
        old_participants = cvs_project.project.participants_access
        old_participants.pop(user_id)
        new_participants = new_project.participants_access
        participants_to_add = {}
        participants_to_remove = []
        participants_to_update = {}

        for user_id, access_level in new_participants.items():
            if user_id not in old_participants:
                participants_to_add[user_id] = access_level
            elif old_participants[user_id] != access_level:
                participants_to_update[user_id] = access_level

        for user_id, access_level in old_participants.items():
            if user_id not in new_participants:
                participants_to_remove.append(user_id)

        project = proj_storage.db_update_project(
            db_connection,
            proj_models.ProjectEdit(
                id=cvs_project.project.id,
                name=cvs_project.project.name,
                participants_to_add=participants_to_add,
                participants_to_remove=participants_to_remove,
                participants_to_update=participants_to_update,
            ),
        )

    return get_cvs_project(db_connection, cvs_project_id, user_id, project)


def delete_cvs_project(
    db_connection: PooledMySQLConnection, cvs_project_id: int, user_id: int
) -> bool:
    logger.debug(f"Deleting CVS project with id={cvs_project_id}.")
    cvs_project = get_cvs_project(db_connection, cvs_project_id, user_id)

    delete_statement = MySQLStatementBuilder(db_connection)
    _, rows = (
        delete_statement.delete(CVS_PROJECT_TABLE)
        .where("id = %s", [cvs_project_id])
        .execute(return_affected_rows=True)
    )

    if rows == 0:
        raise exceptions.CVSProjectFailedDeletionException

    if cvs_project.subproject:
        proj_storage.db_delete_subproject(
            db_connection,
            cvs_project.project.id if cvs_project.project else None,
            cvs_project.subproject.id,
        )
    if cvs_project.project:
        proj_storage.db_delete_project(db_connection, cvs_project.project.id)

    return True


def populate_cvs_project(
    db_connection: PooledMySQLConnection,
    db_result,
    project: proj_models.Project = None,
    subproject: proj_models.SubProject = None,
) -> models.CVSProject:
    logger.debug(f"Populating cvs project with {db_result}")
    return models.CVSProject(
        id=db_result["id"],
        name=db_result["name"],
        description=db_result["description"],
        currency=db_result["currency"],
        owner=db_get_user_safe_with_id(db_connection, db_result["owner_id"]),
        datetime_created=db_result["datetime_created"],
        my_access_right=db_result["my_access_right"],
        project=project,
        subproject=subproject,
        image=(
            file_storage.db_get_file_path(
                db_connection, db_result["image_id"], db_result["owner_id"]
            ).path
            if db_result["image_id"]
            else None
        ),
    )
