import datetime
import logging
import os
from typing import Dict

import sqlalchemy
from flask import Flask, Response, request

from connect_connector import connect_with_connector
from connect_connector_auto_iam_authn import \
    connect_with_connector_auto_iam_authn
from connect_unix import connect_unix_socket
from hash_manager import Hash

app = Flask(__name__)

logger = logging.getLogger()


def init_connection_pool() -> sqlalchemy.engine.base.Engine:

    if os.environ.get("INSTANCE_UNIX_SOCKET"):
        return connect_unix_socket()

    if os.environ.get("INSTANCE_CONNECTION_NAME"):
        return (
            connect_with_connector_auto_iam_authn()
            if os.environ.get("DB_IAM_USER")
            else connect_with_connector()
        )

    raise ValueError(
        "Missing database connection type. Please define one of INSTANCE_HOST, INSTANCE_UNIX_SOCKET, or INSTANCE_CONNECTION_NAME"
    )


# create 'hashes' table in database if it does not already exist
def migrate_db(db: sqlalchemy.engine.base.Engine) -> None:
    with db.connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS hashes"
            "( hash_id SERIAL NOT NULL, time_cast timestamp NOT NULL, "
            "hash VARCHAR(256) NOT NULL, PRIMARY KEY (hash_id) );"
        )

db = None

@app.before_first_request
def init_db() -> sqlalchemy.engine.base.Engine:
    global db
    db = init_connection_pool()
    migrate_db(db)

@app.route("/", methods=["GET"])
def ping():
    return "Pong!"


@app.route("/get-hashes", methods=["POST"])
def get_hashes() -> Response:
    data = request.get_json()
    return save_hash(db, data)

def save_hash(db: sqlalchemy.engine.base.Engine, data: dict) -> Response:
    time_cast = datetime.datetime.now(tz=datetime.timezone.utc)
    
    if data is None:
        logger.warning(f"Received invalid 'data' property: '{data}'")
        return Response(
            response="Invalid data specified.",
            status=400,
        )

    command = Hash()
    hash = command.get_new_hash(data)
   
    try:
        with db.connect() as conn:
           
            check_presence_of_hash = sqlalchemy.text(
                "SELECT * FROM hashes WHERE hash=:hash"
             )
            check_result = conn.execute(check_presence_of_hash, hash=hash).fetchone()
            if check_result is None:
                add_latest_hash = sqlalchemy.text(
                    "INSERT INTO hashes (time_cast, hash) VALUES (:time_cast, :hash)"
                )
                conn.execute(add_latest_hash, time_cast=time_cast, hash=hash)
                print('New NFTs have been listed')
            else:
                print('There are no new NFTs')

    except Exception as e:

        logger.exception(e)
        return Response(
            status=500,
            response="Unable to successfully monitor websites! Please check the "
            "application logs for more details.",
        )

    return Response(
        status=200,
        response=f"Hash successfully added for '{data}' at time {time_cast}!",
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
