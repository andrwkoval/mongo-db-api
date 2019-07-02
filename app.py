from flask import Flask, jsonify, request, abort
from pymongo import MongoClient, ReturnDocument
import datetime

client = MongoClient()  # mongo client to work with MongoDB
db = client.mydb  # select database
border = db.border  # select collection


# field validation in json request
def check_field(obj, col):
    if col in obj:
        if obj[col] is None:
            abort(422)
        return obj[col]


app = Flask(__name__)

# get 10 last person records
@app.route("/last", methods=["GET"])
def get_ten_last():
    # find all records in db (ObjectId is ignored)
    cursor = border.find(projection={'_id': False})
    records = [i for i in cursor]
    # if a number of records is less than 10, then return all the records, return 10 last otherwise
    a = 0 if len(records) < 10 else 10
    return jsonify(records[-a:]), 200

# update or insert new person and their border crossing info
@app.route("/", methods=["POST"])
def add_person():
    # get information about person from json request to update or create in database
    first_name = check_field(request.json, "first_name")
    last_name = check_field(request.json, "last_name")
    birth = check_field(request.json, "birth_date")
    status = check_field(request.json, "status")
    address = check_field(request.json, "address")
    phone_number = check_field(request.json, "phone_number")
    height = check_field(request.json, "height")
    nationality = check_field(request.json, "nationality")
    eye_color = check_field(request.json, "eye_color")
    forbidden_staff = check_field(request.json, "forbidden_staff")
    allowed = check_field(request.json, "allowed")

    # type validation of info about forbidden stuff
    if not (isinstance(forbidden_staff, list) or isinstance(forbidden_staff, str)):
        abort(422)

    # make filter dict to find a record to update
    find_filter = {"first_name": first_name, "last_name": last_name, "birth_date": birth}

    # identify current data and time as a unique border crossing
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # try to get a record about specific person
    doc = border.find_one(find_filter)

    # if person crossed the border earlier
    if doc is not None:
        # update the identifier with unique id of person in db
        find_filter = {'_id': doc['_id']}
        # update the list of border crossings with new crossing attempt
        time_stamp = doc["archive"]
        time_stamp[now] = allowed

        # if person had a list of withdrawn stuff, then add previous stuff to current
        if isinstance(forbidden_staff, list):
            forbidden_staff += doc["forbidden_staff"]
        # create new list of withdrawn stuff
        else:
            temp = [forbidden_staff]
            temp += doc["forbidden_staff"]
            forbidden_staff = temp
    else:
        # if person hasn't crossed the border create new list of staff and new archive of previous crossing attempts
        time_stamp = {now: allowed}
        forbidden_staff = [forbidden_staff]

    # find specific person using filter got earlier, then trying to update if such person exists in db,
    # else insert new record with person and her first border crossing returning updated record
    result = border.find_one_and_update(find_filter, {
        "$set": {
            "first_name": first_name,
            "last_name": last_name,
            "birth_date": birth,
            "status": status,
            "address": address,
            "phone_number": phone_number,
            "height": height,
            "nationality": nationality,
            "eye_color": eye_color,
            "forbidden_staff": list(set(forbidden_staff)),
            "archive": time_stamp
        }
    }, upsert=True, projection={'_id': False}, return_document=ReturnDocument.AFTER)

    return jsonify(result), 201


if __name__ == '__main__':
    app.run(debug=True)
