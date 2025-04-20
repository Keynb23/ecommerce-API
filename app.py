from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime
from marshmallow import ValidationError

# Initialize Flask app
app = Flask(__name__)

# Configure MySQL database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:newpassword123@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and Marshmallow
db = SQLAlchemy(app)
ma = Marshmallow(app)

# ======================================================================
#                        Database Models
# ======================================================================

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

# OrderProduct model: association table for orders and products
class OrderProduct(db.Model):
    __tablename__ = 'order_product'
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    __table_args__ = (db.UniqueConstraint('order_id', 'product_id', name='unique_order_product'),)

# ======================================================================
#                        Marshmallow Schemas
# ======================================================================

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

# ======================================================================
#                        Database Initialization
# ======================================================================

# Create database tables
with app.app_context():
    db.create_all()

# ======================================================================
#                        User Endpoints
# ======================================================================

# Get all users
@app.route('/users', methods=['GET'])
def get_all_users():
    """Retrieve all users from the database."""
    try:
        users = User.query.all()
        print("Success: Retrieved all users")
        return jsonify(users_schema.dump(users))
    except Exception as e:
        print(f"Error: Failed to retrieve all users - {str(e)}")
        return jsonify({"error": str(e)}), 500

# Get single user by ID
@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    """Retrieve a user by their ID."""
    try:
        user = User.query.get_or_404(id)
        print(f"Success: Retrieved user with ID {id}")
        return jsonify(user_schema.dump(user))
    except Exception as e:
        print(f"Error: Failed to retrieve user with ID {id} - {str(e)}")
        return jsonify({"error": str(e)}), 404

