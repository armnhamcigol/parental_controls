// Enhanced Nintendo Switch Parental Controls Dashboard JavaScript
class ParentalControlsDashboard {
    constructor() {
        this.currentState = {
            controlsActive: false,
            lastToggleTime: null,
            lastToggleReason: null,
            systemStatus: 'loading'
        };
        
        this.nintendoDevices = [];
        this.activityLog = [];
        this.init();
    }

    // Initialize the dashboard
    async init() {
        console.log('🎮 Initializing Enhanced Nintendo Switch Parental Controls Dashboard');
        
        this.setupEventListeners();
        await this.loadStatus();
        await this.loadNintendoDevices();
        this.startPeriodicUpdates();
        
        // Show the dashboard with fade-in effect
        document.querySelector('.container').classList.add('fade-in');
    }

    // Setup event listeners
    setupEventListeners() {
        const toggle = document.getElementById('controlsToggle');
        if (toggle) {
            toggle.addEventListener('change', this.handleToggleChange.bind(this));
        }

        // Refresh status when window gains focus
        window.addEventListener('focus', () => {
            this.loadStatus();
        });

        // Handle keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            if (event.ctrlKey && event.key === ' ') {
                event.preventDefault();
                this.toggleControls('Keyboard shortcut');
            }
        });
    }

    // Load current status from API
    async loadStatus() {
        try {
            const response = await fetch('/health');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.updateHealthStatus(data);
            this.updateLastUpdated();
            
        } catch (error) {
            console.error('Failed to load status:', error);
            this.showError('Failed to connect to server');
            this.updateSystemStatus('error');
        }
    }

    // Update dashboard with new status data
    updateStatus(data) {
        this.currentState = data;
        
        // Update toggle state
        const toggle = document.getElementById('controlsToggle');
        if (toggle) {
            toggle.checked = data.controlsActive;
        }
        
        // Update status display
        this.updateSystemStatus(data.systemStatus);
        this.updateLastAction(data.lastToggleReason, data.lastToggleTime);
        this.updateUptime(data.uptime);
        this.updateToggleDescription();
        
        // Update platform status (simulated for now)
        this.updatePlatformStatus();
        
        console.log('📊 Status updated:', data);
    }

    // Update system status indicator
    updateSystemStatus(status) {
        const statusElement = document.getElementById('systemStatus');
        if (statusElement) {
            statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            statusElement.className = `status-value ${status}`;
        }
    }

    // Update last action display
    updateLastAction(reason, time) {
        const actionElement = document.getElementById('lastAction');
        if (actionElement) {
            if (reason && time) {
                const timeAgo = this.getTimeAgo(time);
                actionElement.textContent = `${reason} (${timeAgo})`;
            } else {
                actionElement.textContent = 'None';
            }
        }
    }

    // Update uptime display
    updateUptime(uptimeSeconds) {
        const uptimeElement = document.getElementById('uptime');
        if (uptimeElement && uptimeSeconds) {
            uptimeElement.textContent = this.formatUptime(uptimeSeconds);
        }
    }

    // Update toggle description based on current state
    updateToggleDescription() {
        const descElement = document.getElementById('toggleDescription');
        if (descElement) {
            if (this.currentState.controlsActive) {
                descElement.textContent = '🚫 Parental controls are currently ACTIVE - Gaming and apps are restricted';
                descElement.style.color = '#c53030';
            } else {
                descElement.textContent = '🎮 Parental controls are currently OFF - Kids have full access';
                descElement.style.color = '#2f855a';
            }
        }
    }

    // Update health status from backend
    updateHealthStatus(data) {
        this.updateSystemStatus(data.status || 'unknown');
        
        // Update platform status indicators
        const nintendoStatus = document.getElementById('nintendoStatus');
        if (nintendoStatus) {
            const status = data.components?.nintendo || 'unknown';
            nintendoStatus.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            nintendoStatus.className = `platform-status-badge ${status}`;
        }
        
        const monitoringStatus = document.getElementById('monitoringStatus');
        if (monitoringStatus) {
            const status = this.nintendoDevices.length > 0 ? 'active' : 'inactive';
            monitoringStatus.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            monitoringStatus.className = `platform-status-badge ${status}`;
        }
        
        const backendStatus = document.getElementById('backendStatus');
        if (backendStatus) {
            const status = data.status === 'healthy' ? 'connected' : 'disconnected';
            backendStatus.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            backendStatus.className = `platform-status-badge ${status}`;
        }
        
        console.log('📊 Health status updated:', data);
    }

    // Handle toggle switch change
    async handleToggleChange(event) {
        const newState = event.target.checked;
        const reason = newState ? 'Manual activation' : 'Manual deactivation';
        
        await this.toggleControlsWithState(newState, reason);
    }

    // Toggle parental controls (flip current state)
    async toggleControls(reason = 'Manual toggle', duration = null) {
        const newState = !this.currentState.controlsActive;
        await this.toggleControlsWithState(newState, reason, duration);
    }
    
    // Toggle parental controls to specific state
    async toggleControlsWithState(targetState, reason = 'Manual toggle', duration = null) {
        this.showLoading(true);
        
        try {
            // Use query parameters instead of JSON body to avoid parsing issues
            const params = new URLSearchParams({
                active: targetState.toString(),
                reason: reason
            });
            
            if (duration) {
                params.append('duration', duration.toString());
            }
            
            const response = await fetch(`/api/toggle?${params.toString()}`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.currentState.controlsActive = result.controlsActive;
                this.updateStatus(result);
                this.addToActivityLog(reason, result.controlsActive);
                this.showSuccess(result.message);
                
                // Add visual feedback
                this.flashToggle();
                
                console.log('✅ Toggle successful:', result);
            } else {
                throw new Error(result.error || 'Toggle failed');
            }
            
        } catch (error) {
            console.error('❌ Toggle failed:', error);
            this.showError(`Failed to toggle controls: ${error.message}`);
            
            // Reset toggle to previous state
            const toggle = document.getElementById('controlsToggle');
            if (toggle) {
                toggle.checked = this.currentState.controlsActive;
            }
        } finally {
            this.showLoading(false);
        }
    }

    // Add flash effect to toggle
    flashToggle() {
        const toggleSection = document.querySelector('.toggle-section');
        if (toggleSection) {
            toggleSection.style.transform = 'scale(1.05)';
            setTimeout(() => {
                toggleSection.style.transform = 'scale(1)';
            }, 200);
        }
    }

    // Add activity to log
    addToActivityLog(action, controlsActive) {
        const activity = {
            action: `${action} - Controls ${controlsActive ? 'activated' : 'deactivated'}`,
            timestamp: new Date().toISOString(),
            type: controlsActive ? 'activation' : 'deactivation'
        };
        
        this.activityLog.unshift(activity);
        
        // Keep only last 10 activities
        if (this.activityLog.length > 10) {
            this.activityLog = this.activityLog.slice(0, 10);
        }
        
        this.updateActivityDisplay();
    }

    // Update activity log display
    updateActivityDisplay() {
        const activityList = document.getElementById('activityList');
        if (!activityList) return;
        
        if (this.activityLog.length === 0) {
            activityList.innerHTML = '<p class="no-activity">No recent activity</p>';
            return;
        }
        
        const html = this.activityLog.map(activity => `
            <div class="activity-item">
                <span class="activity-action">${activity.action}</span>
                <span class="activity-time">${this.getTimeAgo(activity.timestamp)}</span>
            </div>
        `).join('');
        
        activityList.innerHTML = html;
    }

    // Show loading overlay
    showLoading(show = true) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            if (show) {
                overlay.classList.add('active');
            } else {
                overlay.classList.remove('active');
            }
        }
    }

    // Show success message
    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    // Show error message
    showError(message) {
        this.showMessage(message, 'error');
    }

    // Show message with auto-dismiss
    showMessage(message, type = 'info') {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.message');
        existingMessages.forEach(msg => msg.remove());
        
        // Create new message
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;
        
        // Insert after status panel
        const statusPanel = document.querySelector('.status-panel');
        if (statusPanel) {
            statusPanel.insertAdjacentElement('afterend', messageDiv);
        }
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }

    // Update last updated timestamp
    updateLastUpdated() {
        const lastUpdatedElement = document.getElementById('lastUpdated');
        if (lastUpdatedElement) {
            lastUpdatedElement.textContent = new Date().toLocaleTimeString();
        }
    }

    // Load Nintendo Switch devices
    async loadNintendoDevices() {
        try {
            const response = await fetch('/api/nintendo/devices');
            if (!response.ok) {
                if (response.status === 401) {
                    this.showError('Nintendo Switch not authenticated');
                    return;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            if (data.success) {
                this.nintendoDevices = data.devices;
                this.updateNintendoDeviceDisplay();
                this.updateDeviceCount(data.count);
                console.log('🎮 Nintendo devices loaded:', data.devices);
            } else {
                throw new Error(data.error || 'Failed to load devices');
            }
            
        } catch (error) {
            console.error('Failed to load Nintendo devices:', error);
            this.showNintendoDeviceError('Failed to load Nintendo Switch devices');
        }
    }
    
    // Update Nintendo device display
    updateNintendoDeviceDisplay() {
        const deviceList = document.getElementById('nintendoDeviceList');
        if (!deviceList) return;
        
        if (this.nintendoDevices.length === 0) {
            deviceList.innerHTML = `
                <div class="no-devices">
                    <p>🎮 No Nintendo Switch devices found</p>
                    <small>Devices will appear here when detected on the network</small>
                </div>
            `;
            return;
        }
        
        const html = this.nintendoDevices.map(device => `
            <div class="device-card ${device.online ? 'online' : 'offline'}">
                <div class="device-header">
                    <div class="device-info">
                        <h4 class="device-name">
                            🎮 ${device.device_name}
                            <span class="device-status ${device.online ? 'online' : 'offline'}">
                                ${device.online ? '🟢 Online' : '🔴 Offline'}
                            </span>
                        </h4>
                        <p class="device-location">${device.location || device.ip_address}</p>
                    </div>
                    <div class="device-controls">
                        <label class="device-toggle">
                            <input type="checkbox" 
                                   ${device.controls_enabled ? 'checked' : ''}
                                   onchange="toggleDeviceControls('${device.device_id}', this.checked)">
                            <span class="device-slider"></span>
                        </label>
                    </div>
                </div>
                
                <div class="device-details">
                    <div class="device-stat">
                        <span class="stat-label">Current Game:</span>
                        <span class="stat-value game-title">${device.current_game || 'Unknown'}</span>
                    </div>
                    
                    <div class="device-stat">
                        <span class="stat-label">Session Time:</span>
                        <span class="stat-value">${device.current_session_minutes || 0} min</span>
                    </div>
                    
                    <div class="device-stat">
                        <span class="stat-label">Response Time:</span>
                        <span class="stat-value">${device.response_time_ms ? device.response_time_ms.toFixed(1) : 'N/A'}ms</span>
                    </div>
                    
                    <div class="device-stat">
                        <span class="stat-label">Activity Level:</span>
                        <span class="stat-value activity-${device.network_activity_level}">
                            ${device.network_activity_level ? device.network_activity_level.charAt(0).toUpperCase() + device.network_activity_level.slice(1) : 'Unknown'}
                        </span>
                    </div>
                    
                    <div class="device-stat">
                        <span class="stat-label">Daily Play Time:</span>
                        <span class="stat-value">${device.today_play_time_minutes || 0} / ${device.daily_limit_minutes || 120} min</span>
                    </div>
                </div>
                
                ${device.enhanced_discovery ? '<div class="enhanced-badge">⚡ Enhanced Discovery</div>' : ''}
            </div>
        `).join('');
        
        deviceList.innerHTML = html;
    }
    
    // Show error for Nintendo device loading
    showNintendoDeviceError(message) {
        const deviceList = document.getElementById('nintendoDeviceList');
        if (deviceList) {
            deviceList.innerHTML = `
                <div class="device-error">
                    <p>❌ ${message}</p>
                    <button onclick="window.dashboard.loadNintendoDevices()" class="retry-btn">🔄 Retry</button>
                </div>
            `;
        }
    }
    
    // Update device count
    updateDeviceCount(count) {
        const deviceCountElement = document.getElementById('deviceCount');
        if (deviceCountElement) {
            deviceCountElement.textContent = count.toString();
        }
    }
    
    // Toggle device controls
    async toggleDeviceControls(deviceId, targetState) {
        console.log(`🎯 DEBUG: Starting device toggle for ${deviceId}, targetState: ${targetState}`);
        this.showLoading(true);
        
        try {
            const requestData = {
                device_id: deviceId,
                active: targetState
            };
            
            console.log('📤 DEBUG: Sending request to /api/nintendo/device_toggle', requestData);
            
            const response = await fetch('/api/nintendo/device_toggle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            console.log(`📥 DEBUG: Response status: ${response.status} ${response.statusText}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ DEBUG: Response not OK, body:', errorText);
                throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
            }
            
            const result = await response.json();
            console.log('📊 DEBUG: Response data:', result);
            
            if (result.success) {
                console.log('✅ DEBUG: Toggle successful, showing success message');
                this.showSuccess(result.message || `Device ${deviceId} controls ${targetState ? 'enabled' : 'disabled'}`);
                
                // Add visual feedback
                this.showMessage(`🎮 ${deviceId}: Controls ${targetState ? 'enabled' : 'disabled'}`, 'info');
                
                // Reload devices to get updated state
                console.log('🔄 DEBUG: Reloading devices to get updated state');
                await this.loadNintendoDevices();
                console.log('✅ DEBUG: Device toggle complete');
            } else {
                console.error('❌ DEBUG: Server returned success=false:', result);
                throw new Error(result.error || 'Device toggle failed');
            }
            
        } catch (error) {
            console.error('❌ DEBUG: Device toggle failed with error:', error);
            console.error('❌ DEBUG: Error stack:', error.stack);
            this.showError(`Failed to toggle ${deviceId} controls: ${error.message}`);
            
            // Reload devices to reset toggle state
            console.log('🔄 DEBUG: Reloading devices after error to reset state');
            await this.loadNintendoDevices();
        } finally {
            console.log('🏁 DEBUG: Device toggle finally block, hiding loading');
            this.showLoading(false);
        }
    }
    
    // Start periodic status updates
    startPeriodicUpdates() {
        // Update every 30 seconds
        setInterval(() => {
            this.loadStatus();
            this.loadNintendoDevices();
        }, 30000);
        
        // Update relative times every minute
        setInterval(() => {
            this.updateActivityDisplay();
            this.updateLastAction(this.currentState.lastToggleReason, this.currentState.lastToggleTime);
        }, 60000);
    }

    // Utility: Get time ago string
    getTimeAgo(timestamp) {
        if (!timestamp) return '';
        
        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffDays > 0) return `${diffDays}d ago`;
        if (diffHours > 0) return `${diffHours}h ago`;
        if (diffMins > 0) return `${diffMins}m ago`;
        return 'Just now';
    }

    // Utility: Format uptime
    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) return `${days}d ${hours}h ${minutes}m`;
        if (hours > 0) return `${hours}h ${minutes}m`;
        if (minutes > 0) return `${minutes}m`;
        return `${Math.floor(seconds)}s`;
    }
}

