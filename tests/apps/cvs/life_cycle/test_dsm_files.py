import pytest
import os
from pathlib import Path
import tests.apps.cvs.testutils as tu
import sedbackend.apps.core.users.implementation as impl_users
import sedbackend.apps.cvs.life_cycle.implementation as impl_life_cycle
import sedbackend.apps.core.files.implementation as impl_files

std_rows = [tu.vcs_model.VcsRowPost(
    index=0,
    stakeholder=tu.tu.random_str(5, 50),
    stakeholder_needs=None,
    stakeholder_expectations=tu.tu.random_str(5, 50),
    iso_process=18,
    subprocess=None
), tu.vcs_model.VcsRowPost(
    index=1,
    stakeholder=tu.tu.random_str(5, 50),
    stakeholder_needs=None,
    stakeholder_expectations=tu.tu.random_str(5, 50),
    iso_process=20,
    subprocess=None
), tu.vcs_model.VcsRowPost(
    index=2,
    stakeholder=tu.tu.random_str(5, 50),
    stakeholder_needs=None,
    stakeholder_expectations=tu.tu.random_str(5, 50),
    iso_process=22,
    subprocess=None
), tu.vcs_model.VcsRowPost(
    index=3,
    stakeholder=tu.tu.random_str(5, 50),
    stakeholder_needs=None,
    stakeholder_expectations=tu.tu.random_str(5, 50),
    iso_process=24,
    subprocess=None
)]


