import json
from pydoc import cli
import random as r

import pytest
from fastapi import HTTPException

import sedbackend.apps.cvs.implementation as impl
import sedbackend.apps.cvs.models as models
import tests.apps.cvs.testutils as tu
import tests.testutils as testutils
import sedbackend.apps.core.users.implementation as impl_users

def test_create_value_driver_no_unit(client, std_headers, std_user):
    #Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    #Act
    name = testutils.random_str(5,50)
    res = client.post(f'api/cvs/project/{project.id}/value-driver/create',
                    headers = std_headers,
                    json = {
                        "name": name
                    })
    
    # Assert
    assert res.status_code == 200
    assert res.json()["name"] == name

    #cleanup
    tu.delete_vd_by_id(res.json()["id"], project.id, current_user.id)
    tu.delete_project_by_id(project.id, current_user.id)

def test_create_value_driver_with_unit(client, std_headers, std_user):
    #Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)

    #Act
    name = testutils.random_str(5,50)
    unit = testutils.random_str(1,30)
    res = client.post(f'api/cvs/project/{project.id}/value-driver/create',
                    headers = std_headers,
                    json = {
                        "name": name,
                        "unit": unit
                    })
    
    # Assert
    assert res.status_code == 200
    assert res.json()["name"] == name
    assert res.json()["unit"] == unit

    #cleanup
    tu.delete_vd_by_id(res.json()["id"], project.id, current_user.id)
    tu.delete_project_by_id(project.id, current_user.id)

def test_edit_value_driver(client, std_headers, std_user):
    #Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    value_driver = tu.seed_random_value_driver(current_user.id, project.id) # Will currently break here because a value driver is created without unit

    #Act
    name = testutils.random_str(5,50)
    unit = testutils.random_str(1,30)
    res = client.put(f'/api/cvs/project/{project.id}/value-driver/{value_driver.id}/edit',
                    headers=std_headers,
                    json = {
                        "name": name,
                        "unit": unit
                    })
    
    #Assert
    assert res.status_code == 200
    assert res.json()["name"] == name

    #cleanup
    tu.delete_vd_by_id(res.json()["id"], project.id, current_user.id)
    tu.delete_project_by_id(project.id, current_user.id)

def test_delete_value_driver(client, std_headers, std_user):
    #Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    value_driver = tu.seed_random_value_driver(current_user.id, project.id) # Will currently break here because a value driver is created without unit

    #Act
    res = client.delete(f'api/cvs/project/{project.id}/value-driver/{value_driver.id}/delete')

    #Assert
    assert res.status_code == 200

    #Cleanup
    tu.delete_project_by_id(project.id, current_user.id)

def test_get_value_driver(client, std_headers, std_user):
    #Setup
    current_user = impl_users.impl_get_user_with_username(std_user.username)
    project = tu.seed_random_project(current_user.id)
    value_driver = tu.seed_random_value_driver(current_user.id, project.id) # Will currently break here because a value driver is created without unit

    #Act
    res = client.get(f'/api/cvs/project/{project.id}/value-driver/get/{value_driver.id}')

    #Assert
    assert res.status_code == 200

    #Cleanup
    tu.delete_vd_by_id(value_driver.id, project.id, current_user.id)
    tu.delete_project_by_id(project.id, current_user.id)

    