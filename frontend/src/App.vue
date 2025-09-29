<script setup lang="ts">
import { ref } from 'vue'
import { Monitor, Key, Setting } from '@element-plus/icons-vue'
import ServerManagement from './components/ServerManagement.vue'

// 当前选中的菜单项
const currentMenu = ref('servers')

// 处理菜单选择
const handleMenuSelect = (index: string) => {
  currentMenu.value = index
}
</script>

<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
    <el-header class="app-header">
      <div class="header-content">
        <h1>SSH密钥管理系统</h1>
        <div class="header-right">
          <!-- 这里可以添加用户信息、登录/退出按钮等 -->
          <el-button type="primary" link>登录</el-button>
        </div>
      </div>
    </el-header>
    
    <!-- 主内容区域 -->
    <div class="app-main">
      <!-- 侧边导航菜单 -->
      <el-aside class="app-sidebar">
        <el-menu 
          active-text-color="#409EFF"
          background-color="#545c64"
          text-color="#fff"
          :default-active="currentMenu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="servers">
            <el-icon><Monitor /></el-icon>
            <span>服务器管理</span>
          </el-menu-item>
          <el-menu-item index="ssh-keys">
            <el-icon><key /></el-icon>
            <span>SSH密钥管理</span>
          </el-menu-item>
          <el-menu-item index="configs">
            <el-icon><setting /></el-icon>
            <span>配置管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 内容区域 -->
      <el-main class="app-content">
        <keep-alive>
          <ServerManagement v-if="currentMenu === 'servers'" />
          <!-- 其他组件可以在这里添加 -->
          <div v-else class="empty-content">
            <el-empty description="功能开发中" />
          </div>
        </keep-alive>
      </el-main>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
}

.header-content h1 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.app-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.app-sidebar {
  width: 200px;
  background-color: #545c64;
}

.app-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #f5f7fa;
}

.empty-content {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 400px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .app-sidebar {
    width: 60px;
  }
  
  .app-sidebar .el-menu-item span {
    display: none;
  }
}
</style>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#app {
  height: 100%;
}
</style>
