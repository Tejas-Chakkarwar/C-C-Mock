class CypherCircleError(Exception):
    """Base error exposed by the application data-access boundary."""


class DatabaseUnavailableError(CypherCircleError):
    pass


class DataIntegrityError(CypherCircleError):
    pass


class QueryError(CypherCircleError):
    pass

