"""
Indexer service: consumes crawled pages from RabbitMQ, cleans and processes
the HTML into plain text, and indexes the result into Elasticsearch with a
BM25-ready mapping.
"""
