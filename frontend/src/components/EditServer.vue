<template>
  <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
    <el-form-item label="服务器名称" prop="name">
      <el-input v-model="form.name" placeholder="请输入服务器名称" />
    </el-form-item>
    
    <el-form-item label="主机名/IP" prop="hostname">
      <el-input v-model="form.hostname" placeholder="请输入主机名或IP地址" />
    </el-form-item>
    
    <el-form-item label="端口" prop="port">
      <el-input v-model.number="form.port" placeholder="请输入SSH端口" />
    </el-form-item>
    
    <el-form-item label="用户名" prop="username">
      <el-input v-model="form.username" placeholder="请输入SSH用户名" />
    </el-form-item>
    
    <el-form-item label="认证方式" prop="authMethod">
      <el-radio-group v-model="form.authMethod">
        <el-radio label="password">密码</el-radio>
        <el-radio label="key">私钥</el-radio>
        <el-radio label="both">两者都用</el-radio>
      </el-radio-group>
    </el-form-item>
    
    <el-form-item v-if="form.authMethod === 'password' || form.authMethod === 'both'" label="密码" prop="password">
      <el-input v-model="form.password" type="password" placeholder="请输入SSH密码" show-password />
      <div class="form-tip">留空表示不修改当前密码</div>
    </el-form-item>
    
    <el-form-item v-if="form.authMethod === 'key' || form.authMethod === 'both'" label="私钥" prop="privateKey">
      <el-input v-model="form.privateKey" type="textarea" placeholder="请输入SSH私钥" :rows="6" />
      <div class="form-tip">留空表示不修改当前私钥</div>
    </el-form-item>
    
    <el-form-item label="描述">
      <el-input v-model="form.description" type="textarea" placeholder="请输入描述信息" :rows="3" />
    </el-form-item>
    
    <el-form-item>
      <div class="form-actions">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </div>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive, defineProps, defineEmits, withDefaults, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { AxiosInstance } from 'axios'

// Props
interface EditServerProps {
  serverId: number
  axios: AxiosInstance | null
}

const props = withDefaults(defineProps<EditServerProps>(), {
  serverId: 0,
  axios: null
})

// Emits
const emit = defineEmits(['success', 'cancel'])

// 表单状态
const formRef = ref()
const form = reactive({
  name: '',
  hostname: '',
  port: 22,
  username: '',
  authMethod: 'password',
  password: '',
  privateKey: '',
  description: ''
})

// 表单验证规则
const rules = reactive({
  name: [
    { required: true, message: '请输入服务器名称', trigger: 'blur' },
    { max: 100, message: '服务器名称不能超过100个字符', trigger: 'blur' }
  ],
  hostname: [
    { required: true, message: '请输入主机名或IP地址', trigger: 'blur' },
    { max: 255, message: '主机名或IP地址不能超过255个字符', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口必须在1-65535之间', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { max: 100, message: '用户名不能超过100个字符', trigger: 'blur' }
  ],
  authMethod: [
    { required: true, message: '请选择认证方式', trigger: 'change' }
  ]
})

// 加载服务器信息
const loadServerInfo = async () => {
  if (!props.axios || !props.serverId) return
  
  try {
    const response = await props.axios.get(`/servers/servers/${props.serverId}`)
    const server = response.data
    
    form.name = server.name
    form.hostname = server.hostname
    form.port = server.port
    form.username = server.username
    form.description = server.description || ''
    
    // 设置认证方式
    if (server.has_private_key && server.has_password) {
      form.authMethod = 'both'
    } else if (server.has_private_key) {
      form.authMethod = 'key'
    } else {
      form.authMethod = 'password'
    }
  } catch (error) {
    console.error('加载服务器信息失败:', error)
    ElMessage.error('加载服务器信息失败')
    emit('cancel')
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!props.axios || !formRef.value) return
  
  try {
    await formRef.value.validate()
    
    // 构建请求数据 - 使用类型断言来解决TypeScript类型错误
    const requestData: any = {
      name: form.name,
      hostname: form.hostname,
      port: form.port,
      username: form.username,
      description: form.description
    }
    
    // 如果用户输入了新的密码或私钥，则添加到请求数据中
    if (form.password) {
      requestData.password = form.password
    }
    
    if (form.privateKey) {
      requestData.private_key = form.privateKey
    }
    
    // 如果用户清空了密码或私钥，则设置为null表示删除
    if (form.authMethod !== 'password' && form.authMethod !== 'both') {
      requestData.password = null
    }
    
    if (form.authMethod !== 'key' && form.authMethod !== 'both') {
      requestData.private_key = null
    }
    
    // 发送请求
    await props.axios.put(`/servers/servers/${props.serverId}`, requestData)
    
    ElMessage.success('服务器更新成功')
    emit('success')
  } catch (error) {
    console.error('更新服务器失败:', error)
    ElMessage.error('更新服务器失败')
  }
}

// 取消操作
const handleCancel = () => {
  emit('cancel')
}

// 组件挂载时加载服务器信息
onMounted(() => {
  loadServerInfo()
})
</script>

<style scoped>
.form-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>