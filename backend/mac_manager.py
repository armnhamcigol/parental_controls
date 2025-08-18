#!/usr/bin/env python3
"""
MAC Address Management Service for Parental Controls
Manages MAC addresses for blocking in OPNsense firewall
"""

import os
import re
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

class MACAddressManager:
    def __init__(self, mac_file_path: str = None):
        """Initialize MAC address manager with file path"""
        if mac_file_path is None:
            # Default to the mac_addresses.txt file location
            project_root = Path(__file__).parent.parent
            mac_file_path = project_root / "mac_addresses" / "mac_addresses.txt"
        
        self.mac_file_path = Path(mac_file_path)
        self.backup_dir = self.mac_file_path.parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Ensure the MAC addresses directory and file exist
        self.mac_file_path.parent.mkdir(exist_ok=True)
        if not self.mac_file_path.exists():
            self.mac_file_path.write_text("")
    
    def normalize_mac(self, mac_address: str) -> str:
        """
        Normalize MAC address to OPNsense format (XX:XX:XX:XX:XX:XX)
        Accepts various formats: XX-XX-XX-XX-XX-XX, XX:XX:XX:XX:XX:XX, XXXXXXXXXXXX
        """
        # Remove all non-alphanumeric characters
        clean_mac = re.sub(r'[^0-9A-Fa-f]', '', mac_address.upper())
        
        if len(clean_mac) != 12:
            raise ValueError(f"Invalid MAC address length: {mac_address}")
        
        # Check if all characters are valid hex
        if not re.match(r'^[0-9A-F]{12}$', clean_mac):
            raise ValueError(f"Invalid MAC address format: {mac_address}")
        
        # Format as XX:XX:XX:XX:XX:XX for OPNsense
        formatted = ':'.join([clean_mac[i:i+2] for i in range(0, 12, 2)])
        return formatted
    
    def validate_device_name(self, name: str) -> str:
        """Validate and clean device name"""
        if not name or not name.strip():
            raise ValueError("Device name cannot be empty")
        
        # Remove potentially problematic characters for OPNsense
        clean_name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name.strip())
        
        if len(clean_name) == 0:
            raise ValueError("Device name contains no valid characters")
        
        if len(clean_name) > 50:
            clean_name = clean_name[:50]
        
        return clean_name
    
    def load_mac_addresses(self) -> List[Dict]:
        """Load MAC addresses from file"""
        devices = []
        
        try:
            if not self.mac_file_path.exists():
                return devices
            
            content = self.mac_file_path.read_text(encoding='utf-8').strip()
            if not content:
                return devices
            
            for line_num, line in enumerate(content.split('\n'), 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Parse the tab-separated format: ID|Name\tMAC\t
                    parts = line.split('\t')
                    if len(parts) < 2:
                        print(f"Warning: Skipping malformed line {line_num}: {line}")
                        continue
                    
                    # Extract ID and name from first part
                    id_name_part = parts[0]
                    mac_part = parts[1]
                    
                    # Split ID and name (format: "ID|Name")
                    if '|' in id_name_part:
                        id_str, name = id_name_part.split('|', 1)
                        try:
                            device_id = int(id_str)
                        except ValueError:
                            device_id = line_num
                    else:
                        # Fallback if no ID format
                        name = id_name_part
                        device_id = line_num
                    
                    # Normalize MAC address
                    try:
                        normalized_mac = self.normalize_mac(mac_part)
                    except ValueError as e:
                        print(f"Warning: Invalid MAC on line {line_num}: {e}")
                        continue
                    
                    # Validate device name
                    try:
                        clean_name = self.validate_device_name(name)
                    except ValueError as e:
                        print(f"Warning: Invalid device name on line {line_num}: {e}")
                        continue
                    
                    devices.append({
                        'id': device_id,
                        'name': clean_name,
                        'mac': normalized_mac,
                        'original_mac': mac_part,
                        'enabled': True,
                        'added_date': datetime.now().isoformat(),
                        'line_number': line_num
                    })
                
                except Exception as e:
                    print(f"Error parsing line {line_num}: {e}")
                    continue
        
        except Exception as e:
            print(f"Error loading MAC addresses: {e}")
            return []
        
        return devices
    
    def save_mac_addresses(self, devices: List[Dict]) -> bool:
        """Save MAC addresses to file with backup"""
        try:
            # Create backup first
            if self.mac_file_path.exists():
                backup_name = f"mac_addresses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                backup_path = self.backup_dir / backup_name
                backup_path.write_text(self.mac_file_path.read_text())
            
            # Sort devices by ID
            sorted_devices = sorted(devices, key=lambda x: x.get('id', 0))
            
            # Write to file in original format
            lines = []
            for device in sorted_devices:
                if device.get('enabled', True):  # Only save enabled devices
                    line = f"{device['id']}|{device['name']}\t{device['original_mac']}\t"
                    lines.append(line)
            
            # Write to file
            self.mac_file_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
            return True
        
        except Exception as e:
            print(f"Error saving MAC addresses: {e}")
            return False
    
    def add_device(self, name: str, mac: str) -> Dict:
        """Add new device to the list"""
        devices = self.load_mac_addresses()
        
        # Validate inputs
        clean_name = self.validate_device_name(name)
        normalized_mac = self.normalize_mac(mac)
        
        # Check for duplicates
        for device in devices:
            if device['mac'] == normalized_mac:
                raise ValueError(f"MAC address {normalized_mac} already exists for device '{device['name']}'")
            if device['name'].lower() == clean_name.lower():
                raise ValueError(f"Device name '{clean_name}' already exists")
        
        # Generate new ID
        max_id = max([d.get('id', 0) for d in devices]) if devices else 0
        new_id = max_id + 1
        
        # Create new device
        new_device = {
            'id': new_id,
            'name': clean_name,
            'mac': normalized_mac,
            'original_mac': mac,
            'enabled': True,
            'added_date': datetime.now().isoformat(),
            'line_number': len(devices) + 1
        }
        
        devices.append(new_device)
        
        if self.save_mac_addresses(devices):
            return new_device
        else:
            raise RuntimeError("Failed to save device to file")
    
    def update_device(self, device_id: int, name: str = None, mac: str = None, enabled: bool = None) -> Dict:
        """Update existing device"""
        devices = self.load_mac_addresses()
        
        # Find device
        device = None
        for d in devices:
            if d['id'] == device_id:
                device = d
                break
        
        if not device:
            raise ValueError(f"Device with ID {device_id} not found")
        
        # Update fields if provided
        if name is not None:
            clean_name = self.validate_device_name(name)
            # Check for name conflicts
            for d in devices:
                if d['id'] != device_id and d['name'].lower() == clean_name.lower():
                    raise ValueError(f"Device name '{clean_name}' already exists")
            device['name'] = clean_name
        
        if mac is not None:
            normalized_mac = self.normalize_mac(mac)
            # Check for MAC conflicts
            for d in devices:
                if d['id'] != device_id and d['mac'] == normalized_mac:
                    raise ValueError(f"MAC address {normalized_mac} already exists")
            device['mac'] = normalized_mac
            device['original_mac'] = mac
        
        if enabled is not None:
            device['enabled'] = enabled
        
        device['updated_date'] = datetime.now().isoformat()
        
        if self.save_mac_addresses(devices):
            return device
        else:
            raise RuntimeError("Failed to save updated device")
    
    def delete_device(self, device_id: int) -> bool:
        """Delete device from list"""
        devices = self.load_mac_addresses()
        
        # Find and remove device
        original_count = len(devices)
        devices = [d for d in devices if d['id'] != device_id]
        
        if len(devices) == original_count:
            raise ValueError(f"Device with ID {device_id} not found")
        
        return self.save_mac_addresses(devices)
    
    def get_device(self, device_id: int) -> Optional[Dict]:
        """Get single device by ID"""
        devices = self.load_mac_addresses()
        for device in devices:
            if device['id'] == device_id:
                return device
        return None
    
    def get_all_devices(self) -> List[Dict]:
        """Get all devices"""
        return self.load_mac_addresses()
    
    def get_enabled_devices(self) -> List[Dict]:
        """Get only enabled devices"""
        devices = self.load_mac_addresses()
        return [d for d in devices if d.get('enabled', True)]
    
    def generate_opnsense_alias_content(self) -> str:
        """Generate content for OPNsense MAC address alias"""
        enabled_devices = self.get_enabled_devices()
        mac_addresses = [device['mac'] for device in enabled_devices]
        
        # OPNsense MAC alias format: one MAC per line
        return '\n'.join(mac_addresses)
    
    def export_for_opnsense(self) -> Dict:
        """Export in format suitable for OPNsense alias creation"""
        enabled_devices = self.get_enabled_devices()
        
        return {
            'alias_name': 'ParentalControlMACs',
            'alias_type': 'mac',
            'description': f'Parental Controls MAC Addresses ({len(enabled_devices)} devices)',
            'content': self.generate_opnsense_alias_content(),
            'devices': enabled_devices
        }
    
    def import_from_text(self, text_content: str) -> Tuple[int, List[str]]:
        """Import MAC addresses from text content"""
        devices = self.load_mac_addresses()
        added_count = 0
        errors = []
        
        for line_num, line in enumerate(text_content.split('\n'), 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                # Try to parse different formats
                if '\t' in line:
                    # Tab-separated format
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        name_part = parts[0]
                        mac_part = parts[1]
                        
                        if '|' in name_part:
                            _, name = name_part.split('|', 1)
                        else:
                            name = name_part
                        
                        self.add_device(name.strip(), mac_part.strip())
                        added_count += 1
                
                elif ',' in line:
                    # Comma-separated format
                    parts = line.split(',')
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        mac = parts[1].strip()
                        self.add_device(name, mac)
                        added_count += 1
                
                else:
                    errors.append(f"Line {line_num}: Unrecognized format")
            
            except Exception as e:
                errors.append(f"Line {line_num}: {str(e)}")
        
        return added_count, errors


if __name__ == "__main__":
    # Test the MAC manager
    manager = MACAddressManager()
    
    print("🔧 MAC Address Manager Test")
    print("=" * 40)
    
    # Load and display current devices
    devices = manager.get_all_devices()
    print(f"\n📱 Found {len(devices)} devices:")
    
    for device in devices:
        status = "✅" if device.get('enabled', True) else "❌"
        print(f"  {status} {device['name']}: {device['mac']}")
    
    # Generate OPNsense export
    export_data = manager.export_for_opnsense()
    print(f"\n🔥 OPNsense Alias: {export_data['alias_name']}")
    print(f"📝 Description: {export_data['description']}")
    print(f"📋 Content preview:")
    
    content_lines = export_data['content'].split('\n')
    for i, line in enumerate(content_lines[:5]):  # Show first 5
        print(f"     {line}")
    
    if len(content_lines) > 5:
        print(f"     ... and {len(content_lines) - 5} more")
