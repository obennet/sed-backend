import tests.apps.cvs.testutils as tu
import testutils as sim_tu
import sedbackend.apps.core.users.implementation as impl_users


def test_run_single_simulation(client, std_headers, std_user):
    # Setup

    current_user = impl_users.impl_get_user_with_username(std_user.username)

    project, vcs, design_group, design, settings = sim_tu.setup_single_simulation(
        current_user.id
    )
    settings.monte_carlo = False

    # Act
    saveSim = client.post(
        f"/api/cvs/project/{project.id}/simulation/run",
        headers=std_headers,
        json={
            "sim_settings": settings.dict(),
            "vcs_ids": [vcs.id],
            "design_group_ids": [design_group.id],
        },
    )
    allSimId = client.get(
        f"/api/cvs/project/{project.id}/simulation/all",
        headers=std_headers
    )
    res = client.get(
       f"/api/cvs/project/{project.id}/simulation/file/{allSimId.json()[-1]['file']}",
        headers=std_headers
    )
    # Assert
    
    assert saveSim.status_code == 200
    assert allSimId.status_code == 200
    assert res.status_code == 200
    assert res.json()['designs'] == design
    assert allSimId.json()[-1]['project_id'] == project.id
    

    # Should probably assert some other stuff about the output to ensure that it is correct.

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)


def test_run_sim_invalid_design_group(client, std_headers, std_user):
    # Setup

    current_user = impl_users.impl_get_user_with_username(std_user.username)

    project, vcs, design_group, design, settings = sim_tu.setup_single_simulation(
        current_user.id
    )
    settings.monte_carlo = False

    # Act
    res = client.post(
        f"/api/cvs/project/{project.id}/simulation/run",
        headers=std_headers,
        json={
            "sim_settings": settings.dict(),
            "vcs_ids": [vcs.id],
            "design_group_ids": [design_group.id + 9999],
        },
    )

    # Assert
    assert res.status_code == 400

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)


def test_run_sim_invalid_vcss(client, std_headers, std_user):
    # Setup

    current_user = impl_users.impl_get_user_with_username(std_user.username)

    project, vcs, design_group, design, settings = sim_tu.setup_single_simulation(
        current_user.id
    )
    settings.monte_carlo = False

    # Act
    res = client.post(
        f"/api/cvs/project/{project.id}/simulation/run",
        headers=std_headers,
        json={
            "sim_settings": settings.dict(),
            "vcs_ids": [vcs.id + 9999],
            "design_group_ids": [design_group.id],
        },
    )

    # Assert
    assert res.status_code == 400

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)


def test_run_sim_end_time_before_start_time(client, std_headers, std_user):
    # Setup

    current_user = impl_users.impl_get_user_with_username(std_user.username)

    project, vcs, design_group, design, settings = sim_tu.setup_single_simulation(
        current_user.id
    )
    settings.monte_carlo = False
    settings.end_time = settings.start_time - 1

    # Act
    res = client.post(
        f"/api/cvs/project/{project.id}/simulation/run",
        headers=std_headers,
        json={
            "sim_settings": settings.dict(),
            "vcs_ids": [vcs.id],
            "design_group_ids": [design_group.id],
        },
    )

    # Assert
    assert res.status_code == 400
    assert "Settings are not correct" in res.json()["detail"]

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_run_sim_flow_time_above_total_time(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)

    project, vcs, design_group, design, settings = sim_tu.setup_single_simulation(
        current_user.id
    )
    settings.monte_carlo = False
    settings.flow_time = settings.start_time * settings.end_time

    # Act
    res = client.post(
        f"/api/cvs/project/{project.id}/simulation/run",
        headers=std_headers,
        json={
            "sim_settings": settings.dict(),
            "vcs_ids": [vcs.id],
            "design_group_ids": [design_group.id],
        },
    )

    # Assert
    assert res.status_code == 400
    assert "Settings are not correct" in res.json()["detail"]

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_run_sim_no_flows(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)

    project, vcs, design_group, design, settings = sim_tu.setup_single_simulation(
        current_user.id
    )
    settings.monte_carlo = False
    settings.flow_start_time = None
    settings.flow_process = None

    # Act
    res = client.post(
        f"/api/cvs/project/{project.id}/simulation/run",
        headers=std_headers,
        json={
            "sim_settings": settings.dict(),
            "vcs_ids": [vcs.id],
            "design_group_ids": [design_group.id],
        },
    )

    # Assert
    assert res.status_code == 400
    assert "Settings are not correct" in res.json()["detail"]

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_run_sim_both_flows(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)

    project, vcs, design_group, design, settings = sim_tu.setup_single_simulation(
        current_user.id
    )
    settings.monte_carlo = False
    settings.flow_start_time = 5
    settings.flow_process = 10

    # Act
    res = client.post(
        f"/api/cvs/project/{project.id}/simulation/run",
        headers=std_headers,
        json={
            "sim_settings": settings.dict(),
            "vcs_ids": [vcs.id],
            "design_group_ids": [design_group.id],
        },
    )

    # Assert
    assert res.status_code == 400
    assert "Settings are not correct" in res.json()["detail"]

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_run_sim_rate_invalid_order(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project, vcs, design_group, design, settings = sim_tu.setup_single_simulation(
        current_user.id
    )
    flow_proc = tu.edit_rate_order_formulas(
        project.id, vcs.id, design_group.id, current_user.id
    )

    settings.monte_carlo = False
    settings.flow_process = (
        flow_proc.iso_process.name
        if flow_proc.iso_process is not None
        else flow_proc.subprocess.name
    )

    # Act
    res = client.post(
        f"/api/cvs/project/{project.id}/simulation/run",
        headers=std_headers,
        json={
            "sim_settings": settings.dict(),
            "vcs_ids": [vcs.id],
            "design_group_ids": [design_group.id],
        },
    )

    # Assert
    assert res.status_code == 400
    assert res.json() == {
        "detail": "Wrong order of rate of entities. Total sum cannot come after per product. Check your VCS table."
    }  # RateWrongOrderException

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_run_sim_invalid_proj(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)

    project, vcs, design_group, design, settings = sim_tu.setup_single_simulation(
        current_user.id
    )

    settings.monte_carlo = False
    project_id = project.id + 10000

    # Act
    res = client.post(
        f"/api/cvs/project/{project_id}/simulation/run",
        headers=std_headers,
        json={
            "sim_settings": settings.dict(),
            "vcs_ids": [vcs.id],
            "design_group_ids": [design_group.id],
        },
    )

    # Assert
    assert res.status_code == 404
    assert res.json() == {"detail": "Sub-project not found."}

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_run_single_simulation_no_values(client, std_headers, std_user):
    # Setup

    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(project.id, current_user.id)
    tu.seed_vcs_table_rows(current_user.id, project.id, vcs.id, 10)
    design_group = tu.seed_random_design_group(project.id)
    designs = tu.seed_random_designs(project.id, design_group.id, 1)
    settings = tu.seed_simulation_settings(project.id, [vcs.id], [designs[0].id])
    settings.monte_carlo = False

    # Act
    saveSim = client.post(
        f"/api/cvs/project/{project.id}/simulation/run",
        headers=std_headers,
        json={
            "sim_settings": settings.dict(),
            "vcs_ids": [vcs.id],
            "design_group_ids": [design_group.id],
        },
    )
    res = client.get(
       f"/api/cvs/project/{project.id}/simulation/file/{saveSim.json()['file']}",
        headers=std_headers
    )
    
    # Assert
    assert res.status_code == 200
    assert res.json()["runs"][0]["max_NPVs"][-1] == 0

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
