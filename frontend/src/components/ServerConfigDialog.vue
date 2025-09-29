<template>
  <el-dialog
    v-model="dialogVisible"
    title="服务器配置信息"
    width="600px"
    :close-on-click-modal="false"
  >
    <div v-if="loading" class="text-center py-6">
      <el-icon><Loading /></el-icon>
      <span class="ml-2">加载中...</span>
    </div>
    
    <div v-else-if="configData" class="config-container">
      <el-form label-width="100px">
        <el-form-item label="服务器ID">
          <el-input v-model="configData.serverId" disabled />
        </el-form-item>
        <el-form-item label="服务器名称">
          <el-input v-model="configData.serverName" disabled />
        </el-form-item>
        <el-form-item label="主机名/IP">
          <el-input v-model="configData.hostname" disabled />
        </el-form-item>
        <el-form-item label="端口">
          <el-input v-model="configData.port" disabled />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="configData.username" disabled />
        </el-form-item>
        <el-form-item label="有私钥">
          <el-input v-model="configData.hasPrivateKey" disabled />
        </el-form-item>
        <el-form-item label="有密码">
          <el-input v-model="configData.hasPassword" disabled />
        </el-form-item>
        <el-form-item label="创建时间">
          <el-input v-model="configData.createdAt" disabled />
        </el-form-item>
        <!-- 其他配置信息字段 -->
        <el-form-item v-for="(value, key) in configData.otherConfigs" :key="key" :label="formatKey(key)">
          <el-input :value="value" disabled />
        </el-form-item>
      </el-form>
    </div>
    
    <div v-else class="text-center py-6 text-gray-500">
      暂无配置信息
    </div>
    
    <template #footer>
      <el-button @click="closeDialog">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, defineProps, defineEmits, withDefaults } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { AxiosInstance } from 'axios'

// Props
interface ServerConfigDialogProps {
  serverId: number | null
  serverName: string
  hostname: string
  port: number
  username: string
  hasPrivateKey: boolean
  hasPassword: boolean
  createdAt: string
  visible: boolean
  axios: AxiosInstance | null
}

const props = withDefaults(defineProps<ServerConfigDialogProps>(), {
  serverId: null,
  serverName: '',
  hostname: '',
  port: 22,
  username: '',
  hasPrivateKey: false,
  hasPassword: false,
  createdAt: '',
  visible: false,
  axios: null
})

// Emits
const emit = defineEmits(['update:visible'])

// 状态
const dialogVisible = ref(props.visible)
const loading = ref(false)
const configData = ref<any>(null)

// 监听visible变化
import { watch, onUnmounted } from 'vue'
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

// 组件卸载时取消监听
onUnmounted(() => {
  unwatchVisible()
})

// 格式化key显示
const formatKey = (key: string | number) => {
  // 将驼峰式转换为空格分隔的中文显示
  const strKey = String(key)
  return strKey.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())
}

// 获取配置数据
const fetchConfigData = async () => {
  if (!props.axios || !props.serverId) return
  
  loading.value = true
  configData.value = null
  
  try {
    // 执行命令获取服务器基本配置信息
    const commands = [
      { name: '操作系统', cmd: 'cat /etc/os-release || uname -a' },
      { name: '内核版本', cmd: 'uname -r' },
      { name: '主机名', cmd: 'hostname' },
      { name: 'IP地址', cmd: "hostname -I || ip addr | grep inet | grep -v 127.0.0.1 | head -1 | awk '{print $2}'" },
      { name: '内存信息', cmd: 'free -h | grep Mem' },
      { name: '磁盘信息', cmd: 'df -h | grep -v tmpfs' },
      { name: 'CPU信息', cmd: 'cat /proc/cpuinfo | grep "model name" | head -1 | cut -d":" -f2' },
      { name: '系统时间', cmd: 'date' }
    ]
    
    // 构建组合命令
    const combinedCommand = commands.map(cmd => `echo "###${cmd.name}:###"; ${cmd.cmd}`).join(' && echo "\n" && ')
    
    // 调用执行命令的API
    const response = await props.axios.post(`/ssh_operations/servers/${props.serverId}/execute`, {
      command: combinedCommand,
      timeout: 60
    })
    
    // 解析命令输出
    const configs: Record<string, string> = {}
    const output = response.data.stdout
    const sections = output.split('\n\n')
    
    sections.forEach((section: string) => {
      const lines = section.trim().split('\n')
      if (lines.length > 0 && lines[0]) {
        const nameLine = lines[0]
        if (nameLine.startsWith('###')) {
          const name = nameLine.replace(/^###|###$/g, '').trim()
          const value = lines.slice(1).join('\n').trim()
          if (value) {
            configs[name] = value
          }
        }
      }
    })
    
    // 如果没有获取到配置信息，使用基本信息
    if (Object.keys(configs).length === 0) {
      configs['配置信息'] = '无法获取详细配置信息，可能是权限不足或命令不支持'
    }
    
    // 构造配置数据
    configData.value = {
      serverId: props.serverId,
      serverName: props.serverName,
      hostname: props.hostname,
      port: props.port,
      username: props.username,
      hasPrivateKey: props.hasPrivateKey ? '是' : '否',
      hasPassword: props.hasPassword ? '是' : '否',
      createdAt: props.createdAt,
      otherConfigs: configs
    }
    
    ElMessage.success('获取服务器配置成功')
  } catch (error) {
    console.error('获取服务器配置失败:', error)
    
    // 显示错误信息，但仍然展示基本信息
    configData.value = {
      serverId: props.serverId,
      serverName: props.serverName,
      hostname: props.hostname,
      port: props.port,
      username: props.username,
      hasPrivateKey: props.hasPrivateKey ? '是' : '否',
      hasPassword: props.hasPassword ? '是' : '否',
      createdAt: props.createdAt,
      otherConfigs: {
        '错误信息': '获取详细配置失败，请检查SSH连接是否正常'
      }
    }
    
    ElMessage.error('获取服务器详细配置失败')
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
  max-height: 400px;
  overflow-y: auto;
}

.text-gray-500 {
  color: #909399;
}
</style>