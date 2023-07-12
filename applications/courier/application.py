import csv
import io
from datetime import datetime
from functools import wraps

from flask import Flask, request, Response, jsonify, make_response
from configuration import Configuration
from models import database, Category, Product, OrderProduct, Order
from email.utils import parseaddr
from sqlalchemy import func
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity, verify_jwt_in_request
from sqlalchemy import and_

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


def roleCheck(role):
    def innerRole(function):
        @wraps(function)
        def decorator(*arguments, **keywordArguments):
            verify_jwt_in_request()
            claims = get_jwt()
            if (("roles" in claims) and (role in claims["roles"])):
                return function(*arguments, **keywordArguments)
            else:
                return jsonify(msg='Missing Authorization Header'), 401

        return decorator

    return innerRole


@application.route('/pick_up_order', methods=['POST'])
@roleCheck('courier')
def pick_up_order():
    if 'Authorization' not in request.headers:
        return make_response(jsonify(msg='Missing Authorization header')), 401

    if not request.is_json:
        return jsonify(), 400

    order_id = request.json.get('id', None)

    if not order_id:
        return jsonify({"message": "Missing order id."}), 400

    try:
        order_id = int(order_id)
    except ValueError:
        return jsonify({"message": "Invalid order id."}), 400

    order = Order.query.filter(Order.id == order_id).first()
    if order_id <= 0 or not order or order.status != 'CREATED':
        return jsonify({"message": "Invalid order id."}), 400

    order.status = "PENDING"
    database.session.add(order)
    database.session.commit()
    return Response(status=200)


@application.route('/orders_to_deliver', methods=['GET'])
@roleCheck('courier')
def orders_to_deliver():
    if 'Authorization' not in request.headers:
        return make_response(jsonify(msg='Missing Authorization header')), 401

    undelivered_orders = Order.query.filter(Order.status == "CREATED")

    orders_data = [{'id': order.id, 'email': order.user} for order in undelivered_orders]

    return jsonify({'orders': orders_data}), 200


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host='0.0.0.0', port=5003)
