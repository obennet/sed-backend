import tests.apps.cvs.testutils as tu
import sedbackend.apps.core.users.implementation as impl_users
import sedbackend.apps.cvs.vcs.implementation as impl_vcs


def test_get_all_value_drivers(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    for _ in range(5):
        tu.seed_random_value_driver(current_user.id)
    # Act
    res = client.get(f'/api/cvs/value-driver/all', headers=std_headers)
    # Assert
    assert res.status_code == 200  # 200 OK
    assert len(res.json()) == 5
    # Cleanup
    tu.delete_vd_from_user(current_user.id)
    


def test_get_all_value_drivers_no_vds(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    # Act
    res = client.get(f'/api/cvs/value-driver/all', headers=std_headers)
    # Assert
    assert res.status_code == 200  # 200 OK
    assert len(res.json()) == 0
    # Cleanup
    tu.delete_vd_from_user(current_user.id)


def test_get_value_driver(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    vd = tu.seed_random_value_driver(current_user.id)
    # Act
    res = client.get(f'/api/cvs/value-driver/{vd.id}', headers=std_headers)
    # Assert
    assert res.status_code == 200  # 200 OK
    assert res.json()['name'] == vd.name
    assert res.json()['unit'] == vd.unit
    # Cleanup
    tu.delete_vd_from_user(current_user.id)


def test_get_value_driver_not_found(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    vd_id = 99999999
    # Act
    res = client.get(f'/api/cvs/value-driver/{vd_id}', headers=std_headers)
    # Assert
    assert res.status_code == 404  # 404 Not Found
    # Cleanup
    tu.delete_vd_from_user(current_user.id)


def test_create_value_driver(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    vd = tu.seed_random_value_driver(current_user.id)
    # Act
    res = client.post(f'/api/cvs/value-driver', headers=std_headers, json={
        'name': vd.name,
        'unit': vd.unit
    })
    # Assert
    assert res.status_code == 200  # 200 OK
    assert res.json()['name'] == vd.name
    assert res.json()['unit'] == vd.unit
    # Cleanup
    tu.delete_vd_from_user(current_user.id)


def test_create_value_driver_missing_name(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    vd = tu.seed_random_value_driver(current_user.id)
    # Act
    res = client.post(f'/api/cvs/value-driver', headers=std_headers, json={
        'unit': vd.unit
    })
    # Assert
    assert res.status_code == 422  # 422 Unprocessable Entity
    # Cleanup
    tu.delete_vd_from_user(current_user.id)


def test_create_value_driver_missing_unit(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    vd = tu.seed_random_value_driver(current_user.id)
    # Act
    res = client.post(f'/api/cvs/value-driver', headers=std_headers, json={
        'name': vd.name
    })
    # Assert
    assert res.status_code == 200  # 200 OK
    # Cleanup
    tu.delete_vd_from_user(current_user.id)


def test_edit_value_driver(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    vd = tu.seed_random_value_driver(current_user.id)
    # Act
    res = client.put(f'/api/cvs/value-driver/{vd.id}', headers=std_headers, json={
        'name': "new name",
        'unit': "new unit"
    })
    # Assert
    assert res.status_code == 200  # 200 OK
    assert res.json()['name'] == "new name"
    assert res.json()['unit'] == "new unit"
    # Cleanup
    tu.delete_vd_from_user(current_user.id)


def test_delete_value_driver(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    vd = tu.seed_random_value_driver(current_user.id)
    # Act
    res = client.delete(f'/api/cvs/value-driver/{vd.id}', headers=std_headers)
    # Assert
    assert res.status_code == 200  # 200 OK
    assert len(impl_vcs.get_all_value_driver(current_user.id)) == 0
    # Cleanup
    tu.delete_vd_from_user(current_user.id)


def test_get_all_value_drivers_from_vcs(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(project.id)
    tu.seed_vcs_table_rows(current_user.id, project.id, vcs.id)
    
    # Act
    res = client.get(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/value-driver/all', headers=std_headers)
    # Assert
    assert res.status_code == 200  # 200 OK
    all_vds = impl_vcs.get_all_value_driver(current_user.id)
    assert len(res.json()) == len(all_vds)
    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_get_all_value_drivers_vcs_row(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(project.id)
    vcs_row = tu.seed_vcs_table_rows(current_user.id, project.id, vcs.id, 1)[0]
    needs = vcs_row.stakeholder_needs
    value_drivers = []
    for need in needs:
        value_drivers += [vd.id for vd in need.value_drivers]
    value_drivers = list(dict.fromkeys(value_drivers))

    # Act
    res = client.get(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/row/{vcs_row.id}/value-driver/all',
                     headers=std_headers)
    # Assert
    assert res.status_code == 200  # 200 OK
    assert len(res.json()) == len(value_drivers)
    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)
