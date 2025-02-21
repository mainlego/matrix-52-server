from flask import Blueprint, request, jsonify
from app.database import Database
from flask_cors import cross_origin

api = Blueprint('api', __name__)
db = Database()

@api.route('/api/user/data', methods=['GET', 'POST', 'OPTIONS'])
@cross_origin(origins="https://myfrontend.onrender.com", headers=['Content-Type'], methods=['GET', 'POST', 'OPTIONS'])
def user_data():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.status_code = 200  # Render требует явного HTTP 200 OK
        response.headers.add('Access-Control-Allow-Origin', 'https://myfrontend.onrender.com')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        return response

    try:
        if request.method == 'GET':
            user_id = request.args.get('user_id')
            if not user_id:
                return jsonify({'error': 'User ID is required'}), 400
            user_data = db.get_user_data(user_id)
            return jsonify(user_data if user_data else {})

        elif request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            user_id = data.get('user_id')
            if not user_id:
                return jsonify({'error': 'User ID is required'}), 400
            db.save_user_data(user_id, name=data.get('name'), birth_date=data.get('birthDate'))
            return jsonify({'status': 'success'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/calculate-matrix', methods=['POST'])
@cross_origin(origins="http://localhost:5173")
def calculate_matrix():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        birth_date = data.get('birthDate')

        if not user_id or not birth_date:
            return jsonify({'error': 'User ID and birth date are required'}), 400

        layout = calculate_layout_from_excel(birth_date)

        db.save_spread(
            user_id=user_id,
            spread_type='period',
            data=layout
        )

        db.update_user_activity(user_id)

        return jsonify(layout)

    except Exception as e:
        print(f"Error in calculate_matrix: {str(e)}")
        return jsonify({'error': str(e)}), 500


def calculate_layout_from_excel(birth_date):
    # Временная заглушка для тестирования
    return {
        'top_row': ['2♡', '8♢', '5♧'],
        'rows': [
            ['2♡', '8♢', '5♧', '3♤', '6♧', '9♢', '4♡'],
            ['7♢', '4♧', '2♡', '8♢', '5♧', '3♤', '6♧'],
            ['9♢', '4♡', '7♢', '4♧', '2♡', '8♢', '5♧'],
            ['3♤', '6♧', '9♢', '4♡', '7♢', '4♧', '2♡'],
            ['8♢', '5♧', '3♤', '6♧', '9♢', '4♡', '7♢'],
            ['4♧', '2♡', '8♢', '5♧', '3♤', '6♧', '9♢'],
            ['4♡', '7♢', '4♧', '2♡', '8♢', '5♧', '3♤']
        ]
    }