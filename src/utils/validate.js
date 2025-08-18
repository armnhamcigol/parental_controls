import config from './config.js';
import logger from './logger.js';

class ValidationUtil {
  constructor() {
    this.results = {
      config: false,
      logging: false,
      connectivity: {
        opnsense: false,
        internet: false
      },
      credentials: {
        nintendo: false,
        google: false,
        microsoft: false
      }
    };
  }

  // Run all validation tests
  async runAll() {
    console.log('🔍 Running system validation...\n');
    
    try {
      await this.validateConfig();
      await this.validateLogging();
      await this.validateConnectivity();
      await this.validateCredentials();
      
      this.printResults();
      return this.isSystemHealthy();
    } catch (error) {
      logger.error('Validation failed', { error: error.message });
      console.error('❌ Validation failed:', error.message);
      return false;
    }
  }

  // Test configuration system
  async validateConfig() {
    try {
      await config.initialize();
      
      // Test basic configuration operations
      await config.set('settings.testValue', 'validation-test');
      const testValue = config.get('settings.testValue');
      
      if (testValue === 'validation-test') {
        this.results.config = true;
        console.log('✅ Configuration system: OK');
      } else {
        console.log('❌ Configuration system: Failed to read/write test value');
      }
    } catch (error) {
      console.log('❌ Configuration system: Failed -', error.message);
    }
  }

  // Test logging system
  async validateLogging() {
    try {
      // Test different log levels
      logger.info('Validation test log entry');
      logger.audit('Validation test audit entry');
      logger.warn('Validation test warning');
      
      this.results.logging = true;
      console.log('✅ Logging system: OK');
    } catch (error) {
      console.log('❌ Logging system: Failed -', error.message);
    }
  }

  // Test network connectivity
  async validateConnectivity() {
    // Test internet connectivity
    try {
      const response = await fetch('https://www.google.com', {
        method: 'HEAD',
        timeout: 5000
      });
      
      if (response.ok) {
        this.results.connectivity.internet = true;
        console.log('✅ Internet connectivity: OK');
      } else {
        console.log('❌ Internet connectivity: Failed - No response');
      }
    } catch (error) {
      console.log('❌ Internet connectivity: Failed -', error.message);
    }

    // Test OPNSense connectivity (SSH test)
    try {
      // This is a dry run - we're not actually connecting
      // In a real implementation, we'd test SSH connectivity here
      console.log('⚠️  OPNSense connectivity: Not tested (dry run mode)');
      console.log('   To test: ssh -i ~/.ssh/id_ed25519_opnsense root@192.168.123.1');
    } catch (error) {
      console.log('❌ OPNSense connectivity: Failed -', error.message);
    }
  }

  // Test platform credentials
  async validateCredentials() {
    const platforms = ['nintendo', 'google', 'microsoft'];
    
    for (const platform of platforms) {
      try {
        // Try to retrieve credentials
        await config.getCredentials(platform);
        this.results.credentials[platform] = true;
        console.log(`✅ ${platform} credentials: Found`);
      } catch (error) {
        console.log(`⚠️  ${platform} credentials: Not configured`);
        console.log(`   Use: npm run setup to configure ${platform} credentials`);
      }
    }
  }

  // Print comprehensive results
  printResults() {
    console.log('\n📊 Validation Summary:');
    console.log('======================');
    
    const configStatus = this.results.config ? '✅ PASS' : '❌ FAIL';
    const loggingStatus = this.results.logging ? '✅ PASS' : '❌ FAIL';
    const internetStatus = this.results.connectivity.internet ? '✅ PASS' : '❌ FAIL';
    
    console.log(`Configuration System: ${configStatus}`);
    console.log(`Logging System: ${loggingStatus}`);
    console.log(`Internet Connectivity: ${internetStatus}`);
    
    console.log('\nPlatform Credentials:');
    Object.entries(this.results.credentials).forEach(([platform, status]) => {
      const statusText = status ? '✅ CONFIGURED' : '⚠️  NOT CONFIGURED';
      console.log(`  ${platform}: ${statusText}`);
    });
    
    console.log('\nNext Steps:');
    console.log('-----------');
    
    if (!this.results.config) {
      console.log('• Fix configuration system issues');
    }
    
    if (!this.results.logging) {
      console.log('• Fix logging system issues');
    }
    
    if (!this.results.connectivity.internet) {
      console.log('• Check internet connection');
    }
    
    const unconfiguredPlatforms = Object.entries(this.results.credentials)
      .filter(([_, status]) => !status)
      .map(([platform, _]) => platform);
    
    if (unconfiguredPlatforms.length > 0) {
      console.log(`• Configure credentials for: ${unconfiguredPlatforms.join(', ')}`);
      console.log('• Run: npm run setup');
    }
    
    if (this.isSystemHealthy()) {
      console.log('\n🎉 System is ready for platform integration!');
    } else {
      console.log('\n⚠️  Please address the issues above before proceeding.');
    }
  }

  // Check if system is healthy
  isSystemHealthy() {
    return this.results.config && 
           this.results.logging && 
           this.results.connectivity.internet;
  }

  // Generate system status report
  getStatusReport() {
    return {
      timestamp: new Date().toISOString(),
      overall: this.isSystemHealthy() ? 'HEALTHY' : 'ISSUES_DETECTED',
      details: this.results
    };
  }
}

// Run validation if called directly
if (process.argv[1] && process.argv[1].includes('validate.js')) {
  const validator = new ValidationUtil();
  const success = await validator.runAll();
  process.exit(success ? 0 : 1);
}

export default ValidationUtil;
