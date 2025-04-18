from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime
from marshmallow import ValidationError, fields

# Initialize Flask app
app = Flask(__name__)

# Configure MySQL database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:newpassword123@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and Marshmallow
db = SQLAlchemy(app)
ma = Marshmallow(app)

# User model: stores user details
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    orders = db.relationship('Order', backref='user', lazy=True)

# Order model: stores order details
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    products = db.relationship('Product', secondary='order_product', backref=db.backref('orders', lazy='dynamic'))

# Product model: stores product details
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

# OrderProduct model: links orders and products
class OrderProduct(db.Model):
    __tablename__ = 'order_product'
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    __table_args__ = (db.UniqueConstraint('order_id', 'product_id', name='unique_order_product'),)

# User schema: serializes/deserializes User model
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_fk = True
        load_instance = True

# Product schema: serializes/deserializes Product model
class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        include_fk = True
        load_instance = True

# Order schema: serializes/deserializes Order model
class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        include_fk = True
        load_instance = True
    products = ma.Nested(ProductSchema, many=True)

# Initialize schema instances
user_schema = UserSchema()
users_schema = UserSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

# Create database tables
with app.app_context():
    db.create_all()

# Get all users
@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    return jsonify(users_schema.dump(users))

# Get single user by ID
@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user_schema.dump(user))







# # Create new user
# @app.route('/users', methods=['POST'])
# def create_user():
#     data = request.get_json()
#     try:
#         user = user_schema.load(data, session=db.session)
#         db.session.add(user)
#         db.session.commit()
#         return jsonify(user_schema.dump(user)), 201
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400
    
    # Create a customer with a POST request
@app.route("/user", methods=["POST"])
def add_user():
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_user = User(name=user_data['name'], email=user_data['email'], address=user_data['address'])
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"Message": "New User added successfully!",
                    "user": user_schema.dump(new_user)}), 201
    
    
    
    
    

# Update existing user
@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json()
    try:
        user = user_schema.load(data, instance=user, session=db.session, partial=True)
        db.session.commit()
        return jsonify(user_schema.dump(user))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Delete user
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200

# Get all products
@app.route('/products', methods=['GET'])
def get_all_products():
    products = Product.query.all()
    return jsonify(products_schema.dump(products))

# Get single product by ID
@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return jsonify(product_schema.dump(product))

# Create new product
@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    try:
        product = product_schema.load(data, session=db.session)
        db.session.add(product)
        db.session.commit()
        return jsonify(product_schema.dump(product)), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Update existing product
@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.get_json()
    try:
        product = product_schema.load(data, instance=product, session=db.session, partial=True)
        db.session.commit()
        return jsonify(product_schema.dump(product))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Delete product
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted"}), 200

# Create new order
@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    try:
        order = order_schema.load(data, session=db.session)
        db.session.add(order)
        db.session.commit()
        return jsonify(order_schema.dump(order)), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Add product to order
@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])
def add_product_to_order(order_id, product_id):
    order = Order.query.get_or_404(order_id)
    product = Product.query.get_or_404(product_id)
    if product in order.products:
        return jsonify({"error": "Product already in order"}), 400
    order.products.append(product)
    db.session.commit()
    return jsonify(order_schema.dump(order))

# Remove product from order
@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product_from_order(order_id, product_id):
    order = Order.query.get_or_404(order_id)
    product = Product.query.get_or_404(product_id)
    if product not in order.products:
        return jsonify({"error": "Product not in order"}), 400
    order.products.remove(product)
    db.session.commit()
    return jsonify({"message": "Product removed from order"})

# Get all orders for a user
@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
    return jsonify(orders_schema.dump(orders))

# Get products in an order
@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_order_products(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify(products_schema.dump(order.products))

# Print URL map for debugging
print(app.url_map)

# Run Flask app in debug mode
if __name__ == '__main__':
    app.run(debug=True)