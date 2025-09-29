import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import axios from 'axios'
import './style.css'
import App from './App.vue'

// 配置axios
axios.defaults.baseURL = 'http://localhost:8000'
// 添加请求拦截器，处理认证等
axios.interceptors.request.use(
  config => {
    // 这里可以添加token等认证信息
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 添加响应拦截器，处理错误等
axios.interceptors.response.use(
  response => {
    return response
  },
  error => {
    // 处理响应错误
    if (error.response?.status === 401) {
      // 未授权，清除token并重定向到登录页
      localStorage.removeItem('token')
      // 这里可以跳转到登录页
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)
app.use(ElementPlus)
app.provide('axios', axios)
app.mount('#app')
