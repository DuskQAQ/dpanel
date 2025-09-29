<template>
  <el-dialog
    v-model="dialogVisible"
    title="XrayR配置列表"
    width="800px"
    :close-on-click-modal="false"
  >
    <div v-if="loading" class="text-center py-6">
      <el-icon><Loading /></el-icon>
      <span class="ml-2">加载配置中...</span>
    </div>
    
    <div v-else-if="configs.length > 0" class="config-list-container">
      <div class="dialog-header mb-4">
        <el-input
          v-model="searchQuery"
          placeholder="搜索配置名称或描述"
          clearable
          style="width: 300px;"
          @input="handleSearch"
        />
        <el-button type="primary" @click="showCreateDialog">添加配置</el-button>
      </div>
      
      <el-table
        :data="filteredConfigs"
        style="width: 100%"
        border
      >
        <el-table-column prop="id" label="配置ID" width="80" />
        <el-table-column prop="name" label="配置名称" />
        <el-table-column prop="config_path" label="配置路径" width="200" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="last_sync_at" label="最后同步时间" width="180" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="updated_at" label="更新时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button type="primary" link size="small" @click="viewConfigDetails(scope.row)">
              详情
            </el-button>
            <el-button type="primary" link size="small" @click="showEditDialog(scope.row)">
              编辑
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(scope.row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <div v-else class="text-center py-10 text-gray-500">
      <el-empty description="暂无XrayR配置" />
      <el-button type="primary" class="mt-4" @click="showCreateDialog">添加配置</el-button>
    </div>
    
    <template #footer>
      <el-button @click="closeDialog">关闭</el-button>
    </template>
  </el-dialog>
  
  <!-- 创建/编辑配置对话框 -->
  <el-dialog
    v-model="configFormVisible"
    :title="editingConfig ? '编辑配置' : '创建配置'"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="configFormRef"
      :model="configForm"
      :rules="configFormRules"
      label-width="100px"
    >
      <el-form-item label="配置名称" prop="name">
        <el-input v-model="configForm.name" placeholder="请输入配置名称" />
      </el-form-item>
      <el-form-item label="配置路径" prop="config_path">
        <el-input v-model="configForm.config_path" placeholder="请输入配置文件路径" />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input
          v-model="configForm.description"
          type="textarea"
          :rows="3"
          placeholder="请输入配置描述"
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="cancelConfigForm">取消</el-button>
      <el-button type="primary" @click="submitConfigForm">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, defineProps, defineEmits, withDefaults, watch, computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import type { AxiosInstance } from 'axios'

// 定义XrayR配置数据类型
interface XrayRConfig {
  id: number
  name: string
  server_id: number
  server_hostname: string
  server_username: string
  config_path: string
  parsed_config: Record<string, any>
  description: string
  last_sync_at: string
  created_at: string
  updated_at: string
}

// 创建/编辑表单数据类型
interface ConfigForm {
  name: string
  config_path: string
  description: string
}

// Props
interface XrayRConfigListProps {
  serverId: number | null
  serverName: string
  visible: boolean
  axios: AxiosInstance | null
}

const props = withDefaults(defineProps<XrayRConfigListProps>(), {
  serverId: null,
  serverName: '',
  visible: false,
  axios: null
})

// Emits
const emit = defineEmits(['update:visible'])

// 状态
const dialogVisible = ref(props.visible)
const loading = ref(false)
const configs = ref<XrayRConfig[]>([])
const searchQuery = ref('')
const configFormVisible = ref(false)
const configFormRef = ref<FormInstance>()
const editingConfig = ref<XrayRConfig | null>(null)
const configForm = ref<ConfigForm>({
  name: '',
  config_path: '',
  description: ''
})

// 表单验证规则
const configFormRules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' },
    { min: 2, max: 50, message: '配置名称长度应在 2 到 50 个字符之间', trigger: 'blur' }
  ],
  config_path: [
    { required: true, message: '请输入配置文件路径', trigger: 'blur' },
    { pattern: /^\/.+/, message: '配置路径必须以斜杠(/)开头', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '描述不能超过 200 个字符', trigger: 'blur' }
  ]
}

// 搜索过滤后的配置列表
const filteredConfigs = computed(() => {
  if (!searchQuery.value) {
    return configs.value
  }
  
  const query = searchQuery.value.toLowerCase()
  return configs.value.filter(config => 
    config.name.toLowerCase().includes(query) || 
    config.description.toLowerCase().includes(query)
  )
})

// 监听visible变化
watch(
  () => props.visible,
  (newVal: boolean) => {
    dialogVisible.value = newVal
    if (newVal && props.serverId) {
      fetchConfigs()
    }
  },
  { immediate: true }
)

