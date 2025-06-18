from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/test')
def test():
    return jsonify({'status': 'working', 'message': 'Flask is responding!'})

@app.route('/')
def home():
    return jsonify({'status': 'basic app working'})

if __name__ == '__main__':
    print("Testing basic Flask...")
    app.run(debug=False, host='0.0.0.0', port=8000)