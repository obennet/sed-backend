from multiprocessing import Pool
from unittest import result
from mysql.connector.pooling import PooledMySQLConnection
from fastapi.logger import logger
from typing import List

import sedbackend.apps.core.authentication.exceptions as auth_exceptions
from sedbackend.apps.core.users.storage import db_get_user_safe_with_id
import sedbackend.apps.cvs.implementation as impl
import sedbackend.apps.cvs.models as models
import sedbackend.apps.cvs.exceptions as cvs_exceptions

from sedbackend.libs.mysqlutils import MySQLStatementBuilder, FetchType, Sort
from sedbackend.libs.datastructures.pagination import ListChunk

CVS_APPLICATION_SID = 'MOD.CVS'

CVS_PROJECT_TABLE = 'cvs_projects'
CVS_PROJECT_COLUMNS = ['id', 'name', 'description', 'owner_id', 'datetime_created']

CVS_VCS_TABLE = 'cvs_vcss'
CVS_VCS_COLUMNS = ['id', 'name', 'description', 'project_id', 'datetime_created', 'year_from', 'year_to']

CVS_VCS_VALUE_DRIVER_TABLE = 'cvs_vcs_value_drivers'
CVS_VCS_VALUE_DRIVER_COLUMNS = ['id', 'name', 'unit', 'project_id']

CVS_VCS_SUBPROCESS_TABLE = 'cvs_vcs_subprocesses'
CVS_VCS_SUBPROCESS_COLUMNS = ['id', 'name', 'parent_process_id', 'project_id', 'order_index']

CVS_VCS_TABLE_ROWS_TABLE = 'cvs_vcs_table_rows'
CVS_VCS_TABLE_ROWS_COLUMNS = ['id', 'node_id', 'row_index', 'vcs_id', 'iso_process_id', 'subprocess_id', 'stakeholder',
                              'stakeholder_expectations']

CVS_VCS_STAKEHOLDER_NEED_TABLE = 'cvs_vcs_stakeholder_needs'
CVS_VCS_STAKEHOLDER_NEED_COLUMNS = ['id', 'table_row_id', 'need', 'rank_weight']

CVS_VCS_NEEDS_DRIVERS_MAP_TABLE = 'cvs_vcs_needs_divers_map'
CVS_VCS_NEEDS_DRIVERS_MAP_COLUMNS = ['id', 'stakeholder_need_id', 'value_driver_id']

DESIGNS_TABLE = 'designs'
DESIGNS_COLUMNS = ['id', 'project', 'vcs', 'name', 'description']

QUANTIFIED_OBJECTIVE_TABLE = 'quantified_objectives'
QUANTIFIED_OBJECTIVE_COLUMNS = ['id', 'design', 'value_driver', 'name', 'property', 'unit']

CVS_BPMN_NODES_TABLE = 'cvs_bpmn_nodes'
CVS_BPMN_NODES_COLUMNS = ['id', 'vcs_id', 'name', 'type', 'pos_x', 'pos_y']

CVS_BPMN_EDGES_TABLE = 'cvs_bpmn_edges'
CVS_BPMN_EDGES_COLUMNS = ['id', 'vcs_id', 'name', 'from_node', 'to_node', 'probability']

CVS_MARKET_INPUT_TABLE = 'cvs_market_input'
CVS_MARKET_INPUT_COLUMN = ['id', 'design', 'table_row', 'time', 'cost', 'revenue']

# ======================================================================================================================
# CVS projects
# ======================================================================================================================

def get_all_cvs_project(db_connection: PooledMySQLConnection, user_id: int) -> ListChunk[models.CVSProject]:
    logger.debug(f'Fetching all CVS projects for user with id={user_id}.')

    where_statement = f'owner_id = %s'
    where_values = [user_id]

    select_statement = MySQLStatementBuilder(db_connection)
    results = select_statement.select(CVS_PROJECT_TABLE, CVS_PROJECT_COLUMNS) \
        .where(where_statement, where_values) \
        .order_by(['id'], Sort.ASCENDING) \
        .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    project_list = []
    for result in results:
        project_list.append(populate_cvs_project(db_connection, result))

    count_statement = MySQLStatementBuilder(db_connection)
    result = count_statement.count(CVS_PROJECT_TABLE) \
        .where(where_statement, where_values) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)
    chunk = ListChunk[models.CVSProject](chunk=project_list, length_total=result['count'])

    return chunk


def get_segment_cvs_project(db_connection: PooledMySQLConnection, index: int, segment_length: int,
                            user_id: int) -> ListChunk[models.CVSProject]:
    logger.debug(f'Fetching segment of CVS projects for user with id={user_id}.')

    where_statement = f'owner_id = %s'
    where_values = [user_id]

    select_statement = MySQLStatementBuilder(db_connection)
    results = select_statement.select(CVS_PROJECT_TABLE, CVS_PROJECT_COLUMNS) \
        .where(where_statement, where_values) \
        .order_by(['name'], Sort.ASCENDING) \
        .limit(segment_length) \
        .offset(index * segment_length) \
        .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    project_list = []
    for result in results:
        project_list.append(populate_cvs_project(db_connection, result))

    count_statement = MySQLStatementBuilder(db_connection)
    result = count_statement.count(CVS_PROJECT_TABLE) \
        .where(where_statement, where_values) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)
    chunk = ListChunk[models.CVSProject](chunk=project_list, length_total=result['count'])

    return chunk