# Create new user
@app.route('/users', methods=['POST'])
def add_user():
    """Create a new user with validated data."""
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        print(f"Error: Failed to validate user data - {e.messages}")
        return jsonify(e.messages), 400

    # Check if user already exists
    existing_user = User.query.filter_by(email=request.json['email']).first()
    if existing_user:
        print(f"Error: Failed to create user - Email {request.json['email']} already exists")
        return jsonify({"error": "User with this email already exists"}), 400

    try:
        db.session.add(user_data)
        db.session.commit()
        print(f"Success: Created new user with email {request.json['email']}")
        return jsonify({
            "message": "New user added successfully!",
            "user": user_schema.dump(user_data)
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error: Failed to create user - {str(e)}")
        return jsonify({"error": str(e)}), 500

# Update existing user
@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    """Update an existing user by ID with validated data."""
    try:
        user = User.query.get_or_404(id)
    except Exception as e:
        print(f"Error: Failed to find user with ID {id} - {str(e)}")
        return jsonify({"error": str(e)}), 404

    try:
        user = user_schema.load(request.get_json(), instance=user, session=db.session, partial=True)
        db.session.commit()
        print(f"Success: Updated user with ID {id}")
        return jsonify(user_schema.dump(user))
    except ValidationError as e:
        print(f"Error: Failed to validate user update data for ID {id} - {e.messages}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error: Failed to update user with ID {id} - {str(e)}")
        return jsonify({"error": str(e)}), 500

# Delete user
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    """Delete a user by ID."""
    try:
        user = User.query.get_or_404(id)
        db.session.delete(user)
        db.session.commit()
        print(f"Success: Deleted user with ID {id}")
        return jsonify({"message": "User deleted"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error: Failed to delete user with ID {id} - {str(e)}")
        return jsonify({"error": str(e)}), 500

# ======================================================================
#                        Product Endpoints
# ======================================================================

# Get all products
@app.route('/products', methods=['GET'])
def get_all_products():
    """Retrieve all products from the database."""
    try:
        products = Product.query.all()
        print("Success: Retrieved all products")
        return jsonify(products_schema.dump(products))
    except Exception as e:
        print(f"Error: Failed to retrieve all products - {str(e)}")
        return jsonify({"error": str(e)}), 500

# Get single product by ID
@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    """Retrieve a product by its ID."""
    try:
        product = Product.query.get_or_404(id)
        print(f"Success: Retrieved product with ID {id}")
        return jsonify(product_schema.dump(product))
    except Exception as e:
        print(f"Error: Failed to retrieve product with ID {id} - {str(e)}")
        return jsonify({"error": str(e)}), 404

# Create new product
@app.route('/products', methods=['POST'])
def create_product():
    """Create a new product with validated data."""
    try:
        product = product_schema.load(request.get_json(), session=db.session)
        db.session.add(product)
        db.session.commit()
        print(f"Success: Created new product {product.product_name}")
        return jsonify(product_schema.dump(product)), 201
    except ValidationError as e:
        print(f"Error: Failed to validate product data - {e.messages}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error: Failed to create product - {str(e)}")
        return jsonify({"error": str(e)}), 500

# Update existing product
@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    """Update an existing product by ID with validated data."""
    try:
        product = Product.query.get_or_404(id)
    except Exception as e:
        print(f"Error: Failed to find product with ID {id} - {str(e)}")
        return jsonify({"error": str(e)}), 404

    try:
        product = product_schema.load(request.get_json(), instance=product, session=db.session, partial=True)
        db.session.commit()
        print(f"Success: Updated product with ID {id}")
        return jsonify(product_schema.dump(product))
    except ValidationError as e:
        print(f"Error: Failed to validate product update data for ID {id} - {e.messages}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error: Failed to update product with ID {id} - {str(e)}")
        return jsonify({"error": str(e)}), 500

# Delete product
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    """Delete a product by ID."""
    try:
        product = Product.query.get_or_404(id)
        db.session.delete(product)
        db.session.commit()
        print(f"Success: Deleted product with ID {id}")
        return jsonify({"message": "Product deleted"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error: Failed to delete product with ID {id} - {str(e)}")
        return jsonify({"error": str(e)}), 500

# ======================================================================
#                        Order Endpoints
# ======================================================================

# Create new order
@app.route('/orders', methods=['POST'])
def create_order():
    """Create a new order with validated data."""
    try:
        order = order_schema.load(request.get_json(), session=db.session)
        db.session.add(order)
        db.session.commit()
        print(f"Success: Created new order with ID {order.id}")
        return jsonify(order_schema.dump(order)), 201
    except ValidationError as e:
        print(f"Error: Failed to validate order data - {e.messages}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error: Failed to create order - {str(e)}")
        return jsonify({"error": str(e)}), 500

# Add product to order
@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])
def add_product_to_order(order_id, product_id):
    """Add a product to an existing order, preventing duplicates."""
    try:
        order = Order.query.get_or_404(order_id)
        product = Product.query.get_or_404(product_id)
    except Exception as e:
        print(f"Error: Failed to find order {order_id} or product {product_id} - {str(e)}")
        return jsonify({"error": str(e)}), 404

    if product in order.products:
        print(f"Error: Failed to add product {product_id} to order {order_id} - Product already in order")
        return jsonify({"error": "Product already in order"}), 400

    try:
        order.products.append(product)
        db.session.commit()
        print(f"Success: Added product {product_id} to order {order_id}")
        return jsonify(order_schema.dump(order))
    except Exception as e:
        db.session.rollback()
        print(f"Error: Failed to add product {product_id} to order {order_id} - {str(e)}")
        return jsonify({"error": str(e)}), 500

# Remove product from order
@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product_from_order(order_id, product_id):
    """Remove a product from an existing order."""
    try:
        order = Order.query.get_or_404(order_id)
        product = Product.query.get_or_404(product_id)
    except Exception as e:
        print(f"Error: Failed to find order {order_id} or product {product_id} - {str(e)}")
        return jsonify({"error": str(e)}), 404

    if product not in order.products:
        print(f"Error: Failed to remove product {product_id} from order {order_id} - Product not in order")
        return jsonify({"error": "Product not in order"}), 400

    try:
        order.products.remove(product)
        db.session.commit()
        print(f"Success: Removed product {product_id} from order {order_id}")
        return jsonify({"message": "Product removed from order"})
    except Exception as e:
        db.session.rollback()
        print(f"Error: Failed to remove product {product_id} from order {order_id} - {str(e)}")
        return jsonify({"error": str(e)}), 500

# Get all orders for a user
@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    """Retrieve all orders for a specific user."""
    try:
        orders = Order.query.filter_by(user_id=user_id).all()
        print(f"Success: Retrieved orders for user ID {user_id}")
        return jsonify(orders_schema.dump(orders))
    except Exception as e:
        print(f"Error: Failed to retrieve orders for user ID {user_id} - {str(e)}")
        return jsonify({"error": str(e)}), 500

# Get products in an order
@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_order_products(order_id):
    """Retrieve all products in a specific order."""
    try:
        order = Order.query.get_or_404(order_id)
        print(f"Success: Retrieved products for order ID {order_id}")
        return jsonify(products_schema.dump(order.products))
    except Exception as e:
        print(f"Error: Failed to retrieve products for order ID {order_id} - {str(e)}")
        return jsonify({"error": str(e)}), 404

# ======================================================================
#                        Application Startup
# ======================================================================

# Print URL map for debugging
print(app.url_map)

# Run Flask app in debug mode
if __name__ == '__main__':
    app.run(debug=True)