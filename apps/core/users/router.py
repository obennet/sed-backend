from fastapi import APIRouter, Depends, Security

from apps.core.authentication.utils import verify_token, get_current_active_user
from apps.core.authentication.models import UserAuth
from apps.core.users.models import User
from apps.core.users.implementation import impl_get_users, impl_post_user, impl_delete_user_from_db, \
    impl_get_user_with_id, impl_get_users_me


router = APIRouter()


@router.get("/me",
            summary="Returns logged in user")
async def get_users_me(current_user: User = Depends(get_current_active_user)):
    return impl_get_users_me(current_user)


@router.get("/list",
            summary="Lists all users",
            description="Produces a list of users in alphabetical order",
            dependencies=[Security(verify_token, scopes=['admin'])])
async def get_users(segment_length: int, index: int):
    return impl_get_users(segment_length, index)


@router.get("/id/{user_id}",
            summary="Get user with ID",
            dependencies=[Security(verify_token, scopes=['admin'])])
async def get_user_with_id(user_id: int):
    return impl_get_user_with_id(user_id)


@router.post("/new",
             summary="Create new user",
             dependencies=[Security(verify_token, scopes=['admin'])])
async def post_user(user: UserAuth):
    return impl_post_user(user)


@router.delete("/id/{user_id}/delete",
               summary="Remove user from DB",
               dependencies=[Security(verify_token, scopes=['admin'])])
async def delete_user_from_db(user_id: int):
    return impl_delete_user_from_db(user_id)
