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