def test_upload_dsm_file(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(project.id, current_user.id)

    rows = [std_rows[0], std_rows[1]]
    table = tu.create_vcs_table(project.id, vcs.id, rows)

    cwd = os.getcwd()
    _test_upload_file = Path(cwd + '/tests/apps/cvs/life_cycle/files/input.csv')
    _file = {'file': ('input.csv', _test_upload_file.open('rb'), 'text/csv')}

    # Act
    res = client.post(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/dsm/file',
                      headers=std_headers,
                      files=_file)

    # Assert
    assert res.status_code == 200

    # Cleanup
    tu.delete_dsm_file_from_vcs_id(project.id, vcs.id, current_user.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)


def test_upload_invalid_file_extension(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(project.id, current_user.id)

    rows = std_rows

    table = tu.create_vcs_table(project.id, vcs.id, rows)

    cwd = os.getcwd()
    _test_upload_file = Path(cwd + '/tests/apps/cvs/life_cycle/files/input-example.xlsx')
    _file = {'file': ('input-example.xlsx', _test_upload_file.open('rb'),
                      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}

    # Act
    res = client.post(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/dsm/file',
                      headers=std_headers,
                      files=_file)

    # Assert
    assert res.status_code == 415  # InvalidFileTypeException

    # Cleanup
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_upload_invalid_dsm_file(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(project.id, current_user.id)

    row1 = tu.vcs_model.VcsRowPost(
        index=0,
        stakeholder=tu.tu.random_str(5, 50),
        stakeholder_needs=None,
        stakeholder_expectations=tu.tu.random_str(5, 50),
        iso_process=18,
        subprocess=None
    )
    row2 = tu.vcs_model.VcsRowPost(
        index=1,
        stakeholder=tu.tu.random_str(5, 50),
        stakeholder_needs=None,
        stakeholder_expectations=tu.tu.random_str(5, 50),
        iso_process=15,
        subprocess=None
    )

    rows = [row1, row2]
    tu.create_vcs_table(project.id, vcs.id, rows)

    cwd = os.getcwd()
    _test_upload_file = Path(cwd + '/tests/apps/cvs/life_cycle/files/input.csv')
    _file = {'file': ('input.csv', _test_upload_file.open('rb'), 'text/csv')}

    # Act
    res = client.post(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/dsm/file',
                      headers=std_headers,
                      files=_file)

    # Assert
    assert res.status_code == 400  # Bad request, should throw ProcessesVcsMatchException

    # Cleanup
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)


def test_get_dsm_file_id(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(project.id, current_user.id)

    rows = [std_rows[0], std_rows[1]]
    table = tu.create_vcs_table(project.id, vcs.id, rows)

    cwd = os.getcwd()
    _test_upload_file = Path(cwd + '/tests/apps/cvs/life_cycle/files/input.csv')
    _file = {'file': ('input.csv', _test_upload_file.open('rb'), 'text/csv')}

    # Act
    client.post(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/dsm/file',
                headers=std_headers,
                files=_file)

    res = client.get(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/dsm/id',
                     headers=std_headers)

    # Assert
    assert res.status_code == 200

    # Cleanup
    tu.delete_dsm_file_from_vcs_id(project.id, vcs.id, current_user.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)


def test_get_dsm_matrix(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(project.id, current_user.id)

    rows = [std_rows[0], std_rows[1]]
    tu.create_vcs_table(project.id, vcs.id, rows)

    cwd = os.getcwd()
    _test_upload_file = Path(cwd + '/tests/apps/cvs/life_cycle/files/input.csv')
    _file = {'file': ('input.csv', _test_upload_file.open('rb'), 'text/csv')}

    # Act
    client.post(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/dsm/file',
                headers=std_headers,
                files=_file)

    res = client.get(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/dsm',
                     headers=std_headers)

    matrix = res.json()

    # Assert
    assert res.status_code == 200
    assert len(matrix) == 5

    # Cleanup
    tu.delete_dsm_file_from_vcs_id(project.id, vcs.id, current_user.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)


def test_save_dsm(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(project.id, current_user.id)

    rows = [std_rows[0], std_rows[1]]
    tu.create_vcs_table(project.id, vcs.id, rows)

    dsm = [["Processes", "Start", "Implementation", "Verification", "End"],
           ["Start", "X", "1", "0", "0"],
           ["Implementation", "0", "X", "1", "0"],
           ["Verification", "0", "0", "X", "1"],
           ["End", "0", "0", "0", "X"]]

    # Act
    res = client.post(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/dsm',
                      headers=std_headers,
                      json=dsm)

    saved_dsm = impl_life_cycle.get_dsm(project.id, vcs.id, current_user.id)

    # Assert
    assert res.status_code == 200
    assert dsm == saved_dsm

    # Cleanup
    tu.delete_dsm_file_from_vcs_id(project.id, vcs.id, current_user.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)


def test_apply_dsm_to_all(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcss = [tu.seed_random_vcs(project.id, current_user.id) for _ in range(3)]

    rows = [std_rows[0], std_rows[1]]
    rows_alt = [std_rows[0], std_rows[1], std_rows[2]]

    tu.create_vcs_table(project.id, vcss[0].id, rows)
    tu.create_vcs_table(project.id, vcss[1].id, rows)
    tu.create_vcs_table(project.id, vcss[2].id, rows_alt)

    dsm = [["Processes", "Start", "Implementation", "Verification", "End"],
           ["Start", "X", "1", "0", "0"],
           ["Implementation", "0", "X", "1", "0"],
           ["Verification", "0", "0", "X", "1"],
           ["End", "0", "0", "0", "X"]]

    # Act
    res = client.post(f'/api/cvs/project/{project.id}/vcs/{vcss[0].id}/dsm/all',
                      headers=std_headers,
                      json=dsm)

    # Assert
    assert res.status_code == 200
    assert [vcs["id"] for vcs in res.json()["success_vcs"]] == [vcss[0].id, vcss[1].id]
    assert [vcs["id"] for vcs in res.json()["failed_vcs"]] == [vcss[2].id]

    # Cleanup
    [tu.delete_dsm_file_from_vcs_id(project.id, vcs["id"], current_user.id) for vcs in res.json()["success_vcs"]]
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id for vcs in vcss])
    tu.delete_project_by_id(project.id, current_user.id)
