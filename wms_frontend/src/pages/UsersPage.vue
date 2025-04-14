<template>
  <q-page padding>
    <div class="q-pa-md">
      <div class="row q-mb-md">
        <div class="col-12">
          <div class="text-h5">用户管理</div>
          <div class="text-subtitle2">管理系统用户、角色和权限</div>
        </div>
      </div>

      <div class="row q-mb-md">
        <div class="col-12">
          <q-btn color="primary" icon="add" label="添加用户" @click="openUserDialog()" />
          <q-btn class="q-ml-sm" color="secondary" icon="refresh" label="刷新" @click="fetchUsers()" />
        </div>
      </div>

      <div class="row">
        <div class="col-12">
          <q-table
            :rows="users"
            :columns="columns"
            row-key="id"
            :loading="loading"
            :filter="filter"
            :pagination.sync="pagination"
            binary-state-sort
          >
            <template v-slot:top-right>
              <q-input
                dense
                debounce="300"
                v-model="filter"
                placeholder="搜索"
              >
                <template v-slot:append>
                  <q-icon name="search" />
                </template>
              </q-input>
            </template>

            <template v-slot:body-cell-is_active="props">
              <q-td :props="props">
                <q-badge :color="props.row.is_active ? 'positive' : 'negative'">
                  {{ props.row.is_active ? '激活' : '禁用' }}
                </q-badge>
              </q-td>
            </template>

            <template v-slot:body-cell-actions="props">
              <q-td :props="props">
                <q-btn flat round dense color="primary" icon="edit" @click="openUserDialog(props.row)" />
                <q-btn flat round dense color="primary" icon="security" @click="openRolesDialog(props.row)" />
                <q-btn flat round dense :color="props.row.is_active ? 'negative' : 'positive'" 
                  :icon="props.row.is_active ? 'block' : 'check_circle'" 
                  @click="toggleUserStatus(props.row)" />
              </q-td>
            </template>
          </q-table>
        </div>
      </div>
    </div>

    <!-- 用户编辑对话框 -->
    <q-dialog v-model="userDialog" persistent>
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">{{ editingUser.id ? '编辑用户' : '添加用户' }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveUser" class="q-gutter-md">
            <q-input
              v-model="editingUser.username"
              label="用户名"
              :rules="[val => !!val || '请输入用户名']"
              outlined
            />

            <q-input
              v-model="editingUser.email"
              label="电子邮箱"
              type="email"
              :rules="[val => !!val || '请输入电子邮箱', isValidEmail]"
              outlined
            />

            <q-input
              v-model="editingUser.password"
              label="密码"
              type="password"
              :rules="[val => !editingUser.id || !!val || '请输入密码']"
              outlined
              :hint="editingUser.id ? '留空表示不修改密码' : ''"
            />

            <div class="row">
              <div class="col-6">
                <q-input
                  v-model="editingUser.first_name"
                  label="名"
                  outlined
                />
              </div>
              <div class="col-6">
                <q-input
                  v-model="editingUser.last_name"
                  label="姓"
                  outlined
                />
              </div>
            </div>

            <div class="row">
              <div class="col-12">
                <q-toggle v-model="editingUser.is_active" label="激活" />
              </div>
            </div>

            <div class="row" v-if="isAdmin">
              <div class="col-12">
                <q-toggle v-model="editingUser.is_admin" label="管理员" />
              </div>
            </div>

            <div class="row">
              <div class="col-12 flex justify-end">
                <q-btn flat label="取消" color="primary" v-close-popup />
                <q-btn type="submit" label="保存" color="primary" :loading="saving" />
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 用户角色对话框 -->
    <q-dialog v-model="rolesDialog" persistent>
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">管理用户角色</div>
          <div class="text-subtitle2">{{ selectedUser?.username }}</div>
        </q-card-section>

        <q-card-section>
          <q-list bordered separator>
            <q-item v-for="role in roles" :key="role.id">
              <q-item-section>
                <q-item-label>{{ role.name }}</q-item-label>
                <q-item-label caption>{{ role.description }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-checkbox v-model="selectedRoles" :val="role.id" />
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="取消" color="primary" v-close-popup />
          <q-btn label="保存" color="primary" @click="saveUserRoles" :loading="savingRoles" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script>
import { defineComponent, ref, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import { userAPI, roleAPI } from 'src/services/api'
import { useAuthStore } from 'src/stores/auth'

export default defineComponent({
  name: 'UsersPage',

  setup() {
    const $q = useQuasar()
    const authStore = useAuthStore()
    const isAdmin = computed(() => authStore.isAdmin)

    const users = ref([])
    const roles = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const savingRoles = ref(false)
    const filter = ref('')
    const pagination = ref({
      sortBy: 'username',
      descending: false,
      page: 1,
      rowsPerPage: 10,
      rowsNumber: 0
    })

    const userDialog = ref(false)
    const rolesDialog = ref(false)
    const editingUser = ref({
      username: '',
      email: '',
      password: '',
      first_name: '',
      last_name: '',
      is_active: true,
      is_admin: false
    })
    const selectedUser = ref(null)
    const selectedRoles = ref([])
    const userRoles = ref([])

    const columns = [
      { name: 'username', align: 'left', label: '用户名', field: 'username', sortable: true },
      { name: 'email', align: 'left', label: '电子邮箱', field: 'email', sortable: true },
      { name: 'full_name', align: 'left', label: '姓名', field: row => `${row.first_name} ${row.last_name}`.trim() || '-', sortable: false },
      { name: 'is_active', align: 'left', label: '状态', field: 'is_active', sortable: true },
      { name: 'is_admin', align: 'left', label: '管理员', field: row => row.is_admin ? '是' : '否', sortable: true },
      { name: 'actions', align: 'center', label: '操作', field: 'actions', sortable: false }
    ]

    const isValidEmail = (val) => {
      const emailPattern = /^(?=[a-zA-Z0-9@._%+-]{6,254}$)[a-zA-Z0-9._%+-]{1,64}@(?:[a-zA-Z0-9-]{1,63}\.){1,8}[a-zA-Z]{2,63}$/
      return emailPattern.test(val) || '请输入有效的电子邮箱'
    }

    const fetchUsers = async () => {
      loading.value = true
      try {
        const response = await userAPI.getUsers()
        users.value = response.data
      } catch (error) {
        console.error('获取用户列表失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取用户列表失败',
          icon: 'error'
        })
      } finally {
        loading.value = false
      }
    }

    const fetchRoles = async () => {
      try {
        const response = await roleAPI.getRoles()
        roles.value = response.data
      } catch (error) {
        console.error('获取角色列表失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取角色列表失败',
          icon: 'error'
        })
      }
    }

    const fetchUserRoles = async (userId) => {
      try {
        const response = await userAPI.getUser(userId)
        const userWithRoles = response.data
        
        // 假设API返回的用户数据中包含roles数组
        if (userWithRoles.roles) {
          userRoles.value = userWithRoles.roles
          selectedRoles.value = userWithRoles.roles.map(role => role.id)
        } else {
          userRoles.value = []
          selectedRoles.value = []
        }
      } catch (error) {
        console.error('获取用户角色失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取用户角色失败',
          icon: 'error'
        })
      }
    }

    const openUserDialog = (user = null) => {
      if (user) {
        // 编辑现有用户
        editingUser.value = { ...user, password: '' }
      } else {
        // 创建新用户
        editingUser.value = {
          username: '',
          email: '',
          password: '',
          first_name: '',
          last_name: '',
          is_active: true,
          is_admin: false
        }
      }
      userDialog.value = true
    }

    const openRolesDialog = async (user) => {
      selectedUser.value = user
      await fetchUserRoles(user.id)
      rolesDialog.value = true
    }

    const saveUser = async () => {
      saving.value = true
      try {
        const userData = { ...editingUser.value }
        
        // 如果是编辑模式且密码为空，则不发送密码字段
        if (userData.id && !userData.password) {
          delete userData.password
        }
        
        if (userData.id) {
          // 更新现有用户
          await userAPI.updateUser(userData.id, userData)
          $q.notify({
            color: 'positive',
            message: '用户更新成功',
            icon: 'check_circle'
          })
        } else {
          // 创建新用户
          await userAPI.createUser(userData)
          $q.notify({
            color: 'positive',
            message: '用户创建成功',
            icon: 'check_circle'
          })
        }
        
        userDialog.value = false
        fetchUsers()
      } catch (error) {
        console.error('保存用户失败:', error)
        $q.notify({
          color: 'negative',
          message: '保存用户失败: ' + (error.response?.data?.error || error.message),
          icon: 'error'
        })
      } finally {
        saving.value = false
      }
    }

    const saveUserRoles = async () => {
      savingRoles.value = true
      try {
        // 获取当前用户的角色ID列表
        const currentRoleIds = userRoles.value.map(role => role.id)
        
        // 找出需要添加的角色
        const rolesToAdd = selectedRoles.value.filter(roleId => !currentRoleIds.includes(roleId))
        
        // 找出需要删除的角色
        const rolesToRemove = currentRoleIds.filter(roleId => !selectedRoles.value.includes(roleId))
        
        // 添加新角色
        for (const roleId of rolesToAdd) {
          await roleAPI.assignRoleToUser(selectedUser.value.id, roleId)
        }
        
        // 删除旧角色
        for (const roleId of rolesToRemove) {
          // 假设我们可以通过用户ID和角色ID找到对应的userRoleId
          const userRole = userRoles.value.find(ur => ur.id === roleId)
          if (userRole) {
            await roleAPI.removeRoleFromUser(userRole.id)
          }
        }
        
        $q.notify({
          color: 'positive',
          message: '用户角色更新成功',
          icon: 'check_circle'
        })
        
        rolesDialog.value = false
        fetchUsers()
      } catch (error) {
        console.error('保存用户角色失败:', error)
        $q.notify({
          color: 'negative',
          message: '保存用户角色失败',
          icon: 'error'
        })
      } finally {
        savingRoles.value = false
      }
    }

    const toggleUserStatus = async (user) => {
      try {
        const updatedUser = { ...user, is_active: !user.is_active }
        await userAPI.updateUser(user.id, updatedUser)
        
        $q.notify({
          color: 'positive',
          message: `用户已${updatedUser.is_active ? '激活' : '禁用'}`,
          icon: 'check_circle'
        })
        
        fetchUsers()
      } catch (error) {
        console.error('更新用户状态失败:', error)
        $q.notify({
          color: 'negative',
          message: '更新用户状态失败',
          icon: 'error'
        })
      }
    }

    onMounted(() => {
      fetchUsers()
      fetchRoles()
    })

    return {
      users,
      roles,
      loading,
      saving,
      savingRoles,
      filter,
      pagination,
      columns,
      userDialog,
      rolesDialog,
      editingUser,
      selectedUser,
      selectedRoles,
      isAdmin,
      isValidEmail,
      fetchUsers,
      openUserDialog,
      openRolesDialog,
      saveUser,
      saveUserRoles,
      toggleUserStatus
    }
  }
})
</script>
