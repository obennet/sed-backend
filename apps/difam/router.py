from typing import List

from fastapi import APIRouter, Security, Depends


router = APIRouter()


@router.get("/{spid}",
            summary="Returns overview of DIFAM project",
            description="Returns overview of DIFAM project",)
async def get_difam_project(spid: int):
    """
    Returns overview difam project information
    """
    return None
