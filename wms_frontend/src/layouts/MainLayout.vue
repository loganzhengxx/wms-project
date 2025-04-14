<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="菜单"
          @click="toggleLeftDrawer"
        />

        <q-toolbar-title>
          智能库存系统
        </q-toolbar-title>

        <q-space />

        <!-- 通知菜单 -->
        <q-btn flat round dense icon="notifications">
          <q-badge color="red" floating>
            {{ unreadNotifications }}
          </q-badge>
          <q-menu>
            <q-list style="min-width: 300px">
              <q-item-label header>通知</q-item-label>
              <q-separator />
              
              <template v-if="notifications.length > 0">
                <q-item v-for="notification in notifications" :key="notification.id" clickable v-close-popup>
                  <q-item-section>
                    <q-item-label>{{ notification.title }}</q-item-label>
                    <q-item-label caption>{{ notification.message }}</q-item-label>
                  </q-item-section>
                  <q-item-section side>
                    <q-badge :color="notification.is_read ? 'grey' : 'primary'" />
                  </q-item-section>
                </q-item>
                <q-separator />
                <q-item clickable v-close-popup @click="markAllAsRead">
                  <q-item-section class="text-center text-primary">标记所有为已读</q-item-section>
                </q-item>
              </template>
              
              <q-item v-else>
                <q-item-section>
                  <q-item-label>暂无通知</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>

        <!-- 用户菜单 -->
        <q-btn flat round dense icon="person">
          <q-menu>
            <q-list style="min-width: 200px">
              <q-item-label header>{{ currentUser?.username || '用户' }}</q-item-label>
              <q-separator />
              
              <q-item clickable v-close-popup to="/profile">
                <q-item-section avatar>
                  <q-icon name="account_circle" />
                </q-item-section>
                <q-item-section>个人资料</q-item-section>
              </q-item>
              
              <q-item clickable v-close-popup to="/settings">
                <q-item-section avatar>
                  <q-icon name="settings" />
                </q-item-section>
                <q-item-section>设置</q-item-section>
              </q-item>
              
              <q-separator />
              
              <q-item clickable v-close-popup @click="logout">
                <q-item-section avatar>
                  <q-icon name="logout" />
                </q-item-section>
                <q-item-section>退出登录</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      bordered
      :width="240"
      :breakpoint="500"
    >
      <q-scroll-area class="fit">
        <q-list padding>
          <q-item-label header>导航菜单</q-item-label>

          <q-item clickable v-ripple to="/" exact>
            <q-item-section avatar>
              <q-icon name="dashboard" />
            </q-item-section>
            <q-item-section>
              仪表盘
            </q-item-section>
          </q-item>

          <q-expansion-item
            expand-separator
            icon="inventory"
            label="库存管理"
          >
            <q-item clickable v-ripple to="/inventory">
              <q-item-section avatar>
                <q-icon name="inventory_2" />
              </q-item-section>
              <q-item-section>
                库存查询
              </q-item-section>
            </q-item>
            
            <q-item clickable v-ripple to="/inventory/adjust">
              <q-item-section avatar>
                <q-icon name="compare_arrows" />
              </q-item-section>
              <q-item-section>
                库存调整
              </q-item-section>
            </q-item>
            
            <q-item clickable v-ripple to="/inventory/transactions">
              <q-item-section avatar>
                <q-icon name="receipt_long" />
              </q-item-section>
              <q-item-section>
                库存交易记录
              </q-item-section>
            </q-item>
          </q-expansion-item>

          <q-expansion-item
            expand-separator
            icon="category"
            label="产品管理"
          >
            <q-item clickable v-ripple to="/products">
              <q-item-section avatar>
                <q-icon name="inventory" />
              </q-item-section>
              <q-item-section>
                产品列表
              </q-item-section>
            </q-item>
            
            <q-item clickable v-ripple to="/products/categories">
              <q-item-section avatar>
                <q-icon name="folder" />
              </q-item-section>
              <q-item-section>
                产品类别
              </q-item-section>
            </q-item>
            
            <q-item clickable v-ripple to="/products/attributes">
              <q-item-section avatar>
                <q-icon name="label" />
              </q-item-section>
              <q-item-section>
                产品属性
              </q-item-section>
            </q-item>
          </q-expansion-item>

          <q-expansion-item
            expand-separator
            icon="warehouse"
            label="仓库管理"
          >
            <q-item clickable v-ripple to="/warehouses">
              <q-item-section avatar>
                <q-icon name="store" />
              </q-item-section>
              <q-item-section>
                仓库列表
              </q-item-section>
            </q-item>
            
            <q-item clickable v-ripple to="/warehouses/zones">
              <q-item-section avatar>
                <q-icon name="grid_view" />
              </q-item-section>
              <q-item-section>
                区域管理
              </q-item-section>
            </q-item>
            
            <q-item clickable v-ripple to="/warehouses/locations">
              <q-item-section avatar>
                <q-icon name="place" />
              </q-item-section>
              <q-item-section>
                位置管理
              </q-item-section>
            </q-item>
          </q-expansion-item>

          <q-expansion-item
            expand-separator
            icon="assignment"
            label="任务管理"
          >
            <q-item clickable v-ripple to="/tasks">
              <q-item-section avatar>
                <q-icon name="list" />
              </q-item-section>
              <q-item-section>
                任务列表
              </q-item-section>
            </q-item>
            
            <q-item clickable v-ripple to="/tasks/my">
              <q-item-section avatar>
                <q-icon name="person" />
              </q-item-section>
              <q-item-section>
                我的任务
              </q-item-section>
            </q-item>
            
            <q-item clickable v-ripple to="/tasks/create">
              <q-item-section avatar>
                <q-icon name="add" />
              </q-item-section>
              <q-item-section>
                创建任务
              </q-item-section>
            </q-item>
          </q-expansion-item>

          <q-expansion-item
            expand-separator
            icon="people"
            label="用户管理"
            v-if="isAdmin"
          >
            <q-item clickable v-ripple to="/users">
              <q-item-section avatar>
                <q-icon name="person" />
              </q-item-section>
              <q-item-section>
                用户列表
              </q-item-section>
            </q-item>
            
            <q-item clickable v-ripple to="/roles">
              <q-item-section avatar>
                <q-icon name="badge" />
              </q-item-section>
              <q-item-section>
                角色管理
              </q-item-section>
            </q-item>
            
            <q-item clickable v-ripple to="/permissions">
              <q-item-section avatar>
                <q-icon name="security" />
              </q-item-section>
              <q-item-section>
                权限管理
              </q-item-section>
            </q-item>
          </q-expansion-item>

          <q-expansion-item
            expand-separator
            icon="bar_chart"
            label="报表与分析"
          >
            <q-item clickable v-ripple to="/reports/inventory">
              <q-item-section avatar>
                <q-icon name="inventory" />
              </q-item-section>
              <q-item-section>
                库存报表
              </q-item-section>
            </q-item>
            
            <q-item clickable v-ripple to="/reports/activity">
              <q-item-section avatar>
                <q-icon name="history" />
              </q-item-section>
              <q-item-section>
                活动报表
              </q-item-section>
            </q-item>
            
            <q-item clickable v-ripple to="/reports/custom">
              <q-item-section avatar>
                <q-icon name="tune" />
              </q-item-section>
              <q-item-section>
                自定义报表
              </q-item-section>
            </q-item>
          </q-expansion-item>

          <q-item clickable v-ripple to="/settings" v-if="isAdmin">
            <q-item-section avatar>
              <q-icon name="settings" />
            </q-item-section>
            <q-item-section>
              系统设置
            </q-item-section>
          </q-item>
        </q-list>
      </q-scroll-area>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script>
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from 'src/stores/auth'
import { notificationAPI } from 'src/services/api'

