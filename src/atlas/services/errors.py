class ServiceError(Exception):
    """Base error for service use cases. API and CLI map this to user-facing failures."""


class NotFoundError(ServiceError):
    def __init__(self, entity: str, key: str | int):
        self.entity = entity
        self.key = key
        super().__init__(f"{entity} {key!r} not found")


class AlreadyExistsError(ServiceError):
    def __init__(self, entity: str, key: str):
        self.entity = entity
        self.key = key
        super().__init__(f"{entity} {key!r} already exists")


class ValidationError(ServiceError):
    pass


class ConflictError(ServiceError):
    """The request is valid but clashes with current state (e.g. deleting a quest item that
    still has children, or completing one that is not eligible without override)."""


class UpstreamError(ServiceError):
    """A remote service Atlas depends on (such as a link preview) could not be read."""
