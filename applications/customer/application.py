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


@application.route('/search', methods=["GET"])
@roleCheck(role='customer')
def search():
    if 'Authorization' not in request.headers:
        return jsonify(msg='Missing Authorization Header'), 401

    product_name = request.args.get('name')
    category_name = request.args.get('category')

    query = Product.query
    if product_name:
        query = query.filter(Product.name.ilike(f'%{product_name}%'))
    if category_name:
        query = query.filter(Product.categories.any(Category.name.ilike(f'%{category_name}%')))

    results = query.all()

    categories = set()
    products = []

    for result in results:
        product_categories = [category.name for category in result.categories]
        categories.update(product_categories)
        product = {
            'categories': product_categories,
            'id': result.id,
            'name': result.name,
            'price': result.price
        }
        products.append(product)

    # Fetch all categories when no search parameters are provided
    if not product_name and not category_name:
        all_categories = Category.query.all()
        categories = [category.name for category in all_categories]

    response_data = {
        'categories': list(categories),
        'products': products
    }

    return jsonify(response_data), 200


@application.route('/order', methods=["POST"])
@roleCheck(role='customer')
def create_order():
    try:
        access_token = request.headers.get('Authorization')
    except:
        return Response(status=400)
    if 'Authorization' not in request.headers:
        return jsonify({'msg': 'Missing Authorization Header'}), 401
    if not request.is_json:
        return jsonify({'message': 'Request body is missing or is not a JSON object'}), 400

    data = request.get_json()

    if 'requests' not in data:
        return jsonify({'message': 'Field requests is missing.'}), 400

    requests = data['requests']

    for i, request_data in enumerate(requests):
        if 'id' not in request_data:
            return jsonify({'message': f'Product id is missing for request number {i}.'}), 400
        if 'quantity' not in request_data:
            return jsonify({'message': f'Product quantity is missing for request number {i}.'}), 400

        product_id = request_data['id']
        quantity = request_data['quantity']

        if not isinstance(product_id, int) or product_id <= 0:
            return jsonify({'message': f'Invalid product id for request number {i}.'}), 400

        product_exists = Product.query.filter_by(id=product_id).first()
        if not product_exists:
            return jsonify({'message': f'Invalid product for request number {i}.'}), 400

        if not isinstance(quantity, int) or quantity <= 0:
            return jsonify({'message': f'Invalid product quantity for request number {i}.'}), 400

    total_price = 0.0
    for request_data in requests:
        product_id = request_data['id']
        quantity = request_data['quantity']
        product = Product.query.filter_by(id=product_id).first()
        total_price += product.price * quantity

    order = Order(total_price=total_price, status="CREATED", dateOf=datetime.now(), user=get_jwt_identity())
    order_id = order.id
    database.session.add(order)
    database.session.commit()

    for request_data in requests:
        product_id = request_data['id']
        quantity = request_data['quantity']
        product = Product.query.get(product_id)  # Mozda visak???
        order_product = OrderProduct(order_id=order_id, product_id=product_id, quantity=quantity)
        order.order_products.append(order_product)

    database.session.commit()

    return jsonify({'id': order.id}), 200


@application.route('/status', methods=['GET'])
@roleCheck('customer')
def get_order_status():
    try:
        access_token = request.headers.get('Authorization')
    except:
        return Response(status=400)
    if not access_token:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    orders = Order.query.filter_by(user=get_jwt_identity()).all()

    orders_list = []
    for order in orders:
        order_data = {
            "products": [],
            "price": order.total_price,
            "status": order.status,
            "timestamp": order.dateOf
        }
        for order_product in order.order_products:
            product_data = {
                "categories": [category.name for category in order_product.product.categories],
                "name": order_product.product.name,
                "price": order_product.product.price,
                "quantity": order_product.quantity
            }
            order_data["products"].append(product_data)
        orders_list.append(order_data)

    response = {"orders": orders_list}

    return jsonify(response), 200


@application.route('/delivered', methods=['POST'])
@roleCheck('customer')
def delivered():
    if 'Authorization' not in request.headers:
        return make_response(jsonify(msg='Missing Authorization header')), 401

    order_id = request.json.get('id', None)

    if not order_id:
        return jsonify({'message': 'Missing order id.'}), 400

    try:
        order_id = int(request.json.get('id'))
    except ValueError:
        return jsonify({"message": "Invalid order id."}), 400

    order = Order.query.filter(Order.id == order_id).first()
    
    if order_id <= 0 or not order or order.status != 'PENDING':
        return jsonify({'message': 'Invalid order id.'}), 400

    order.status = 'COMPLETE'
    database.session.add(order)
    database.session.commit()

    return Response(status=200)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host='0.0.0.0', port=5002)
