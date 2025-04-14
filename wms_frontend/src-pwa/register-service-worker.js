// src-pwa/register-service-worker.js

import { register } from 'register-service-worker'
import { Notify } from 'quasar'

// The ready(), registered(), cached(), updatefound() and updated()
// events are fired when the service worker lifecycle phase changes.
// The offline() and error() events are fired when the service worker
// encounters an error or the browser is offline.

register(process.env.SERVICE_WORKER_FILE, {
  // The registrationOptions object will be passed as the second argument
  // to ServiceWorkerContainer.register()
  // https://developer.mozilla.org/en-US/docs/Web/API/ServiceWorkerContainer/register#Parameter

  // registrationOptions: { scope: './' },

  ready (registration) {
    console.log('Service worker is active.')
  },

  registered (registration) {
    console.log('Service worker has been registered.')
  },

  cached (registration) {
    console.log('Content has been cached for offline use.')
    Notify.create({
      message: '内容已缓存，可离线使用',
      color: 'positive',
      icon: 'cloud_done'
    })
  },

  updatefound (registration) {
    console.log('New content is downloading.')
    Notify.create({
      message: '正在下载新内容',
      color: 'info',
      icon: 'cloud_download'
    })
  },

  updated (registration) {
    console.log('New content is available; please refresh.')
    Notify.create({
      message: '新版本可用，请刷新页面',
      color: 'primary',
      icon: 'refresh',
      actions: [
        { label: '刷新', handler: () => { window.location.reload() } }
      ],
      timeout: 0
    })
  },

  offline () {
    console.log('No internet connection found. App is running in offline mode.')
    Notify.create({
      message: '当前处于离线模式',
      color: 'warning',
      icon: 'cloud_off'
    })
  },

  error (err) {
    console.error('Error during service worker registration:', err)
    Notify.create({
      message: '服务工作线程注册错误',
      color: 'negative',
      icon: 'error'
    })
  }
})
