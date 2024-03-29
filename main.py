import psycopg2, struct ,os
import json
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import timedelta ,datetime
from azure.storage.blob import BlobServiceClient
from flask_swagger_ui import get_swaggerui_blueprint

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

blob_service_client = BlobServiceClient.from_connection_string(conn_str=os.getenv('AZURE_CONNECTION_STORAGE'))
try:
    container_client = blob_service_client.get_container_client(container="linkupabj")
    container_client.get_container_properties()
except Exception as e:
    container_client = blob_service_client.create_container("linkupabj")

#--------------------------
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/static/swagger.json'  # Our API url (can of course be a local resource)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Test application"
    },
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
#--------------------------

#Page d'acceuil
@app.route("/")
def index():
    return "<h1>Hello LINKUP!</h1>"

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

#Route pour l'update des users
@app.route('/users', methods=['PUT'])
@jwt_required()
def put_user():
    email = request.json.get("email")
    public = request.json.get("is_public")
    password = request.json.get("password")

    current_user_id = get_jwt_identity()
    try:
        conn = connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET email = '"+email+"', is_public = '"+public+"', password = '"+password+"' WHERE id = '"+str(current_user_id)+"'")
        conn.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)
    return jsonify({"State": 400})

#Route pour le delete des users
@app.route("/users",methods=['DELETE'])
@jwt_required()
def delete_users():
    current_user_id = get_jwt_identity()
    try:
        conn = connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id='"+str(current_user_id)+"'")
        conn.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)
        return jsonify({"State": 400})

#POST
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
        if email == None:
            cursor.execute("SELECT * FROM post p INNER JOIN users u on u.id = p.users WHERE u.is_public = true;")
        else:
            cursor.execute("SELECT * FROM post p INNER JOIN users u on u.id = p.users WHERE u.is_public = true and u.email ='"+email+"';")
        informations = cursor.fetchall()
    except Exception as e:
        print(e)
        
    datas=[]
    for information in informations:
        datas.append({
        "id": information[0],
        "contenu": information[1],
        "postAt": information[2],
        "user": information[3],
        "attachments": get_attachemet(information[0])
    })
    return jsonify(datas)

#Route pour le delete de post et des attachments si il y a
@app.route("/posts",methods=['DELETE'])
@jwt_required()
def delete_posts():
    post_id = request.json.get('id')
    current_user_id = get_jwt_identity()
    attachements = []
    try:
        conn = connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attachements a USING  post p WHERE p.id = a.post and a.post='"+str(post_id)+"' and p.users='"+str(current_user_id)+"';")
        cursor.execute("DELETE FROM post p WHERE p.id='"+str(post_id)+"' and p.users='"+str(current_user_id)+"';")
        conn.commit()
        return jsonify({"State": 201})
    except Exception as e:
        print(e)
        return jsonify({"State": 400})

#ATTACHMENT
#Route de publication des attachments 
@app.route('/attachments', methods=['POST'])
@jwt_required()
def post_attachments():
    current_user_id = get_jwt_identity()
    description= request.form['description']
    postid = request.form['postid']

    try:
        fichier = request.files['namefile']
        namefile = fichier.filename.replace(" ", "")
        blob_client = container_client.get_blob_client(namefile)
        blob_client.upload_blob(namefile)
        name = "https://linkupstorageabj.blob.core.windows.net/linkupabj/" + namefile
        conn = connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO attachements(fileurl, description , post)
            VALUES ('"""+name+"""','"""+description+"""','"""+str(postid)+"""');
        """)
        conn.commit()
       
        return jsonify({"State": 201})
    except Exception as e:
        print(e)
        return jsonify({"State": 400,
                    "error": str(e)})

#DATABASE
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

#Fonction permettant d'obtenir les attachments d'un post
def get_attachemet(id):
    informations = []
    try:
        conn = connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attachements a WHERE a.post = "+str(id)+";")
        informations = cursor.fetchall()
    except Exception as e:
        print(e)
        
    datas=[]
    for information in informations:
        datas.append({
        "id": information[0],
        "fileurl": information[1],
        "description": information[2],
    })
    return datas



def connection():
    conn_string = "host={0} user={1} dbname={2} port=5432 password={3} sslmode={4}".format(host, user, dbname, password, sslmode)
    return  psycopg2.connect(conn_string)
