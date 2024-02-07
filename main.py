import psycopg2, struct ,os
import json
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager

host = os.environ["AZURE_SQL_HOST"]
dbname = os.environ["AZURE_SQL_DB"]
user = os.environ["AZURE_SQL_USER"]
password = os.environ["AZURE_SQL_PASSWORD"]
sslmode = "require"


app = Flask(__name__)
@app.route("/")
def index():
    return "<h1>Hello LINKUP!</h1>"


@app.route('/post', methods=['DELETE'])
def delete_post():
    uid = request.args.get("id", None)

    current_user_id = get_jwt_identity()
    try:
        conn = connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM post
            WHERE users='"""+current_user_id+"""' and id= '"""+uid+"""'
        """)
        cursor.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)

    return jsonify({"State": 400})



@app.route("/start", methods=['GET'])
def start():
    try:
        conn = connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(180) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                is_public BOOLEAN NOT NULL DEFAULT false,
                is_admin BOOLEAN NOT NULL DEFAULT false
            );
        """)
        conn.commit()
    except Exception as e:
        print(e)

    try:
        conn = connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE post (
                id SERIAL PRIMARY KEY,
                textContents VARCHAR(255) NOT NULL,
                postAt VARCHAR(255) NOT NULL,
                users int NOT NULL,
                FOREIGN KEY (users) REFERENCES users(id)
            );
        """)
        conn.commit()
    except Exception as e:
        print(e)
    
    try:
        conn = connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE attachements (
                id SERIAL PRIMARY KEY,
                fileurl VARCHAR(255) NOT NULL,
                description VARCHAR(255) NOT NULL,
                post int NOT NULL,
                FOREIGN KEY (post) REFERENCES post(id)
            );
        """)
        conn.commit()
    except Exception as e:
        print(e)

    return "<h1>start fini</h1>"


if __name__ == "__main__":
    app.run(debug=True)


def connection():
    conn_string = "host={0} user={1} dbname={2} port=5432 password={3} sslmode={4}".format(host, user, dbname, password, sslmode)
    return  psycopg2.connect(conn_string)
