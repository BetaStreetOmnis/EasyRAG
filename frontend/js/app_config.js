/**
 * 应用配置管理模块
 * 负责加载、保存和管理应用配置
 */

class AppConfigManager {
  constructor() {
    this.configPath = 'config/default_apps.json';
    this.localStorageKey = 'apps';
  }

  /**
   * 安全地从 localStorage 读取 JSON
   * @param {string} key
   * @returns {any|null}
   */
  _safeGetItem(key) {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch (e) {
      console.warn('localStorage 读取失败:', e);
      return null;
    }
  }

  /**
   * 安全地写入 localStorage
   * @param {string} key
   * @param {any} value
   * @returns {boolean}
   */
  _safeSetItem(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (e) {
      console.warn('localStorage 写入失败:', e);
      return false;
    }
  }

  /**
   * 加载应用配置
   * 优先从localStorage加载，如果不存在则从配置文件加载
   * @returns {Promise<Array>} 应用列表
   */
  async loadApps() {
    // 先尝试从localStorage加载
    const localApps = this._safeGetItem(this.localStorageKey);
    if (localApps && Array.isArray(localApps)) {
      return localApps;
    }

    // 如果localStorage中没有，则从配置文件加载
    try {
      const response = await fetch(this.configPath);
      if (!response.ok) {
        throw new Error(`无法加载配置文件: ${response.statusText}`);
      }
      const defaultApps = await response.json();

      // 保存到localStorage以便后续使用
      this._safeSetItem(this.localStorageKey, defaultApps);

      return defaultApps;
    } catch (error) {
      console.error('加载默认应用配置失败:', error);
      return [];
    }
  }

  /**
   * 保存应用列表到localStorage
   * @param {Array} apps 应用列表
   */
  saveApps(apps) {
    this._safeSetItem(this.localStorageKey, apps);
  }

  /**
   * 添加新应用
   * @param {Object} app 应用对象
   * @returns {Promise<Array>} 更新后的应用列表
   */
  async addApp(app) {
    const apps = await this.loadApps();
    apps.push(app);
    this.saveApps(apps);
    return apps;
  }

  /**
   * 删除应用
   * @param {number} index 要删除的应用索引
   * @returns {Promise<Array>} 更新后的应用列表
   */
  async deleteApp(index) {
    const apps = await this.loadApps();
    apps.splice(index, 1);
    this.saveApps(apps);
    return apps;
  }

  /**
   * 重置为默认配置
   * @returns {Promise<Array>} 默认应用列表
   */
  async resetToDefault() {
    localStorage.removeItem(this.localStorageKey);
    return this.loadApps(); // 重新加载默认配置
  }
}

// 导出单例实例
const appConfigManager = new AppConfigManager();
if (typeof window !== 'undefined') {
    window.appConfigManager = appConfigManager;
}

export default appConfigManager;
