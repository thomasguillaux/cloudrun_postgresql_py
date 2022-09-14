import os

import pg8000
import sqlalchemy
from google.cloud.sql.connector import Connector, IPTypes


def connect_with_connector_auto_iam_authn() -> sqlalchemy.engine.base.Engine:

    instance_connection_name = os.environ["INSTANCE_CONNECTION_NAME"]  
    db_iam_user = os.environ["DB_IAM_USER"]  
    db_name = os.environ["DB_NAME"]  

    ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

    # initialize Cloud SQL Python Connector object
    connector = Connector()

    def getconn() -> pg8000.dbapi.Connection:
        conn: pg8000.dbapi.Connection = connector.connect(
            instance_connection_name,
            "pg8000",
            user=db_iam_user,
            db=db_name,
            enable_iam_auth=True,
            ip_type=ip_type,
        )
        return conn

    pool = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,  # 30 seconds
        pool_recycle=1800,  # 30 minutes
    )
    return pool