// Global functions for quick action buttons
async function toggleWithReason(reason) {
    if (window.dashboard) {
        await window.dashboard.toggleControls(reason);
    }
}

async function toggleWithDuration(reason, durationMinutes) {
    if (window.dashboard) {
        await window.dashboard.toggleControls(reason, durationMinutes);
    }
}

// Global function for device control toggles
async function toggleDeviceControls(deviceId, targetState) {
    console.log(`🎮 DEBUG: Global toggleDeviceControls called with deviceId='${deviceId}', targetState=${targetState}`);
    if (window.dashboard) {
        console.log('✅ DEBUG: Dashboard found, calling method');
        await window.dashboard.toggleDeviceControls(deviceId, targetState);
    } else {
        console.error('❌ DEBUG: window.dashboard not found!');
        console.error('❌ DEBUG: Available on window:', Object.keys(window).filter(k => k.includes('dash')));
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DEBUG: DOM loaded, initializing dashboard...');
    try {
        window.dashboard = new ParentalControlsDashboard();
        console.log('✅ DEBUG: Dashboard initialized successfully');
        
        // Test the global function
        window.testToggle = function() {
            console.log('🧪 DEBUG: Test function called');
            if (window.dashboard) {
                console.log('✅ DEBUG: Dashboard object exists');
                window.dashboard.toggleDeviceControls('newswitch', false);
            } else {
                console.error('❌ DEBUG: Dashboard object not found');
            }
        };
        console.log('🧪 DEBUG: Test function created. Try: testToggle()');
        
    } catch (error) {
        console.error('❌ DEBUG: Failed to initialize dashboard:', error);
        console.error('❌ DEBUG: Error stack:', error.stack);
    }
});

// Service Worker for offline functionality (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then((registration) => {
                console.log('SW registered: ', registration);
            })
            .catch((registrationError) => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
