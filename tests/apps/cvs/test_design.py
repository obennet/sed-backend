import random as r

import pytest
from fastapi import HTTPException

import sedbackend.apps.cvs.design.implementation
import sedbackend.apps.cvs.implementation as impl
import sedbackend.apps.cvs.models as models
import sedbackend.apps.cvs.vcs.implementation
import tests.apps.cvs.testutils as tu
import tests.testutils as testutils
import sedbackend.apps.core.users.implementation as impl_users

def test_create_design(client, std_headers, std_user):
    #Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    current_project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(current_user.id, current_project.id)

    #Act
    res = client.post(f'/api/cvs/project/{current_project.id}/vcs/{vcs.id}/design/create', 
                    headers=std_headers,
                    json={
                        "name": testutils.random_str(5,50),
                        "description": testutils.random_str(20,200)
                    })
    
    # Assert
    assert res.status_code == 200

    #Cleanup
    tu.delete_design_by_id(res.json()["id"], current_project.id, vcs.id, current_user.id)
    tu.delete_VCS_with_ids([vcs.id],current_project.id, current_user.id)
    tu.delete_project_by_id(current_project.id, current_user.id)

def test_get_design(client, std_headers, std_user):
    #setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    current_project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(current_user.id, current_project.id)
    design = tu.seed_random_designs(current_project.id, vcs.id, current_user.id, 1)[0]

    #Act
    res = client.get(f'/api/cvs/project/{current_project.id}/vcs/{vcs.id}/design/get/{design.id}', headers=std_headers)

    #Assert
    assert res.status_code == 200
    assert res.json()["id"] == design.id

    #Cleanup 
    tu.delete_design_by_id(design.id, current_project.id, vcs.id, current_user.id)
    tu.delete_VCS_with_ids([vcs.id],current_project.id, current_user.id)
    tu.delete_project_by_id(current_project.id, current_user.id)

