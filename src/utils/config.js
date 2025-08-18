import fs from 'fs/promises';
import path from 'path';
import crypto from 'crypto';
import dotenv from 'dotenv';
import logger from './logger.js';

// Load environment variables
dotenv.config();

class ConfigManager {
  constructor() {
    this.configPath = path.join('config');
    this.encryptionKey = process.env.ENCRYPTION_KEY;
    this.config = {};
    this.initialized = false;
  }

  // Initialize configuration system
  async initialize() {
    try {
      // Ensure config directory exists
      await fs.mkdir(this.configPath, { recursive: true });
      
      // Generate encryption key if not provided
      if (!this.encryptionKey) {
        this.encryptionKey = crypto.randomBytes(32).toString('hex');
        logger.warn('Generated new encryption key. Store this securely!', {
          key: this.encryptionKey
        });
      }

      // Load existing configuration files
      await this.loadConfiguration();
      
      this.initialized = true;
      logger.info('Configuration system initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize configuration system', { error: error.message });
      throw error;
    }
  }

  // Load all configuration files
  async loadConfiguration() {
    try {
      // Load profiles
      this.config.profiles = await this.loadJsonFile('profiles.json', []);
      
      // Load schedules
      this.config.schedules = await this.loadJsonFile('schedules.json', {});
      
      // Load system settings
      this.config.settings = await this.loadJsonFile('settings.json', {
        webPort: 3000,
        logLevel: 'info',
        autoStart: false,
        enableScheduling: true
      });

      logger.info('Configuration loaded successfully');
    } catch (error) {
      logger.error('Failed to load configuration', { error: error.message });
      throw error;
    }
  }

  // Load JSON file with default fallback
  async loadJsonFile(filename, defaultValue = {}) {
    const filePath = path.join(this.configPath, filename);
    try {
      const data = await fs.readFile(filePath, 'utf8');
      return JSON.parse(data);
    } catch (error) {
      if (error.code === 'ENOENT') {
        // File doesn't exist, create with default value
        await this.saveJsonFile(filename, defaultValue);
        return defaultValue;
      }
      throw error;
    }
  }

  // Save JSON file
  async saveJsonFile(filename, data) {
    const filePath = path.join(this.configPath, filename);
    await fs.writeFile(filePath, JSON.stringify(data, null, 2));
  }

  // Encrypt sensitive data
  encrypt(text) {
    if (!this.encryptionKey) {
      throw new Error('Encryption key not available');
    }
    
    const algorithm = 'aes-256-gcm';
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipher(algorithm, this.encryptionKey);
    
    let encrypted = cipher.update(text, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    const authTag = cipher.getAuthTag();
    
    return {
      encrypted,
      iv: iv.toString('hex'),
      authTag: authTag.toString('hex')
    };
  }

  // Decrypt sensitive data
  decrypt(encryptedData) {
    if (!this.encryptionKey) {
      throw new Error('Encryption key not available');
    }
    
    const algorithm = 'aes-256-gcm';
    const decipher = crypto.createDecipher(algorithm, this.encryptionKey);
    
    decipher.setAuthTag(Buffer.from(encryptedData.authTag, 'hex'));
    
    let decrypted = decipher.update(encryptedData.encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    
    return decrypted;
  }

  // Store encrypted credentials
  async storeCredentials(platform, credentials) {
    try {
      const credentialsFile = path.join(this.configPath, 'credentials.enc');
      let allCredentials = {};
      
      // Load existing credentials
      try {
        const data = await fs.readFile(credentialsFile, 'utf8');
        allCredentials = JSON.parse(data);
      } catch (error) {
        // File doesn't exist yet
      }
      
      // Encrypt new credentials
      const encrypted = this.encrypt(JSON.stringify(credentials));
      allCredentials[platform] = encrypted;
      
      // Save updated credentials
      await fs.writeFile(credentialsFile, JSON.stringify(allCredentials, null, 2));
      
      logger.audit('Credentials stored', { platform });
    } catch (error) {
      logger.error('Failed to store credentials', { platform, error: error.message });
      throw error;
    }
  }

  // Retrieve encrypted credentials
  async getCredentials(platform) {
    try {
      const credentialsFile = path.join(this.configPath, 'credentials.enc');
      const data = await fs.readFile(credentialsFile, 'utf8');
      const allCredentials = JSON.parse(data);
      
      if (!allCredentials[platform]) {
        throw new Error(`No credentials found for platform: ${platform}`);
      }
      
      const decrypted = this.decrypt(allCredentials[platform]);
      return JSON.parse(decrypted);
    } catch (error) {
      logger.error('Failed to retrieve credentials', { platform, error: error.message });
      throw error;
    }
  }

  // Get configuration value
  get(key, defaultValue = null) {
    const keys = key.split('.');
    let value = this.config;
    
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return defaultValue;
      }
    }
    
    return value;
  }

