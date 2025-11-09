class BadUsageError(Exception):
    pass


class RemoteResourceNotFoundError(BadUsageError):
    pass


class UnexpectedRuntimeError(Exception):
    pass
