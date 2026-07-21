class IngestionException(Exception): pass
class ProviderException(IngestionException): pass
class ValidationException(IngestionException): pass
class PipelineException(IngestionException): pass

class ProviderUnavailableException(ProviderException):
    def __init__(self, provider: str, reason: str, required_version: str = "N/A"):
        self.provider = provider
        self.reason = reason
        self.required_version = required_version
        super().__init__(f"Provider {provider} unavailable: {reason}")

class DependencyUnavailableException(ProviderException): pass
class UnsupportedRuntimeException(ProviderException): pass