export default defineComponent({
  name: 'MainLayout',

  setup () {
    const leftDrawerOpen = ref(false)
    const router = useRouter()
    const authStore = useAuthStore()
    const notifications = ref([])
    
    const currentUser = computed(() => authStore.currentUser)
    const isAdmin = computed(() => authStore.isAdmin)
    const unreadNotifications = computed(() => 
      notifications.value.filter(n => !n.is_read).length
    )

    const toggleLeftDrawer = () => {
      leftDrawerOpen.value = !leftDrawerOpen.value
    }

    const logout = () => {
      authStore.logout()
      router.push('/login')
    }

    const fetchNotifications = async () => {
      try {
        const response = await notificationAPI.getNotifications()
        notifications.value = response.data
      } catch (error) {
        console.error('获取通知失败:', error)
      }
    }

    const markAllAsRead = async () => {
      try {
        await notificationAPI.markAllAsRead()
        notifications.value = notifications.value.map(n => ({
          ...n,
          is_read: true
        }))
      } catch (error) {
        console.error('标记通知为已读失败:', error)
      }
    }

    onMounted(() => {
      fetchNotifications()
      
      // 定期刷新通知
      const notificationInterval = setInterval(fetchNotifications, 60000) // 每分钟刷新一次
      
      // 组件卸载时清除定时器
      return () => {
        clearInterval(notificationInterval)
      }
    })

    return {
      leftDrawerOpen,
      toggleLeftDrawer,
      currentUser,
      isAdmin,
      notifications,
      unreadNotifications,
      logout,
      markAllAsRead
    }
  }
})
</script>
