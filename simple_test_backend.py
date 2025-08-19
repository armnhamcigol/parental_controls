#!/usr/bin/env python3
"""
Simple Test Backend for Nintendo Switch Integration
Minimal version to test if everything works
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Serve the dashboard
@app.route('/')
def serve_dashboard():
    return send_from_directory('.', 'enhanced_dashboard.html')

# Basic API endpoints
@app.route('/api/status')
def get_status():
    return jsonify({
        'success': True,
        'controls_active': True,
        'firewall_connected': True,
        'nintendo_available': True,
        'timestamp': '2025-08-18T19:50:00Z'
    })

@app.route('/api/toggle', methods=['POST'])
def toggle_parental_controls():
    return jsonify({
        'success': True,
        'controls_active': True,
        'message': 'Parental controls toggled'
    })

@app.route('/api/nintendo/devices')
def get_nintendo_devices():
    return jsonify({
        'success': True,
        'authenticated': True,
        'devices': [
            {
                'device_id': 'newswitch',
                'device_name': 'newswitch',
                'device_type': 'nintendo_switch',
                'online': True,
                'current_game': 'Super Mario Odyssey',
                'controls_enabled': True,
                'today_play_time_minutes': 67,
                'daily_limit_minutes': 180,
                'ip_address': '192.168.123.134'
            },
            {
                'device_id': 'backroom',
                'device_name': 'backroom', 
                'device_type': 'nintendo_switch',
                'online': True,
                'current_game': 'Mario Kart 8 Deluxe',
                'controls_enabled': False,
                'today_play_time_minutes': 23,
                'daily_limit_minutes': 120,
                'ip_address': '192.168.123.135'
            }
        ]
    })

@app.route('/api/nintendo/toggle', methods=['POST'])
def toggle_nintendo_device():
    data = request.get_json() or {}
    device_id = data.get('device_id') or request.form.get('device_id') or request.args.get('device_id')
    enabled = data.get('enabled') or request.form.get('enabled') or request.args.get('enabled')
    
    # Convert string 'true'/'false' to boolean
    if isinstance(enabled, str):
        enabled = enabled.lower() == 'true'
    
    print(f"🎮 Toggling Nintendo device {device_id}: {'ON' if enabled else 'OFF'}")
    
    return jsonify({
        'success': True,
        'device_id': device_id,
        'controls_enabled': enabled,
        'message': f'Nintendo Switch controls {"enabled" if enabled else "disabled"} for {device_id}'
    })

@app.route('/api/nintendo/authenticate', methods=['POST'])
def nintendo_authenticate():
    return jsonify({
        'success': True,
        'authenticated': True,
        'message': 'Already authenticated'
    })

@app.route('/api/nintendo/integrated_status')
def get_integrated_status():
    return jsonify({
        'success': True,
        'integrated_status': {
            'enhanced_discovery_available': True,
            'real_nintendo_available': True,
            'authenticated': True,
            'manager_type': 'Integrated'
        }
    })

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Simple Test Backend',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    print("🚀 Starting Simple Test Backend")
    print("📱 Dashboard: http://127.0.0.1:8445")
    print("🔧 Backend API: http://127.0.0.1:8445/api")
    
    # Check if dashboard file exists
    if os.path.exists('enhanced_dashboard.html'):
        print("✅ enhanced_dashboard.html found")
    else:
        print("❌ enhanced_dashboard.html not found")
    
    app.run(host='127.0.0.1', port=8445, debug=True)
