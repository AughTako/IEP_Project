from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class ProductCategory(database.Model):
    __tablename__ = "productcategories"
    id = database.Column(database.Integer, primary_key=True)
    threadId = database.Column(database.Integer, database.ForeignKey("products.id"), nullable=False)
    tagId = database.Column(database.Integer, database.ForeignKey("categories.id"), nullable=False)


class Product(database.Model):
    __tablename__ = "products"
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False)
    price = database.Column(database.Float, nullable=False)
    
    categories = database.relationship("Category", secondary=ProductCategory.__table__, back_populates="products")

    def __repr__(self):
        return "({}, {}, {}, {})".format(str(self.categories), self.id, self.name, self.price)


class Category(database.Model):
    __tablename__ = "categories"
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False)

    products = database.relationship("Product", secondary=ProductCategory.__table__, back_populates="categories")

    def __repr__(self):
        return "({})".format(self.name)


class Order(database.Model):
    __tablename__ = "orders"
    id = database.Column(database.Integer, primary_key=True)
    total_price = database.Column(database.Float, nullable=False)
    status = database.Column(database.String(50), nullable=False)
    dateOf = database.Column(database.DateTime, nullable=False)
    user = database.Column(database.String(256), nullable=False)

    order_products = database.relationship("OrderProduct", back_populates="order")

    def __repr__(self):
        return f'id: {self.id} status: {self.status} date: {self.dateOf} user: {self.user}'


class OrderProduct(database.Model):
    __tablename__ = "order_products"
    order_id = database.Column(database.Integer, database.ForeignKey("orders.id"), primary_key=True)
    product_id = database.Column(database.Integer, database.ForeignKey("products.id"), primary_key=True)
    quantity = database.Column(database.Integer, nullable=False)

    order = database.relationship("Order", back_populates="order_products")
    product = database.relationship("Product", backref="order_products")
