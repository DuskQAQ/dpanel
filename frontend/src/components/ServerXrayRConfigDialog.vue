<template>
  <el-dialog
    v-model="dialogVisible"
    title="XrayR配置信息"
    width="800px"
    :close-on-click-modal="false"
  >
    <div v-if="loading" class="text-center py-6">
      <el-icon><Loading /></el-icon>
      <span class="ml-2">加载中...</span>
    </div>
    
    <div v-else-if="configData" class="config-container">
      <el-form label-width="120px">
        <el-form-item label="服务器信息">
          <div>{{ configData.server_info.name }} ({{ configData.server_info.hostname }}:{{ configData.server_info.port }})</div>
        </el-form-item>
        
        <el-form-item label="配置路径">
          <div>{{ configPath }}</div>
        </el-form-item>
        
        <el-form-item label="配置内容" v-if="configData.config_content">
          <el-input
            v-model="configData.config_content"
            type="textarea"
            :rows="15"
            disabled
            style="font-family: monospace; font-size: 12px;"
          />
        </el-form-item>
        
        <el-form-item label="解析结果" v-if="configData.parsed_config">
          <el-input
            v-model="formattedParsedConfig"
            type="textarea"
            :rows="15"
            disabled
            style="font-family: monospace; font-size: 12px;"
          />
        </el-form-item>
        
        <el-form-item v-if="configData.error">
          <div class="error-message">{{ configData.error }}</div>
        </el-form-item>
      </el-form>
    </div>
    
    <div v-else class="text-center py-6 text-gray-500">
      暂无配置信息
    </div>
    
    <template #footer>
      <div class="dialog-actions">
        <el-button @click="checkConfigFile">检查配置文件</el-button>
        <el-button @click="fetchConfigData">刷新配置</el-button>
        <el-button @click="closeDialog">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits, withDefaults, watch, onUnmounted } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { AxiosInstance } from 'axios'

// Props
interface ServerXrayRConfigDialogProps {
  serverId: number | null
  visible: boolean
  axios: AxiosInstance | null
  configPath?: string
}

const props = withDefaults(defineProps<ServerXrayRConfigDialogProps>(), {
  serverId: null,
  visible: false,
  axios: null,
  configPath: '/etc/XrayR/config.yml'
})

// Emits
const emit = defineEmits(['update:visible'])

// 状态
const dialogVisible = ref(props.visible)
const loading = ref(false)
const configData = ref<any>(null)
const configPath = ref(props.configPath)

// 格式化解析后的配置
const formattedParsedConfig = computed(() => {
  if (!configData.value?.parsed_config) return ''
  try {
    return JSON.stringify(configData.value.parsed_config, null, 2)
  } catch (error) {
    return JSON.stringify(configData.value.parsed_config)
  }
})

// 监听visible变化
const unwatchVisible = watch(
  () => props.visible,
  (newVal: boolean) => {
    dialogVisible.value = newVal
    if (newVal && props.serverId) {
      fetchConfigData()
    }
  },
  { immediate: true }
)

// 监听configPath变化
const unwatchConfigPath = watch(
  () => props.configPath,
  (newPath: string) => {
    configPath.value = newPath
  }
)

// 组件卸载时取消监听
onUnmounted(() => {
  unwatchVisible()
  unwatchConfigPath()
})

// 获取配置数据
const fetchConfigData = async () => {
  if (!props.axios || !props.serverId) return
  
  loading.value = true
  configData.value = null
  
  try {
    // 调用获取配置的API
    const response = await props.axios.post(`/server_configs/servers/${props.serverId}/config`, {
      config_path: configPath.value,
      simplify: false
    })
    
    configData.value = response.data
    
    if (configData.value.success) {
      ElMessage.success('获取XrayR配置成功')
    } else {
      ElMessage.warning('获取XrayR配置失败: ' + configData.value.error)
    }
  } catch (error) {
    console.error('获取XrayR配置失败:', error)
    ElMessage.error('获取XrayR配置失败')
  } finally {
    loading.value = false
  }
}

// 检查配置文件是否存在
const checkConfigFile = async () => {
  if (!props.axios || !props.serverId) return
  
  loading.value = true
  
  try {
    // 调用检查配置文件的API
    const response = await props.axios.get(`/server_configs/servers/${props.serverId}/config/check`, {
      params: {
        config_path: configPath.value
      }
    })
    
    if (response.data.success && response.data.exists) {
      ElMessage.success(`配置文件 ${configPath.value} 存在`)
    } else {
      ElMessage.warning(`配置文件 ${configPath.value} 不存在`)
    }
  } catch (error) {
    console.error('检查配置文件失败:', error)
    ElMessage.error('检查配置文件失败')
  } finally {
    loading.value = false
  }
}

// 关闭对话框
const closeDialog = () => {
  emit('update:visible', false)
}
</script>

<style scoped>
.config-container {
  max-height: 500px;
  overflow-y: auto;
}

.text-gray-500 {
  color: #909399;
}

.error-message {
  color: #f56c6c;
  background-color: #fef0f0;
  padding: 10px;
  border-radius: 4px;
  font-size: 14px;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>