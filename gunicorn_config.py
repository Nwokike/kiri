# Gunicorn configuration for Kiri Research Labs
# Optimized for Google Cloud 1GB RAM VM

# Bind to socket
bind = "127.0.0.1:8000"

# Workers - 2 workers for 1GB RAM constraint
# Using gthread for better I/O handling without async overhead
workers = 2
worker_class = "gthread"
threads = 2
worker_connections = 100
timeout = 120
keepalive = 5

# Memory leak prevention - recycle workers after N requests
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "kiri"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Graceful timeout
graceful_timeout = 30
