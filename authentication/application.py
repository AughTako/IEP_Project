from flask import Flask, request, Response, jsonify, make_response
from configuration import Configuration
from models import database, User, UserRole
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity
from sqlalchemy import and_

application = Flask(__name__)
application.config.from_object(Configuration)

import re


def is_valid_email(email):
    # Regular expression pattern for email validation
    pattern = r'^[\w\.-]+@[\w-]+\.[a-zA-Z]{2,}$'

    # Match the email against the pattern
    match = re.match(pattern, email)

    # Return True if the email matches the pattern, False otherwise
    return bool(match)


@application.route("/register_courier", methods=["POST"])
def register_courier():
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0
    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0

    if forenameEmpty:
        return make_response(jsonify(message='Field forename is missing.')), 400
    if surnameEmpty:
        return make_response(jsonify(message='Field surname is missing.')), 400
    if emailEmpty:
        return make_response(jsonify(message='Field email is missing.')), 400
    if passwordEmpty:
        return make_response(jsonify(message='Field password is missing.')), 400

    if not is_valid_email(email):
        return make_response(jsonify(message='Invalid email.')), 400
    if (len(password) < 8):
        return make_response(jsonify(message='Invalid password.')), 400

    alreadyExists = User.query.filter(User.email == email).first()
    if alreadyExists:
        return make_response(jsonify(message='Email already exists.')), 400

    user = User(email=email, password=password, forename=forename, surname=surname)
    database.session.add(user)
    database.session.commit()

    userRole = UserRole(userId=user.id, roleId=2)
    database.session.add(userRole)
    database.session.commit()

    return Response("Registration successful!", status=200)


@application.route("/register_customer", methods=["POST"])
def register_customer():
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0
    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0

    if forenameEmpty:
        return make_response(jsonify(message='Field forename is missing.')), 400
    if surnameEmpty:
        return make_response(jsonify(message='Field surname is missing.')), 400
    if emailEmpty:
        return make_response(jsonify(message='Field email is missing.')), 400
    if passwordEmpty:
        return make_response(jsonify(message='Field password is missing.')), 400

    if not is_valid_email(email):
        return make_response(jsonify(message='Invalid email.')), 400
    if (len(password) < 8):
        return make_response(jsonify(message='Invalid password.')), 400

    alreadyExists = User.query.filter(User.email == email).first()
    if alreadyExists:
        return make_response(jsonify(message='Email already exists.')), 400

    user = User(email=email, password=password, forename=forename, surname=surname)
    database.session.add(user)
    database.session.commit()

    userRole = UserRole(userId=user.id, roleId=3)
    database.session.add(userRole)
    database.session.commit()

    return Response("Registration successful!", status=200)


jwt = JWTManager(application)


@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0

    if (emailEmpty):
        return make_response(jsonify(message='Field email is missing.')), 400
    if (passwordEmpty):
        return make_response(jsonify(message='Field password is missing.')), 400

    if not is_valid_email(email):
        return make_response(jsonify(message='Invalid email.')), 400

    user = User.query.filter(and_(User.email == email, User.password == password)).first()

    if not user:
        return make_response(jsonify(message="Invalid credentials.")), 400

    additionalClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": [str(role) for role in user.roles]
    }

    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims)
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims)

    # return Response ( accessToken, status = 200 )
    return make_response(jsonify(accessToken=accessToken, refreshToken=refreshToken)), 200


@application.route("/delete", methods=['POST'])
@jwt_required()
def delete():
    if 'Authorization' not in request.headers:
        return make_response(jsonify(msg='Missing Authorization header')), 401
    identity = get_jwt_identity()
    user = User.query.filter(User.email == identity).first()
    if not user:
        return make_response(jsonify(message="Unknown user.")), 400
    database.session.delete(user)
    database.session.commit()
    return Response(status=200)


@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()

    additionalClaims = {
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"]
    }

    return Response(create_access_token(identity=identity, additional_claims=additionalClaims), status=200)


if (__name__ == "__main__"):
    database.init_app(application)
    application.run(debug=True, host='0.0.0.0', port=5000)
