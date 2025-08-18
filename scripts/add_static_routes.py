#!/usr/bin/env python3
"""
Add static file serving routes to the Pi backend
"""

import subprocess

# Routes to add before the if __name__ == '__main__': line
static_routes = '''
from flask import send_from_directory, send_file
import os

@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    return send_file('/home/pi/parental-controls/src/web/index.html')

@app.route('/style.css')
def serve_css():
    """Serve CSS file"""
    return send_file('/home/pi/parental-controls/src/web/style.css', mimetype='text/css')

@app.route('/app.js')
def serve_js():
    """Serve JavaScript file"""
    return send_file('/home/pi/parental-controls/src/web/app.js', mimetype='application/javascript')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve other static files"""
    static_dir = '/home/pi/parental-controls/src/web'
    if os.path.exists(os.path.join(static_dir, filename)):
        return send_from_directory(static_dir, filename)
    else:
        return "File not found", 404

'''

def update_backend():
    """Add static file serving to the backend"""
    
    print("🔧 Adding static file serving routes to Pi backend...")
    
    # SSH command to get current backend content
    get_backend_cmd = [
        "ssh", "-i", "~/.ssh/id_rsa_raspberry_pi", 
        "pi@192.168.123.7",
        "cat /home/pi/parental-controls/backend.py"
    ]
    
    try:
        result = subprocess.run(get_backend_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"❌ Failed to get current backend: {result.stderr}")
            return False
        
        current_content = result.stdout
        
        # Find the old @app.route('/') section and replace it
        lines = current_content.split('\n')
        updated_lines = []
        skip_old_route = False
        
        for i, line in enumerate(lines):
            if '@app.route(\'/\')' in line and 'def index():' in lines[i+1] if i+1 < len(lines) else False:
                # Found the old route, skip until we find the end
                skip_old_route = True
                # Add our new routes instead
                updated_lines.extend(static_routes.strip().split('\n'))
                continue
            elif skip_old_route:
                if line.strip().startswith('if __name__'):
                    # Found the end, stop skipping and add this line
                    skip_old_route = False
                    updated_lines.append(line)
                else:
                    # Skip lines in the old route
                    continue
            else:
                updated_lines.append(line)
        
        # Join back and save to temp file
        updated_content = '\n'.join(updated_lines)
        
        # Write to temporary file
        with open('temp_backend_static.py', 'w') as f:
            f.write(updated_content)
        
        # Copy updated file to Pi
        scp_cmd = [
            "scp", "-i", "~/.ssh/id_rsa_raspberry_pi",
            "temp_backend_static.py",
            "pi@192.168.123.7:/home/pi/parental-controls/backend.py"
        ]
        
        result = subprocess.run(scp_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to upload updated backend: {result.stderr}")
            return False
        
        print("✅ Backend updated with static file serving")
        
        # Clean up temp file
        import os
        try:
            os.remove('temp_backend_static.py')
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating backend: {e}")
        return False

if __name__ == "__main__":
    if update_backend():
        print("\n🔄 Restarting backend service...")
        
        # Restart the backend service
        restart_cmd = [
            "ssh", "-i", "~/.ssh/id_rsa_raspberry_pi",
            "pi@192.168.123.7",
            "pkill -f backend.py; sleep 3; cd /home/pi/parental-controls && nohup python3 backend.py > backend.log 2>&1 &"
        ]
        
        result = subprocess.run(restart_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Backend restarted successfully")
            print("\n🎯 Now try the dashboard - it should load the updated CSS and JS!")
            print("📱 Dashboard: http://192.168.123.7:8443/")
        else:
            print(f"❌ Failed to restart backend: {result.stderr}")
    else:
        print("❌ Failed to update backend")
