import psycopg2, struct ,os
import json
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import timedelta ,datetime

host = os.environ["AZURE_SQL_HOST"]
dbname = os.environ["AZURE_SQL_DB"]
user = os.environ["AZURE_SQL_USER"]
password = os.environ["AZURE_SQL_PASSWORD"]
sslmode = "require"
ACCESS_EXPIRES = timedelta(hours=1)

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.environ["APP_SUPER_KEY"] 
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = ACCESS_EXPIRES
jwt = JWTManager(app)

#Page d'acceuil
@app.route("/")
def index():
    return "<h1>Hello LINKUP!</h1>"

#Route pour le delete de post
@app.route('/post', methods=['DELETE'])
@jwt_required() 
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
        conn.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)

    return jsonify({"State": 400})

#USERS
#Route pour login
@app.route("/login",methods=['POST'])
def post_login():
    email = request.json.get('email')
    password = request.json.get('password')

    data_login=[]
    try:
        conn = connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users where email='"+email+"' and password='"+password+"';")
        data_login = cursor.fetchall()
    except Exception as e:
        print(e)

    if len(data_login)!=1:
         return jsonify({"Message": "Erreur dans l'email ou dans le password"}), 401
    
    token_access = create_access_token(identity=data_login[0][0])
    return jsonify({ "token": token_access, "uid": data_login[0][0] })

#Route pour le register
@app.route("/register",methods=['POST'])
def post_register():
    email = request.json.get('email')
    password = request.json.get('password')

    data_login=[]
    try:
        conn = connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users(email,password) VALUES ('"+email+"','"+password+"');")
        conn.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)
        return jsonify({"State": 400})
 
#Route pour le get des users
@app.route("/users",methods=['GET'])
def get_all_users():
    email = request.json.get('email',None)

    informations = []
    try:
        conn = connection()
        cursor = conn.cursor()
        if email != None:
            cursor.execute("SELECT * FROM users WHERE email='"+email+"';")
        else:
            cursor.execute("SELECT * FROM users;")
        informations = cursor.fetchall()
    except Exception as e:
        print(e)
        
    datas=[]
    print(len(informations))
    for information in informations:
        datas.append({
        "id": information[0],
        "email": information[1],
        "is_public": information[3],
        "is_admin": information[4]
    })
    return jsonify(datas)


@app.route('/users', methods=['PUT'])
@jwt_required()
def put_user():
    email = request.json.get("email", None)
    public = request.json.get("is_public", None)
    password = request.json.get("password", None)

    current_user_id = get_jwt_identity()
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET email = '"+email+"', is_public = '"+public+"', password = '"+password+"' WHERE id = '"+current_user_id+"'")
        cursor.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)
    return jsonify({"State": 400})


#Route pour le get des users
@app.route("/users",methods=['DELETE'])
@jwt_required()
def get_all_users():
    current_user_id = get_jwt_identity()
    try:
        conn = connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id='"+current_user_id+"'")
        conn.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)
        return jsonify({"State": 400})

#Route pour la creation d'un post
@app.route("/posts",methods=['POST'])
@jwt_required() 
def post_posts():
    contenu = request.json.get('contenu')
    formatted_date = datetime.now().strftime("%d, %B, %Y")
    print(formatted_date)
    current_user_id = get_jwt_identity()
    data_login=[]
    try:
        conn = connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO post(textContents,postAt,users) VALUES ('"+contenu+"','"+str(formatted_date)+"','"+str(current_user_id)+"');")
        conn.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)
        return jsonify({"State": 400})

#Route pour recuperer les posts d'un user
@app.route("/posts",methods=['GET'])
@jwt_required() 
def get_posts():
    email = request.json.get('email',None)
    informations = []
    try:
        conn = connection()
        cursor = conn.cursor()
        if email != None:
            cursor.execute("SELECT * FROM posts p INNER JOIN users u on u.id = p.users WHERE u.is_public = true;")
        else:
            cursor.execute("SELECT * FROM posts p INNER JOIN users u on u.id = p.users WHERE u.is_public = true and u.email ='"+email+"';")
        informations = cursor.fetchall()
    except Exception as e:
        print(e)
        
    datas=[]
    print(len(informations))
    for information in informations:
        datas.append({
        "id": information[0],
        "contenu": information[1],
        "postAt": information[2],
        "user": information[3]
    })
    return jsonify(datas)

#Route pour recuperer les posts d'un user
@app.route("/attchment",methods=['GET'])
@jwt_required() 
def get_posts():


#Route de creation de table
@app.route("/creation_table", methods=['GET'])
def creation_table():
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
