import tests.testutils as testutils
import tests.apps.cvs.testutils as tu
import sedbackend.apps.core.users.implementation as impl_users
from sedbackend.apps.cvs.vcs import implementation as impl_vcs, models as vcs_model
from sedbackend.apps.cvs.link_design_lifecycle import (
    implementation as impl_connect,
    models as connect_model,
)
from sedbackend.apps.cvs.market_input import (
    implementation as impl_market_input,
    models as market_input_model,
)

def test_iso_processes_exist(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    # Act
    res = client.get(
        f"/api/cvs/vcs/iso-processes/all", headers=std_headers
    )

    # Assert
    assert res.status_code == 200
    assert len(res.json()) == 30

    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)


def test_create_formulas(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    vcs = tu.seed_random_vcs(project.id, current_user.id)
    vcs_rows = tu.seed_vcs_table_rows(current_user.id, project.id, vcs.id, 1)
    if vcs_rows is None:
        raise Exception
    design_group = tu.seed_random_design_group(project.id)
    value_driver = tu.seed_random_value_driver(current_user.id, project.id)
    external_factor = tu.seed_random_external_factor(project.id)

    # Act
    time = f'2+{{vd:{str(value_driver.id)},"{str(value_driver.name)} [{str(value_driver.unit)}]"}}+5+{{vd:{str(value_driver.id)},"{str(value_driver.name)} [{str(value_driver.unit)}]"}}+2'
    time_latex = f"2+\\class{{vd}}{{\\identifier{{vd:{str(value_driver.id)}}}{{\\text{{{str(value_driver.name)} [{str(value_driver.unit)}]}}}}}}+5+\\class{{vd}}{{\\identifier{{vd:{str(value_driver.id)}}}{{\\text{{{str(value_driver.name)} [{str(value_driver.unit)}]}}}}}}+2"
    cost = f'2+{{ef:{str(external_factor.id)},"{str(external_factor.name)} [{str(external_factor.unit)}]"}}'
    cost_latex = f"2+\\class{{ef}}{{\\identifier{{ef:{str(external_factor.id)}}}{{\\text{{{str(external_factor.name)} [{str(external_factor.unit)}]}}}}}}"
    revenue = f'20+{{vd:{str(value_driver.id)},"{str(value_driver.name)} [{str(value_driver.unit)}]"}}+{{ef:{str(external_factor.id)},"{str(external_factor.name)} [{str(external_factor.unit)}]"}}'
    revenue_latex = f"20+\\class{{vd}}{{\\identifier{{vd:{str(value_driver.id)}}}{{\\text{{{str(value_driver.name)} [{str(value_driver.unit)}]}}}}}}+\\class{{ef}}{{\\identifier{{ef:{str(external_factor.id)}}}{{\\text{{{str(external_factor.name)} [{str(external_factor.unit)}]}}}}}}"
    time_comment = testutils.random_str(10, 200)
    cost_comment = testutils.random_str(10, 200)
    revenue_comment = None

    rate = tu.random_rate_choice()

    time_unit = tu.random_time_unit()
    res = client.put(
        f"/api/cvs/project/{project.id}/vcs/{vcs.id}/design-group/{design_group.id}/formulas",
        headers=std_headers,
        json=[
            {
                "vcs_row_id": vcs_rows[0].id,
                "time": {"text": time, "latex": time_latex, "comment": time_comment},
                "time_unit": time_unit,
                "cost": {"text": cost, "latex": cost_latex, "comment": cost_comment},
                "revenue": {
                    "text": revenue,
                    "latex": revenue_latex,
                    "comment": revenue_comment,
                },
                "rate": rate,
            }
        ],
    )

    res_get = client.get(
        f"/api/cvs/project/{project.id}/vcs/{vcs.id}/design-group/{design_group.id}/formulas/all",
        headers=std_headers,
    )

    # Assert
    assert res.status_code == 200
    assert res_get.json()[0]["used_value_drivers"][0]["id"] == value_driver.id
    assert res_get.json()[0]["used_external_factors"][0]["id"] == external_factor.id
    assert res_get.json()[0]["time"]["text"] == time
    assert res_get.json()[0]["time"]["latex"] == time_latex
    assert res_get.json()[0]["time"]["comment"] == time_comment
    assert res_get.json()[0]["cost"]["text"] == cost
    assert res_get.json()[0]["cost"]["latex"] == cost_latex
    assert res_get.json()[0]["cost"]["comment"] == cost_comment
    assert res_get.json()[0]["revenue"]["text"] == revenue
    assert res_get.json()[0]["revenue"]["latex"] == revenue_latex
    assert res_get.json()[0]["revenue"]["comment"] == revenue_comment
    assert res_get.json()[0]["rate"] == rate

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_create_formulas_no_optional(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    vcs = tu.seed_random_vcs(project.id, current_user.id)
    vcs_rows = tu.seed_vcs_table_rows(current_user.id, project.id, vcs.id, 1)
    if vcs_rows is None:
        raise Exception
    design_group = tu.seed_random_design_group(project.id)

    # Act
    time = testutils.random_str(10, 200)
    time_unit = tu.random_time_unit()
    cost = testutils.random_str(10, 200)
    revenue = testutils.random_str(10, 200)
    rate = tu.random_rate_choice()

    res = client.put(
        f"/api/cvs/project/{project.id}/vcs/{vcs.id}/design-group/{design_group.id}/formulas",
        headers=std_headers,
        json=[
            {
                "vcs_row_id": vcs_rows[0].id,
                "time": {"text": time, "latex": time, "comment": ""},
                "time_unit": time_unit,
                "cost": {"text": cost, "latex": cost, "comment": ""},
                "revenue": {"text": revenue, "latex": revenue, "comment": ""},
                "rate": rate,
            }
        ],
    )

    # Assert
    assert res.status_code == 200
    assert res.json() == True

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_get_all_formulas(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    vcs = tu.seed_random_vcs(project.id, current_user.id)
    design_group = tu.seed_random_design_group(project.id)

    # Act
    formulas = tu.seed_random_formulas(
        project.id, vcs.id, design_group.id, current_user.id
    )

    res = client.get(
        f"/api/cvs/project/{project.id}/vcs/{vcs.id}/design-group/{design_group.id}/formulas/all",
        headers=std_headers,
    )

    # Assert
    assert res.status_code == 200
    assert len(res.json()) == len(formulas)

    # Cleanup
    tu.delete_formulas(
        project.id,
        [(formula.vcs_row_id, formula.design_group_id) for formula in formulas],
    )
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_get_all_formulas_invalid_project(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    invalid_proj_id = project.id + 1

    vcs = tu.seed_random_vcs(project.id, current_user.id)
    design_group = tu.seed_random_design_group(project.id)

    # Act
    tu.seed_random_formulas(project.id, vcs.id, design_group.id, current_user.id)

    res = client.get(
        f"/api/cvs/project/{invalid_proj_id}/vcs/{vcs.id}/design-group/{design_group.id}/formulas/all",
        headers=std_headers,
    )

    # Assert
    assert res.status_code == 404

    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_get_all_formulas_invalid_vcs(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    vcs = tu.seed_random_vcs(project.id, current_user.id)
    invalid_vcs_id = vcs.id + 1

    design_group = tu.seed_random_design_group(project.id)

    # Act
    tu.seed_random_formulas(project.id, vcs.id, design_group.id, current_user.id)

    res = client.get(
        f"/api/cvs/project/{project.id}/vcs/{invalid_vcs_id}/design-group/{design_group.id}/formulas/all",
        headers=std_headers,
    )

    # Assert
    assert res.status_code == 404

    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def get_all_formulas_invalid_design_group(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    vcs = tu.seed_random_vcs(project.id, current_user.id)

    design_group = tu.seed_random_design_group(project.id)
    invalid_dg_id = design_group.id + 1

    # Act
    tu.seed_random_formulas(project.id, vcs.id, design_group.id, current_user.id)

    res = client.get(
        f"/api/cvs/project/{project.id}/vcs/{vcs.id}/design-group/{invalid_dg_id}/formulas/all",
        headers=std_headers,
    )

    # Assert
    assert res.status_code == 404

    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_edit_formulas(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    vcs = tu.seed_random_vcs(project.id, current_user.id)
    design_group = tu.seed_random_design_group(project.id)

    formulas = tu.seed_random_formulas(
        project.id, vcs.id, design_group.id, current_user.id, 1
    )

    value_driver = tu.seed_random_value_driver(current_user.id, project.id)
    external_factor = tu.seed_random_external_factor(project.id)

    # Act

    time = (
        "2+{vd:"
        + str(value_driver.id)
        + ',"'
        + str(value_driver.name)
        + '"}+{vd:'
        + str(value_driver.id)
        + ',"'
        + str(value_driver.name)
        + '"}'
    )
    cost = "2+{ef:" + str(external_factor.id) + ',"' + str(external_factor.name) + '"}'
    revenue = (
        "20+{vd:"
        + str(value_driver.id)
        + ',"'
        + str(value_driver.name)
        + '"}+{ef:'
        + str(external_factor.id)
        + ',"'
        + str(external_factor.name)
        + '"}'
    )

    time_unit = tu.random_time_unit()
    rate = tu.random_rate_choice()

    res = client.put(
        f"/api/cvs/project/{project.id}/vcs/{vcs.id}/design-group/{formulas[0].design_group_id}/formulas",
        headers=std_headers,
        json=[
            {
                "vcs_row_id": formulas[0].vcs_row_id,
                "time": {"text": time, "latex": time, "comment": ""},
                "time_unit": time_unit,
                "cost": {"text": cost, "latex": cost, "comment": ""},
                "revenue": {"text": revenue, "latex": revenue, "comment": ""},
                "rate": rate,
            }
        ],
    )

    res_get = client.get(
        f"/api/cvs/project/{project.id}/vcs/{vcs.id}/design-group/{design_group.id}/formulas/all",
        headers=std_headers,
    )

    # Assert
    assert res.status_code == 200
    assert res_get.json()[0]["used_value_drivers"][0]["id"] == value_driver.id
    assert res_get.json()[0]["used_external_factors"][0]["id"] == external_factor.id

    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_edit_formulas_no_optional(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    vcs = tu.seed_random_vcs(project.id, current_user.id)
    design_group = tu.seed_random_design_group(project.id)

    # Act
    formulas = tu.seed_random_formulas(
        project.id, vcs.id, design_group.id, current_user.id, 1
    )

    time = testutils.random_str(10, 200)
    time_unit = tu.random_time_unit()
    cost = testutils.random_str(10, 200)
    revenue = testutils.random_str(10, 200)
    rate = tu.random_rate_choice()

    res = client.put(
        f"/api/cvs/project/{project.id}/vcs/{vcs.id}/design-group/{formulas[0].design_group_id}/formulas",
        headers=std_headers,
        json=[
            {
                "vcs_row_id": formulas[0].vcs_row_id,
                "time": {"text": time, "latex": time, "comment": ""},
                "time_unit": time_unit,
                "cost": {"text": cost, "latex": cost, "comment": ""},
                "revenue": {"text": revenue, "latex": revenue, "comment": ""},
                "rate": rate,
            }
        ],
    )

    # Assert
    assert res.status_code == 200
    assert res.json() == True

    # Cleanup
    tu.delete_formulas(
        project.id,
        [(formula.vcs_row_id, formula.design_group_id) for formula in formulas],
    )
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_edit_formulas_invalid_dg(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    vcs = tu.seed_random_vcs(project.id, current_user.id)
    vcs_rows = tu.seed_vcs_table_rows(current_user.id, project.id, vcs.id, 1)
    if vcs_rows == None:
        raise Exception
    row_id = vcs_rows[0].id
    design_group = tu.seed_random_design_group(project.id)
    dg_invalid_id = design_group.id + 1

    # Act
    time = testutils.random_str(10, 200)
    time_unit = tu.random_time_unit()
    cost = testutils.random_str(10, 200)
    revenue = testutils.random_str(10, 200)
    rate = tu.random_rate_choice()

    res = client.put(
        f"/api/cvs/project/{project.id}/vcs/{vcs.id}/design-group/{dg_invalid_id}/formulas",
        headers=std_headers,
        json=[
            {
                "vcs_row_id": row_id,
                "time": {"text": time, "latex": time, "comment": ""},
                "time_unit": time_unit,
                "cost": {"text": cost, "latex": cost, "comment": ""},
                "revenue": {"text": revenue, "latex": revenue, "comment": ""},
                "rate": rate,
            }
        ],
    )

    # Assert
    assert res.status_code == 404

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_edit_formulas_invalid_vcs_row(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    vcs = tu.seed_random_vcs(project.id, current_user.id)
    vcs_rows = tu.seed_vcs_table_rows(current_user.id, project.id, vcs.id, 1)
    if vcs_rows == None:
        raise Exception
    row_id = vcs_rows[0].id + 1
    design_group = tu.seed_random_design_group(project.id)

    # Act
    time = testutils.random_str(10, 200)
    time_unit = tu.random_time_unit()
    cost = testutils.random_str(10, 200)
    revenue = testutils.random_str(10, 200)
    rate = tu.random_rate_choice()

    res = client.put(
        f"/api/cvs/project/{project.id}/vcs/{vcs.id}/design-group/{design_group.id}/formulas",
        headers=std_headers,
        json=[
            {
                "vcs_row_id": row_id,
                "time": {"text": time, "latex": time, "comment": ""},
                "time_unit": time_unit,
                "cost": {"text": cost, "latex": cost, "comment": ""},
                "revenue": {"text": revenue, "latex": revenue, "comment": ""},
                "rate": rate,
            }
        ],
    )

    # Assert
    assert res.status_code == 404

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_edit_formulas_invalid_project(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    invalid_proj_id = project.id + 1

    vcs = tu.seed_random_vcs(project.id, current_user.id)
    vcs_rows = tu.seed_vcs_table_rows(current_user.id, project.id, vcs.id, 1)
    if vcs_rows is None:
        raise Exception
    row_id = vcs_rows[0].id
    design_group = tu.seed_random_design_group(project.id)

    # Act
    time = testutils.random_str(10, 200)
    time_unit = tu.random_time_unit()
    cost = testutils.random_str(10, 200)
    revenue = testutils.random_str(10, 200)
    rate = tu.random_rate_choice()

    res = client.put(
        f"/api/cvs/project/{invalid_proj_id}/vcs/{vcs.id}/design-group/{design_group.id}/formulas",
        headers=std_headers,
        json=[
            {
                "vcs_row_id": row_id,
                "time": {"text": time, "latex": time, "comment": ""},
                "time_unit": time_unit,
                "cost": {"text": cost, "latex": cost, "comment": ""},
                "revenue": {"text": revenue, "latex": revenue, "comment": ""},
                "rate": rate,
            }
        ],
    )

    # Assert
    assert res.status_code == 404

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_delete_formulas(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    vcs = tu.seed_random_vcs(project.id, current_user.id)
    design_group = tu.seed_random_design_group(project.id)

    # Act
    formulas = tu.seed_random_formulas(
        project.id, vcs.id, design_group.id, current_user.id, 1
    )

    res = client.delete(
        f"/api/cvs/project/{project.id}/vcs-row/{formulas[0].vcs_row_id}/design-group/{formulas[0].design_group_id}/formulas",
        headers=std_headers,
    )

    # Assert
    assert res.status_code == 200

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_delete_formulas_invalid_project(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    invalid_proj_id = project.id + 1

    vcs = tu.seed_random_vcs(project.id, current_user.id)
    design_group = tu.seed_random_design_group(project.id)

    # Act
    formulas = tu.seed_random_formulas(
        project.id, vcs.id, design_group.id, current_user.id, 1
    )

    res = client.delete(
        f"/api/cvs/project/{invalid_proj_id}/vcs-row/{formulas[0].vcs_row_id}/design-group/"
        f"{formulas[0].design_group_id}/formulas",
        headers=std_headers,
    )

    # Assert
    assert res.status_code == 404

    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_delete_formulas_invalid_vcs_row(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    vcs = tu.seed_random_vcs(project.id, current_user.id)
    design_group = tu.seed_random_design_group(project.id)

    # Act
    formulas = tu.seed_random_formulas(
        project.id, vcs.id, design_group.id, current_user.id, 1
    )
    invalid_vcs_row_id = formulas[0].vcs_row_id + 1

    res = client.delete(
        f"/api/cvs/project/{project.id}/vcs-row/{invalid_vcs_row_id}/design-group/{formulas[0].design_group_id}/formulas",
        headers=std_headers,
    )

    # Assert
    assert res.status_code == 404

    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_delete_formulas_invalid_design_group(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    vcs = tu.seed_random_vcs(project.id, current_user.id)
    design_group = tu.seed_random_design_group(project.id)
    invalid_dg_id = design_group.id + 1

    # Act
    formulas = tu.seed_random_formulas(
        project.id, vcs.id, design_group.id, current_user.id, 1
    )

    res = client.delete(
        f"/api/cvs/project/{project.id}/vcs-row/{formulas[0].vcs_row_id}/design-group/{invalid_dg_id}/formulas",
        headers=std_headers,
    )

    # Assert
    assert res.status_code == 400

    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_get_vcs_dg_pairs(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    vcss = [tu.seed_random_vcs(project.id, current_user.id) for _ in range(4)]
    dgs = [tu.seed_random_design_group(project.id) for _ in range(4)]

    formulas = []
    for i in range(4):
        formulas.append(
            tu.seed_random_formulas(
                project.id, vcss[i].id, dgs[i].id, current_user.id, 1
            )
        )

    # Act
    res = client.get(
        f"/api/cvs/project/{project.id}/vcs/design/formula-pairs", headers=std_headers
    )

    # Assert
    assert res.status_code == 200
    assert len(res.json()) == len(vcss) * len(dgs)

    # Cleanup
    tu.delete_formulas(
        project.id,
        [(formula[0].vcs_row_id, formula[0].design_group_id) for formula in formulas],
    )
    [tu.delete_design_group(project.id, design_group.id) for design_group in dgs]
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id for vcs in vcss])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_get_vcs_dg_pairs_invalid_project(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    invalid_proj_id = project.id + 1

    vcss = [tu.seed_random_vcs(project.id, current_user.id) for _ in range(4)]
    dgs = [tu.seed_random_design_group(project.id) for _ in range(4)]

    formulas = []
    for i in range(4):
        formulas.append(
            tu.seed_random_formulas(
                project.id, vcss[i].id, dgs[i].id, current_user.id, 1
            )
        )

        # Act
    res = client.get(
        f"/api/cvs/project/{invalid_proj_id}/vcs/design/formula-pairs",
        headers=std_headers,
    )

    # Assert
    assert res.status_code == 404

    # Cleanup
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)


def test_get_all_formulas_name_change(client, std_headers, std_user):
    # Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    vcs = tu.seed_random_vcs(project.id, current_user.id)
    vcs_rows = tu.seed_vcs_table_rows(current_user.id, project.id, vcs.id, 1)
    design_group = tu.seed_random_design_group(project.id)
    value_driver = tu.seed_random_value_driver(current_user.id, project.id)
    value_driver2 = tu.seed_random_value_driver(current_user.id, project.id)
    external_factor = tu.seed_random_external_factor(project.id)

    time = (
        "2+{vd:"
        + str(value_driver.id)
        + ',"'
        + str(value_driver.name)
        + '"}+{vd:'
        + str(value_driver.id)
        + ',"'
        + str(value_driver.name)
        + '"}'
    )
    time_latex = f"2+\\class{{vd}}{{\\identifier{{vd:{str(value_driver.id)}}}{{\\text{{{str(value_driver.name)}}}}}}}+\\class{{vd}}{{\\identifier{{vd:{str(value_driver.id)}}}{{\\text{{{str(value_driver.name)}}}}}}}"
    cost = "2+{ef:" + str(external_factor.id) + ',"' + str(external_factor.name) + '"}'
    cost_latex = f"2+\\class{{ef}}{{\\identifier{{ef:{str(external_factor.id)}}}{{\\text{{{str(external_factor.name)}}}}}}}"
    revenue = (
        "20+{vd:"
        + str(value_driver2.id)
        + ',"'
        + str(value_driver2.name)
        + '"}+{ef:'
        + str(external_factor.id)
        + ',"'
        + str(external_factor.name)
        + '"}'
    )
    revenue_latex = f"20+\\class{{vd}}{{\\identifier{{vd:{str(value_driver2.id)}}}{{\\text{{{str(value_driver2.name)}}}}}}}+\\class{{ef}}{{\\identifier{{vd:{str(external_factor.id)}}}{{\\text{{{str(external_factor.name)}}}}}}}"

    rate = tu.random_rate_choice()

    time_unit = tu.random_time_unit()

    # Act
    formula_post = connect_model.FormulaRowPost(
        vcs_row_id=vcs_rows[0].id,
        time=connect_model.Formula(text=time, latex=time_latex, comment=""),
        time_unit=time_unit,
        cost=connect_model.Formula(text=cost, latex=cost_latex, comment=""),
        revenue=connect_model.Formula(text=revenue, latex=revenue_latex, comment=""),
        rate=rate,
    )

    impl_connect.edit_formulas(project.id, vcs.id, design_group.id, [formula_post])

    impl_vcs.edit_value_driver(
        value_driver.id,
        vcs_model.ValueDriverPut(name="new VD name", unit="VD unit"),
        current_user.id,
    )
    impl_market_input.update_external_factor(
        project.id,
        market_input_model.ExternalFactor(
            id=external_factor.id, name="new EF name", unit="EF unit"
        ),
    )
    impl_vcs.delete_value_driver(project.id, value_driver2.id)

    res = client.get(
        f"/api/cvs/project/{project.id}/vcs/{vcs.id}/design-group/{design_group.id}/formulas/all",
        headers=std_headers,
    )

    # Assert
    assert res.status_code == 200
    assert "new VD name [VD unit]" in res.json()[0]["time"]["text"]
    assert "new VD name [VD unit]" in res.json()[0]["time"]["latex"]
    assert "new EF name [EF unit]" in res.json()[0]["cost"]["text"]
    assert "new EF name [EF unit]" in res.json()[0]["cost"]["latex"]
    assert "UNDEFINED [N/A]" in res.json()[0]["revenue"]["text"]
    assert "UNDEFINED [N/A]" in res.json()[0]["revenue"]["latex"]

    # Cleanup
    tu.delete_design_group(project.id, design_group.id)
    tu.delete_VCS_with_ids(current_user.id, project.id, [vcs.id])
    tu.delete_project_by_id(project.id, current_user.id)
    tu.delete_vd_from_user(current_user.id)
