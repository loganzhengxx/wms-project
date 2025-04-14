<template>
  <q-page class="flex flex-center bg-grey-2">
    <q-card class="login-card q-pa-lg">
      <q-card-section class="text-center">
        <div class="text-h5 q-mb-md">智能库存系统</div>
        <div class="text-subtitle2 q-mb-xl">请登录您的账户</div>
      </q-card-section>

      <q-card-section>
        <q-form @submit="onSubmit" class="q-gutter-md">
          <q-input
            v-model="email"
            label="电子邮箱"
            type="email"
            :rules="[val => !!val || '请输入电子邮箱', isValidEmail]"
            outlined
          >
            <template v-slot:prepend>
              <q-icon name="email" />
            </template>
          </q-input>

          <q-input
            v-model="password"
            label="密码"
            :type="isPwd ? 'password' : 'text'"
            :rules="[val => !!val || '请输入密码']"
            outlined
          >
            <template v-slot:prepend>
              <q-icon name="lock" />
            </template>
            <template v-slot:append>
              <q-icon
                :name="isPwd ? 'visibility_off' : 'visibility'"
                class="cursor-pointer"
                @click="isPwd = !isPwd"
              />
            </template>
          </q-input>

          <div class="flex justify-between items-center q-mt-md">
            <q-checkbox v-model="rememberMe" label="记住我" />
            <q-btn flat color="primary" label="忘记密码?" size="sm" to="/forgot-password" />
          </div>

          <div class="q-mt-lg">
            <q-btn
              type="submit"
              color="primary"
              label="登录"
              class="full-width"
              :loading="loading"
            />
          </div>

          <div class="text-center q-mt-sm">
            <q-btn flat color="primary" label="注册新账户" size="sm" to="/register" />
          </div>
        </q-form>
      </q-card-section>

      <q-dialog v-model="errorDialog">
        <q-card>
          <q-card-section class="row items-center">
            <q-avatar icon="error" color="negative" text-color="white" />
            <span class="q-ml-sm">登录失败</span>
          </q-card-section>

          <q-card-section>
            {{ errorMessage }}
          </q-card-section>

          <q-card-actions align="right">
            <q-btn flat label="确定" color="primary" v-close-popup />
          </q-card-actions>
        </q-card>
      </q-dialog>
    </q-card>
  </q-page>
</template>

<script>
import { defineComponent, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from 'src/stores/auth'

export default defineComponent({
  name: 'LoginPage',

  setup () {
    const router = useRouter()
    const authStore = useAuthStore()

    const email = ref('')
    const password = ref('')
    const isPwd = ref(true)
    const rememberMe = ref(false)
    const loading = ref(false)
    const errorDialog = ref(false)
    const errorMessage = ref('')

    const isValidEmail = (val) => {
      const emailPattern = /^(?=[a-zA-Z0-9@._%+-]{6,254}$)[a-zA-Z0-9._%+-]{1,64}@(?:[a-zA-Z0-9-]{1,63}\.){1,8}[a-zA-Z]{2,63}$/
      return emailPattern.test(val) || '请输入有效的电子邮箱'
    }

    const onSubmit = async () => {
      loading.value = true
      try {
        await authStore.login({
          email: email.value,
          password: password.value
        })
        
        // 登录成功，重定向到首页
        router.push('/')
      } catch (error) {
        console.error('登录失败:', error)
        errorMessage.value = error.response?.data?.error || '登录失败，请检查您的凭据'
        errorDialog.value = true
      } finally {
        loading.value = false
      }
    }

    return {
      email,
      password,
      isPwd,
      rememberMe,
      loading,
      errorDialog,
      errorMessage,
      isValidEmail,
      onSubmit
    }
  }
})
</script>

<style lang="scss" scoped>
.login-card {
  width: 100%;
  max-width: 400px;
  border-radius: 8px;
}

@media (max-width: 599px) {
  .login-card {
    width: 90%;
  }
}
</style>
