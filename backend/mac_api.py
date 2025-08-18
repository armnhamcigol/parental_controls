#!/usr/bin/env python3
"""
MAC Address Management API
Simple Flask API for managing parental control MAC addresses
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
from pathlib import Path

# Add the backend directory to the path so we can import mac_manager
sys.path.append(str(Path(__file__).parent))
from mac_manager import MACAddressManager

app = Flask(__name__)
CORS(app)  # Allow frontend to connect

# Initialize MAC manager
mac_manager = MACAddressManager()

@app.route('/api/mac/devices', methods=['GET'])
def get_devices():
    """Get all MAC address devices"""
    try:
        devices = mac_manager.get_all_devices()
        return jsonify({
            'success': True,
            'devices': devices,
            'count': len(devices)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mac/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    """Get specific device by ID"""
    try:
        device = mac_manager.get_device(device_id)
        if device:
            return jsonify({
                'success': True,
                'device': device
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mac/devices', methods=['POST'])
def add_device():
    """Add new device"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        name = data.get('name')
        mac = data.get('mac')
        
        if not name or not mac:
            return jsonify({
                'success': False,
                'error': 'Name and MAC address are required'
            }), 400
        
        device = mac_manager.add_device(name, mac)
        return jsonify({
            'success': True,
            'device': device,
            'message': f'Device "{name}" added successfully'
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mac/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    """Update existing device"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        name = data.get('name')
        mac = data.get('mac')
        enabled = data.get('enabled')
        
        device = mac_manager.update_device(device_id, name=name, mac=mac, enabled=enabled)
        return jsonify({
            'success': True,
            'device': device,
            'message': f'Device updated successfully'
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mac/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Delete device"""
    try:
        success = mac_manager.delete_device(device_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Device deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to delete device'
            }), 500
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mac/export/opnsense', methods=['GET'])
def export_opnsense():
    """Export for OPNsense alias creation"""
    try:
        export_data = mac_manager.export_for_opnsense()
        return jsonify({
            'success': True,
            'export': export_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mac/import', methods=['POST'])
def import_devices():
    """Import devices from text content"""
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({
                'success': False,
                'error': 'Content field is required'
            }), 400
        
        content = data['content']
        added_count, errors = mac_manager.import_from_text(content)
        
        return jsonify({
            'success': True,
            'added_count': added_count,
            'errors': errors,
            'message': f'Imported {added_count} devices' + (f' with {len(errors)} errors' if errors else '')
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mac/stats', methods=['GET'])
def get_stats():
    """Get statistics about MAC addresses"""
    try:
        all_devices = mac_manager.get_all_devices()
        enabled_devices = mac_manager.get_enabled_devices()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_devices': len(all_devices),
                'enabled_devices': len(enabled_devices),
                'disabled_devices': len(all_devices) - len(enabled_devices),
                'last_updated': max([d.get('updated_date', d.get('added_date', '')) for d in all_devices]) if all_devices else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'MAC Address Management API',
        'version': '1.0.0'
    })

@app.route('/')
def index():
    """Serve the MAC management interface"""
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>MAC Address Management</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #007bff; color: white; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        .device-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; }
        .device-card { border: 1px solid #ccc; padding: 15px; border-radius: 5px; background: #f9f9f9; }
        .device-enabled { border-left: 4px solid #28a745; }
        .device-disabled { border-left: 4px solid #dc3545; opacity: 0.7; }
        .form-group { margin: 10px 0; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 3px; }
        .btn { padding: 10px 15px; border: none; border-radius: 3px; cursor: pointer; margin: 5px; }
        .btn-primary { background: #007bff; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .alert { padding: 10px; margin: 10px 0; border-radius: 3px; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .export-section { background: #f8f9fa; }
        .mac-address { font-family: monospace; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 MAC Address Management</h1>
            <p>Manage MAC addresses for parental controls</p>
        </div>

        <div id="alerts"></div>

        <div class="section">
            <h2>📱 Add New Device</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr auto; gap: 15px; align-items: end;">
                <div class="form-group">
                    <label for="deviceName">Device Name</label>
                    <input type="text" id="deviceName" placeholder="e.g., Aaron's iPhone">
                </div>
                <div class="form-group">
                    <label for="deviceMAC">MAC Address</label>
                    <input type="text" id="deviceMAC" placeholder="e.g., AA:BB:CC:DD:EE:FF">
                </div>
                <button class="btn btn-primary" onclick="addDevice()">Add Device</button>
            </div>
        </div>

        <div class="section">
            <h2>📋 Device List</h2>
            <div id="deviceStats" style="margin-bottom: 15px;"></div>
            <div id="deviceList" class="device-list"></div>
        </div>

        <div class="section export-section">
            <h2>🔥 OPNsense Export</h2>
            <p>Generate alias content for OPNsense firewall:</p>
            <button class="btn btn-secondary" onclick="generateExport()">Generate Export</button>
            <div id="exportContent" style="margin-top: 15px;"></div>
        </div>
    </div>

    <script>
        const API_BASE = '/api/mac';
        
        function showAlert(message, type = 'success') {
            const alertsDiv = document.getElementById('alerts');
            const alert = document.createElement('div');
            alert.className = `alert alert-${type}`;
            alert.textContent = message;
            alertsDiv.appendChild(alert);
            
            setTimeout(() => {
                alert.remove();
            }, 5000);
        }

        async function loadDevices() {
            try {
                const response = await fetch(`${API_BASE}/devices`);
                const data = await response.json();
                
                if (data.success) {
                    displayDevices(data.devices);
                    displayStats(data.devices);
                } else {
                    showAlert('Failed to load devices: ' + data.error, 'error');
                }
            } catch (error) {
                showAlert('Error loading devices: ' + error.message, 'error');
            }
        }

        function displayStats(devices) {
            const enabled = devices.filter(d => d.enabled).length;
            const disabled = devices.length - enabled;
            
            document.getElementById('deviceStats').innerHTML = `
                <strong>📊 Stats:</strong> 
                ${devices.length} total devices, 
                ${enabled} enabled, 
                ${disabled} disabled
            `;
        }

        function displayDevices(devices) {
            const deviceList = document.getElementById('deviceList');
            
            if (devices.length === 0) {
                deviceList.innerHTML = '<p>No devices found. Add some devices above.</p>';
                return;
            }

            deviceList.innerHTML = devices.map(device => `
                <div class="device-card ${device.enabled ? 'device-enabled' : 'device-disabled'}">
                    <h4>${device.name}</h4>
                    <p class="mac-address">${device.mac}</p>
                    <p><small>ID: ${device.id} • Status: ${device.enabled ? 'Enabled' : 'Disabled'}</small></p>
                    <div>
                        <button class="btn btn-secondary" onclick="toggleDevice(${device.id}, ${!device.enabled})">
                            ${device.enabled ? 'Disable' : 'Enable'}
                        </button>
                        <button class="btn btn-danger" onclick="deleteDevice(${device.id})">Delete</button>
                    </div>
                </div>
            `).join('');
        }

        async function addDevice() {
            const name = document.getElementById('deviceName').value.trim();
            const mac = document.getElementById('deviceMAC').value.trim();
            
            if (!name || !mac) {
                showAlert('Please enter both device name and MAC address', 'error');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/devices`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, mac })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showAlert(data.message);
                    document.getElementById('deviceName').value = '';
                    document.getElementById('deviceMAC').value = '';
                    loadDevices();
                } else {
                    showAlert('Failed to add device: ' + data.error, 'error');
                }
            } catch (error) {
                showAlert('Error adding device: ' + error.message, 'error');
            }
        }

        async function toggleDevice(deviceId, enabled) {
            try {
                const response = await fetch(`${API_BASE}/devices/${deviceId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enabled })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showAlert(`Device ${enabled ? 'enabled' : 'disabled'} successfully`);
                    loadDevices();
                } else {
                    showAlert('Failed to update device: ' + data.error, 'error');
                }
            } catch (error) {
                showAlert('Error updating device: ' + error.message, 'error');
            }
        }

        async function deleteDevice(deviceId) {
            if (!confirm('Are you sure you want to delete this device?')) {
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/devices/${deviceId}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showAlert('Device deleted successfully');
                    loadDevices();
                } else {
                    showAlert('Failed to delete device: ' + data.error, 'error');
                }
            } catch (error) {
                showAlert('Error deleting device: ' + error.message, 'error');
            }
        }

        async function generateExport() {
            try {
                const response = await fetch(`${API_BASE}/export/opnsense`);
                const data = await response.json();
                
                if (data.success) {
                    const export_data = data.export;
                    document.getElementById('exportContent').innerHTML = `
                        <h4>Alias: ${export_data.alias_name}</h4>
                        <p><strong>Description:</strong> ${export_data.description}</p>
                        <p><strong>Type:</strong> MAC Address</p>
                        <h5>Content for OPNsense:</h5>
                        <textarea style="width: 100%; height: 200px; font-family: monospace;" readonly>${export_data.content}</textarea>
                        <p><small>Copy the content above and paste it into OPNsense when creating a MAC address alias.</small></p>
                    `;
                } else {
                    showAlert('Failed to generate export: ' + data.error, 'error');
                }
            } catch (error) {
                showAlert('Error generating export: ' + error.message, 'error');
            }
        }

        // Load devices when page loads
        window.addEventListener('load', loadDevices);
    </script>
</body>
</html>
    '''

if __name__ == '__main__':
    print("🚀 Starting MAC Address Management API")
    print("📝 Available endpoints:")
    print("   GET  /                     - Web interface")
    print("   GET  /api/mac/devices      - List all devices")
    print("   POST /api/mac/devices      - Add new device") 
    print("   PUT  /api/mac/devices/{id} - Update device")
    print("   DEL  /api/mac/devices/{id} - Delete device")
    print("   GET  /api/mac/export/opnsense - Export for OPNsense")
    print("   GET  /health               - Health check")
    print("")
    print("🌐 Access the web interface at: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
