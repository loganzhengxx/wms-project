// 用于API请求的服务
import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: process.env.API_URL || 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器，添加认证令牌
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Token ${token}`
    }
    
    // 添加租户ID
    const tenantId = localStorage.getItem('tenantId')
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId
    }
    
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器，处理错误
api.interceptors.response.use(
  response => {
    return response
  },
  error => {
    // 处理401错误（未授权）
    if (error.response && error.response.status === 401) {
      // 清除本地存储的认证信息
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      
      // 重定向到登录页面
      window.location.href = '/#/login'
    }
    return Promise.reject(error)
  }
)

// 认证相关API
export const authAPI = {
  login(credentials) {
    return api.post('/accounts/auth/login/', credentials)
  },
  register(userData) {
    return api.post('/accounts/auth/register/', userData)
  },
  getCurrentUser() {
    return api.get('/accounts/auth/me/')
  }
}

// 用户管理API
export const userAPI = {
  getUsers(params) {
    return api.get('/accounts/users/', { params })
  },
  getUser(id) {
    return api.get(`/accounts/users/${id}/`)
  },
  createUser(userData) {
    return api.post('/accounts/users/', userData)
  },
  updateUser(id, userData) {
    return api.put(`/accounts/users/${id}/`, userData)
  },
  deleteUser(id) {
    return api.delete(`/accounts/users/${id}/`)
  }
}

// 角色和权限API
export const roleAPI = {
  getRoles() {
    return api.get('/accounts/roles/')
  },
  getRole(id) {
    return api.get(`/accounts/roles/${id}/`)
  },
  createRole(roleData) {
    return api.post('/accounts/roles/', roleData)
  },
  updateRole(id, roleData) {
    return api.put(`/accounts/roles/${id}/`, roleData)
  },
  deleteRole(id) {
    return api.delete(`/accounts/roles/${id}/`)
  },
  getPermissions() {
    return api.get('/accounts/permissions/')
  },
  assignPermissionToRole(roleId, permissionId) {
    return api.post('/accounts/role-permissions/', {
      role: roleId,
      permission: permissionId
    })
  },
  removePermissionFromRole(rolePermissionId) {
    return api.delete(`/accounts/role-permissions/${rolePermissionId}/`)
  },
  assignRoleToUser(userId, roleId) {
    return api.post('/accounts/user-roles/', {
      user: userId,
      role: roleId
    })
  },
  removeRoleFromUser(userRoleId) {
    return api.delete(`/accounts/user-roles/${userRoleId}/`)
  }
}

// 仓库管理API
export const warehouseAPI = {
  getWarehouses() {
    return api.get('/warehouse/warehouses/')
  },
  getWarehouse(id) {
    return api.get(`/warehouse/warehouses/${id}/`)
  },
  createWarehouse(warehouseData) {
    return api.post('/warehouse/warehouses/', warehouseData)
  },
  updateWarehouse(id, warehouseData) {
    return api.put(`/warehouse/warehouses/${id}/`, warehouseData)
  },
  deleteWarehouse(id) {
    return api.delete(`/warehouse/warehouses/${id}/`)
  },
  getZones(warehouseId) {
    return api.get('/warehouse/zones/', { params: { warehouse_id: warehouseId } })
  },
  getLocations(warehouseId, zoneId) {
    const params = {}
    if (warehouseId) params.warehouse_id = warehouseId
    if (zoneId) params.zone_id = zoneId
    return api.get('/warehouse/locations/', { params })
  }
}

// 任务管理API
export const taskAPI = {
  getTasks(params) {
    return api.get('/warehouse/tasks/', { params })
  },
  getTask(id) {
    return api.get(`/warehouse/tasks/${id}/`)
  },
  createTask(taskData) {
    return api.post('/warehouse/tasks/', taskData)
  },
  updateTask(id, taskData) {
    return api.put(`/warehouse/tasks/${id}/`, taskData)
  },
  deleteTask(id) {
    return api.delete(`/warehouse/tasks/${id}/`)
  },
  assignTask(id, userId) {
    return api.post(`/warehouse/tasks/${id}/assign/`, { user_id: userId })
  },
  startTask(id) {
    return api.post(`/warehouse/tasks/${id}/start/`)
  },
  completeTask(id) {
    return api.post(`/warehouse/tasks/${id}/complete/`)
  },
  cancelTask(id, notes) {
    return api.post(`/warehouse/tasks/${id}/cancel/`, { notes })
  },
  getTaskHistory(id) {
    return api.get(`/warehouse/task-history/`, { params: { task_id: id } })
  }
}

// 产品管理API
export const productAPI = {
  getCategories() {
    return api.get('/inventory/categories/')
  },
  getProducts(params) {
    return api.get('/inventory/products/', { params })
  },
  getProduct(id) {
    return api.get(`/inventory/products/${id}/`)
  },
  createProduct(productData) {
    return api.post('/inventory/products/', productData)
  },
  updateProduct(id, productData) {
    return api.put(`/inventory/products/${id}/`, productData)
  },
  deleteProduct(id) {
    return api.delete(`/inventory/products/${id}/`)
  },
  getProductInventory(id) {
    return api.get(`/inventory/products/${id}/inventory/`)
  },
  getProductBatches(id) {
    return api.get(`/inventory/products/${id}/batches/`)
  }
}

// 库存管理API
export const inventoryAPI = {
  getInventory(params) {
    return api.get('/inventory/inventory/', { params })
  },
  adjustInventory(id, quantity, reason, batchId) {
    return api.post(`/inventory/inventory/${id}/adjust/`, {
      quantity,
      reason,
      batch_id: batchId
    })
  },
  getBatches(params) {
    return api.get('/inventory/batches/', { params })
  },
  getBatchInventory(id) {
    return api.get(`/inventory/batches/${id}/inventory/`)
  },
  getInventoryTransactions(params) {
    return api.get('/inventory/inventory-transactions/', { params })
  }
}

// 供应商管理API
export const supplierAPI = {
  getSuppliers(params) {
    return api.get('/inventory/suppliers/', { params })
  },
  getSupplier(id) {
    return api.get(`/inventory/suppliers/${id}/`)
  },
  createSupplier(supplierData) {
    return api.post('/inventory/suppliers/', supplierData)
  },
  updateSupplier(id, supplierData) {
    return api.put(`/inventory/suppliers/${id}/`, supplierData)
  },
  deleteSupplier(id) {
    return api.delete(`/inventory/suppliers/${id}/`)
  },
  getSupplierProducts(id) {
    return api.get(`/inventory/suppliers/${id}/products/`)
  }
}

// 通知API
export const notificationAPI = {
  getNotifications() {
    return api.get('/core/notifications/')
  },
  markAsRead(id) {
    return api.post(`/core/notifications/${id}/mark_as_read/`)
  },
  markAllAsRead() {
    return api.post('/core/notifications/mark_all_as_read/')
  }
}

export default {
  authAPI,
  userAPI,
  roleAPI,
  warehouseAPI,
  taskAPI,
  productAPI,
  inventoryAPI,
  supplierAPI,
  notificationAPI
}
