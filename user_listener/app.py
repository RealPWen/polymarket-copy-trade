from flask import Flask, render_template, request, jsonify
from visualize_trader import TraderVisualizer
from polymarket_data_fetcher import PolymarketDataFetcher
import os
import pandas as pd

app = Flask(__name__)
visualizer = TraderVisualizer()
fetcher = PolymarketDataFetcher()

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

@app.route('/stream/<address>')
def stream_trades(address):
    try:
        # Get the 20 most recent trades for the address
        trades_df = fetcher.get_trades(wallet_address=address, limit=20, silent=True)
        if trades_df.empty:
            return jsonify([])
        
        # Prepare data for frontend
        trades_df['date_str'] = pd.to_datetime(trades_df['timestamp'], unit='s').dt.strftime('%m-%d %H:%M:%S')
        trades_list = trades_df.to_dict('records')
        return jsonify(trades_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/<address>')
def get_analysis_data(address):
    try:
        # Perform full analysis
        analysis_df, trades_df, active_df = visualizer.analyzer.analyze_trader(address, limit=5000)
        
        # Prepare PnL data for chart
        pnl_data = []
        if not analysis_df.empty:
            df_temp = analysis_df.copy()
            df_temp['date'] = df_temp['date'].dt.strftime('%Y-%m-%d %H:%M')
            pnl_data = df_temp[['date', 'cumulative_pnl']].to_dict('records')
            
            # Prepare wins/losses
            df_wins = df_temp[df_temp['pnl'] > 0].sort_values('pnl', ascending=False).head(10)
            df_losses = df_temp[df_temp['pnl'] < 0].sort_values('pnl', ascending=True).head(10)
            top_wins = df_wins.to_dict('records')
            top_losses = df_losses.to_dict('records')
        else:
            top_wins = []
            top_losses = []

        # Prepare positions
        active_list = []
        if not active_df.empty:
            active_list = active_df.to_dict('records')

        return jsonify({
            "pnl_history": pnl_data,
            "top_wins": top_wins,
            "top_losses": top_losses,
            "active_positions": active_list
        })
    except Exception as e:
        print(f"Update error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, port=5005)
