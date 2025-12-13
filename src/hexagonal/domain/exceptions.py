class DomainException(Exception):
    def __init__(self, message: str = ""):
        self.message = f"Domain Exception: {message}"


class DomainValueError(DomainException, ValueError):
    def __init__(self, message: str = ""):
        self.message = f"Domain Value Error: {message}"


class AggregateNotFound(DomainException):
    def __init__(self, message: str = ""):
        self.message = f"Aggregate Not Found Exception: {message}"


class AggregateVersionMismatch(DomainException):
    def __init__(self, message: str = ""):
        self.message = f"Aggregate Version Mismatch Exception: {message}"


class HandlerNotRegistered(DomainException):
    def __init__(self, message: str = ""):
        self.message = f"Handler Not Registered Exception: {message}"


class HandlerNotFound(DomainException):
    def __init__(self, message: str = ""):
        self.message = f"Handler Not Found Exception: {message}"


class HandlerAlreadyRegistered(DomainException):
    def __init__(self, message: str = ""):
        self.message = f"Handler Already Registered Exception: {message}"


class InfrastructureNotInitialized(DomainException, RuntimeError):
    def __init__(self, message: str = ""):
        self.message = f"Infrastructure Not Initialized Exception: {message}"
