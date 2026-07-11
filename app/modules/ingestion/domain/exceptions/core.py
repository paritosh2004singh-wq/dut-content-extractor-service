class IngestionException(Exception): pass
class ProviderException(IngestionException): pass
class ValidationException(IngestionException): pass
class PipelineException(IngestionException): pass
