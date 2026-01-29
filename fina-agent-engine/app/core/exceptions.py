"""Custom exception hierarchy for FINA Agent Engine.

This module defines all custom exceptions used throughout the application,
providing clear error handling and appropriate HTTP status codes.
"""


class FinaAgentException(Exception):
    """Base exception for FINA Agent.
    
    All custom exceptions in the application should inherit from this class.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code to return when this exception is raised
    """
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ConfigurationError(FinaAgentException):
    """Configuration or environment variable error.
    
    Raised when there are issues with application configuration,
    missing environment variables, or invalid configuration values.
    """
    
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class MCPConnectionError(FinaAgentException):
    """MCP Server connection failed.
    
    Raised when unable to establish or maintain connection with
    the MCP (Model Context Protocol) server.
    """
    
    def __init__(self, message: str):
        super().__init__(message, status_code=503)


class IngestionError(FinaAgentException):
    """PDF ingestion or vector database error.
    
    Raised when there are issues processing PDF documents or
    interacting with the vector database.
    """
    
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class AuthorizationError(FinaAgentException):
    """Authorization/governance error.
    
    Raised when authorization checks fail, such as invalid supervisors
    or segregation of duties violations.
    """
    
    def __init__(self, message: str):
        super().__init__(message, status_code=403)


class ValidationError(FinaAgentException):
    """Input validation error.
    
    Raised when user input fails validation checks.
    """
    
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class ThreadNotFoundError(FinaAgentException):
    """Thread ID not found in database.
    
    Raised when attempting to access a non-existent conversation thread.
    """
    
    def __init__(self, thread_id: str):
        super().__init__(f"Thread ID '{thread_id}' not found", status_code=404)


class ConflictOfInterestError(AuthorizationError):
    """Conflict of interest in approval process.
    
    Raised when the same person attempts to both create and approve a request.
    """
    
    def __init__(self):
        super().__init__("Conflict of Interest: Creator and Approver must be different")
