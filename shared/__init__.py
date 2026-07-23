"""
Shared package used across all microservices in the distributed search engine:
crawler, indexer, search-api.

Keep this package dependency-light — every service imports it, so avoid pulling
in heavy libraries here (those belong in the service that actually needs them).
"""