def test_get_all_designs(client, std_headers, std_user):
    #setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(current_user.id, project.id)
    designs = tu.seed_random_designs(project.id, vcs.id, current_user.id)

    amount_of_designs = len(designs)
    #Act
    
    res = client.get(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/design/get/all', headers=std_headers)


    #Assert
    assert res.status_code == 200
    assert amount_of_designs == len(res.json()["chunk"])

    #cleanup
    tu.delete_designs(designs, project.id, vcs.id, current_user.id)
    tu.delete_VCS_with_ids([vcs.id], project.id, current_user.id)
    tu.delete_project_by_id(project.id, current_user.id)

def test_delete_design(client, std_headers, std_user):
    #Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(current_user.id, project.id)
    design = tu.seed_random_designs(project.id, vcs.id, current_user.id, 1)[0]

    #Act
    res = client.delete(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/design/{design.id}/delete', headers=std_headers)

    #Assert
    assert res.status_code == 200
    #Should probably assert that it actually is gone too

    #Cleanup
    tu.delete_VCS_with_ids([vcs.id], project.id, current_user.id)
    tu.delete_project_by_id(project.id, current_user.id)

def test_edit_design(client, std_headers, std_user):
    #Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(current_user.id, project.id)
    design = tu.seed_random_designs(project.id, vcs.id, current_user.id, 1)[0]

    #Act
    new_name = testutils.random_str(5,50)
    res = client.put(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/design/{design.id}/edit',
                    headers=std_headers,
                    json={
                        "name": new_name,
                        "description": design.description
                    })
    
    #Assert
    assert res.status_code == 200
    assert res.json()["name"] != design.name
    assert res.json()["name"] == new_name
    assert res.json()["description"] == design.description
    
    #Cleanup
    tu.delete_design_by_id(design.id, project.id, vcs.id, current_user.id)
    tu.delete_VCS_with_ids([vcs.id], project.id, current_user.id)
    tu.delete_project_by_id(project.id, current_user.id)

def test_create_quantified_objective(client, std_headers, std_user):
    #Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(current_user.id, project.id)
    design = tu.seed_random_designs(project.id, vcs.id, current_user.id, 1)[0]
    vd = tu.seed_random_value_driver(current_user.id, project.id)

    #Act
    res = client.post(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/design/{design.id}/value_driver/{vd.id}/quantified-objective/create',
                    headers=std_headers,
                    json={
                        "name": testutils.random_str(5,50),
                        "property": r.uniform(0.5, 100),
                        "unit": testutils.random_str(5, 50)
                    })
    
    #Assert
    assert res.status_code == 200

    #Cleanup
    tu.delete_qo_and_vd(res.json()["id"], vd.id, project.id, vcs.id, design.id, current_user.id)
    tu.delete_design_by_id(design.id, project.id, vcs.id, current_user.id)
    tu.delete_VCS_with_ids([vcs.id], project.id, current_user.id)
    tu.delete_project_by_id(project.id, current_user.id)

def test_get_quantified_objective(client, std_headers, std_user):
    #Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(current_user.id, project.id)
    design = tu.seed_random_designs(project.id, vcs.id, current_user.id, 1)[0]
    qo = tu.seed_random_quantified_objectives(project.id, vcs.id, design.id, current_user.id, 1)[0]

    #Act
    res = client.get(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/design/{design.id}/value_driver/{qo.value_driver.id}/quantified_objective/get/{qo.id}', headers=std_headers)

    #Assert
    assert res.status_code == 200

    #Cleanup
    tu.delete_qo_and_vd(qo.id, qo.value_driver.id, project.id, vcs.id, design.id, current_user.id)
    tu.delete_design_by_id(design.id, project.id, vcs.id, current_user.id)
    tu.delete_VCS_with_ids([vcs.id], project.id, current_user.id)
    tu.delete_project_by_id(project.id, current_user.id)

def test_get_all_quantified_objectives(client, std_headers, std_user):
    #Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(current_user.id, project.id)
    design = tu.seed_random_designs(project.id, vcs.id, current_user.id, 1)[0]
    quantified_objectives = tu.seed_random_quantified_objectives(project.id, vcs.id, design.id, current_user.id, 10)

    #Act
    res = client.get(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/design/{design.id}/quantified_objective/get/all', headers=std_headers)

    #Assert
    assert res.status_code == 200
    assert len(quantified_objectives) == len(res.json())

    #Cleanup
    tu.delete_quantified_objectives(quantified_objectives, project.id, vcs.id, design.id, current_user.id)
    tu.delete_design_by_id(design.id, project.id, vcs.id, current_user.id)
    tu.delete_VCS_with_ids([vcs.id], project.id, current_user.id)
    tu.delete_project_by_id(project.id, current_user.id)

def test_delete_quantified_objective(client, std_headers, std_user):
    #setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(current_user.id, project.id)
    design = tu.seed_random_designs(project.id, vcs.id, current_user.id, 1)[0]
    qo = tu.seed_random_quantified_objectives(project.id, vcs.id, design.id, current_user.id, 1)[0]

    #Act
    res = client.delete(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/design/{design.id}/value_driver/{qo.value_driver.id}/quantified-objective/{qo.id}/delete', headers=std_headers)

    
    #Assert
    assert res.status_code == 200
    assert sedbackend.apps.cvs.vcs.implementation.get_value_driver(qo.value_driver.id, project.id, current_user.id) is not None

    #Cleanup
    tu.delete_vd_by_id(qo.value_driver.id, project.id, current_user.id)
    tu.delete_design_by_id(design.id, project.id, vcs.id, current_user.id)
    tu.delete_VCS_with_ids([vcs.id], project.id, current_user.id)
    tu.delete_project_by_id(project.id, current_user.id)

def test_edit_quantified_objective(client, std_headers, std_user):
    #setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(current_user.id, project.id)
    design = tu.seed_random_designs(project.id, vcs.id, current_user.id, 1)[0]
    qo = tu.seed_random_quantified_objectives(project.id, vcs.id, design.id, current_user.id, 1)[0]

    #Act
    new_name = testutils.random_str(5,50)
    new_unit = testutils.random_str(5,50)
    res = client.put(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/design/{design.id}/value_driver/{qo.value_driver.id}/quantified-objective/{qo.id}/edit',
                    headers=std_headers,
                    json={
                        "name": new_name,
                        "property": qo.property,
                        "unit": new_unit
                    })
    
    #Assert
    assert res.status_code == 200
    assert res.json()["name"] == new_name
    assert res.json()["property"]  == qo.property
    assert res.json()["unit"] != qo.unit

    #Cleanup
    tu.delete_qo_and_vd(qo.id, qo.value_driver.id, project.id, vcs.id, design.id, current_user.id)
    tu.delete_design_by_id(design.id, project.id, vcs.id, current_user.id)
    tu.delete_VCS_with_ids([vcs.id], project.id, current_user.id)
    tu.delete_project_by_id(project.id, current_user.id)


def test_delete_qo_when_design_deleted(client, std_headers, std_user):
    #Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    vcs = tu.seed_random_vcs(current_user.id, project.id)
    design = tu.seed_random_designs(project.id, vcs.id, current_user.id, 1)[0]
    quantified_objectives = tu.seed_random_quantified_objectives(project.id, vcs.id, design.id, current_user.id, 10)

    #Act
    res = client.delete(f'/api/cvs/project/{project.id}/vcs/{vcs.id}/design/{design.id}/delete', headers=std_headers)

    #Assert
    assert res.status_code == 200
    not_exist = False
    try:
        sedbackend.apps.cvs.design.implementation.get_all_quantified_objectives(design.id, project.id, vcs.id, current_user.id)
    except(HTTPException):
        not_exist = True
    assert not_exist

    #Cleanup 
    tu.delete_VCS_with_ids([vcs.id], project.id, current_user.id)
    tu.delete_project_by_id(project.id, current_user.id)

