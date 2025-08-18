#!/usr/bin/env python3
"""
Debug script to check OPNsense firewall rule state
"""

import subprocess
import xml.etree.ElementTree as ET
import sys

def ssh_command(command):
    """Execute SSH command on OPNsense"""
    try:
        ssh_cmd = [
            "ssh", "-i", "/home/pi/.ssh/id_ed25519_opnsense", 
            "root@192.168.123.1",
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

def analyze_config():
    """Analyze the current OPNsense configuration"""
    print("🔍 Analyzing OPNsense configuration...")
    
    # Get the config
    success, config = ssh_command("cat /conf/config.xml")
    if not success:
        print(f"❌ Failed to get config: {config}")
        return
    
    try:
        root = ET.fromstring(config)
        
        # Find all rules in filter section
        filter_section = root.find("filter")
        if filter_section is None:
            print("❌ No filter section found")
            return
        
        print(f"📋 Found filter section with {len(filter_section.findall('rule'))} rules")
        
        # Look for parental control rules
        for i, rule in enumerate(filter_section.findall("rule")):
            descr = rule.find("descr")
            if descr is not None and descr.text:
                if "ParentalControl" in descr.text:
                    print(f"\n🎯 Found ParentalControl rule #{i}:")
                    print(f"   Description: {descr.text}")
                    
                    # Check if disabled
                    disabled_elem = rule.find("disabled")
                    if disabled_elem is not None:
                        print(f"   Disabled: {disabled_elem.text}")
                        is_enabled = disabled_elem.text != "1"
                    else:
                        print(f"   Disabled: (no disabled element - rule is enabled)")
                        is_enabled = True
                    
                    print(f"   Status: {'🟢 ENABLED' if is_enabled else '🔴 DISABLED'}")
                    
                    # Show other rule details
                    interface = rule.find("interface")
                    if interface is not None:
                        print(f"   Interface: {interface.text}")
                    
                    protocol = rule.find("protocol")
                    if protocol is not None:
                        print(f"   Protocol: {protocol.text}")
                    
                    # Check source
                    source = rule.find("source")
                    if source is not None:
                        address = source.find("address")
                        if address is not None:
                            print(f"   Source: {address.text}")
                    
                    # Show full rule XML (first 500 chars)
                    rule_xml = ET.tostring(rule, encoding='unicode')[:500]
                    print(f"   XML Preview: {rule_xml}...")
        
        # Also check aliases
        print(f"\n🏷️  Checking aliases...")
        aliases_section = root.find(".//OPNsense/Firewall/Alias/aliases")
        if aliases_section is not None:
            for alias in aliases_section.findall("alias"):
                name_elem = alias.find("name")
                if name_elem is not None and "ParentalControl" in name_elem.text:
                    print(f"   Found alias: {name_elem.text}")
                    content = alias.find("content")
                    if content is not None:
                        print(f"   Content: {content.text[:100]}...")
        
    except Exception as e:
        print(f"❌ Error parsing config: {e}")

def test_reload_commands():
    """Test different reload commands"""
    print(f"\n🔄 Testing reload commands...")
    
    commands = [
        "/usr/local/etc/rc.filter_configure",
        "/usr/local/sbin/pfctl -f /tmp/rules.debug",
        "/usr/local/sbin/configctl filter reload",
        "configctl filter reload",
        "/usr/local/etc/rc.reload_all"
    ]
    
    for cmd in commands:
        print(f"\n🧪 Testing: {cmd}")
        success, output = ssh_command(cmd)
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        if output:
            print(f"   Output: {output[:200]}...")

if __name__ == "__main__":
    print("🛡️ OPNsense Rule Debug Script")
    print("=" * 50)
    
    analyze_config()
    test_reload_commands()
    
    print(f"\n🏁 Debug complete!")
