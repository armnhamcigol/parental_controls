# Parental Controls Automation Project

## Overview
A comprehensive local automation system for managing children's screen time and device access across multiple platforms. This project integrates Nintendo Switch parental controls, Google Family Link, Microsoft Family Safety, and OPNSense firewall rules to provide centralized parental control management.

## Project Goals
- **Unified Control**: Single interface to manage restrictions across all platforms
- **Automation**: Scheduled application of parental controls based on time/day
- **Local Operation**: No cloud dependencies - runs entirely on local infrastructure
- **Security**: Secure credential management and comprehensive audit logging
- **Flexibility**: Easy override and adjustment capabilities for parents

## Architecture

### Technology Stack
- **Backend**: Node.js with JavaScript (per user preference)
- **Frontend**: Simple HTML/CSS/JavaScript with Express.js server
- **Database**: Local JSON files or SQLite for configuration storage
- **Security**: Local encryption for sensitive credentials
- **Logging**: File-based audit logging with rotation

### Platform Integrations
1. **Nintendo Switch Parental Controls**: API/app automation for gaming restrictions
2. **Google Family Link**: OAuth2 integration for Android device management
3. **Microsoft Family Safety**: Microsoft Graph API for Windows/Xbox controls
4. **OPNSense Firewall**: SSH-based rule management for network-level blocking

## Directory Structure
```
C:\Warp\parental_control\
├── WARP.md                 # This documentation
├── package.json            # Node.js dependencies
├── .gitignore             # Git ignore patterns
├── config/                # Configuration files (encrypted)
│   ├── credentials.enc    # Encrypted API credentials
│   ├── profiles.json      # Child profiles and settings
│   └── schedules.json     # Automated scheduling rules
├── src/                   # Source code
│   ├── controller.js      # Main orchestration layer
│   ├── nintendo/          # Nintendo Switch integration
│   │   └── controller.js
│   ├── google/            # Google Family Link integration
│   │   └── family.js
│   ├── microsoft/         # Microsoft Family Safety integration
│   │   └── family.js
│   ├── opnsense/          # OPNSense firewall integration
│   │   └── firewall.js
│   ├── web/               # Web dashboard
│   │   ├── index.html
│   │   ├── style.css
│   │   └── app.js
│   └── utils/             # Utility functions
│       ├── encryption.js  # Credential encryption/decryption
│       ├── logger.js      # Audit logging
│       └── scheduler.js   # Task scheduling
├── logs/                  # Log files
│   ├── audit.log         # Comprehensive audit trail
│   ├── errors.log        # Error logging
│   └── access.log        # Web dashboard access
└── tests/                 # Test files
    ├── unit/             # Unit tests
    └── integration/      # Integration tests
```

## Network Infrastructure

### OPNSense Firewall Access
- **SSH Connection**: `ssh -i ~/.ssh/id_ed25519_opnsense root@192.168.123.1`
- **Firewall Rules**: Create/modify rules to block gaming devices by MAC/IP
- **Device Management**: Track and manage gaming console network access

### Raspberry Pi Integration (Optional)
- **SSH Connection**: `ssh -i ~/.ssh/id_rsa_raspberry_pi pi@192.168.123.7`
- **Local Monitoring**: Additional monitoring or control node if needed

## Security Considerations

### Credential Management
- **No Hard-coded Secrets**: All credentials stored in encrypted configuration files
- **Local Encryption**: Use Node.js crypto module for credential encryption
- **Key Rotation**: Regular rotation procedures for API credentials and SSH keys
- **Environment Variables**: Use .env files for non-sensitive configuration

### Audit Logging
- **Comprehensive Logging**: All actions logged with timestamps and user context
- **Log Rotation**: Automatic log file rotation to prevent disk space issues
- **Audit Trail**: Complete trail of all parental control changes
- **Error Tracking**: Detailed error logging for troubleshooting

## Development Guidelines

### Code Standards
- **JavaScript**: Use modern ES6+ features, maintain consistent coding style
- **Error Handling**: Comprehensive error handling with graceful degradation
- **Modular Design**: Separate modules for each platform integration
- **Configuration**: External configuration files, no hardcoded values

