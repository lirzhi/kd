# ES = {
#     "hosts": "http://elasticsearch:9200",
#     "username": "elastic",
#     "password": "1433223aa"
# }

# REDIS = {
#     "host": "redis",
#     "port": 6379,
#     "db": 1,
#     "username": "default", 
#     "password": "1433223aa"
# }

# MYSQL = {
#     "host": "mysql",
#     "port": 3306,
#     "user": "root",
#     "password": "1433223aa",
#     "database": "rag",
#     "pool_size": 40,
#     "max_overflow": 20
# }

# SVR_QUEUE_NAME = "handle_info_queue"
# SVR_QUEUE_RETENTION = 60*60
# SVR_QUEUE_MAX_LEN = 1024
# SVR_CONSUMER_NAME = "handle_info_consumer"
# SVR_CONSUMER_GROUP_NAME = "handle_info_consumer_group"
# ES = {
#     "hosts": "http://127.0.0.1:9200",
#     "username": "elastic",
#     "password": "1433223aa"
# }

# REDIS = {
#     "host": "127.0.0.1",
#     "port": 6379,
#     "db": 1,
#     "username": "default", 
#     "password": "1433223aa"
# }

# MYSQL = {
#     "host": "127.0.0.1",
#     "port": 3306,
#     "user": "root",
#     "password": "1433223aa",
#     "database": "rag",
#     "pool_size": 40,
#     "max_overflow": 20
# }

# SVR_QUEUE_NAME = "handle_info_queue"
# SVR_QUEUE_RETENTION = 60*60
# SVR_QUEUE_MAX_LEN = 1024
# SVR_CONSUMER_NAME = "handle_info_consumer"
# SVR_CONSUMER_GROUP_NAME = "handle_info_consumer_group"
HOST = "127.0.0.1"

ES = {
    "hosts": f"http://{HOST}:9200",
    "username": "elastic",
    "password": "1433223aa"
}

REDIS = {
    "host": HOST,
    "port": 6379,
    "db": 1,
    "username": "default", 
    "password": "1433223aa"
}

MYSQL = {
    "host": HOST,
    "port": 3306,
    "user": "root",
    "password": "1433223aa",
    "database": "rag",
    "pool_size": 40,
    "max_overflow": 20
}

SVR_QUEUE_NAME = "handle_info_queue"
SVR_QUEUE_RETENTION = 60*60
SVR_QUEUE_MAX_LEN = 1024
SVR_CONSUMER_NAME = "handle_info_consumer"
SVR_CONSUMER_GROUP_NAME = "handle_info_consumer_group"