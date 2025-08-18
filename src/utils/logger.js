import winston from 'winston';
import path from 'path';

// Define log levels and colors
const logLevels = {
  error: 0,
  warn: 1,
  info: 2,
  audit: 3,
  debug: 4
};

const logColors = {
  error: 'red',
  warn: 'yellow',
  info: 'green',
  audit: 'blue',
  debug: 'magenta'
};

winston.addColors(logColors);

// Create logger configuration
const logger = winston.createLogger({
  levels: logLevels,
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp({
      format: 'YYYY-MM-DD HH:mm:ss'
    }),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'parental-controls' },
  transports: [
    // Error log file
    new winston.transports.File({ 
      filename: path.join('logs', 'errors.log'), 
      level: 'error',
      maxsize: 5242880, // 5MB
      maxFiles: 5,
      tailable: true
    }),
    
    // Audit log file for all actions
    new winston.transports.File({ 
      filename: path.join('logs', 'audit.log'), 
      level: 'audit',
      maxsize: 5242880, // 5MB
      maxFiles: 10,
      tailable: true
    }),
    
    // Combined log file
    new winston.transports.File({ 
      filename: path.join('logs', 'combined.log'),
      maxsize: 5242880, // 5MB
      maxFiles: 5,
      tailable: true
    })
  ]
});

// Add console transport for development
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    )
  }));
}

// Custom audit logging function
logger.audit = (message, metadata = {}) => {
  logger.log('audit', message, {
    timestamp: new Date().toISOString(),
    type: 'AUDIT',
    ...metadata
  });
};

// Platform-specific logging functions
logger.nintendo = (action, data = {}) => {
  logger.audit(`Nintendo Switch: ${action}`, {
    platform: 'nintendo',
    action,
    ...data
  });
};

logger.google = (action, data = {}) => {
  logger.audit(`Google Family: ${action}`, {
    platform: 'google',
    action,
    ...data
  });
};

logger.microsoft = (action, data = {}) => {
  logger.audit(`Microsoft Family: ${action}`, {
    platform: 'microsoft',
    action,
    ...data
  });
};

logger.opnsense = (action, data = {}) => {
  logger.audit(`OPNSense Firewall: ${action}`, {
    platform: 'opnsense',
    action,
    ...data
  });
};

// Error handling for logger itself
logger.on('error', (error) => {
  console.error('Logger error:', error);
});

export default logger;