### Testing Strategy
- **Unit Tests**: Test individual functions and modules
- **Integration Tests**: Test API connections (use carefully with real services)
- **Dry Run Mode**: Test mode that simulates changes without applying them
- **Validation Scripts**: Check connectivity and credentials before operations

### Git Workflow
- **No New Branches**: Work on main branch only (per user rules)
- **Small Commits**: Incremental changes that are tested individually
- **Comprehensive Messages**: Clear commit messages describing changes

## Platform-Specific Implementation

### Nintendo Switch Parental Controls
- **Research Required**: Identify available APIs or automation methods
- **Features**: Screen time limits, game restrictions, bedtime enforcement
- **Authentication**: Handle Nintendo account authentication securely
- **Scheduling**: Automated application of daily/weekly restrictions

### Google Family Link
- **OAuth2 Flow**: Implement secure Google OAuth2 authentication
- **API Integration**: Use Family Link API for device management
- **Features**: App time limits, device bedtime, location tracking
- **Error Handling**: Robust handling of API rate limits and errors

### Microsoft Family Safety
- **Graph API**: Integration with Microsoft Graph for family features
- **Features**: Screen time, app restrictions, content filters
- **Authentication**: Microsoft account authentication with proper scopes
- **Monitoring**: Activity reports and usage statistics

### OPNSense Firewall
- **SSH Automation**: Secure SSH connection for rule management
- **Rule Management**: Create/delete firewall rules for device blocking
- **Device Tracking**: Maintain database of device MAC addresses and IPs
- **Network Control**: Block internet access at network level

## Installation and Setup

### Prerequisites
- Node.js 18+ installed
- SSH key access to OPNSense firewall configured
- API credentials for Google, Microsoft, and Nintendo services
- Git repository initialized

### Initial Setup
1. Clone/initialize repository in `C:\Warp\parental_control\`
2. Run `npm install` to install dependencies
3. Configure encrypted credential storage
4. Set up child profiles and initial restrictions
5. Test connectivity to all platforms
6. Configure automated scheduling (optional)

### Configuration Steps
1. **API Credentials**: Securely store all API keys and secrets
2. **Child Profiles**: Create profiles for each child with individual settings
3. **Device Inventory**: Document all gaming devices and their MAC/IP addresses
4. **Schedule Setup**: Configure automated restriction schedules
5. **Testing**: Run validation scripts to ensure all integrations work

## Operations and Maintenance

### Daily Operations
- **Health Checks**: Automated verification that all integrations are functional
- **Log Monitoring**: Review audit logs for any issues or unauthorized changes
- **Status Dashboard**: Web interface showing current restrictions across all platforms

### Rollback Procedures
- **Nintendo Switch**: Document steps to revert parental control changes
- **Google Family**: Process to remove or modify Family Link restrictions
- **Microsoft Family**: Steps to adjust or remove Family Safety settings
- **OPNSense**: Commands to remove firewall rules and restore access
- **Configuration Backup**: Regular backups of all configuration files

### Troubleshooting
- **Connectivity Issues**: Steps to diagnose and resolve API connection problems
- **Authentication Problems**: Procedures for refreshing expired credentials
- **SSH Access**: Troubleshooting OPNSense firewall SSH connectivity
- **Log Analysis**: How to use audit logs for problem diagnosis

## Future Enhancements
- **Mobile App**: React Native app for remote parental control
- **Advanced Scheduling**: More sophisticated time-based rule management
- **Reporting**: Detailed usage reports and analytics
- **Additional Platforms**: Integration with other gaming platforms (PlayStation, Steam, etc.)
- **Machine Learning**: Automated detection of excessive usage patterns

## Support and Documentation
- **API Documentation**: Links to official documentation for each platform
- **Community Resources**: Relevant forums and communities for each platform
- **Troubleshooting Guides**: Platform-specific troubleshooting procedures
- **Update Procedures**: How to update the system when APIs change

---

*Last Updated: 2025-08-18*
*Project: Local Parental Controls Automation*
*Environment: Windows 11 with WSL2 Ubuntu*
