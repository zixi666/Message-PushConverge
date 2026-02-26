import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '../utils/request'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')

  const login = async (loginData) => {
    try {
      const res = await request.post('/auth/login', loginData)
      const tokenData = res.data
      token.value = tokenData.token
      username.value = loginData.username
      localStorage.setItem('token', tokenData.token)
      localStorage.setItem('username', loginData.username)
      ElMessage.success('登录成功')
      router.push('/')
      return true
    } catch (error) {
      return false
    }
  }

  const register = async (registerData) => {
    try {
      await request.post('/auth/register', registerData)
      ElMessage.success('注册成功，请登录')
      router.push('/login')
      return true
    } catch (error) {
      return false
    }
  }

  const changePassword = async (passwordData) => {
    try {
      await request.post('/auth/change_password', passwordData)
      ElMessage.success('密码修改成功，请重新登录')
      logout()
      return true
    } catch (error) {
      return false
    }
  }

  const logout = () => {
    token.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    router.push('/login')
  }

  const isLoggedIn = () => {
    return !!token.value
  }

  return {
    token,
    username,
    login,
    register,
    changePassword,
    logout,
    isLoggedIn,
  }
})