class SynqError(Exception):
    """Base class for application-level errors that map to a specific HTTP response."""

    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class CalendarNotConnectedError(SynqError):
    status_code = 401


class AIServiceError(SynqError):
    status_code = 500
