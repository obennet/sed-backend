from typing import Any
from datetime import datetime
import os

from pydantic import BaseModel
from fastapi.datastructures import UploadFile


class StoredFilePost(BaseModel):
    filename: str
    owner_id: int
    extension: str
    file_object: Any
    subproject_id: int

    @staticmethod
    def import_fastapi_file(file: UploadFile, current_user_id: int, subproject_id: int):
        filename = file.filename
        extension = os.path.splitext(file.filename)[1]
        return StoredFilePost(filename=filename,
                              extension=extension,
                              owner_id=current_user_id,
                              file_object=file.file,
                              subproject_id=subproject_id)


class StoredFileEntry(BaseModel):
    id: int
    temp: bool
    filename: str
    insert_timestamp: datetime
    owner_id: int
    extension: str
    subproject_id: int


class StoredFile(BaseModel):
    id: int
    temp: bool
    uuid: str
    filename: str
    insert_timestamp: datetime
    directory: str
    owner_id: int
    extension: str


class StoredFilePath(BaseModel):
    id: int
    filename: str
    path: str
    extension: str


class StoredFileReadout(BaseModel):
    id: int
    filename: str
    content: str
