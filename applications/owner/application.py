import csv
import io
from functools import wraps
import json
from flask import Flask, request, Response, jsonify, make_response
from configuration import Configuration
from models import database, Category, Product, OrderProduct, Order, ProductCategory
from email.utils import parseaddr
from sqlalchemy import func, select, case, desc
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity, verify_jwt_in_request
from sqlalchemy import and_, or_

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


@application.route('/update', methods=["POST"])
@roleCheck(role='owner')
def update():
    if 'Authorization' not in request.headers:
        return jsonify(msg='Missing Authorization Header'), 401

    if 'file' not in request.files:
        return jsonify(message='Field file is missing.'), 400

    file = request.files['file']
    existing_product_names = set()
    products = {}
    categories = set()

    for line_number, line in enumerate(file.readlines()):
        line = line.strip().decode('utf-8')
        values = line.split(',')

        if len(values) != 3:
            database.session.rollback()
            return jsonify(message=f'Incorrect number of values on line {line_number}.'), 400

        categories_list = values[0].strip().split('|')
        product_name = values[1].strip()
        price = values[2].strip()

        try:
            price = float(price)
            if price <= 0:
                database.session.rollback()
                return jsonify(message=f'Incorrect price on line {line_number}.'), 400
        except ValueError:
            database.session.rollback()
            return jsonify(message=f'Incorrect price on line {line_number}.'), 400

        if product_name in existing_product_names:
            database.session.rollback()
            return jsonify(message=f'Product {product_name} already exists.'), 400

        existing_product_check = Product.query.filter_by(name=product_name).first()
        if existing_product_check:
            database.session.rollback()
            return jsonify(message=f'Product {product_name} already exists.'), 400

        existing_product_names.add(product_name)

        for category_name in categories_list:
            categories.add(category_name)

        products[product_name] = {"categories": categories_list, "price": price}

    try:
        category_objects = [Category(name=category_name) for category_name in categories]
        database.session.bulk_save_objects(category_objects)
        database.session.commit()

        for product_name, data in products.items():
            product = Product(name=product_name, price=data["price"])
            product.categories = Category.query.filter(Category.name.in_(data["categories"])).all()
            database.session.add(product)
        database.session.commit()
        return Response(status=200)
    except Exception:
        database.session.rollback()
        return jsonify(message='Error occurred during database update.'), 500


from sqlalchemy.orm import class_mapper

@application.route('/product_statistics', methods=['GET'])
@roleCheck('owner')
def product_statistics():
    if 'Authorization' not in request.headers:
        return jsonify(msg='Missing Authorization header'), 401

    product_info = database.session.query(
        Product.name,
        func.sum(
            case([(Order.status == "COMPLETE", OrderProduct.quantity)], else_=0)
        ).label("sold"),
        func.sum(
            case([(Order.status != "COMPLETE", OrderProduct.quantity)], else_=0)
        ).label("waiting")
    ).join(OrderProduct, Product.id == OrderProduct.product_id) \
        .join(Order, OrderProduct.order_id == Order.id) \
        .group_by(Product.name).all()

    statistics = []
    for product in product_info:
        category_dict = {
            "name": product.name,
            "sold": int(product.sold),
            "waiting": int(product.waiting)
        }
        statistics.append(category_dict)

    return jsonify({"statistics": statistics}), 200

@application.route('/category_statistics', methods=["GET"])
@roleCheck(role='owner')
def statistics():
    if 'Authorization' not in request.headers:
        return jsonify(msg='Missing Authorization header'), 401

    category_info = database.session.query(
        Category.name,
        func.sum(case([(Order.status == 'COMPLETE', OrderProduct.quantity)], else_=0)).label('sold')
    ).outerjoin(ProductCategory) \
        .outerjoin(Product) \
        .outerjoin(OrderProduct) \
        .outerjoin(Order) \
        .group_by(Category.name) \
        .order_by(desc('sold'), Category.name) \
        .all()

    result = [category.name for category in category_info]

    return jsonify({'statistics': result}), 200



if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host='0.0.0.0', port=5001)