// 获取配置列表
const fetchConfigs = async () => {
  if (!props.axios || !props.serverId) return
  
  loading.value = true
    configs.value = []
    
    try {
      // 调用API获取指定服务器的所有XrayR配置
      const response = await props.axios.get(`/xrayr-configs/servers/${props.serverId}/configs`)
      
      // 验证响应数据格式
      if (Array.isArray(response.data)) {
        configs.value = response.data.map((item: any) => ({
          id: item.id,
          name: item.name,
          server_id: item.server_id,
          server_hostname: item.server_hostname,
          server_username: item.server_username,
          config_path: item.config_path,
          parsed_config: item.parsed_config || {},
          description: item.description || '',
          last_sync_at: item.last_sync_at || '',
          created_at: item.created_at,
          updated_at: item.updated_at
        }))
        
        ElMessage.success(`成功获取${props.serverName}的XrayR配置列表`)
      } else {
        throw new Error('响应数据格式无效')
      }
    } catch (error: any) {
      console.error('获取XrayR配置列表失败:', error)
      
      // 处理错误情况
      let errorMessage = '获取XrayR配置列表失败'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }
      
      ElMessage.error(errorMessage)
    } finally {
      loading.value = false
    }
}

// 搜索配置
const handleSearch = () => {
  // 搜索逻辑已在computed属性中实现
}

// 显示创建配置对话框
const showCreateDialog = () => {
  editingConfig.value = null
  configForm.value = {
    name: '',
    config_path: '/etc/XrayR/config.yml', // 默认路径
    description: ''
  }
  configFormVisible.value = true
}

// 显示编辑配置对话框
const showEditDialog = (config: XrayRConfig) => {
  editingConfig.value = config
  configForm.value = {
    name: config.name,
    config_path: config.config_path,
    description: config.description
  }
  configFormVisible.value = true
}

// 提交配置表单
const submitConfigForm = async () => {
  if (!props.axios || !props.serverId) return
  
  // 验证表单
  const valid = await configFormRef.value?.validate()
  if (!valid) return
  
  loading.value = true
  
  try {
      if (editingConfig.value) {
        // 更新配置
        const response = await props.axios.put(
          `/xrayr-configs/servers/${props.serverId}/configs/${editingConfig.value.id}`,
          {
            name: configForm.value.name,
            config_path: configForm.value.config_path,
            description: configForm.value.description
          }
        )
        
        // 更新本地配置列表
        const index = configs.value.findIndex(c => c.id === editingConfig.value!.id)
        if (index !== -1) {
          configs.value[index] = { ...configs.value[index], ...response.data }
        }
        
        ElMessage.success('配置更新成功')
      } else {
        // 创建配置
        const response = await props.axios.post(
          `/xrayr-configs/servers/${props.serverId}/configs`,
          {
            name: configForm.value.name,
            config_path: configForm.value.config_path,
            description: configForm.value.description
          }
        )
        
        // 添加到本地配置列表
        configs.value.push(response.data)
        
        ElMessage.success('配置创建成功')
      }
      
      // 关闭对话框
      configFormVisible.value = false
    } catch (error: any) {
      console.error(editingConfig.value ? '更新配置失败' : '创建配置失败', error)
      
      // 处理错误情况
      let errorMessage = editingConfig.value ? '更新配置失败' : '创建配置失败'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }
      
      ElMessage.error(errorMessage)
    } finally {
      loading.value = false
    }
}

// 取消配置表单
const cancelConfigForm = () => {
  configFormVisible.value = false
  configFormRef.value?.resetFields()
}

// 删除配置
const handleDelete = async (config: XrayRConfig) => {
  if (!props.axios || !props.serverId) return
  
  try {
      await ElMessageBox.confirm(
        `确定要删除配置 "${config.name}" 吗？`,
        '删除确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      
      loading.value = true
      
      // 调用API删除配置
      await props.axios.delete(
        `/xrayr-configs/servers/${props.serverId}/configs/${config.id}`
      )
      
      // 从本地配置列表中移除
      configs.value = configs.value.filter(c => c.id !== config.id)
      
      ElMessage.success('配置删除成功')
    } catch (error: any) {
      // 用户取消删除操作时也会进入catch，但不需要显示错误
      if (error !== 'cancel') {
        console.error('删除配置失败:', error)
        
        // 处理错误情况
        let errorMessage = '删除配置失败'
        if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail
        } else if (error.message) {
          errorMessage = error.message
        }
        
        ElMessage.error(errorMessage)
      }
    } finally {
      loading.value = false
    }
}

// 查看配置详情
const viewConfigDetails = async (config: XrayRConfig) => {
  if (!props.axios || !props.serverId) return
  
  loading.value = true
  
  try {
      // 调用API获取配置详情
      const response = await props.axios.get(
        `/xrayr-configs/servers/${props.serverId}/configs/${config.id}`
      )
      
      // 显示配置的详细信息
      ElMessageBox({
        title: `配置详情: ${response.data.name}`,
        message: `<pre style="white-space: pre-wrap; word-break: break-all;">${JSON.stringify(response.data.parsed_config || {}, null, 2)}</pre>`,
        dangerouslyUseHTMLString: true,
        confirmButtonText: '关闭',
        customClass: 'config-details-dialog'
      })
    } catch (error: any) {
      console.error('获取配置详情失败:', error)
      
      // 处理错误情况
      let errorMessage = '获取配置详情失败'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }
      
      ElMessage.error(errorMessage)
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
.config-list-container {
  max-height: 500px;
  overflow-y: auto;
}

.text-gray-500 {
  color: #909399;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-details-dialog .el-message-box__content {
  max-height: 400px;
  overflow-y: auto;
}
</style>