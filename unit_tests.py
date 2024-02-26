import pytest
from app import app, db, mongo, UserInfo, UserSpending

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users_vouchers.db'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Populate test data
            user1 = UserInfo(user_id=1, name='Name 1', email='name1@example.com', age=25)
            user2 = UserInfo(user_id=2, name='Name 2', email='name2@example.com', age=30)
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            
            spending1 = UserSpending(user_id=1, money_spent=100, year=2021)
            spending2 = UserSpending(user_id=2, money_spent=200, year=2022)
            db.session.add(spending1)
            db.session.add(spending2)
            db.session.commit()
        yield client
    # Teardown
    with app.app_context():
        db.session.remove()
        db.drop_all()

def test_all_users(client):
    response = client.get('/all_users')
    assert response.status_code == 200
    data = response.json['users']
    assert len(data) == 2
    assert data[0]['name'] == 'Name 1'
    assert data[1]['name'] == 'Name 2'

def test_average_spending_by_age(client):
    response = client.get('/average_spending_by_age/1')
    assert response.status_code == 200
    data = response.json
    assert data['user_name'] == 'Name 1'
    assert data['total_spending'] == 300

def test_write_to_mongodb(client):
    data = {
        'user_id': 2,
        'money_spent': 150,
        'year': 2023
    }
    response = client.post('/write_to_mongodb', json=data)
    assert response.status_code == 201
    # Check if data is written to MongoDB (you need to implement this test)

def test_average_spending_by_age_range(client):
    response = client.get('/average_spending_by_age_range')
    assert response.status_code == 200
    data = response.json['average_spending_by_age_range']
    assert data['25-30'] == 150  # Assuming Bob's spending is 150

def test_user_spending_records(client):
    response = client.get('/user_spending_records')
    assert response.status_code == 200
    data = response.json['user_spending_records']
    assert len(data) == 2  # Assuming there are two spending records