  // Set configuration value
  async set(key, value) {
    const keys = key.split('.');
    const lastKey = keys.pop();
    let current = this.config;
    
    // Navigate to the parent object
    for (const k of keys) {
      if (!current[k] || typeof current[k] !== 'object') {
        current[k] = {};
      }
      current = current[k];
    }
    
    current[lastKey] = value;
    
    // Save the appropriate file based on the key
    if (key.startsWith('profiles')) {
      await this.saveJsonFile('profiles.json', this.config.profiles);
    } else if (key.startsWith('schedules')) {
      await this.saveJsonFile('schedules.json', this.config.schedules);
    } else if (key.startsWith('settings')) {
      await this.saveJsonFile('settings.json', this.config.settings);
    }
    
    logger.audit('Configuration updated', { key, value: typeof value });
  }

  // Add a child profile
  async addChildProfile(profile) {
    if (!this.config.profiles) {
      this.config.profiles = [];
    }
    
    // Validate required fields
    if (!profile.name || !profile.id) {
      throw new Error('Profile must have name and id');
    }
    
    // Check for duplicate IDs
    if (this.config.profiles.some(p => p.id === profile.id)) {
      throw new Error(`Profile with ID ${profile.id} already exists`);
    }
    
    // Add default settings
    const fullProfile = {
      id: profile.id,
      name: profile.name,
      age: profile.age || 10,
      platforms: {
        nintendo: { enabled: false, screenTimeMinutes: 60 },
        google: { enabled: false, screenTimeMinutes: 120 },
        microsoft: { enabled: false, screenTimeMinutes: 90 },
        opnsense: { enabled: false, blockedDevices: [] }
      },
      schedule: {
        weekdays: { start: '16:00', end: '20:00' },
        weekends: { start: '09:00', end: '21:00' }
      },
      restrictions: {
        bedtime: '21:00',
        contentFilter: true,
        allowedApps: [],
        blockedApps: []
      },
      ...profile
    };
    
    this.config.profiles.push(fullProfile);
    await this.saveJsonFile('profiles.json', this.config.profiles);
    
    logger.audit('Child profile added', { profileId: profile.id, name: profile.name });
    return fullProfile;
  }

  // Get child profile by ID
  getChildProfile(profileId) {
    return this.config.profiles?.find(p => p.id === profileId);
  }

  // Update child profile
  async updateChildProfile(profileId, updates) {
    const profileIndex = this.config.profiles?.findIndex(p => p.id === profileId);
    if (profileIndex === -1) {
      throw new Error(`Profile with ID ${profileId} not found`);
    }
    
    this.config.profiles[profileIndex] = {
      ...this.config.profiles[profileIndex],
      ...updates
    };
    
    await this.saveJsonFile('profiles.json', this.config.profiles);
    logger.audit('Child profile updated', { profileId, updates: Object.keys(updates) });
  }

  // Get all child profiles
  getAllChildProfiles() {
    return this.config.profiles || [];
  }
}

// Export singleton instance
const config = new ConfigManager();
export default config;
