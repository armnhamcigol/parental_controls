import express from 'express';
import path from 'path';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import config from './utils/config.js';
import logger from './utils/logger.js';

class ParentalControlsController {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 3000;
    this.state = {
      controlsActive: false,
      lastToggleTime: null,
      lastToggleReason: null,
      systemStatus: 'initializing'
    };
    this.setupMiddleware();
    this.setupRoutes();
  }

  // Initialize the controller
  async initialize() {
    try {
      await config.initialize();
      
      // Load current state from config
      const savedState = config.get('state', {});
      this.state = {
        ...this.state,
        ...savedState,
        systemStatus: 'ready'
      };

      logger.info('Parental Controls Controller initialized', {
        controlsActive: this.state.controlsActive,
        port: this.port
      });
    } catch (error) {
      logger.error('Failed to initialize controller', { error: error.message });
      this.state.systemStatus = 'error';
      throw error;
    }
  }

  // Setup Express middleware
  setupMiddleware() {
    // Security middleware
    this.app.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          scriptSrc: ["'self'", "'unsafe-inline'"],
          imgSrc: ["'self'", "data:"]
        }
      }
    }));

    // Rate limiting
    const limiter = rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100, // limit each IP to 100 requests per windowMs
      message: 'Too many requests from this IP, please try again later.'
    });
    this.app.use('/api/', limiter);

    // CORS and parsing
    this.app.use(cors());
    this.app.use(express.json());
    this.app.use(express.urlencoded({ extended: true }));

    // Static files
    this.app.use(express.static(path.join(process.cwd(), 'src', 'web')));

    // Logging middleware
    this.app.use((req, res, next) => {
      logger.audit('HTTP Request', {
        method: req.method,
        url: req.url,
        ip: req.ip,
        userAgent: req.get('User-Agent')
      });
      next();
    });
  }

  // Setup API routes
  setupRoutes() {
    // Serve the main dashboard
    this.app.get('/', (req, res) => {
      res.sendFile(path.join(process.cwd(), 'src', 'web', 'index.html'));
    });

    // API Routes
    this.app.get('/api/status', this.getStatus.bind(this));
    this.app.post('/api/toggle', this.toggleControls.bind(this));
    this.app.get('/api/profiles', this.getProfiles.bind(this));
    this.app.post('/api/profiles', this.createProfile.bind(this));
    this.app.put('/api/profiles/:id', this.updateProfile.bind(this));
    this.app.delete('/api/profiles/:id', this.deleteProfile.bind(this));
    
    // Health check endpoint
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        systemStatus: this.state.systemStatus
      });
    });

    // 404 handler
    this.app.use((req, res) => {
      res.status(404).json({ error: 'Not found' });
    });

    // Error handler
    this.app.use((error, req, res, next) => {
      logger.error('Express error', { error: error.message, stack: error.stack });
      res.status(500).json({ error: 'Internal server error' });
    });
  }

  // Get current system status
  async getStatus(req, res) {
    try {
      const profiles = config.getAllChildProfiles();
      const systemInfo = {
        controlsActive: this.state.controlsActive,
        lastToggleTime: this.state.lastToggleTime,
        lastToggleReason: this.state.lastToggleReason,
        systemStatus: this.state.systemStatus,
        profileCount: profiles.length,
        uptime: process.uptime(),
        timestamp: new Date().toISOString()
      };

      res.json(systemInfo);
    } catch (error) {
      logger.error('Failed to get status', { error: error.message });
      res.status(500).json({ error: 'Failed to get status' });
    }
  }

  // Toggle parental controls on/off
  async toggleControls(req, res) {
    try {
      const { reason = 'Manual toggle', duration } = req.body;
      const newState = !this.state.controlsActive;
      
      logger.audit('Parental controls toggle requested', {
        currentState: this.state.controlsActive,
        newState,
        reason,
        duration,
        ip: req.ip
      });

      // Update state
      this.state.controlsActive = newState;
      this.state.lastToggleTime = new Date().toISOString();
      this.state.lastToggleReason = reason;

      // Save state to config
      await config.set('state', this.state);

      // Apply/remove controls across all platforms
      const result = await this.applyControlsToAllPlatforms(newState, reason);

      // Schedule automatic re-enable if duration specified
      if (newState === false && duration) {
        this.scheduleAutoReEnable(duration, 'Automatic re-enable after duration');
      }

      logger.audit('Parental controls toggled successfully', {
        controlsActive: this.state.controlsActive,
        reason,
        platformResults: result
      });

      res.json({
        success: true,
        controlsActive: this.state.controlsActive,
        message: `Parental controls ${newState ? 'activated' : 'deactivated'}`,
        lastToggleTime: this.state.lastToggleTime,
        lastToggleReason: this.state.lastToggleReason,
        platformResults: result
      });

    } catch (error) {
      logger.error('Failed to toggle controls', { error: error.message });
      res.status(500).json({ 
        success: false, 
        error: 'Failed to toggle controls',
        details: error.message 
      });
    }
  }

  // Apply controls to all platforms
  async applyControlsToAllPlatforms(enableControls, reason) {
    const results = {
      nintendo: { success: false, message: 'Not implemented yet' },
      google: { success: false, message: 'Not implemented yet' },
      microsoft: { success: false, message: 'Not implemented yet' },
      opnsense: { success: false, message: 'Not implemented yet' }
    };

    logger.audit('Applying controls to all platforms', {
      enableControls,
      reason,
      platforms: Object.keys(results)
    });

    // TODO: Implement actual platform integrations
    // For now, we'll simulate the operations

    // Simulate Nintendo Switch controls
    try {
      results.nintendo = { 
        success: true, 
        message: `Nintendo controls ${enableControls ? 'enabled' : 'disabled'} (simulated)` 
      };
      logger.nintendo(`Controls ${enableControls ? 'enabled' : 'disabled'}`, { reason });
    } catch (error) {
      results.nintendo = { success: false, message: error.message };
    }

    // Simulate Google Family controls
    try {
      results.google = { 
        success: true, 
        message: `Google Family controls ${enableControls ? 'enabled' : 'disabled'} (simulated)` 
      };
      logger.google(`Controls ${enableControls ? 'enabled' : 'disabled'}`, { reason });
    } catch (error) {
      results.google = { success: false, message: error.message };
    }

    // Simulate Microsoft Family controls
    try {
      results.microsoft = { 
        success: true, 
        message: `Microsoft Family controls ${enableControls ? 'enabled' : 'disabled'} (simulated)` 
      };
      logger.microsoft(`Controls ${enableControls ? 'enabled' : 'disabled'}`, { reason });
    } catch (error) {
      results.microsoft = { success: false, message: error.message };
    }

    // Simulate OPNSense firewall controls
    try {
      results.opnsense = { 
        success: true, 
        message: `Firewall rules ${enableControls ? 'enabled' : 'disabled'} (simulated)` 
      };
      logger.opnsense(`Firewall rules ${enableControls ? 'enabled' : 'disabled'}`, { reason });
    } catch (error) {
      results.opnsense = { success: false, message: error.message };
    }

    return results;
  }

  // Schedule automatic re-enable after specified duration
  scheduleAutoReEnable(durationMinutes, reason) {
    const durationMs = durationMinutes * 60 * 1000;
    
    setTimeout(async () => {
      try {
        logger.audit('Auto re-enabling parental controls', { 
          duration: durationMinutes,
          reason 
        });
        
        this.state.controlsActive = true;
        this.state.lastToggleTime = new Date().toISOString();
        this.state.lastToggleReason = reason;
        
        await config.set('state', this.state);
        await this.applyControlsToAllPlatforms(true, reason);
        
        logger.audit('Parental controls auto re-enabled', { duration: durationMinutes });
      } catch (error) {
        logger.error('Failed to auto re-enable controls', { error: error.message });
      }
    }, durationMs);

    logger.audit('Scheduled auto re-enable', { 
      durationMinutes, 
      scheduleTime: new Date(Date.now() + durationMs).toISOString() 
    });
  }

  // Get all child profiles
  async getProfiles(req, res) {
    try {
      const profiles = config.getAllChildProfiles();
      res.json(profiles);
    } catch (error) {
      logger.error('Failed to get profiles', { error: error.message });
      res.status(500).json({ error: 'Failed to get profiles' });
    }
  }

  // Create new child profile
  async createProfile(req, res) {
    try {
      const profile = await config.addChildProfile(req.body);
      logger.audit('Child profile created', { profileId: profile.id, name: profile.name });
      res.status(201).json(profile);
    } catch (error) {
      logger.error('Failed to create profile', { error: error.message });
      res.status(400).json({ error: error.message });
    }
  }

  // Update child profile
  async updateProfile(req, res) {
    try {
      const profileId = req.params.id;
      await config.updateChildProfile(profileId, req.body);
      const updatedProfile = config.getChildProfile(profileId);
      
      logger.audit('Child profile updated', { profileId, updates: Object.keys(req.body) });
      res.json(updatedProfile);
    } catch (error) {
      logger.error('Failed to update profile', { error: error.message });
      res.status(400).json({ error: error.message });
    }
  }

  // Delete child profile
  async deleteProfile(req, res) {
    try {
      const profileId = req.params.id;
      const profiles = config.getAllChildProfiles();
      const filteredProfiles = profiles.filter(p => p.id !== profileId);
      
      await config.set('profiles', filteredProfiles);
      logger.audit('Child profile deleted', { profileId });
      
      res.json({ success: true, message: 'Profile deleted' });
    } catch (error) {
      logger.error('Failed to delete profile', { error: error.message });
      res.status(400).json({ error: error.message });
    }
  }

  // Start the web server
  async start() {
    try {
      await this.initialize();
      
      this.server = this.app.listen(this.port, () => {
        logger.info('Parental Controls Server started', {
          port: this.port,
          environment: process.env.NODE_ENV || 'development',
          controlsActive: this.state.controlsActive
        });
        console.log(`🌐 Parental Controls Dashboard: http://localhost:${this.port}`);
        console.log(`📊 Health Check: http://localhost:${this.port}/health`);
        console.log(`🔧 API Status: http://localhost:${this.port}/api/status`);
      });

      // Graceful shutdown
      process.on('SIGTERM', this.shutdown.bind(this));
      process.on('SIGINT', this.shutdown.bind(this));

    } catch (error) {
      logger.error('Failed to start server', { error: error.message });
      throw error;
    }
  }

  // Graceful shutdown
  async shutdown() {
    logger.info('Shutting down Parental Controls Server...');
    
    if (this.server) {
      this.server.close(() => {
        logger.info('Server closed successfully');
        process.exit(0);
      });
    } else {
      process.exit(0);
    }
  }
}

// Start the server if this file is run directly
if (process.argv[1] && process.argv[1].includes('controller.js')) {
  const controller = new ParentalControlsController();
  controller.start().catch(error => {
    console.error('Failed to start controller:', error);
    process.exit(1);
  });
}

export default ParentalControlsController;
