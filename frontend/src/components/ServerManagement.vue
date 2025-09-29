<template>
  <div class="server-management">
    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <span>服务器管理</span>
          <el-button type="primary" @click="showCreateDialog">添加服务器</el-button>
        </div>
      </template>
      <el-table
        v-loading="loading"
        :data="serversList"
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="服务器名称" />
        <el-table-column prop="hostname" label="主机名/IP" />
        <el-table-column prop="port" label="端口" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="hasPrivateKey" label="有私钥" width="80" :formatter="formatBoolean" />
        <el-table-column prop="hasPassword" label="有密码" width="80" :formatter="formatBoolean" />
        <el-table-column prop="createdAt" label="创建时间" width="180" />
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="scope">
            <el-button type="primary" link @click="handleGetConfig(scope.row)">获取配置</el-button>
            <el-button type="primary" link @click="handleXrayRConfig(scope.row)">XrayR配置</el-button>
            <el-button type="primary" link @click="handleTestConnection(scope.row)">测试连接</el-button>
            <el-button type="primary" link @click="handleEdit(scope.row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="dialogVisible" title="创建服务器" width="500px">
    <CreateServer v-if="dialogVisible" @success="handleCreateSuccess" @cancel="dialogVisible = false" />
  </el-dialog>
  
  <el-dialog v-model="editDialogVisible" title="编辑服务器" width="500px">
    <EditServer 
      v-if="editDialogVisible"
      :server-id="selectedServer?.id || 0"
      :axios="axios"
      @success="handleEditSuccess"
      @cancel="editDialogVisible = false"
    />
  </el-dialog>
    
    <ServerXrayRConfigDialog
      v-if="xrayrConfigDialogVisible"
      v-model:visible="xrayrConfigDialogVisible"
      :server-id="selectedServer?.id || null"
      :axios="axios"
      config-path="/etc/XrayR/config.yml"
    />
    
    <XrayRConfigList
      v-if="xrayrConfigVisible"
      v-model:visible="xrayrConfigVisible"
      :server-id="selectedServer?.id || null"
      :server-name="selectedServer?.name || ''"
      :axios="axios"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, inject, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { AxiosInstance } from 'axios'
import CreateServer from './CreateServer.vue'
import EditServer from './EditServer.vue'
import ServerXrayRConfigDialog from './ServerXrayRConfigDialog.vue'
import XrayRConfigList from './XrayRConfigList.vue'

// 注入axios
const axios = inject<AxiosInstance>('axios') || null

// 状态
const loading = ref(false)
const serversList = ref<any[]>([])
const dialogVisible = ref(false)
const xrayrConfigDialogVisible = ref(false)
const xrayrConfigVisible = ref(false)
const editDialogVisible = ref(false)
const selectedServer = ref<any>(null)

// 格式化布尔值显示
const formatBoolean = (_row: any, _column: any, cellValue: boolean) => {
  return cellValue ? '是' : '否'
}

// 加载服务器列表
const loadServers = async () => {
  if (!axios) return
  
  loading.value = true
  try {
    // 注意：根据之前的分析，实际API路径是/servers/servers/
    const response = await axios.get('/servers/servers/')
    serversList.value = response.data.map((server: any) => ({
      id: server.id,
      name: server.name,
      hostname: server.hostname,
      port: server.port,
      username: server.username,
      hasPrivateKey: server.has_private_key,
      hasPassword: server.has_password,
      createdAt: server.created_at,
      updatedAt: server.updated_at
    }))
  } catch (error: any) {
    console.error('加载服务器列表失败:', error)
    // 尝试获取更具体的错误信息
    const errorMessage = error.response?.data?.detail || '加载服务器列表失败'
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  dialogVisible.value = true
}

// 处理创建成功
const handleCreateSuccess = () => {
  dialogVisible.value = false
  ElMessage.success('服务器创建成功')
  loadServers()
}

// 处理获取配置
const handleGetConfig = (row: any) => {
  selectedServer.value = row
  // 使用nextTick确保selectedServer更新后再显示对话框
  setTimeout(() => {
    xrayrConfigDialogVisible.value = true
  }, 0)
}

// 处理XrayR配置列表
const handleXrayRConfig = (row: any) => {
  selectedServer.value = row
  // 使用nextTick确保selectedServer更新后再显示对话框
  setTimeout(() => {
    xrayrConfigVisible.value = true
  }, 0)
}

// 处理编辑
const handleEdit = (row: any) => {
  selectedServer.value = row
  // 使用nextTick确保selectedServer更新后再显示对话框
  setTimeout(() => {
    editDialogVisible.value = true
  }, 0)
}

// 处理编辑成功
const handleEditSuccess = () => {
  editDialogVisible.value = false
  ElMessage.success('服务器更新成功')
  loadServers()
}

// 处理测试连接
const handleTestConnection = async (row: any) => {
  if (!axios) {
    ElMessage.error('axios未初始化，请刷新页面重试')
    return
  }
  
  try {
    // 确保row和row.id存在
    if (!row || !row.id) {
      ElMessage.error('无效的服务器数据')
      return
    }
    
    // 调用测试连接API
    const response = await axios.post(`/servers/servers/${row.id}/test-connection`)
    
    // 显示成功消息
    const message = response.data?.message || '连接测试成功'
    ElMessage.success(message)
  } catch (error: any) {
    console.error('连接测试失败:', error)
    // 显示错误消息
    const errorMessage = error.response?.data?.detail || error.message || '连接测试失败'
    ElMessage.error(errorMessage)
  }
}

// 处理删除
const handleDelete = async (row: any) => {
  if (!axios) {
    ElMessage.error('axios未初始化，请刷新页面重试')
    return
  }
  
  try {
    // 确保row和row.id存在
    if (!row || !row.id) {
      ElMessage.error('无效的服务器数据')
      return
    }
    
    // 确认删除操作
    const confirmResult = await ElMessageBox.confirm(
      `确定要删除服务器 "${row.name || row.hostname}" 吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    if (confirmResult !== 'confirm') return
    
    await axios.delete(`/servers/servers/${row.id}`)
    ElMessage.success('服务器删除成功')
    loadServers()
  } catch (error: any) {
    console.error('删除服务器失败:', error)
    // 用户取消删除操作时也会进入catch，但不需要显示错误
    if (error !== 'cancel') {
      // 尝试获取更具体的错误信息
      const errorMessage = error.response?.data?.detail || error.message || '删除服务器失败'
      ElMessage.error(errorMessage)
    }
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadServers()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>