# Gunicorn configuration for Kiri Research Labs
# Optimized for Google Cloud 1GB RAM VM

import multiprocessing

# Bind to socket
bind = "127.0.0.1:8000"

# Workers - use 2 for 1GB RAM to avoid OOM
workers = 2
worker_class = "sync"
worker_connections = 100
timeout = 120
keepalive = 5

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
