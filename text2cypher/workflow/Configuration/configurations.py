# Vendorizado do CyVerACT (Androna et al., IPM 2026), sob CC BY-SA 4.0.
# Acrescentado o campo timeout_execucao; hoje serve só de referência dos campos do config.
# A config schema is useful for indicating which fields are available in the configurable dict
# inside the config

from typing_extensions import TypedDict

class ConfigSchema(TypedDict):
    model: str
    model_name: str
    attempts_w_filtered: int # how many times to try with the filtered schema to correct the cypher query of it has errors
    total_attempts: int # how many times to try to correct the cypher query of it has errors, in total (with filtered and full schema)
    timeout_execucao: float  # limite (s) para executar a query no Neo4j
