// src-pwa/custom-service-worker.js

/*
 * 这个文件被用作 Workbox 的入口点
 * 它将被编译成 dist/pwa/service-worker.js
 *
 * 更多信息请参考:
 * https://quasar.dev/quasar-cli/developing-pwa/configuring-pwa
 */

import { precacheAndRoute } from 'workbox-precaching'
import { registerRoute } from 'workbox-routing'
import { StaleWhileRevalidate, CacheFirst, NetworkFirst } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'
import { CacheableResponsePlugin } from 'workbox-cacheable-response'

// 使用 self.__WB_MANIFEST 预缓存所有资源
// 这个变量将在构建时被替换为实际的资源列表
precacheAndRoute(self.__WB_MANIFEST)

// 缓存API请求
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'api-cache',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 60 * 60 * 24 // 1天
      })
    ]
  })
)

// 缓存静态资源
registerRoute(
  ({ request }) => request.destination === 'style' || 
                   request.destination === 'script' || 
                   request.destination === 'font',
  new CacheFirst({
    cacheName: 'static-resources',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: 60,
        maxAgeSeconds: 60 * 60 * 24 * 30 // 30天
      })
    ]
  })
)

// 缓存图片
registerRoute(
  ({ request }) => request.destination === 'image',
  new StaleWhileRevalidate({
    cacheName: 'images',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: 60,
        maxAgeSeconds: 60 * 60 * 24 * 30 // 30天
      })
    ]
  })
)

// 离线回退页面
const offlineFallbackPage = '/offline.html'

// 安装事件 - 预缓存离线页面
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('offline-cache').then((cache) => {
      return cache.add(offlineFallbackPage)
    })
  )
})

// 当网络请求失败时提供离线页面
self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(offlineFallbackPage)
      })
    )
  }
})

// 后台同步
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-inventory-transactions') {
    event.waitUntil(syncInventoryTransactions())
  }
})

// 同步库存交易
async function syncInventoryTransactions() {
  try {
    const db = await openDB('wms-offline-db', 1)
    const tx = db.transaction('pending-transactions', 'readwrite')
    const store = tx.objectStore('pending-transactions')
    
    const pendingTransactions = await store.getAll()
    
    for (const transaction of pendingTransactions) {
      try {
        const response = await fetch('/api/inventory/transactions/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(transaction)
        })
        
        if (response.ok) {
          await store.delete(transaction.id)
        }
      } catch (error) {
        console.error('Failed to sync transaction:', error)
      }
    }
    
    await tx.complete
  } catch (error) {
    console.error('Error during sync:', error)
  }
}

// 打开数据库
function openDB(name, version) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(name, version)
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result
      if (!db.objectStoreNames.contains('pending-transactions')) {
        db.createObjectStore('pending-transactions', { keyPath: 'id' })
      }
    }
    
    request.onsuccess = (event) => {
      resolve(event.target.result)
    }
    
    request.onerror = (event) => {
      reject(event.target.error)
    }
  })
}

// 推送通知
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json()
    
    const options = {
      body: data.body,
      icon: '/icons/icon-128x128.png',
      badge: '/icons/badge-72x72.png',
      data: {
        url: data.url
      }
    }
    
    event.waitUntil(
      self.registration.showNotification(data.title, options)
    )
  }
})

// 点击通知
self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  
  if (event.notification.data && event.notification.data.url) {
    event.waitUntil(
      clients.openWindow(event.notification.data.url)
    )
  }
})
