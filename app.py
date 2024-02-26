from flask import Flask, request, jsonify, render_template
from flask_pymongo import PyMongo
from flask_sqlalchemy import SQLAlchemy
from jsonschema import ValidationError, validate

app = Flask(__name__)

# Database configurations
app.config["MONGO_URI"] = "mongodb://localhost:27017/users_vouchers"
mongo = PyMongo(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users_vouchers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# SQLAlchemy Models
class UserInfo(db.Model):
    __tablename__ = 'user_info'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)

class UserSpending(db.Model):
    __tablename__ = 'user_spending'
    user_id = db.Column(db.Integer, primary_key=True)
    money_spent = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    
with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return '<h1>Hello Flask!</h1>'

@app.route('/all_users', methods=['GET'])
def all_users():
    all_users_info = UserInfo.query.all()

    if not all_users_info:
        return jsonify({'message': 'No users found.'}), 404

    users_data = [{'user_id': user.user_id, 'name': user.name, 'email': user.email, 'age': user.age} for user in all_users_info]

    return jsonify({'users': users_data})

@app.route('/average_spending_by_age/<int:user_id>', methods=['GET'])
def average_spending_by_age(user_id):
    user_info = UserInfo.query.get(user_id)

    if not user_info:
        return jsonify({'message': 'User not found.'}), 404

    user_spending = UserSpending.query.filter_by(user_id=user_id).all()
    total_spending = sum(entry.money_spent for entry in user_spending)

    return jsonify({'user_id': user_id, 'user_name': user_info.name, 'total_spending': total_spending})

@app.route('/vouchers')
def create_collection():
    mongo.db.create_collection('vouchers')
    return 'Collection created successfully!'

user_spending = {
    "type": "object",
    "properties": {
        key: {"type": "integer"} for key in ['user_id', 'money_spent', 'year']
    },
    "required": ["user_id", "money_spent", "year"]
}

@app.route('/user_spendings')
def user_spendings():
    return render_template('user_spendings.html')

@app.route('/write_to_mongodb', methods=['POST'])
def write_to_mongodb():
    if request.method != 'POST':
        return jsonify({'message': 'Method Not Allowed'}), 405

    data = request.get_json()

    try:
        validate(instance=data, schema=user_spending)
        mongo.db.user_spending.insert_one(data)
        return jsonify({'message': 'Data written to MongoDB successfully.'}), 201
    except ValidationError as e:
        return jsonify({'message': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'message': f'Error writing to MongoDB: {str(e)}'}), 500

@app.route('/average_spending_by_age_range', methods=['GET'])
def average_spending_by_age_range():
    age_ranges = {
        '18-24': (18, 24),
        '25-30': (25, 30),
        '31-36': (31, 36),
        '37-47': (37, 47),
        '>47': (48, 120)
    }

    average_spending_by_age_range = {}

    for range_name, (lower, upper) in age_ranges.items():
        total_spending_in_range = 0
        total_users_in_range = UserInfo.query.filter(UserInfo.age >= lower, UserInfo.age <= upper).count()
        if total_users_in_range > 0:
            user_ids = [user.user_id for user in UserInfo.query.filter(UserInfo.age >= lower, UserInfo.age <= upper)]
            total_spending_in_range = sum(entry.money_spent for entry in UserSpending.query.filter(UserSpending.user_id.in_(user_ids)).all())
        average_spending = total_spending_in_range / total_users_in_range if total_users_in_range > 0 else 0
        average_spending_by_age_range[range_name] = average_spending

    return jsonify({'average_spending_by_age_range': average_spending_by_age_range})

@app.route('/user_spending_records', methods=['GET'])
def user_spending_records():
    user_spending_data = list(mongo.db.user_spending.find())

    if not user_spending_data:
        return jsonify({'message': 'No user spending records found.'}), 404

    records = [{
        'user_id': record['user_id'],
        'money_spent': record['money_spent'],
        'year': record['year']
    } for record in user_spending_data]

    return jsonify({'user_spending_records': records})

if __name__ == '__main__':    
    app.run(debug=True)