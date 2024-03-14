import tests.apps.cvs.testutils as tu
import sedbackend.apps.core.users.implementation as impl_users
import sedbackend.apps.cvs.vcs.implementation as impl_vcs


def test_get_all_subprocesses(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    tu.seed_random_subprocesses(project.id, 5)
    # Act
    res = client.get(f'/api/cvs/project/{project.id}/subprocess/all', headers=std_headers)
    # Assert
    assert res.status_code == 200  # 200 OK
    assert len(res.json()) == 5
    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_get_all_subprocesses_no_subprocesses(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    # Act
    res = client.get(f'/api/cvs/project/{project.id}/subprocess/all', headers=std_headers)
    # Assert
    assert res.status_code == 200  # 200 OK
    assert len(res.json()) == 0
    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_get_subprocess(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    subprocess = tu.seed_random_subprocesses(project.id, 1)[0]
    # Act
    res = client.get(f'/api/cvs/project/{project.id}/subprocess/{subprocess.id}', headers=std_headers)
    # Assert
    assert res.status_code == 200  # 200 OK
    assert res.json()['name'] == subprocess.name
    assert res.json()['parent_process']['id'] == subprocess.parent_process.id
    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_get_subprocess_not_found(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    tu.seed_random_subprocesses(project.id, 1)
    # Act
    res = client.get(f'/api/cvs/project/{project.id}/subprocess/99999999', headers=std_headers)
    # Assert
    assert res.status_code == 404  # 404 Not Found
    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_create_subprocess(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    subprocess = tu.seed_random_subprocesses(project.id, 1)[0]
    # Act
    res = client.post(f'/api/cvs/project/{project.id}/subprocess', headers=std_headers, json={
        'name': 'New subprocess',
        'parent_process_id': subprocess.parent_process.id
    })
    # Assert
    assert res.status_code == 200  # 200 OK
    assert res.json()['name'] == 'New subprocess'
    assert res.json()['parent_process']['id'] == subprocess.parent_process.id
    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_edit_subprocess(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(project.id, current_user.id)
    subprocess = tu.seed_random_subprocesses(project.id, 1)[0]
    # Act
    res = client.put(f'/api/cvs/project/{project.id}/subprocess/{subprocess.id}', headers=std_headers, json={
        'name': 'New name',
        'parent_process_id': subprocess.parent_process.id
    })

    subprocess_edit = impl_vcs.get_subprocess(project.id, subprocess.id)
    # Assert
    assert res.status_code == 200  # 200 OK
    assert subprocess_edit.name == 'New name'
    assert subprocess_edit.parent_process.id == subprocess.parent_process.id
    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_delete_subprocess(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(project.id, current_user.id)
    subprocess = tu.seed_random_subprocesses(project.id, 1)[0]
    # Act
    res = client.delete(f'/api/cvs/project/{project.id}/subprocess/{subprocess.id}', headers=std_headers)
    # Assert
    assert res.status_code == 200  # 200 OK
    assert len(impl_vcs.get_all_subprocess(project.id)) == 0
    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)
