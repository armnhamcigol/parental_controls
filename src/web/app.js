// Parental Controls Dashboard JavaScript
class ParentalControlsDashboard {
    constructor() {
        this.currentState = {
            controlsActive: false,
            lastToggleTime: null,
            lastToggleReason: null,
            systemStatus: 'loading'
        };
        
        this.activityLog = [];
        this.init();
    }

    // Initialize the dashboard
    async init() {
        console.log('🛡️ Initializing Parental Controls Dashboard');
        
        this.setupEventListeners();
        await this.loadStatus();
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
            const response = await fetch('/api/status');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.updateStatus(data);
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

    // Update platform status indicators
    updatePlatformStatus() {
        const platforms = ['nintendo', 'google', 'microsoft', 'opnsense'];
        
        platforms.forEach(platform => {
            const statusElement = document.getElementById(`${platform}Status`);
            if (statusElement) {
                statusElement.textContent = 'Simulated';
                statusElement.className = 'platform-status-badge simulated';
            }
        });
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

    // Start periodic status updates
    startPeriodicUpdates() {
        // Update every 30 seconds
        setInterval(() => {
            this.loadStatus();
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

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new ParentalControlsDashboard();
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
