from flask import Flask, render_template, request, jsonify
from visualize_trader import TraderVisualizer
import os

app = Flask(__name__)
visualizer = TraderVisualizer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    address = request.json.get('address')
    if not address:
        return jsonify({"error": "Address is required"}), 400
    
    try:
        # analyze_and_get_html returns the HTML string
        html_content = visualizer.analyze_and_get_html(address)
        return jsonify({"html": html_content})
    except Exception as e:
        print(f"Error analyzing trader: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, port=5005)
