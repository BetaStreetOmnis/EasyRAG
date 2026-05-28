import appConfigManager from './app_config.js';
import '../script.js';

if (typeof window !== 'undefined' && !window.appConfigManager) {
    window.appConfigManager = appConfigManager;
}
