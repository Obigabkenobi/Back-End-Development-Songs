from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# GET HEALTH STATUS
######################################################################
@app.route("/health", methods=["GET"])
def get_health():
    songs = list(db.songs.find({}, {"_id": 0}))

    if songs:
        return {"status": "OK"}, 200

######################################################################
# GET COUNT
######################################################################
@app.route("/count", methods=["GET"])
def get_count():
    count = db.songs.count_documents({})

    return {"count": count}, 200

######################################################################
# GET SONGS
######################################################################
@app.route("/song", methods=["GET"])
def songs():
    songs = list(db.songs.find({}, {"_id": 0}))
    
    if songs:       
        return {"songs": songs}, 200

######################################################################
# GET SONG BY ID
######################################################################
@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    song = db.songs.find_one({"id": id})
    
    if song:
        return jsonify({"song": song}), 200
    
    return {"message": "song with id not found"}, 404 

######################################################################
# CREATE SONG
######################################################################
@app.route("/song", methods=["POST"])
def create_song():
    data = request.get_json()
    song = db.songs.find_one({"id": data["id"]})

    if song:
        return {"Message": f"song with id {song['id']} already present"}, 302

    insert_id: InsertOneResult = db.songs.insert_one(data)
    return {"inserted id": parse_json(insert_id.inserted_id)}, 201

######################################################################
# UPDATE SONG
######################################################################
@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    data = request.json
    song = db.songs.find_one({"id": id})

    if song == None:
        return {"message": "song not found"}, 404

    updated_data = {"$set": data}
    result = db.songs.update_one({"id": id}, updated_data)

    if result.modified_count == 0:
        return {"message": "song found, but nothing updated"}, 200
    else:
        return parse_json(db.songs.find_one({"id": id})), 201

######################################################################
# DELETE SONG
######################################################################
@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    result = db.songs.delete_one({"id": id})

    if result.deleted_count == 0:
        return {"message": "song not found"}, 404
    else:
        return "", 204
    

