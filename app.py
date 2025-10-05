from flask import Flask, request, jsonify, send_from_directory
import requests

app = Flask(__name__)

API_KEY = "4ada243f77006b3fd439ac844a1bf900"  # Replace with your actual key

@app.route('/api/weather')
def get_weather():
    city = request.args.get('city')
    if not city:
        return jsonify({'error': 'City is required'}), 400

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    res = requests.get(url)
    if res.status_code != 200:
        return jsonify({'error': 'City not found'}), 404
    return jsonify(res.json())

@app.route('/api/forecast')
def get_forecast():
    city = request.args.get('city')
    if not city:
        return jsonify({'error': 'City is required'}), 400

    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
    res = requests.get(url)
    if res.status_code != 200:
        return jsonify({'error': 'City not found'}), 404
    return jsonify(res.json())

@app.route('/site/<path:filename>')
def serve_site(filename):
    return send_from_directory('site', filename)

if __name__ == '__main__':
    app.run(debug=True)