def get_cvs_project(db_connection: PooledMySQLConnection, project_id: int, user_id: int) -> models.CVSProject:
    logger.debug(f'Fetching CVS project with id={project_id}.')

    select_statement = MySQLStatementBuilder(db_connection)
    result = select_statement \
        .select(CVS_PROJECT_TABLE, CVS_PROJECT_COLUMNS) \
        .where('id = %s', [project_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    if result is None:
        raise cvs_exceptions.CVSProjectNotFoundException

    if result['owner_id'] != user_id:
        raise auth_exceptions.UnauthorizedOperationException

    return populate_cvs_project(db_connection, result)


def create_cvs_project(db_connection: PooledMySQLConnection, project: models.CVSProjectPost,
                       user_id: int) -> models.CVSProject:
    logger.debug(f'Creating a CVS project for user with id={user_id}.')

    insert_statement = MySQLStatementBuilder(db_connection)
    insert_statement \
        .insert(table=CVS_PROJECT_TABLE, columns=['name', 'description', 'owner_id']) \
        .set_values([project.name, project.description, user_id]) \
        .execute(fetch_type=FetchType.FETCH_NONE)

    project_id = insert_statement.last_insert_id

    return get_cvs_project(db_connection, project_id, user_id)


def edit_cvs_project(db_connection: PooledMySQLConnection, project_id: int, user_id: int,
                     new_project: models.CVSProjectPost) -> models.CVSProject:
    logger.debug(f'Editing CVS project with id={project_id}.')

    old_project = get_cvs_project(db_connection, project_id, user_id)

    if (old_project.name, old_project.description) == (new_project.name, new_project.description):
        # No change
        return old_project

    # Updating
    update_statement = MySQLStatementBuilder(db_connection)
    update_statement.update(
        table=CVS_PROJECT_TABLE,
        set_statement='name = %s, description = %s',
        values=[new_project.name, new_project.description],
    )
    update_statement.where('id = %s', [project_id])
    _, rows = update_statement.execute(return_affected_rows=True)

    if rows == 0:
        raise cvs_exceptions.CVSProjectFailedToUpdateException

    return get_cvs_project(db_connection, project_id, user_id)


def delete_cvs_project(db_connection: PooledMySQLConnection, project_id: int, user_id: int) -> bool:
    logger.debug(f'Deleting CVS project with id={project_id}.')

    select_statement = MySQLStatementBuilder(db_connection)
    result = select_statement \
        .select(CVS_PROJECT_TABLE, ['owner_id']) \
        .where('id = %s', [project_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    if result is None:
        raise cvs_exceptions.CVSProjectNotFoundException

    if result['owner_id'] != user_id:
        raise auth_exceptions.UnauthorizedOperationException

    delete_statement = MySQLStatementBuilder(db_connection)
    _, rows = delete_statement.delete(CVS_PROJECT_TABLE) \
        .where('id = %s', [project_id]) \
        .execute(return_affected_rows=True)

    if rows == 0:
        raise cvs_exceptions.CVSProjectFailedDeletionException

    return True


def populate_cvs_project(db_connection: PooledMySQLConnection, db_result) -> models.CVSProject:
    return models.CVSProject(
        id=db_result['id'],
        name=db_result['name'],
        description=db_result['description'],
        owner=db_get_user_safe_with_id(db_connection, db_result['owner_id']),
        datetime_created=db_result['datetime_created'],
    )


# ======================================================================================================================
# VCS (Value Creation Strategy)
# ======================================================================================================================

def get_all_vcs(db_connection: PooledMySQLConnection, project_id: int, user_id: int) -> ListChunk[models.VCS]:
    logger.debug(f'Fetching all VCSs for project with id={project_id}.')

    where_statement = f'project_id = %s'
    where_values = [project_id]

    select_statement = MySQLStatementBuilder(db_connection)
    results = select_statement.select(CVS_VCS_TABLE, CVS_VCS_COLUMNS) \
        .where(where_statement, where_values) \
        .order_by(['id'], Sort.ASCENDING) \
        .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    vcs_list = []
    for result in results:
        vcs_list.append(populate_vcs(db_connection, result, project_id, user_id))

    count_statement = MySQLStatementBuilder(db_connection)
    result = count_statement.count(CVS_VCS_TABLE) \
        .where(where_statement, where_values) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)
    chunk = ListChunk[models.VCS](chunk=vcs_list, length_total=result['count'])

    return chunk


def get_segment_vcs(db_connection: PooledMySQLConnection, project_id: int, segment_length: int, index: int,
                    user_id: int) -> ListChunk[models.VCS]:
    logger.debug(f'Fetching VCS segment for project with id={project_id}.')

    where_statement = f'project_id = %s'
    where_values = [project_id]

    select_statement = MySQLStatementBuilder(db_connection)
    results = select_statement.select(CVS_VCS_TABLE, CVS_VCS_COLUMNS) \
        .where(where_statement, where_values) \
        .order_by(['id'], Sort.ASCENDING) \
        .limit(segment_length) \
        .offset(index * segment_length) \
        .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    vcs_list = []
    for result in results:
        vcs_list.append(populate_vcs(db_connection, result, project_id, user_id))

    count_statement = MySQLStatementBuilder(db_connection)
    result = count_statement.count(CVS_VCS_TABLE) \
        .where(where_statement, where_values) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)
    chunk = ListChunk[models.VCS](chunk=vcs_list, length_total=result['count'])

    return chunk


def get_vcs(db_connection: PooledMySQLConnection, vcs_id: int, project_id: int, user_id: int) -> models.VCS:
    logger.debug(f'Fetching VCS with id={vcs_id}.')

    select_statement = MySQLStatementBuilder(db_connection)
    result = select_statement \
        .select(CVS_VCS_TABLE, CVS_VCS_COLUMNS) \
        .where('id = %s', [vcs_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    if result is None:
        raise cvs_exceptions.VCSNotFoundException

    if result['project_id'] != project_id:
        raise auth_exceptions.UnauthorizedOperationException

    return populate_vcs(db_connection, result, project_id, user_id)


def create_vcs(db_connection: PooledMySQLConnection, vcs_post: models.VCSPost, project_id: int,
               user_id: int) -> models.VCS:
    logger.debug(f'Creating a VCS in project with id={project_id}.')

    get_cvs_project(db_connection, project_id, user_id)  # performs checks for existing project and correct user

    insert_statement = MySQLStatementBuilder(db_connection)
    insert_statement \
        .insert(table=CVS_VCS_TABLE, columns=['name', 'description', 'project_id', 'year_from', 'year_to']) \
        .set_values([vcs_post.name, vcs_post.description, project_id, vcs_post.year_from, vcs_post.year_to]) \
        .execute(fetch_type=FetchType.FETCH_NONE)
    vcs_id = insert_statement.last_insert_id

    return get_vcs(db_connection, vcs_id, project_id, user_id)


def edit_vcs(db_connection: PooledMySQLConnection, vcs_id: int, project_id: int, user_id: int,
             new_vcs: models.VCSPost) -> models.VCS:
    logger.debug(f'Editing VCS with id={vcs_id}.')

    old_vcs = get_vcs(db_connection, vcs_id, project_id, user_id)

    o = (old_vcs.name, old_vcs.description, old_vcs.year_from, old_vcs.year_to)
    n = (new_vcs.name, new_vcs.description, new_vcs.year_from, new_vcs.year_to)
    if o == n:  # No change
        return old_vcs

    # Updating
    update_statement = MySQLStatementBuilder(db_connection)
    update_statement.update(
        table=CVS_VCS_TABLE,
        set_statement='name = %s, description = %s, year_from = %s, year_to = %s',
        values=[new_vcs.name, new_vcs.description, new_vcs.year_from, new_vcs.year_to],
    )
    update_statement.where('id = %s', [vcs_id])
    _, rows = update_statement.execute(return_affected_rows=True)

    if rows == 0:
        raise cvs_exceptions.VCSFailedToUpdateException

    return get_vcs(db_connection, vcs_id, project_id, user_id)


def delete_vcs(db_connection: PooledMySQLConnection, vcs_id: int, project_id: int, user_id: int) -> bool:
    logger.debug(f'Deleting VCS with id={vcs_id}.')

    select_statement = MySQLStatementBuilder(db_connection)

    result = select_statement \
        .select(CVS_VCS_TABLE, CVS_VCS_COLUMNS) \
        .where('id = %s', [vcs_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    if result is None:
        raise cvs_exceptions.VCSNotFoundException

    if result['project_id'] != project_id:
        raise auth_exceptions.UnauthorizedOperationException

    get_cvs_project(db_connection, project_id, user_id)  # performs checks for existing project and correct user

    delete_statement = MySQLStatementBuilder(db_connection)
    _, rows = delete_statement.delete(CVS_VCS_TABLE) \
        .where('id = %s', [vcs_id]) \
        .execute(return_affected_rows=True)

    if rows == 0:
        raise cvs_exceptions.VCSFailedDeletionException

    return True


def populate_vcs(db_connection: PooledMySQLConnection, db_result, project_id: int, user_id: int) -> models.VCS:
    return models.VCS(
        id=db_result['id'],
        name=db_result['name'],
        description=db_result['description'],
        project=get_cvs_project(db_connection, project_id=project_id, user_id=user_id),
        datetime_created=db_result['datetime_created'],
        year_from=db_result['year_from'],
        year_to=db_result['year_to'],
    )


# ======================================================================================================================
# VCS Value driver
# ======================================================================================================================

def get_all_value_driver(db_connection: PooledMySQLConnection, project_id: int,
                         user_id: int) -> ListChunk[models.VCSValueDriver]:
    logger.debug(f'Fetching all value drivers for project with id={project_id}.')

    where_statement = f'project_id = %s'
    where_values = [project_id]

    select_statement = MySQLStatementBuilder(db_connection)
    results = select_statement \
        .select(CVS_VCS_VALUE_DRIVER_TABLE, CVS_VCS_VALUE_DRIVER_COLUMNS) \
        .where(where_statement, where_values) \
        .order_by(['id'], Sort.ASCENDING) \
        .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    value_driver_list = []
    for result in results:
        value_driver_list.append(populate_value_driver(db_connection, result, project_id, user_id))

    count_statement = MySQLStatementBuilder(db_connection)
    result = count_statement \
        .count(CVS_VCS_VALUE_DRIVER_TABLE) \
        .where(where_statement, where_values) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)
    chunk = ListChunk[models.VCSValueDriver](chunk=value_driver_list, length_total=result['count'])

    return chunk


def get_value_driver(db_connection: PooledMySQLConnection, value_driver_id: int, project_id: int,
                     user_id: int) -> models.VCSValueDriver:

    logger.debug(f'Fetching value driver for project with id={value_driver_id}.')

    where_statement = f'id = %s'
    where_values = [value_driver_id]

    select_statement = MySQLStatementBuilder(db_connection)
    result = select_statement \
        .select(CVS_VCS_VALUE_DRIVER_TABLE, CVS_VCS_VALUE_DRIVER_COLUMNS) \
        .where(where_statement, where_values) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    value_driver = populate_value_driver(db_connection, result, project_id, user_id)

    if result is None:
        raise cvs_exceptions.ValueDriverNotFoundException(value_driver_id=value_driver_id)

    if result['project_id'] != project_id:
        raise auth_exceptions.UnauthorizedOperationException

    return value_driver


def create_value_driver(db_connection: PooledMySQLConnection, value_driver_post: models.VCSValueDriverPost,
                        project_id: int, user_id: int) -> models.VCSValueDriver:
    logger.debug(f'Creating a value driver in project with id={project_id}.')

    get_cvs_project(db_connection, project_id, user_id)  # performs checks for existing project and correct user

    insert_statement = MySQLStatementBuilder(db_connection)
    insert_statement \
        .insert(table=CVS_VCS_VALUE_DRIVER_TABLE, columns=['name', 'unit', 'project_id']) \
        .set_values([value_driver_post.name, value_driver_post.unit, project_id]) \
        .execute(fetch_type=FetchType.FETCH_NONE)
    value_driver_id = insert_statement.last_insert_id

    return get_value_driver(db_connection, value_driver_id, project_id, user_id)


def edit_value_driver(db_connection: PooledMySQLConnection, value_driver_id: int, project_id: int, user_id: int,
                      new_value_driver: models.VCSValueDriverPost) -> models.VCSValueDriver:
    logger.debug(f'Editing value driver with id={value_driver_id}.')

    old_value_driver = get_value_driver(db_connection, value_driver_id, project_id, user_id)
    if old_value_driver.name == new_value_driver.name:  # No change
        return old_value_driver

    # Updating
    update_statement = MySQLStatementBuilder(db_connection)
    update_statement.update(
        table=CVS_VCS_VALUE_DRIVER_TABLE,
        set_statement='name = %s, unit = %s',
        values=[new_value_driver.name, new_value_driver.unit],
    )
    update_statement.where('id = %s', [value_driver_id])
    _, rows = update_statement.execute(return_affected_rows=True)

    if rows == 0:
        raise cvs_exceptions.ValueDriverFailedToUpdateException

    return get_value_driver(db_connection, value_driver_id, project_id, user_id)


def delete_value_driver(db_connection: PooledMySQLConnection, value_driver_id: int, project_id: int,
                        user_id: int) -> bool:
    logger.debug(f'Deleting value driver with id={value_driver_id}.')

    get_cvs_project(db_connection, project_id, user_id)  # performs checks for existing project and correct user

    select_statement = MySQLStatementBuilder(db_connection)
    result = select_statement \
        .select(CVS_VCS_VALUE_DRIVER_TABLE, CVS_VCS_VALUE_DRIVER_COLUMNS) \
        .where('id = %s', [value_driver_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    if result is None:
        raise cvs_exceptions.ValueDriverNotFoundException(value_driver_id=value_driver_id)

    if result['project_id'] != project_id:
        raise auth_exceptions.UnauthorizedOperationException

    delete_statement = MySQLStatementBuilder(db_connection)
    _, rows = delete_statement.delete(CVS_VCS_VALUE_DRIVER_TABLE) \
        .where('id = %s', [value_driver_id]) \
        .execute(return_affected_rows=True)

    if rows == 0:
        raise cvs_exceptions.ValueDriverFailedDeletionException

    return True


def populate_value_driver(db_connection: PooledMySQLConnection, db_result, project_id: int,
                          user_id: int) -> models.VCSValueDriver:
    return models.VCSValueDriver(
        id=db_result['id'],
        name=db_result['name'],
        unit=db_result['unit'],
        project=get_cvs_project(db_connection, project_id=project_id, user_id=user_id),
    )


# ======================================================================================================================
# VCS ISO Processes
# ======================================================================================================================


def get_all_iso_process() -> ListChunk[models.VCSISOProcess]:
    logger.debug(f'Fetching all ISO processes.')

    iso_processes = [process.value for process in models.VCSISOProcesses]
    chunk = ListChunk[models.VCSISOProcess](chunk=iso_processes, length_total=len(iso_processes))

    return chunk


def get_iso_process(iso_process_id: int) -> models.VCSISOProcess:
    logger.debug(f'Fetching ISO process with id={iso_process_id}.')

    for p in models.VCSISOProcesses:
        if p.value.id == iso_process_id:
            return p.value

    raise cvs_exceptions.ISOProcessNotFoundException


# ======================================================================================================================
# VCS Subprocesses
# ======================================================================================================================

def get_all_subprocess(db_connection: PooledMySQLConnection, project_id: int,
                       user_id: int) -> ListChunk[models.VCSSubprocess]:
    logger.debug(f'Fetching all subprocesses for project with id={project_id}.')

    where_statement = f'project_id = %s'
    where_values = [project_id]

    select_statement = MySQLStatementBuilder(db_connection)
    results = select_statement \
        .select(CVS_VCS_SUBPROCESS_TABLE, CVS_VCS_SUBPROCESS_COLUMNS) \
        .where(where_statement, where_values) \
        .order_by(['id'], Sort.ASCENDING) \
        .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    subprocess_list = [populate_subprocess(db_connection, result, project_id, user_id) for result in results]

    count_statement = MySQLStatementBuilder(db_connection)
    result = count_statement \
        .count(CVS_VCS_SUBPROCESS_TABLE) \
        .where(where_statement, where_values) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)
    chunk = ListChunk[models.VCSSubprocess](chunk=subprocess_list, length_total=result['count'])

    return chunk


def get_subprocess(db_connection: PooledMySQLConnection, subprocess_id: int, project_id: int,
                   user_id: int) -> models.VCSSubprocess:
    logger.debug(f'Fetching subprocess with id={subprocess_id}.')

    select_statement = MySQLStatementBuilder(db_connection)
    result = select_statement \
        .select(CVS_VCS_SUBPROCESS_TABLE, CVS_VCS_SUBPROCESS_COLUMNS) \
        .where('id = %s', [subprocess_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    if result is None:
        raise cvs_exceptions.SubprocessNotFoundException(subprocess_id)

    if result['project_id'] != project_id:
        raise auth_exceptions.UnauthorizedOperationException

    return populate_subprocess(db_connection, result, project_id, user_id)


def create_subprocess(db_connection: PooledMySQLConnection, subprocess_post: models.VCSSubprocessPost,
                      project_id: int, user_id: int) -> models.VCSSubprocess:
    logger.debug(f'Creating a subprocesses in project with id={project_id}.')

    # performing necessary checks
    get_cvs_project(db_connection, project_id, user_id)
    get_iso_process(subprocess_post.parent_process_id)

    columns = ['name', 'parent_process_id', 'project_id', 'order_index']
    values = [subprocess_post.name, subprocess_post.parent_process_id, project_id, subprocess_post.order_index]

    insert_statement = MySQLStatementBuilder(db_connection)
    insert_statement \
        .insert(table=CVS_VCS_SUBPROCESS_TABLE, columns=columns) \
        .set_values(values) \
        .execute(fetch_type=FetchType.FETCH_NONE)
    subprocess_id = insert_statement.last_insert_id

    return get_subprocess(db_connection, subprocess_id, project_id, user_id)


def edit_subprocess(db_connection: PooledMySQLConnection, subprocess_id: int, project_id: int, user_id: int,
                    new_subprocess: models.VCSSubprocessPost) -> models.VCSSubprocess:
    logger.debug(f'Editing subprocesses with id={subprocess_id}.')

    old_subprocess = get_subprocess(db_connection, subprocess_id, project_id, user_id)
    o = (old_subprocess.name, old_subprocess.parent_process.id)
    n = (new_subprocess.name, new_subprocess.parent_process_id)
    if o == n:  # No change
        return old_subprocess

    # performing necessary checks
    get_cvs_project(db_connection, project_id, user_id)
    get_iso_process(new_subprocess.parent_process_id)

    # Updating
    update_statement = MySQLStatementBuilder(db_connection)
    update_statement.update(
        table=CVS_VCS_SUBPROCESS_TABLE,
        set_statement='name = %s, parent_process_id = %s',
        values=[new_subprocess.name, new_subprocess.parent_process_id],
    )
    update_statement.where('id = %s', [subprocess_id])
    _, rows = update_statement.execute(return_affected_rows=True)

    if rows == 0:
        raise cvs_exceptions.SubprocessFailedToUpdateException(subprocess_id)

    return get_subprocess(db_connection, subprocess_id, project_id, user_id)


def delete_subprocess(db_connection: PooledMySQLConnection, subprocess_id: int, project_id: int, user_id: int) -> bool:
    logger.debug(f'Deleting subprocesses with id={subprocess_id}.')

    get_cvs_project(db_connection, project_id, user_id)  # performing necessary checks

    select_statement = MySQLStatementBuilder(db_connection)
    result = select_statement \
        .select(CVS_VCS_SUBPROCESS_TABLE, CVS_VCS_SUBPROCESS_COLUMNS) \
        .where('id = %s', [subprocess_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    if result is None:
        raise cvs_exceptions.SubprocessNotFoundException(subprocess_id)

    if result['project_id'] != project_id:
        raise auth_exceptions.UnauthorizedOperationException

    delete_statement = MySQLStatementBuilder(db_connection)
    _, rows = delete_statement.delete(CVS_VCS_SUBPROCESS_TABLE) \
        .where('id = %s', [subprocess_id]) \
        .execute(return_affected_rows=True)

    if rows == 0:
        raise cvs_exceptions.SubprocessFailedDeletionException(subprocess_id)

    return True


def populate_subprocess(db_connection: PooledMySQLConnection, db_result, project_id: int,
                        user_id: int) -> models.VCSSubprocess:
    logger.debug(f'Populating model for subprocess with id={db_result["id"]}.')
    return models.VCSSubprocess(
        id=db_result['id'],
        name=db_result['name'],
        parent_process=get_iso_process(db_result['parent_process_id']),
        project=get_cvs_project(db_connection, project_id, user_id),
        order_index=db_result['order_index'],
    )


def update_subprocess_indices(db_connection: PooledMySQLConnection, subprocess_ids: List[int], order_indices: List[int],
                              project_id: int, user_id: int) -> bool:
    logger.debug(f'Updating indices for subprocesses with ids={subprocess_ids}.')

    # Performs necessary checks
    subprocesses = [get_subprocess(db_connection, _id, project_id, user_id) for _id in subprocess_ids]

    for subprocess, index in zip(subprocesses, order_indices):
        if index == subprocess.order_index:
            continue  # skipping since otherwise affected rows will be 0

        update_statement = MySQLStatementBuilder(db_connection)
        update_statement.update(
            table=CVS_VCS_SUBPROCESS_TABLE,
            set_statement='order_index = %s',
            values=[index],
        )
        update_statement.where('id = %s', [subprocess.id])
        _, rows = update_statement.execute(return_affected_rows=True)

        if rows == 0:
            raise cvs_exceptions.SubprocessFailedToUpdateException(subprocess_id=subprocess.id)

    return True


# ======================================================================================================================
# VCS Table
# ======================================================================================================================

def get_vcs_table(db_connection: PooledMySQLConnection, vcs_id: int, project_id: int, user_id: int) -> models.TableGet:
    logger.debug(f'Fetching all table for VCS with id={vcs_id}.')
    table_rows = get_all_table_rows(db_connection, vcs_id, project_id, user_id)
    return models.TableGet(table_rows=table_rows)


# DO NOT USE IN API CALLS
def get_vcs_table_row(db_connection: PooledMySQLConnection, node_id: int, project_id: int,
                      user_id: int) -> models.TableRowGet or None:
    logger.debug(f'Fetching vcs table row with id={node_id}.')

    select_statement = MySQLStatementBuilder(db_connection)
    result = select_statement \
        .select(CVS_VCS_TABLE_ROWS_TABLE, CVS_VCS_TABLE_ROWS_COLUMNS) \
        .where('node_id = %s', [node_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    if result is not None:
        return populate_table_row(db_connection, result, project_id, user_id)
    else:
        return None


def get_all_table_rows(db_connection: PooledMySQLConnection, vcs_id: int, project_id: int,
                       user_id: int) -> List[models.TableRowGet]:
    logger.debug(f'Fetching all table rows for VCS with id={vcs_id}')

    where_statement = f'vcs_id = %s'
    where_values = [vcs_id]

    select_statement = MySQLStatementBuilder(db_connection)
    results = select_statement \
        .select(CVS_VCS_TABLE_ROWS_TABLE, CVS_VCS_TABLE_ROWS_COLUMNS) \
        .where(where_statement, where_values) \
        .order_by(['id'], Sort.ASCENDING) \
        .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    return [populate_table_row(db_connection, result, project_id, user_id) for result in results]


def populate_table_row(db_connection: PooledMySQLConnection, db_result, project_id: int,
                       user_id: int) -> models.TableRowGet:
    logger.debug(f'Populating model for table row with id={db_result["id"]}.')

    iso_process, subprocesss = None, None
    if db_result['iso_process_id'] is not None:
        iso_process = get_iso_process(db_result['iso_process_id']) # Gets a iso process based on the id that we got from the DB result
    elif db_result['subprocess_id'] is not None:
        try:
            subprocesss = get_subprocess(db_connection, db_result['subprocess_id'], project_id, user_id) # Runs a new query on subprocess table based on the id that is in the result of the db query. Why is that not referenced as a foreign key and run as a single query here?????
        except cvs_exceptions.SubprocessNotFoundException:
            # If a subprocess is deleted but used in a table, the subprocess wont be found and thus this exception
            pass

    return models.TableRowGet(
        id=db_result['id'],
        node_id=db_result['node_id'],
        row_index=db_result['row_index'],
        iso_process=iso_process,
        subprocess=subprocesss,
        stakeholder=db_result['stakeholder'],
        stakeholder_expectations=db_result['stakeholder_expectations'],
        stakeholder_needs=get_stakeholder_needs(db_connection, db_result['id'], project_id, user_id),
    )


def get_stakeholder_needs(db_connection: PooledMySQLConnection, table_row_id: int, project_id: int,
                          user_id: int) -> List[models.StakeholderNeedGet]:
    logger.debug(f'Fetching all stakeholder needs for VCS table row with id={table_row_id}.')

    where_statement = f'table_row_id = %s'
    where_values = [table_row_id]

    results = MySQLStatementBuilder(db_connection) \
        .select(CVS_VCS_STAKEHOLDER_NEED_TABLE, CVS_VCS_STAKEHOLDER_NEED_COLUMNS) \
        .where(where_statement, where_values) \
        .order_by(['id'], Sort.ASCENDING) \
        .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    return [populate_stakeholder_need(db_connection, result, project_id, user_id) for result in results]


def populate_stakeholder_need(db_connection: PooledMySQLConnection, db_result, project_id: int,
                              user_id: int) -> models.StakeholderNeedGet:
    logger.debug(f'Populating model for stakeholder need with id={db_result["id"]}.')
    return models.StakeholderNeedGet(
        id=db_result['id'],
        need=db_result['need'],
        rank_weight=db_result['rank_weight'],
        value_drivers=get_drivers_from_needs(db_connection, db_result['id'], project_id, user_id),
    )


def get_drivers_from_needs(db_connection: PooledMySQLConnection, stakeholder_need_id: int, project_id: int,
                           user_id: int) -> List[models.ValueDriverGet]:
    logger.debug(f'Fetching all value drivers for stakeholder need with id={stakeholder_need_id}.')

    where_statement = f'stakeholder_need_id = %s'
    where_values = [stakeholder_need_id]

    results = MySQLStatementBuilder(db_connection) \
        .select(CVS_VCS_NEEDS_DRIVERS_MAP_TABLE, ['value_driver_id']) \
        .where(where_statement, where_values) \
        .order_by(['value_driver_id'], Sort.ASCENDING) \
        .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    value_drivers = []
    for result in results:
        value_driver = get_value_driver(db_connection, result['value_driver_id'], project_id, user_id)
        value_drivers.append(models.ValueDriverGet(id=value_driver.id, name=value_driver.name))

    return value_drivers


def create_vcs_table(db_connection: PooledMySQLConnection, new_table: models.TablePost, vcs_id: int, project_id: int,
                     user_id: int) -> bool:
    logger.debug(f'Creating table for VCS with id={vcs_id}.')

    # Getting ids of any existing rows
    results = MySQLStatementBuilder(db_connection) \
        .select(CVS_VCS_TABLE_ROWS_TABLE, ['id']) \
        .where(f'vcs_id = %s', [vcs_id]) \
        .order_by(['id'], Sort.ASCENDING) \
        .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    # Deleting any existing rows
    for result in results:
        delete_statement = MySQLStatementBuilder(db_connection)
        _, rows = delete_statement.delete(CVS_VCS_TABLE_ROWS_TABLE) \
            .where('id = %s', [result['id']]) \
            .execute(return_affected_rows=True)

        if rows == 0:
            raise cvs_exceptions.VCSTableRowFailedDeletionException(result['id'])

    # Creating new rows
    for i, table_row in enumerate(new_table.table_rows):

        # Checking processes
        if (table_row.iso_process_id is None) and (table_row.subprocess_id is None):
            # no process provided
            iso_process_id = None
            subprocess_id = None

        elif (table_row.iso_process_id is not None) and (table_row.subprocess_id is not None):
            # two processes provided
            raise cvs_exceptions.VCSTableProcessAmbiguity(table_row_id=i)

        elif table_row.iso_process_id is not None:
            # iso process provided
            
            iso_process = impl.get_iso_process(table_row.iso_process_id)
            iso_process_id = iso_process.id
            subprocess_id = None
            new_node = models.NodePost(
                    name = iso_process.name,
                    node_type = "process"
                )
            if(table_row.node_id is None):    
                node = create_bpmn_node(db_connection, new_node, project_id, vcs_id, user_id)
                table_row.node_id = node.id
            else: 
                update_bpmn_node(db_connection, table_row.node_id, new_node, project_id, vcs_id, user_id)
            
        else:
            # subprocess provided
            iso_process_id = None
            subprocess = impl.get_subprocess(table_row.subprocess_id, project_id, user_id)
            subprocess_id = subprocess.id
            new_node = models.NodePost(
                name = subprocess.name,
                node_type = "process"
            )
            if(table_row.node_id is None):   
                node = create_bpmn_node(db_connection, new_node, project_id, vcs_id, user_id)
                table_row.node_id = node.id
            else:
                update_bpmn_node(db_connection, table_row.node_id, new_node, project_id, vcs_id, user_id)
            

        # Further checking provided data
        stakeholder = table_row.stakeholder if table_row.stakeholder is not None else ''
        stakeholder_exp = table_row.stakeholder_expectations if table_row.stakeholder_expectations is not None else ''

        columns = ['node_id', 'vcs_id', 'row_index', 'iso_process_id', 'subprocess_id', 'stakeholder', 'stakeholder_expectations']
        values = [table_row.node_id, vcs_id, table_row.row_index, iso_process_id, subprocess_id, stakeholder, stakeholder_exp]

        insert_statement = MySQLStatementBuilder(db_connection)
        insert_statement \
            .insert(table=CVS_VCS_TABLE_ROWS_TABLE, columns=columns) \
            .set_values(values) \
            .execute(fetch_type=FetchType.FETCH_NONE)
        table_row_id = insert_statement.last_insert_id

        for stakeholder_need in table_row.stakeholder_needs:

            need = stakeholder_need.need if stakeholder_need is not None else ''
            rank_weight = stakeholder_need.rank_weight if stakeholder_need.rank_weight is not None else 0

            insert_statement = MySQLStatementBuilder(db_connection)
            insert_statement \
                .insert(table=CVS_VCS_STAKEHOLDER_NEED_TABLE, columns=['table_row_id', 'need', 'rank_weight']) \
                .set_values([table_row_id, need, rank_weight]) \
                .execute(fetch_type=FetchType.FETCH_NONE)
            stakeholder_need_id = insert_statement.last_insert_id

            for value_driver_id in stakeholder_need.value_driver_ids:
                get_value_driver(db_connection, value_driver_id, project_id, user_id)  # perfoms necessary controls

                insert_statement = MySQLStatementBuilder(db_connection)
                insert_statement \
                    .insert(table=CVS_VCS_NEEDS_DRIVERS_MAP_TABLE, columns=['stakeholder_need_id', 'value_driver_id']) \
                    .set_values([stakeholder_need_id, value_driver_id]) \
                    .execute(fetch_type=FetchType.FETCH_NONE)

    return True


# ======================================================================================================================
# CVS Design
# ======================================================================================================================

def create_design(db_connection: PooledMySQLConnection, design_post: models.DesignPost, vcs_id: int, project_id: int, user_id: int) -> models.Design:
    logger.debug(f'creating design with vcs_id={vcs_id} and project_id={project_id}')
    get_cvs_project(db_connection, project_id, user_id)

    insert_statement = MySQLStatementBuilder(db_connection)
    insert_statement \
        .insert(table=DESIGNS_TABLE, columns=['project', 'vcs', 'name', 'description']) \
        .set_values([project_id, vcs_id, design_post.name, design_post.description]) \
        .execute(fetch_type=FetchType.FETCH_NONE)
    design_id = insert_statement.last_insert_id

    table_rows = get_all_table_rows(db_connection, vcs_id, project_id, user_id)

    # Create market input for each table row

    for row in table_rows:
        market_input = models.MarketInputPost(
            time=0,
            cost=0,
            revenue=0
        )
        create_market_input(db_connection, design_id, row.id, market_input)

    return get_design(db_connection, design_id, project_id, vcs_id, user_id)

def get_design(db_connection: PooledMySQLConnection, design_id: int, project_id: int, vcs_id: int, user_id: int) -> models.Design:
    select_statement = MySQLStatementBuilder(db_connection)
    result = select_statement \
        .select(DESIGNS_TABLE, DESIGNS_COLUMNS)\
        .where('id = %s', [design_id])\
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)
    
    if result is None:
        raise cvs_exceptions.DesignNotFoundException

    if result['project'] != project_id:
        raise auth_exceptions.UnauthorizedOperationException

    return populate_design(db_connection, result, project_id, vcs_id, user_id)

def get_all_designs(db_connection: PooledMySQLConnection, project_id: int, vcs_id: int, user_id: int) -> ListChunk[models.Design]:
    logger.debug(f'Fetching all Designs with project_id={project_id}, vcs_id={vcs_id}')
    
    select_statement = MySQLStatementBuilder(db_connection)
    results = select_statement \
        .select(DESIGNS_TABLE, DESIGNS_COLUMNS) \
        .where('vcs = %s and project = %s', [vcs_id, project_id]) \
        .order_by(['id'], Sort.ASCENDING) \
        .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    logger.debug(results)

    design_list = []
    for result in results:
        design_list.append(populate_design(db_connection, result, project_id, vcs_id, user_id))
    
    count_statement = MySQLStatementBuilder(db_connection)
    result = count_statement.count(DESIGNS_TABLE) \
        .where('vcs = %s', [vcs_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)
    chunk = ListChunk[models.Design](chunk=design_list, length_total=result['count'])
    return chunk
    
def delete_design(db_connection: PooledMySQLConnection, design_id: int, project_id: int, vcs_id: int, user_id: int) -> bool:
    logger.debug(f'Deleting design with id={design_id}')

    select_statement = MySQLStatementBuilder(db_connection)
    result = select_statement\
        .select(DESIGNS_TABLE, DESIGNS_COLUMNS)\
        .where('id = %s', [design_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)
    
    if result is None: 
        raise cvs_exceptions.DesignNotFoundException
    
    if result['project'] != project_id:
        raise auth_exceptions.UnauthorizedOperationException
    
    if result['vcs'] != vcs_id:
        raise auth_exceptions.UnauthorizedOperationException
    

    if(delete_all_quantified_objectives(db_connection, design_id)):
        pass
    else:
        raise cvs_exceptions.QuantifiedObjectivesNotDeleted

    delete_statement = MySQLStatementBuilder(db_connection)
    _, rows = delete_statement.delete(DESIGNS_TABLE) \
        .where('id = %s', [design_id]) \
        .execute(return_affected_rows=True)
    
    if rows ==0:
        raise cvs_exceptions.DesignNotFoundException
    
    return True

def edit_design(db_connection: PooledMySQLConnection, design_id: int, project_id: int, vcs_id: int, user_id: int, updated_design: models.DesignPost) -> models.Design:
    logger.debug(f'Editing Design with id = {design_id}')

    update_statement = MySQLStatementBuilder(db_connection)
    update_statement.update(
        table=DESIGNS_TABLE,
        set_statement='name = %s, description = %s',
        values=[updated_design.name, updated_design.description]
    )
    update_statement.where('id = %s', [design_id])
    _, rows = update_statement.execute(return_affected_rows=True)

    if rows == 0:
        raise cvs_exceptions.DesignNotFoundException
    
    return(get_design(db_connection, design_id, project_id, vcs_id, user_id))

def populate_design(db_connection: PooledMySQLConnection, db_result, project_id: int, vcs_id: int, user_id: int) -> models.Design:
    return models.Design(
        id=db_result['id'],
        vcs=get_vcs(db_connection, vcs_id=vcs_id, project_id=project_id, user_id=user_id),
        name=db_result['name'],
        description=db_result['description']
    )

# ======================================================================================================================
# CVS Quantified Objectives
# ======================================================================================================================

def get_quantified_objective(db_connection: PooledMySQLConnection, quantified_objective_id: int, 
    design_id: int, value_driver_id: int, project_id: int, user_id: int) -> models.QuantifiedObjective:
    
    select_statement = MySQLStatementBuilder(db_connection)
    result = select_statement \
    .select(QUANTIFIED_OBJECTIVE_TABLE, QUANTIFIED_OBJECTIVE_COLUMNS) \
    .where('id = %s', [quantified_objective_id]) \
    .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    if result is None:
        raise cvs_exceptions.QuantifiedObjectiveNotFoundException

    return populate_QO(db_connection, result, design_id, value_driver_id, project_id, user_id)

def get_all_quantified_objectives(db_connection: PooledMySQLConnection, design_id: int, 
    project_id: int, user_id: int) -> List[models.QuantifiedObjective]:
    
    select_statement = MySQLStatementBuilder(db_connection)
    res = select_statement \
    .select(QUANTIFIED_OBJECTIVE_TABLE, QUANTIFIED_OBJECTIVE_COLUMNS) \
    .where('design = %s', [design_id]) \
    .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    if res is None:
        raise cvs_exceptions.QuantifiedObjectiveNotFoundException
    
    QO_list = []

    for result in res:
        QO_list.append(populate_QO(db_connection, result, design_id, result['value_driver'], project_id, user_id))

    return QO_list


def create_quantified_objective(db_connection: PooledMySQLConnection, design_id: int, value_driver_id: int, 
    quantified_objective_post: models.QuantifiedObjectivePost, project_id: int, user_id: int) -> models.QuantifiedObjective:

    insert_statement = MySQLStatementBuilder(db_connection)
    insert_statement \
        .insert(table=QUANTIFIED_OBJECTIVE_TABLE, columns=['design', 'value_driver', 'name', 'property', 'unit']) \
        .set_values([design_id, value_driver_id, quantified_objective_post.name, quantified_objective_post.property, quantified_objective_post.unit]) \
        .execute(fetch_type=FetchType.FETCH_NONE)
    quantified_id = insert_statement.last_insert_id

    return get_quantified_objective(db_connection, quantified_id, design_id, value_driver_id, project_id, user_id)
    
def delete_quantified_objective(db_connection: PooledMySQLConnection, quantified_objective_id: int, value_driver_id: int, design_id: int,
    user_id: int) -> bool:

    select_statement = MySQLStatementBuilder(db_connection)
    result = select_statement \
        .select(QUANTIFIED_OBJECTIVE_TABLE, QUANTIFIED_OBJECTIVE_COLUMNS) \
        .where('id = %s', [quantified_objective_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    if result is None:
        raise cvs_exceptions.QuantifiedObjectiveNotFoundException
    
    if result['design'] != design_id:
        raise auth_exceptions.UnauthorizedOperationException
    
    if result['value_driver'] != value_driver_id:
        raise auth_exceptions.UnauthorizedOperationException
    
    delete_statement = MySQLStatementBuilder(db_connection)
    _, rows = delete_statement.delete(QUANTIFIED_OBJECTIVE_TABLE) \
        .where('id = %s', [quantified_objective_id]) \
        .execute(return_affected_rows=True)

    if rows == 0:
        raise cvs_exceptions.QuantifiedObjectiveNotFoundException
    
    return True

def delete_all_quantified_objectives(db_connection: PooledMySQLConnection, design_id: int) -> bool:
    logger.debug(f'Deleting all quantified objectives with design id = {design_id}')

    delete_statement = MySQLStatementBuilder(db_connection)
    _, rows = delete_statement.delete(QUANTIFIED_OBJECTIVE_TABLE) \
        .where('design = %s', [design_id]) \
        .execute(return_affected_rows=True)
  
    return True

def edit_quantified_objective(db_connection: PooledMySQLConnection, quantified_objective_id: int, design_id: int,
    value_driver_id: int, updated_QO: models.QuantifiedObjectivePost, user_id: int, project_id: int) -> models.QuantifiedObjective:
    logger.debug(f'Editing quantified objective with id = {quantified_objective_id}')

    update_statement = MySQLStatementBuilder(db_connection)
    update_statement.update(
        table=QUANTIFIED_OBJECTIVE_TABLE,
        set_statement='name = %s, property = %s, unit = %s',
        values=[updated_QO.name, updated_QO.property, updated_QO.unit]
    )
    update_statement.where('id = %s', [quantified_objective_id])
    _, rows = update_statement.execute(return_affected_rows=True)

    if rows == 0:
        raise cvs_exceptions.QuantifiedObjectiveNotFoundException
    
    return(get_quantified_objective(db_connection, quantified_objective_id, design_id, value_driver_id, project_id, user_id))




def populate_QO(db_connection: PooledMySQLConnection, db_result, 
    design_id: int, value_driver_id: int, project_id: int, user_id: int) -> models.QuantifiedObjective:
    return models.QuantifiedObjective(
        id = db_result['id'],
        design = design_id,
        value_driver = get_value_driver(db_connection, value_driver_id, project_id, user_id),
        name=db_result['name'],
        property = db_result['property'],
        unit = db_result['unit'],
        processes = get_table_rows_from_driver(db_connection, value_driver_id, project_id, user_id)
    )


#TODO change the way that stakeholder needs and value drivers are stored. 
def get_table_rows_from_driver(db_connection: PooledMySQLConnection, value_driver_id: int, 
                project_id: int, user_id: int) -> List[models.TableRowGet]:
    
    select_statement = MySQLStatementBuilder(db_connection)
    stakeholder_need_ids = select_statement \
    .select(CVS_VCS_NEEDS_DRIVERS_MAP_TABLE, ['stakeholder_need_id']) \
    .where('value_driver_id = %s', [value_driver_id]) \
    .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    table_rows = []
    for need_id in stakeholder_need_ids:
        select_statement = MySQLStatementBuilder(db_connection)
        table_row_ids = select_statement \
        .select(CVS_VCS_STAKEHOLDER_NEED_TABLE, ['table_row_id']) \
        .where('id = %s', [need_id['stakeholder_need_id']]) \
        .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

        
        
        for table_row_id in table_row_ids:
            select_statement = MySQLStatementBuilder(db_connection)
            result = select_statement \
            .select(CVS_VCS_TABLE_ROWS_TABLE, CVS_VCS_TABLE_ROWS_COLUMNS) \
            .where('id = %s', [table_row_id['table_row_id']]) \
            .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

            table_rows.append(populate_table_row(db_connection, result, project_id, user_id))
    
    return table_rows

# ======================================================================================================================
# BPMN Table
# ======================================================================================================================

def populate_bpmn_node(db_connection, result, project_id, user_id) -> models.NodeGet:
    logger.debug(f'Populating model for node with id={result["id"]}.')

    return models.NodeGet(
        id=result['id'],
        vcs_id=result['vcs_id'],
        name=result['name'],
        node_type=result['type'],
        pos_x=result['pos_x'],
        pos_y=result['pos_y'],
        vcs_table_row=get_vcs_table_row(db_connection, result['id'], project_id, user_id)
    )


def populate_bpmn_edge(result) -> models.EdgeGet:
    logger.debug(f'Populating model for edge with id={result["id"]}.')
    return models.EdgeGet(
        id=result['id'],
        vcs_id=result['vcs_id'],
        name=result['name'],
        from_node=result['from_node'],
        to_node=result['to_node'],
        probability=result['probability']
    )


def get_bpmn_node(db_connection: PooledMySQLConnection, node_id: int, project_id: int,
                  user_id: int) -> models.NodeGet:
    logger.debug(f'Fetching node with id={node_id}.')

    select_statement = MySQLStatementBuilder(db_connection)
    result = select_statement \
        .select(CVS_BPMN_NODES_TABLE, CVS_BPMN_NODES_COLUMNS) \
        .where('id = %s', [node_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    if result is None:
        raise cvs_exceptions.NodeNotFoundException

    return populate_bpmn_node(db_connection, result, project_id, user_id)


def create_bpmn_node(db_connection: PooledMySQLConnection, node: models.NodePost, project_id: int, vcs_id: int,
                     user_id: int) -> models.NodeGet:
    logger.debug(f'Creating a node for vcs with id={vcs_id}.')
    columns = ['vcs_id', 'name', 'type']
    values = [vcs_id, node.name, node.node_type]

    insert_statement = MySQLStatementBuilder(db_connection)
    insert_statement \
        .insert(table=CVS_BPMN_NODES_TABLE, columns=columns) \
        .set_values(values) \
        .execute(fetch_type=FetchType.FETCH_NONE)
    node_id = insert_statement.last_insert_id

    return get_bpmn_node(db_connection, node_id, project_id, user_id)


def delete_bpmn_node(db_connection: PooledMySQLConnection, node_id: int) -> bool:

    delete_statement = MySQLStatementBuilder(db_connection)
    _, rows = delete_statement.delete(CVS_BPMN_NODES_TABLE) \
        .where('id = %s', [node_id]) \
        .execute(return_affected_rows=True)

    if rows == 0:
        raise cvs_exceptions.NodeFailedDeletionException(node_id)

    return True


def update_bpmn_node(db_connection: PooledMySQLConnection, node_id: int, node: models.NodePost, project_id: int,
                     vcs_id: int, user_id: int) -> models.NodeGet:
    logger.debug(f'Updating node with id={node_id}.')

    # Performs necessary checks
    get_bpmn_node(db_connection, node_id, project_id, user_id)

    update_statement = MySQLStatementBuilder(db_connection)
    update_statement.update(
        table=CVS_BPMN_NODES_TABLE,
        set_statement='vcs_id = %s, name = %s, type = %s, pos_x = %s, pos_y = %s',
        values=[vcs_id, node.name, node.node_type, node.pos_x, node.pos_y],
    )
    update_statement.where('id = %s', [node_id])
    _, rows = update_statement.execute(return_affected_rows=True)

    if rows == 0:
        raise cvs_exceptions.NodeFailedToUpdateException

    return get_bpmn_node(db_connection, node_id, project_id, user_id)


def get_bpmn_edge(db_connection: PooledMySQLConnection, edge_id: int) -> models.EdgeGet:
    logger.debug(f'Fetching edge with id={edge_id}.')

    select_statement = MySQLStatementBuilder(db_connection)
    result = select_statement \
        .select(CVS_BPMN_EDGES_TABLE, CVS_BPMN_EDGES_COLUMNS) \
        .where('id = %s', [edge_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    if result is None:
        raise cvs_exceptions.EdgeNotFoundException

    return populate_bpmn_edge(result)


def create_bpmn_edge(db_connection: PooledMySQLConnection, edge: models.EdgePost, vcs_id: int) -> models.EdgeGet:
    logger.debug(f'Creating an edge for vcs with id={vcs_id}.')

    columns = ['vcs_id', 'name', 'from_node', 'to_node', 'probability']
    values = [vcs_id, edge.name, edge.from_node, edge.to_node, edge.probability]

    insert_statement = MySQLStatementBuilder(db_connection)
    insert_statement \
        .insert(table=CVS_BPMN_EDGES_TABLE, columns=columns) \
        .set_values(values) \
        .execute(fetch_type=FetchType.FETCH_NONE)
    edge_id = insert_statement.last_insert_id

    return get_bpmn_edge(db_connection, edge_id)


def delete_bpmn_edge(db_connection: PooledMySQLConnection, edge_id: int) -> bool:
    get_bpmn_edge(db_connection, edge_id)  # checks

    delete_statement = MySQLStatementBuilder(db_connection)
    _, rows = delete_statement.delete(CVS_BPMN_EDGES_TABLE) \
        .where('id = %s', [edge_id]) \
        .execute(return_affected_rows=True)

    if rows == 0:
        raise cvs_exceptions.EdgeFailedDeletionException(edge_id)

    return True


def update_bpmn_edge(db_connection: PooledMySQLConnection, edge_id: int, edge: models.EdgePost,
                     vcs_id: int) -> models.EdgeGet:
    logger.debug(f'Updating edge with id={edge_id}.')

    # Performs necessary checks
    get_bpmn_edge(db_connection, edge_id)

    update_statement = MySQLStatementBuilder(db_connection)
    update_statement.update(
        table=CVS_BPMN_EDGES_TABLE,
        set_statement='vcs_id = %s, name = %s, from_node = %s, to_node = %s, probability = %s',
        values=[vcs_id, edge.name, edge.from_node, edge.to_node, edge.probability],
    )
    update_statement.where('id = %s', [edge_id])
    _, rows = update_statement.execute(return_affected_rows=True)

    return get_bpmn_edge(db_connection, edge_id)


def get_bpmn(db_connection: PooledMySQLConnection, vcs_id: int, project_id, user_id) -> models.BPMNGet:
    logger.debug(f'Get BPMN for vcs with id={vcs_id}.')

    where_statement = f'vcs_id = %s'
    where_values = [vcs_id]

    select_statement = MySQLStatementBuilder(db_connection)
    nodes = select_statement \
        .select(CVS_BPMN_NODES_TABLE, CVS_BPMN_NODES_COLUMNS) \
        .where(where_statement, where_values) \
        .order_by(['id'], Sort.ASCENDING) \
        .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    select_statement = MySQLStatementBuilder(db_connection)
    edges = select_statement \
        .select(CVS_BPMN_EDGES_TABLE, CVS_BPMN_EDGES_COLUMNS) \
        .where(where_statement, where_values) \
        .order_by(['id'], Sort.ASCENDING) \
        .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    return models.BPMNGet(
        vcs_id=vcs_id,
        nodes=[populate_bpmn_node(db_connection, node, project_id, user_id) for node in nodes],
        edges=[populate_bpmn_edge(edge) for edge in edges],
    )


def update_bpmn(db_connection: PooledMySQLConnection, vcs_id: int, project_id: int, user_id: int,
                nodes: List[models.NodeGet], edges: List[models.EdgeGet]) -> models.BPMNGet:
    logger.debug(f'Updating bpmn with vcs id={vcs_id}.')

    for node in nodes:
        new_node = models.NodePost(
            vcs_id=vcs_id,
            name=node.name,
            node_type=node.node_type,
            pos_x=node.pos_x,
            pos_y=node.pos_y
        )
        update_bpmn_node(db_connection, node.id, new_node, project_id, vcs_id, user_id)

    for edge in edges:
        new_edge = models.EdgePost(
            vcs_id=vcs_id,
            name=edge.name,
            from_node=edge.from_node,
            to_node=edge.to_node,
            probability=edge.probability,
        )
        update_bpmn_edge(db_connection, edge.id, new_edge, vcs_id)

    return get_bpmn(db_connection, vcs_id, project_id, user_id)


# ======================================================================================================================
# Market Input Table
# ======================================================================================================================

def populate_market_input(db_result) -> models.MarketInputGet:
    return models.MarketInputGet(
        id=db_result['id'],
        design=db_result['design'],
        table_row=db_result['table_row'],
        time=db_result['time'],
        cost=db_result['cost'],
        revenue=db_result['revenue']
    )


def get_market_input(db_connection: PooledMySQLConnection, market_input_id: int) -> models.MarketInputGet:
    logger.debug(f'Fetching market input with id={market_input_id}.')

    select_statement = MySQLStatementBuilder(db_connection)
    db_result = select_statement \
        .select(CVS_MARKET_INPUT_TABLE, CVS_MARKET_INPUT_COLUMN) \
        .where('id = %s', [market_input_id]) \
        .execute(fetch_type=FetchType.FETCH_ONE, dictionary=True)

    if db_result is None:
        raise cvs_exceptions.MarketInputNotFoundException

    return populate_market_input(db_result)


def get_all_market_input(db_connection: PooledMySQLConnection, design_id: int) -> List[models.MarketInputGet]:
    logger.debug(f'Fetching all market inputs for design with id={design_id}.')

    select_statement = MySQLStatementBuilder(db_connection)
    results = select_statement \
        .select(CVS_MARKET_INPUT_TABLE, CVS_MARKET_INPUT_COLUMN) \
        .where('design = %s', [design_id]) \
        .order_by(['id'], Sort.ASCENDING) \
        .execute(fetch_type=FetchType.FETCH_ALL, dictionary=True)

    return [populate_market_input(db_result) for db_result in results]


def create_market_input(db_connection: PooledMySQLConnection, design_id: int, table_row_id: int,
                        market_input: models.MarketInputPost) -> models.MarketInputGet:
    logger.debug(f'Create market input')

    columns = ['design', 'table_row', 'time', 'cost', 'revenue']
    values = [design_id, table_row_id, market_input.time, market_input.cost, market_input.revenue]

    insert_statement = MySQLStatementBuilder(db_connection)
    insert_statement \
        .insert(table=CVS_MARKET_INPUT_TABLE, columns=columns) \
        .set_values(values) \
        .execute(fetch_type=FetchType.FETCH_NONE)
    market_input_id = insert_statement.last_insert_id

    return get_market_input(db_connection, market_input_id)


def update_market_input(db_connection: PooledMySQLConnection, market_input_id: int,
                        market_input: models.MarketInputPost) -> models.MarketInputGet:
    logger.debug(f'Update market input with id={market_input_id}')

    get_market_input(db_connection, market_input_id)  # Performs necessary checks

    update_statement = MySQLStatementBuilder(db_connection)
    update_statement.update(
        table=CVS_MARKET_INPUT_TABLE,
        set_statement='time = %s, cost = %s, revenue = %s',
        values=[market_input.time, market_input.cost, market_input.revenue],
    )
    update_statement.where('id = %s', [market_input_id])
    _, rows = update_statement.execute(return_affected_rows=True)

    return get_market_input(db_connection, market_input_id)
