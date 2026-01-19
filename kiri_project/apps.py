"""
Kiri Project App Configuration.
Handles SQLite PRAGMA settings via connection signals (Django 6.0+ compatible).
"""
from django.apps import AppConfig


class KiriProjectConfig(AppConfig):
    name = 'kiri_project'
    verbose_name = 'Kiri Research Labs'
    
    def ready(self):
        # Register SQLite connection signal for PRAGMAs
        from django.db.backends.signals import connection_created
        connection_created.connect(configure_sqlite_connection)


def configure_sqlite_connection(sender, connection, **kwargs):
    """
    Configure SQLite PRAGMAs on each connection.
    These settings optimize for 1GB RAM production environment.
    """
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        # WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL;")
        # Wait up to 5 seconds for locks
        cursor.execute("PRAGMA busy_timeout=5000;")
        # Faster syncing (slightly less safe, but WAL protects us)
        cursor.execute("PRAGMA synchronous=NORMAL;")
        # ~8MB cache in pages (page_size is typically 4KB)
        cursor.execute("PRAGMA cache_size=2000;")
        # Store temp tables in memory
        cursor.execute("PRAGMA temp_store=MEMORY;")
        # 128MB memory-mapped I/O for faster reads
        cursor.execute("PRAGMA mmap_size=134217728;")
        # Limit WAL file size to 64MB
        cursor.execute("PRAGMA journal_size_limit=67108864;")
