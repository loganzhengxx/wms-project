<template>
  <q-page padding>
    <div class="q-pa-md">
      <div class="row q-mb-md">
        <div class="col-12">
          <div class="text-h5">库存管理</div>
          <div class="text-subtitle2">查看和管理库存</div>
        </div>
      </div>

      <div class="row q-mb-md">
        <div class="col-12">
          <q-btn color="primary" icon="add" label="添加库存" @click="openAddInventoryDialog()" />
          <q-btn class="q-ml-sm" color="secondary" icon="refresh" label="刷新" @click="fetchInventory()" />
        </div>
      </div>

      <div class="row q-mb-md">
        <div class="col-12 col-md-3 q-pr-md-md">
          <q-select
            v-model="filter.warehouse"
            :options="warehouseOptions"
            label="仓库"
            dense
            outlined
            clearable
            emit-value
            map-options
            @update:model-value="fetchInventory"
          />
        </div>
        <div class="col-12 col-md-3 q-pr-md-md q-pt-xs-sm">
          <q-input
            v-model="filter.product"
            label="产品名称/SKU"
            dense
            outlined
            clearable
            @keyup.enter="fetchInventory"
          />
        </div>
        <div class="col-12 col-md-3 q-pr-md-md q-pt-xs-sm">
          <q-select
            v-model="filter.lowStock"
            :options="[
              { label: '所有库存', value: false },
              { label: '仅低库存', value: true }
            ]"
            label="库存状态"
            dense
            outlined
            emit-value
            map-options
            @update:model-value="fetchInventory"
          />
        </div>
        <div class="col-12 col-md-3 q-pt-xs-sm">
          <q-btn color="primary" icon="search" label="搜索" @click="fetchInventory" />
          <q-btn class="q-ml-sm" color="secondary" flat label="重置" @click="resetFilters" />
        </div>
      </div>

      <div class="row">
        <div class="col-12">
          <q-table
            :rows="inventory"
            :columns="columns"
            row-key="id"
            :loading="loading"
            :pagination.sync="pagination"
            binary-state-sort
          >
            <template v-slot:body-cell-available_quantity="props">
              <q-td :props="props">
                <q-badge :color="getStockLevelColor(props.row)">
                  {{ props.value }}
                </q-badge>
              </q-td>
            </template>

            <template v-slot:body-cell-actions="props">
              <q-td :props="props">
                <q-btn flat round dense color="primary" icon="edit" @click="openAdjustDialog(props.row)" />
                <q-btn flat round dense color="primary" icon="history" @click="viewTransactions(props.row)" />
                <q-btn flat round dense color="primary" icon="list" @click="viewBatches(props.row)" />
              </q-td>
            </template>
          </q-table>
        </div>
      </div>
    </div>

    <!-- 添加库存对话框 -->
    <q-dialog v-model="addInventoryDialog" persistent>
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">添加库存</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveNewInventory" class="q-gutter-md">
            <q-select
              v-model="newInventory.product_id"
              :options="productOptions"
              label="产品"
              :rules="[val => !!val || '请选择产品']"
              outlined
              emit-value
              map-options
            />

            <q-select
              v-model="newInventory.warehouse_id"
              :options="warehouseOptions"
              label="仓库"
              :rules="[val => !!val || '请选择仓库']"
              outlined
              emit-value
              map-options
              @update:model-value="fetchLocations"
            />

            <q-select
              v-model="newInventory.location_id"
              :options="locationOptions"
              label="位置"
              :rules="[val => !!val || '请选择位置']"
              outlined
              emit-value
              map-options
              :disable="!newInventory.warehouse_id"
            />

            <q-input
              v-model.number="newInventory.quantity"
              label="数量"
              type="number"
              :rules="[
                val => val !== null && val !== undefined || '请输入数量',
                val => val >= 0 || '数量不能为负数'
              ]"
              outlined
            />

            <q-select
              v-model="newInventory.batch_id"
              :options="batchOptions"
              label="批次"
              outlined
              clearable
              emit-value
              map-options
            />

            <q-input
              v-model="newInventory.notes"
              label="备注"
              outlined
            />

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

    <!-- 库存调整对话框 -->
    <q-dialog v-model="adjustDialog" persistent>
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">调整库存</div>
          <div class="text-subtitle2">{{ selectedInventory?.product_name }} - {{ selectedInventory?.location_name }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveAdjustment" class="q-gutter-md">
            <div class="row q-mb-md">
              <div class="col-12">
                <div class="text-subtitle1">当前库存: {{ selectedInventory?.quantity || 0 }}</div>
                <div class="text-subtitle1">可用库存: {{ selectedInventory?.available_quantity || 0 }}</div>
              </div>
            </div>

            <q-input
              v-model.number="adjustment.quantity"
              label="调整数量"
              type="number"
              :rules="[val => val !== 0 || '调整数量不能为0']"
              outlined
              hint="正数表示增加，负数表示减少"
            />

            <q-select
              v-model="adjustment.batch_id"
              :options="batchOptions"
              label="批次"
              outlined
              clearable
              emit-value
              map-options
            />

            <q-input
              v-model="adjustment.reason"
              label="调整原因"
              outlined
              :rules="[val => !!val || '请输入调整原因']"
            />

            <div class="row">
              <div class="col-12 flex justify-end">
                <q-btn flat label="取消" color="primary" v-close-popup />
                <q-btn type="submit" label="保存" color="primary" :loading="adjusting" />
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 库存交易记录对话框 -->
    <q-dialog v-model="transactionsDialog" persistent maximized>
      <q-card>
        <q-card-section class="row items-center">
          <div class="text-h6">库存交易记录</div>
          <div class="text-subtitle2 q-ml-md">{{ selectedInventory?.product_name }} - {{ selectedInventory?.location_name }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-separator />

        <q-card-section style="max-height: 80vh" class="scroll">
          <q-table
            :rows="transactions"
            :columns="transactionColumns"
            row-key="id"
            :loading="loadingTransactions"
            :pagination.sync="transactionPagination"
            binary-state-sort
          >
            <template v-slot:body-cell-transaction_type="props">
              <q-td :props="props">
                <q-badge :color="props.value === 'increase' ? 'positive' : 'negative'">
                  {{ props.value === 'increase' ? '增加' : '减少' }}
                </q-badge>
              </q-td>
            </template>
          </q-table>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 批次库存对话框 -->
    <q-dialog v-model="batchesDialog" persistent>
      <q-card style="min-width: 600px">
        <q-card-section>
          <div class="text-h6">批次库存</div>
          <div class="text-subtitle2">{{ selectedInventory?.product_name }} - {{ selectedInventory?.location_name }}</div>
        </q-card-section>

        <q-separator />

        <q-card-section style="max-height: 60vh" class="scroll">
          <q-table
            :rows="batches"
            :columns="batchColumns"
            row-key="id"
            :loading="loadingBatches"
          >
            <template v-slot:body-cell-available_quantity="props">
              <q-td :props="props">
                <q-badge :color="props.value > 0 ? 'positive' : 'negative'">
                  {{ props.value }}
                </q-badge>
              </q-td>
            </template>

            <template v-slot:body-cell-expiry_date="props">
              <q-td :props="props">
                <q-badge :color="isExpired(props.value) ? 'negative' : 'positive'">
                  {{ props.value || '无到期日期' }}
                </q-badge>
              </q-td>
            </template>
          </q-table>
        </q-card-section>

        <q-separator />

        <q-card-actions align="right">
          <q-btn flat label="关闭" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script>
import { defineComponent, ref, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import { inventoryAPI, productAPI, warehouseAPI } from 'src/services/api'

export default defineComponent({
  name: 'InventoryPage',

  setup() {
    const $q = useQuasar()

    // 库存列表相关
    const inventory = ref([])
    const loading = ref(false)
    const pagination = ref({
      sortBy: 'product_name',
      descending: false,
      page: 1,
      rowsPerPage: 10,
      rowsNumber: 0
    })
    const filter = ref({
      warehouse: null,
      product: '',
      lowStock: false
    })

    // 选项数据
    const warehouses = ref([])
    const products = ref([])
    const locations = ref([])
    const batches = ref([])

    // 添加库存相关
    const addInventoryDialog = ref(false)
    const newInventory = ref({
      product_id: null,
      warehouse_id: null,
      location_id: null,
      quantity: 0,
      batch_id: null,
      notes: ''
    })
    const saving = ref(false)

    // 库存调整相关
    const adjustDialog = ref(false)
    const selectedInventory = ref(null)
    const adjustment = ref({
      quantity: 0,
      reason: '',
      batch_id: null
    })
    const adjusting = ref(false)

    // 交易记录相关
    const transactionsDialog = ref(false)
    const transactions = ref([])
    const loadingTransactions = ref(false)
    const transactionPagination = ref({
      sortBy: 'created_at',
      descending: true,
      page: 1,
      rowsPerPage: 10,
      rowsNumber: 0
    })

    // 批次库存相关
    const batchesDialog = ref(false)
    const loadingBatches = ref(false)

    const columns = [
      { name: 'product_name', align: 'left', label: '产品名称', field: 'product_name', sortable: true },
      { name: 'product_sku', align: 'left', label: 'SKU', field: row => row.product_sku || '-', sortable: false },
      { name: 'warehouse_name', align: 'left', label: '仓库', field: 'warehouse_name', sortable: true },
      { name: 'location_name', align: 'left', label: '位置', field: 'location_name', sortable: true },
      { name: 'quantity', align: 'right', label: '总数量', field: 'quantity', sortable: true },
      { name: 'reserved_quantity', align: 'right', label: '预留数量', field: 'reserved_quantity', sortable: true },
      { name: 'available_quantity', align: 'right', label: '可用数量', field: 'available_quantity', sortable: true },
      { name: 'actions', align: 'center', label: '操作', field: 'actions', sortable: false }
    ]

    const transactionColumns = [
      { name: 'created_at', align: 'left', label: '时间', field: 'created_at', sortable: true },
      { name: 'transaction_type', align: 'center', label: '类型', field: 'transaction_type', sortable: true },
      { name: 'quantity', align: 'right', label: '数量', field: 'quantity', sortable: true },
      { name: 'previous_quantity', align: 'right', label: '之前数量', field: 'previous_quantity', sortable: true },
      { name: 'new_quantity', align: 'right', label: '新数量', field: 'new_quantity', sortable: true },
      { name: 'batch_number', align: 'left', label: '批次', field: 'batch_number', sortable: true },
      { name: 'reference_type', align: 'left', label: '引用类型', field: 'reference_type', sortable: true },
      { name: 'user_name', align: 'left', label: '操作人', field: 'user_name', sortable: true },
      { name: 'notes', align: 'left', label: '备注', field: 'notes', sortable: false }
    ]

    const batchColumns = [
      { name: 'batch_number', align: 'left', label: '批次号', field: 'batch_number', sortable: true },
      { name: 'quantity', align: 'right', label: '数量', field: 'quantity', sortable: true },
      { name: 'reserved_quantity', align: 'right', label: '预留数量', field: 'reserved_quantity', sortable: true },
      { name: 'available_quantity', align: 'right', label: '可用数量', field: 'available_quantity', sortable: true },
      { name: 'manufacturing_date', align: 'left', label: '生产日期', field: 'manufacturing_date', sortable: true },
      { name: 'expiry_date', align: 'left', label: '到期日期', field: 'expiry_date', sortable: true },
      { name: 'received_date', align: 'left', label: '接收日期', field: 'received_date', sortable: true }
    ]

    const warehouseOptions = computed(() => {
      return warehouses.value.map(warehouse => ({
        label: warehouse.name,
        value: warehouse.id
      }))
    })

    const productOptions = computed(() => {
      return products.value.map(product => ({
        label: `${product.name} (${product.sku})`,
        value: product.id
      }))
    })

    const locationOptions = computed(() => {
      return locations.value.map(location => ({
        label: `${location.name} (${location.code})`,
        value: location.id
      }))
    })

    const batchOptions = computed(() => {
      return batches.value.map(batch => ({
        label: `${batch.batch_number} (${batch.expiry_date ? '到期: ' + batch.expiry_date : '无到期日期'})`,
        value: batch.id
      }))
    })

    const fetchInventory = async () => {
      loading.value = true
      try {
        const params = {}
        if (filter.value.warehouse) params.warehouse_id = filter.value.warehouse
        if (filter.value.product) params.product = filter.value.product
        if (filter.value.lowStock) params.low_stock = true
        
        const response = await inventoryAPI.getInventory(params)
        inventory.value = response.data
      } catch (error) {
        console.error('获取库存列表失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取库存列表失败',
          icon: 'error'
        })
      } finally {
        loading.value = false
      }
    }

    const fetchWarehouses = async () => {
      try {
        const response = await warehouseAPI.getWarehouses()
        warehouses.value = response.data
      } catch (error) {
        console.error('获取仓库列表失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取仓库列表失败',
          icon: 'error'
        })
      }
    }

    const fetchProducts = async () => {
      try {
        const response = await productAPI.getProducts()
        products.value = response.data
      } catch (error) {
        console.error('获取产品列表失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取产品列表失败',
          icon: 'error'
        })
      }
    }

    const fetchLocations = async () => {
      if (!newInventory.value.warehouse_id) {
        locations.value = []
        return
      }
      
      try {
        const response = await warehouseAPI.getLocations(newInventory.value.warehouse_id)
        locations.value = response.data
      } catch (error) {
        console.error('获取位置列表失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取位置列表失败',
          icon: 'error'
        })
      }
    }

    const fetchBatches = async (productId) => {
      if (!productId) {
        batches.value = []
        return
      }
      
      try {
        const response = await productAPI.getProductBatches(productId)
        batches.value = response.data
      } catch (error) {
        console.error('获取批次列表失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取批次列表失败',
          icon: 'error'
        })
      }
    }

    const resetFilters = () => {
      filter.value = {
        warehouse: null,
        product: '',
        lowStock: false
      }
      fetchInventory()
    }

    const getStockLevelColor = (inventoryItem) => {
      if (!inventoryItem.product_min_stock_level) return 'positive'
      
      if (inventoryItem.available_quantity <= 0) {
        return 'negative'
      } else if (inventoryItem.available_quantity < inventoryItem.product_min_stock_level) {
        return 'warning'
      } else {
        return 'positive'
      }
    }

    const isExpired = (date) => {
      if (!date) return false
      return new Date(date) < new Date()
    }

    const openAddInventoryDialog = () => {
      newInventory.value = {
        product_id: null,
        warehouse_id: null,
        location_id: null,
        quantity: 0,
        batch_id: null,
        notes: ''
      }
      addInventoryDialog.value = true
    }

    const saveNewInventory = async () => {
      saving.value = true
      try {
        // 假设API支持添加库存
        await inventoryAPI.adjustInventory(
          null, // 新库存没有ID
          newInventory.value.quantity,
          newInventory.value.notes || '初始库存',
          newInventory.value.batch_id
        )
        
        $q.notify({
          color: 'positive',
          message: '库存添加成功',
          icon: 'check_circle'
        })
        
        addInventoryDialog.value = false
        fetchInventory()
      } catch (error) {
        console.error('添加库存失败:', error)
        $q.notify({
          color: 'negative',
          message: '添加库存失败: ' + (error.response?.data?.error || error.message),
          icon: 'error'
        })
      } finally {
        saving.value = false
      }
    }

    const openAdjustDialog = async (inventoryItem) => {
      selectedInventory.value = inventoryItem
      adjustment.value = {
        quantity: 0,
        reason: '',
        batch_id: null
      }
      
      // 获取产品的批次
      await fetchBatches(inventoryItem.product_id)
      
      adjustDialog.value = true
    }

    const saveAdjustment = async () => {
      adjusting.value = true
      try {
        await inventoryAPI.adjustInventory(
          selectedInventory.value.id,
          adjustment.value.quantity,
          adjustment.value.reason,
          adjustment.value.batch_id
        )
        
        $q.notify({
          color: 'positive',
          message: '库存调整成功',
          icon: 'check_circle'
        })
        
        adjustDialog.value = false
        fetchInventory()
      } catch (error) {
        console.error('调整库存失败:', error)
        $q.notify({
          color: 'negative',
          message: '调整库存失败: ' + (error.response?.data?.error || error.message),
          icon: 'error'
        })
      } finally {
        adjusting.value = false
      }
    }

    const viewTransactions = async (inventoryItem) => {
      selectedInventory.value = inventoryItem
      loadingTransactions.value = true
      
      try {
        const params = {
          product_id: inventoryItem.product_id,
          location_id: inventoryItem.location_id
        }
        
        const response = await inventoryAPI.getInventoryTransactions(params)
        transactions.value = response.data
        
        transactionsDialog.value = true
      } catch (error) {
        console.error('获取交易记录失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取交易记录失败',
          icon: 'error'
        })
      } finally {
        loadingTransactions.value = false
      }
    }

    const viewBatches = async (inventoryItem) => {
      selectedInventory.value = inventoryItem
      loadingBatches.value = true
      
      try {
        // 假设API支持获取库存的批次
        const response = await inventoryAPI.getBatchInventory(inventoryItem.id)
        batches.value = response.data
        
        batchesDialog.value = true
      } catch (error) {
        console.error('获取批次库存失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取批次库存失败',
          icon: 'error'
        })
      } finally {
        loadingBatches.value = false
      }
    }

    onMounted(() => {
      fetchInventory()
      fetchWarehouses()
      fetchProducts()
    })

    return {
      // 库存列表相关
      inventory,
      loading,
      pagination,
      filter,
      columns,
      fetchInventory,
      resetFilters,
      getStockLevelColor,
      
      // 选项数据
      warehouseOptions,
      productOptions,
      locationOptions,
      batchOptions,
      
      // 添加库存相关
      addInventoryDialog,
      newInventory,
      saving,
      openAddInventoryDialog,
      saveNewInventory,
      fetchLocations,
      
      // 库存调整相关
      adjustDialog,
      selectedInventory,
      adjustment,
      adjusting,
      openAdjustDialog,
      saveAdjustment,
      
      // 交易记录相关
      transactionsDialog,
      transactions,
      loadingTransactions,
      transactionPagination,
      transactionColumns,
      viewTransactions,
      
      // 批次库存相关
      batchesDialog,
      batches,
      loadingBatches,
      batchColumns,
      viewBatches,
      isExpired
    }
  }
})
</script>
