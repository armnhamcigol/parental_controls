#!/usr/bin/env python3
"""
OPNsense Integration for Parental Controls
Manages firewall rules and aliases for MAC address blocking
"""

import subprocess
import xml.etree.ElementTree as ET
import tempfile
import uuid
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add the backend directory to the path so we can import mac_manager
sys.path.append(str(Path(__file__).parent))
from mac_manager import MACAddressManager

class OPNsenseManager:
    def __init__(self, ssh_key_path: str = None, router_ip: str = "192.168.123.1"):
        """Initialize OPNsense manager"""
        self.router_ip = router_ip
        self.ssh_key_path = ssh_key_path or "~/.ssh/id_ed25519_opnsense"
        self.mac_manager = MACAddressManager()
        
    def ssh_command(self, command: str) -> tuple[bool, str]:
        """Execute command on OPNsense via SSH"""
        try:
            ssh_cmd = [
                "ssh", "-i", self.ssh_key_path, 
                f"root@{self.router_ip}",
                command
            ]
            
            result = subprocess.run(
                ssh_cmd, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            return result.returncode == 0, result.stdout.strip()
        
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, f"SSH error: {str(e)}"
    
    def backup_config(self) -> bool:
        """Create backup of current OPNsense configuration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"config_backup_parental_controls_{timestamp}.xml"
        
        success, output = self.ssh_command(f"cp /conf/config.xml /conf/{backup_name}")
        if success:
            print(f"✅ Configuration backed up as {backup_name}")
            return True
        else:
            print(f"❌ Failed to backup configuration: {output}")
            return False
    
    def get_config_xml(self) -> Optional[str]:
        """Get current OPNsense configuration XML"""
        success, config = self.ssh_command("cat /conf/config.xml")
        if success:
            return config
        else:
            print(f"❌ Failed to get configuration: {config}")
            return None
    
    def apply_config_xml(self, xml_content: str) -> bool:
        """Apply new configuration XML to OPNsense"""
        try:
            # Create temporary file with new config
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as temp_file:
                temp_file.write(xml_content)
                temp_file_path = temp_file.name
            
            # Copy to OPNsense
            scp_cmd = [
                "scp", "-i", self.ssh_key_path,
                temp_file_path,
                f"root@{self.router_ip}:/tmp/new_config.xml"
            ]
            
            result = subprocess.run(scp_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Failed to copy config: {result.stderr}")
                return False
            
            # Apply the configuration
            success, output = self.ssh_command("mv /tmp/new_config.xml /conf/config.xml")
            if not success:
                print(f"❌ Failed to apply config: {output}")
                return False
            
            # Apply pending changes and reload the configuration
            # First apply any pending changes
            success, output = self.ssh_command("configctl webgui restart configd")
            if not success:
                print(f"⚠️ Warning: Failed to restart configd: {output}")
            
            # Apply the filter configuration specifically
            success, output = self.ssh_command("configctl filter reload")
            if not success:
                print(f"⚠️ Warning: Failed initial filter reload: {output}")
            
            # Force apply all pending changes
            success, output = self.ssh_command("/usr/local/etc/rc.configure_firewall")
            if success:
                print("✅ Configuration applied and firewall reloaded")
                return True
            else:
                print(f"❌ Failed to apply firewall config: {output}")
                # Try alternative reload method
                success, output = self.ssh_command("/usr/local/etc/rc.filter_configure")
                if success:
                    print("✅ Configuration applied via alternative method")
                    return True
                else:
                    print(f"❌ Failed to reload config: {output}")
                    return False
        
        except Exception as e:
            print(f"❌ Error applying configuration: {e}")
            return False
        finally:
            # Clean up temp file
            try:
                Path(temp_file_path).unlink()
            except:
                pass
    
    def find_alias_by_name(self, root: ET.Element, alias_name: str) -> Optional[ET.Element]:
        """Find existing alias by name in XML"""
        # Look in the correct location: OPNsense/Firewall/Alias/aliases
        aliases_section = root.find(".//OPNsense/Firewall/Alias/aliases")
        if aliases_section is None:
            return None
        
        for alias in aliases_section.findall("alias"):
            name_elem = alias.find("name")
            if name_elem is not None and name_elem.text == alias_name:
                return alias
        
        return None
    
    def create_or_update_mac_alias(self, alias_name: str = "ParentalControlMACs") -> bool:
        """Create or update MAC address alias in OPNsense"""
        print(f"🔧 Creating/updating MAC alias: {alias_name}")
        
        # Get current devices
        enabled_devices = self.mac_manager.get_enabled_devices()
        if not enabled_devices:
            print("⚠️ No enabled devices found")
            return False
        
        # Backup configuration first
        if not self.backup_config():
            return False
        
        # Get current configuration
        config_xml = self.get_config_xml()
        if not config_xml:
            return False
        
        try:
            # Parse XML
            root = ET.fromstring(config_xml)
            
# Find or create aliases section in correct OPNsense structure
            opnsense = root.find("OPNsense")
            if opnsense is None:
                opnsense = ET.SubElement(root, "OPNsense")
            
            firewall = opnsense.find("Firewall")
            if firewall is None:
                firewall = ET.SubElement(opnsense, "Firewall")
            
            alias_section = firewall.find("Alias")
            if alias_section is None:
                alias_section = ET.SubElement(firewall, "Alias")
                ET.SubElement(alias_section, "version").text = "1.0.1"
            
            aliases = alias_section.find("aliases")
            if aliases is None:
                aliases = ET.SubElement(alias_section, "aliases")
            
            # Find existing alias or create new one
            existing_alias = self.find_alias_by_name(root, alias_name)
            
            if existing_alias is not None:
                print(f"📝 Updating existing alias: {alias_name}")
                alias_elem = existing_alias
            else:
                print(f"➕ Creating new alias: {alias_name}")
                alias_elem = ET.SubElement(aliases, "alias")
                alias_elem.set("uuid", str(uuid.uuid4()))
            
            # Clear existing content
            for child in list(alias_elem):
                alias_elem.remove(child)
            
            # Set alias properties
            ET.SubElement(alias_elem, "enabled").text = "1"
            ET.SubElement(alias_elem, "name").text = alias_name
            ET.SubElement(alias_elem, "type").text = "mac"
            ET.SubElement(alias_elem, "path_expression").text = ""
            ET.SubElement(alias_elem, "proto").text = ""
            ET.SubElement(alias_elem, "interface").text = ""
            ET.SubElement(alias_elem, "counters").text = "0"
            ET.SubElement(alias_elem, "updatefreq").text = ""
            
            # Add MAC addresses
            mac_addresses = [device['mac'] for device in enabled_devices]
            content = '\n'.join(mac_addresses)
            ET.SubElement(alias_elem, "content").text = content
            
            # Set description
            description = f"Parental Controls MAC Addresses ({len(enabled_devices)} devices) - Auto-generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ET.SubElement(alias_elem, "description").text = description
            
            # Convert back to XML string
            xml_str = ET.tostring(root, encoding='unicode')
            
            # Apply the configuration
            if self.apply_config_xml(xml_str):
                print(f"✅ MAC alias '{alias_name}' created/updated with {len(enabled_devices)} devices")
                
                # Print summary
                print("📱 Devices in alias:")
                for device in enabled_devices:
                    print(f"   • {device['name']}: {device['mac']}")
                
                return True
            else:
                return False
        
        except ET.ParseError as e:
            print(f"❌ XML parsing error: {e}")
            return False
        except Exception as e:
            print(f"❌ Error creating alias: {e}")
            return False
    
    def create_parental_control_rule(self, rule_name: str = "ParentalControlBlock", enabled: bool = True) -> bool:
        """Create firewall rule to block traffic from MAC alias"""
        print(f"🔥 Creating firewall rule: {rule_name}")
        
        # Backup configuration first
        if not self.backup_config():
            return False
        
        # Get current configuration
        config_xml = self.get_config_xml()
        if not config_xml:
            return False
        
        try:
            # Parse XML
            root = ET.fromstring(config_xml)
            
            # Find filter section
            filter_section = root.find("filter")
            if filter_section is None:
                filter_section = ET.SubElement(root, "filter")
            
            # Check if rule already exists
            existing_rule = None
            for rule in filter_section.findall("rule"):
                descr = rule.find("descr")
                if descr is not None and descr.text and rule_name in descr.text:
                    existing_rule = rule
                    break
            
            if existing_rule is not None:
                print(f"📝 Updating existing rule: {rule_name}")
                rule_elem = existing_rule
                # Clear existing content
                for child in list(rule_elem):
                    rule_elem.remove(child)
            else:
                print(f"➕ Creating new rule: {rule_name}")
                rule_elem = ET.SubElement(filter_section, "rule")
                rule_elem.set("uuid", str(uuid.uuid4()))
            
            # Set rule properties
            ET.SubElement(rule_elem, "type").text = "block"
            ET.SubElement(rule_elem, "interface").text = "lan"
            ET.SubElement(rule_elem, "ipprotocol").text = "inet46"
            ET.SubElement(rule_elem, "statetype").text = "keep state"
            ET.SubElement(rule_elem, "direction").text = "in"
            ET.SubElement(rule_elem, "quick").text = "1"
            ET.SubElement(rule_elem, "disabled").text = "0" if enabled else "1"
            
            # Source (MAC alias)
            source = ET.SubElement(rule_elem, "source")
            ET.SubElement(source, "address").text = "ParentalControlMACs"
            
            # Destination (any)
            destination = ET.SubElement(rule_elem, "destination")
            ET.SubElement(destination, "any").text = "1"
            
            # Description
            description = f"{rule_name} - Block devices in ParentalControlMACs alias - Auto-generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ET.SubElement(rule_elem, "descr").text = description
            
            # Convert back to XML string
            xml_str = ET.tostring(root, encoding='unicode')
            
            # Apply the configuration
            if self.apply_config_xml(xml_str):
                print(f"✅ Firewall rule '{rule_name}' created/updated ({'enabled' if enabled else 'disabled'})")
                return True
            else:
                return False
        
        except Exception as e:
            print(f"❌ Error creating firewall rule: {e}")
            return False
    
    def toggle_parental_controls(self, enable: bool) -> bool:
        """Toggle parental control rule on/off"""
        action = "enable" if enable else "disable"
        print(f"🔄 {action.title()}ing parental controls...")
        
        # Get current configuration
        config_xml = self.get_config_xml()
        if not config_xml:
            return False
        
        try:
            # Parse XML
            root = ET.fromstring(config_xml)
            
            # Find the parental control rule
            filter_section = root.find("filter")
            if filter_section is None:
                print("❌ No filter section found")
                return False
            
            rule_found = False
            for rule in filter_section.findall("rule"):
                descr = rule.find("descr")
                if descr is not None and descr.text and "ParentalControlBlock" in descr.text:
                    # Update the disabled flag
                    disabled_elem = rule.find("disabled")
                    if disabled_elem is None:
                        disabled_elem = ET.SubElement(rule, "disabled")
                    
                    disabled_elem.text = "0" if enable else "1"
                    rule_found = True
                    break
            
            if not rule_found:
                print("❌ Parental control rule not found")
                return False
            
            # Convert back to XML string
            xml_str = ET.tostring(root, encoding='unicode')
            
            # Apply the configuration
            if self.apply_config_xml(xml_str):
                print(f"✅ Parental controls {action}d successfully")
                return True
            else:
                return False
        
        except Exception as e:
            print(f"❌ Error toggling parental controls: {e}")
            return False
    
    def get_parental_control_status(self) -> Dict:
        """Get current status of parental controls"""
        config_xml = self.get_config_xml()
        if not config_xml:
            return {"error": "Failed to get configuration"}
        
        try:
            root = ET.fromstring(config_xml)
            
            # Check for MAC alias
            alias_exists = self.find_alias_by_name(root, "ParentalControlMACs") is not None
            
            # Check for firewall rule
            rule_enabled = False
            rule_exists = False
            
            filter_section = root.find("filter")
            if filter_section is not None:
                for rule in filter_section.findall("rule"):
                    descr = rule.find("descr")
                    if descr is not None and descr.text and "ParentalControlBlock" in descr.text:
                        rule_exists = True
                        disabled_elem = rule.find("disabled")
                        rule_enabled = disabled_elem is None or disabled_elem.text != "1"
                        break
            
            # Get device count
            enabled_devices = self.mac_manager.get_enabled_devices()
            
            return {
                "alias_exists": alias_exists,
                "rule_exists": rule_exists,
                "rule_enabled": rule_enabled,
                "device_count": len(enabled_devices),
                "controls_active": alias_exists and rule_exists and rule_enabled,
                "last_checked": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"error": f"Failed to get status: {e}"}


def main():
    """Main function for testing"""
    print("🔧 OPNsense Parental Controls Integration")
    print("=" * 50)
    
    manager = OPNsenseManager()
    
    # Test connection
    print("\n🔗 Testing OPNsense connection...")
    success, output = manager.ssh_command("echo 'Connection test successful'")
    if success:
        print(f"✅ {output}")
    else:
        print(f"❌ Connection failed: {output}")
        return
    
    # Get current status
    print("\n📊 Current status:")
    status = manager.get_parental_control_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Ask user what to do
    print("\n🤔 What would you like to do?")
    print("1. Create/update MAC alias")
    print("2. Create/update firewall rule")
    print("3. Enable parental controls")
    print("4. Disable parental controls")
    print("5. Setup complete system (alias + rule)")
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == "1":
        manager.create_or_update_mac_alias()
    elif choice == "2":
        manager.create_parental_control_rule()
    elif choice == "3":
        manager.toggle_parental_controls(True)
    elif choice == "4":
        manager.toggle_parental_controls(False)
    elif choice == "5":
        print("\n🚀 Setting up complete parental control system...")
        if manager.create_or_update_mac_alias():
            if manager.create_parental_control_rule(enabled=False):
                print("✅ Complete setup successful! Use option 3 to enable controls.")
            else:
                print("❌ Rule creation failed")
        else:
            print("❌ Alias creation failed")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
