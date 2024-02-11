class CVSProjectNotFoundException(Exception):
    pass


class CVSProjectFailedToUpdateException(Exception):
    pass


class CVSProjectFailedDeletionException(Exception):
    pass


class CVSProjectNoMatchException(Exception):
    pass


class SubProjectFailedDeletionException(Exception):
    pass


class CVSProjectImageInvalidFormatException(Exception):
    pass