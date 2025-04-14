import { defineStore } from 'pinia'
import { authAPI } from 'src/services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    tenantId: localStorage.getItem('tenantId') || '',
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user && (state.user.is_admin || state.user.is_superuser),
    currentUser: (state) => state.user
  },

  actions: {
    async login(credentials) {
      this.loading = true
      this.error = null
      try {
        const response = await authAPI.login(credentials)
        this.setAuthData(response.data)
        return response
      } catch (error) {
        this.error = error.response?.data?.error || '登录失败，请检查您的凭据'
        throw error
      } finally {
        this.loading = false
      }
    },

    async register(userData) {
      this.loading = true
      this.error = null
      try {
        const response = await authAPI.register(userData)
        this.setAuthData(response.data)
        return response
      } catch (error) {
        this.error = error.response?.data?.error || '注册失败，请检查您的输入'
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchCurrentUser() {
      if (!this.token) return null
      
      this.loading = true
      try {
        const response = await authAPI.getCurrentUser()
        this.user = response.data
        localStorage.setItem('user', JSON.stringify(response.data))
        return response.data
      } catch (error) {
        console.error('获取当前用户信息失败:', error)
        if (error.response && error.response.status === 401) {
          this.logout()
        }
        return null
      } finally {
        this.loading = false
      }
    },

    setAuthData(data) {
      this.token = data.token
      this.user = data.user || {
        id: data.user_id,
        email: data.email,
        username: data.username,
        is_admin: data.is_admin,
        is_staff: data.is_staff,
        tenant_id: data.tenant_id
      }
      this.tenantId = data.tenant_id || this.user.tenant_id || ''
      
      // 保存到本地存储
      localStorage.setItem('token', this.token)
      localStorage.setItem('user', JSON.stringify(this.user))
      localStorage.setItem('tenantId', this.tenantId)
    },

    logout() {
      this.token = ''
      this.user = null
      this.tenantId = ''
      this.error = null
      
      // 清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('tenantId')
    }
  }
})
