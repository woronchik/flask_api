from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from celery import Celery
from elasticsearch import Elasticsearch

app = Flask(__name__)

host = '127.0.0.1'
user = 'woron'
password = '21011991w26021967W'
db_name = 'postgres'

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{user}:{password}@{host}/{db_name}'
app.config['CACHE_TYPE'] = 'memcached'
app.config['CACHE_MEMCACHED_SERVERS'] = ['host:port']
app.config['JWT_SECRET_KEY'] = 'secret'

db = SQLAlchemy(app)
cache = Cache(app)
jwt = JWTManager(app)
celery = Celery(app.name, broker='pyamqp://user:password@host/vhost')
es = Elasticsearch(['http://host:port'])

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

@celery.task
def process_file(file_path):
    pass

@app.route('/register', methods=['POST'])
def register():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    user = User(email=email, password=password)
    db.session.add(user)
    db.session.commit()
    return jsonify(msg='User created'), 201

@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    user = User.query.filter_by(email=email, password=password).first()
    if not user:
        return jsonify(msg='Bad email or password'), 401
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200

@app.route('/upload', methods=['POST'])
@jwt_required()
def upload():
    file = request.files['file']
    filename = file.filename
    file_path = f'/path/to/upload/folder/{filename}'
    file.save(file_path)
    process_file.delay(file_path)
    return jsonify(msg='File uploaded and being processed'), 202

@app.route('/file/<int:file_id>', methods=['GET'])
@jwt_required()
def file(file_id):
    return jsonify(file=file), 200

if __name__ == '__main__':
    app.run()