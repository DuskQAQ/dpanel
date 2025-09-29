<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="formRules"
    label-width="100px"
    @submit.prevent
  >
    <el-form-item label="服务器名称" prop="name">
      <el-input v-model="formData.name" placeholder="请输入服务器名称" />
    </el-form-item>
    
    <el-form-item label="主机名/IP" prop="hostname">
      <el-input v-model="formData.hostname" placeholder="请输入主机名或IP地址" />
    </el-form-item>
    
    <el-form-item label="端口" prop="port">
      <el-input-number v-model="formData.port" :min="1" :max="65535" placeholder="请输入端口号" />
    </el-form-item>
    
    <el-form-item label="用户名" prop="username">
      <el-input v-model="formData.username" placeholder="请输入SSH用户名" />
    </el-form-item>
    
    <el-form-item label="认证方式" prop="authMethod">
      <el-radio-group v-model="formData.authMethod">
        <el-radio label="password">密码</el-radio>
        <el-radio label="privateKey">私钥</el-radio>
        <el-radio label="both">两者都有</el-radio>
      </el-radio-group>
    </el-form-item>
    
    <el-form-item v-if="formData.authMethod === 'password' || formData.authMethod === 'both'" label="密码" prop="password">
      <el-input v-model="formData.password" type="password" placeholder="请输入SSH密码" />
    </el-form-item>
    
    <el-form-item v-if="formData.authMethod === 'privateKey' || formData.authMethod === 'both'" label="私钥" prop="privateKey">
      <el-input
        v-model="formData.privateKey"
        type="textarea"
        placeholder="请输入SSH私钥内容"
        :rows="6"
      />
    </el-form-item>
    
    <el-form-item label="描述" prop="description">
      <el-input v-model="formData.description" type="textarea" placeholder="请输入描述信息" :rows="3" />
    </el-form-item>
    
    <el-form-item>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </div>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, inject } from 'vue'
import { ElMessage } from 'element-plus'
import type { AxiosInstance } from 'axios'
import type { FormInstance, FormRules } from 'element-plus'

// 注入axios
const axios = inject<AxiosInstance>('axios')

// 定义事件
const emit = defineEmits<{
  success: []
  cancel: []
}>()

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const formData = ref({
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
const formRules = ref<FormRules>({
  name: [
    { required: true, message: '请输入服务器名称', trigger: 'blur' },
    { max: 100, message: '服务器名称不能超过100个字符', trigger: 'blur' }
  ],
  hostname: [
    { required: true, message: '请输入主机名或IP地址', trigger: 'blur' },
    { max: 255, message: '主机名或IP地址不能超过255个字符', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口号', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口号必须在1-65535之间', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入SSH用户名', trigger: 'blur' },
    { max: 100, message: '用户名不能超过100个字符', trigger: 'blur' }
  ],
  password: [
    {
      required: formData.value.authMethod === 'password' || formData.value.authMethod === 'both',
      message: '请输入SSH密码',
      trigger: 'blur'
    }
  ],
  privateKey: [
    {
      required: formData.value.authMethod === 'privateKey' || formData.value.authMethod === 'both',
      message: '请输入SSH私钥',
      trigger: 'blur'
    }
  ]
})

// 处理取消
const handleCancel = () => {
  emit('cancel')
}

// 处理提交
const handleSubmit = async () => {
  if (!formRef.value || !axios) return
  
  try {
    await formRef.value.validate()
    
    // 构建请求数据
    const requestData = {
      name: formData.value.name,
      hostname: formData.value.hostname,
      port: formData.value.port,
      username: formData.value.username,
      password: formData.value.password || undefined,
      privateKey: formData.value.privateKey || undefined,
      description: formData.value.description || undefined
    }
    
    // 发送请求
    await axios.post('/servers/servers/', requestData)
    
    // 触发成功事件
    emit('success')
    
    // 重置表单
    resetForm()
  } catch (error) {
    console.error('创建服务器失败:', error)
    ElMessage.error('创建服务器失败，请稍后重试')
  }
}

// 重置表单
const resetForm = () => {
  formData.value = {
    name: '',
    hostname: '',
    port: 22,
    username: '',
    authMethod: 'password',
    password: '',
    privateKey: '',
    description: ''
  }
  if (formRef.value) {
    formRef.value.resetFields()
  }
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>