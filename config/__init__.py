# Initialize PyMySQL as MySQLdb for MySQL database engine support
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

# TiDB Compatibility: Bypass Django's MySQL 8.4+ minimum version check
# TiDB identifies as MySQL 8.0.11 for compatibility with MySQL 8.0 client drivers
try:
    from django.db.backends.mysql.base import DatabaseWrapper
    DatabaseWrapper.check_database_version_supported = lambda self: None
except Exception:
    pass
