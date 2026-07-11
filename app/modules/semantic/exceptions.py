class SemanticDomainException(Exception):
    """Base exception for the Semantic Domain Layer."""
    pass

class RegistryException(SemanticDomainException):
    """Raised when an error occurs during component registration or lookup."""
    pass

class FactoryException(SemanticDomainException):
    """Raised when the factory fails to instantiate a component."""
    pass

class ValidationException(SemanticDomainException):
    """Raised when semantic validation fails critically."""
    pass

class ProcessorException(SemanticDomainException):
    """Raised when a processor encounters an unrecoverable error."""
    pass

class ResolverException(SemanticDomainException):
    """Raised when a resolver fails to resolve relationships."""
    pass

class EnrichmentException(SemanticDomainException):
    """Raised when AI/ML enrichment fails."""
    pass

class PipelineException(SemanticDomainException):
    """Raised when the orchestrator pipeline fails."""
    pass
