<template>
  <q-page padding>
    <div class="q-pa-md">
      <div class="row q-mb-md">
        <div class="col-12">
          <div class="text-h5">任务管理</div>
          <div class="text-subtitle2">管理仓库操作任务</div>
        </div>
      </div>

      <div class="row q-mb-md">
        <div class="col-12">
          <q-btn color="primary" icon="add" label="创建任务" @click="openTaskDialog()" />
          <q-btn class="q-ml-sm" color="secondary" icon="refresh" label="刷新" @click="fetchTasks()" />
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
            @update:model-value="fetchTasks"
          />
        </div>
        <div class="col-12 col-md-3 q-pr-md-md q-pt-xs-sm">
          <q-select
            v-model="filter.status"
            :options="statusOptions"
            label="状态"
            dense
            outlined
            clearable
            emit-value
            map-options
            @update:model-value="fetchTasks"
          />
        </div>
        <div class="col-12 col-md-3 q-pr-md-md q-pt-xs-sm">
          <q-select
            v-model="filter.type"
            :options="taskTypeOptions"
            label="任务类型"
            dense
            outlined
            clearable
            emit-value
            map-options
            @update:model-value="fetchTasks"
          />
        </div>
        <div class="col-12 col-md-3 q-pt-xs-sm">
          <q-btn color="primary" icon="search" label="搜索" @click="fetchTasks" />
          <q-btn class="q-ml-sm" color="secondary" flat label="重置" @click="resetFilters" />
        </div>
      </div>

      <div class="row">
        <div class="col-12">
          <q-table
            :rows="tasks"
            :columns="columns"
            row-key="id"
            :loading="loading"
            :pagination.sync="pagination"
            binary-state-sort
          >
            <template v-slot:body-cell-status="props">
              <q-td :props="props">
                <q-badge :color="getStatusColor(props.value)">
                  {{ getStatusLabel(props.value) }}
                </q-badge>
              </q-td>
            </template>

            <template v-slot:body-cell-priority="props">
              <q-td :props="props">
                <q-badge :color="getPriorityColor(props.value)">
                  {{ getPriorityLabel(props.value) }}
                </q-badge>
              </q-td>
            </template>

            <template v-slot:body-cell-actions="props">
              <q-td :props="props">
                <q-btn flat round dense color="primary" icon="visibility" @click="viewTaskDetails(props.row)" />
                <q-btn flat round dense color="primary" icon="edit" @click="openTaskDialog(props.row)" 
                  v-if="canEditTask(props.row)" />
                <q-btn flat round dense color="primary" icon="assignment_ind" @click="openAssignDialog(props.row)" 
                  v-if="canAssignTask(props.row)" />
                <q-btn flat round dense color="positive" icon="play_arrow" @click="startTask(props.row)" 
                  v-if="canStartTask(props.row)" />
                <q-btn flat round dense color="negative" icon="cancel" @click="cancelTask(props.row)" 
                  v-if="canCancelTask(props.row)" />
                <q-btn flat round dense color="positive" icon="check" @click="completeTask(props.row)" 
                  v-if="canCompleteTask(props.row)" />
              </q-td>
            </template>
          </q-table>
        </div>
      </div>
    </div>

    <!-- 任务编辑对话框 -->
    <q-dialog v-model="taskDialog" persistent maximized>
      <q-card>
        <q-card-section class="row items-center">
          <div class="text-h6">{{ editingTask.id ? '编辑任务' : '创建任务' }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-separator />

        <q-card-section class="q-pa-md" style="max-height: 80vh" scroll>
          <q-form @submit="saveTask" class="q-gutter-md">
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <q-select
                  v-model="editingTask.task_type"
                  :options="taskTypeOptions"
                  label="任务类型"
                  :rules="[val => !!val || '请选择任务类型']"
                  outlined
                  emit-value
                  map-options
                  @update:model-value="onTaskTypeChange"
                />
              </div>
              <div class="col-12 col-md-6">
                <q-select
                  v-model="editingTask.warehouse_id"
                  :options="warehouseOptions"
                  label="仓库"
                  :rules="[val => !!val || '请选择仓库']"
                  outlined
                  emit-value
                  map-options
                />
              </div>
            </div>

            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <q-select
                  v-model="editingTask.priority"
                  :options="priorityOptions"
                  label="优先级"
                  :rules="[val => !!val || '请选择优先级']"
                  outlined
                  emit-value
                  map-options
                />
              </div>
              <div class="col-12 col-md-6">
                <q-input
                  v-model="editingTask.due_date"
                  label="截止日期"
                  type="date"
                  outlined
                />
              </div>
            </div>

            <div class="row q-col-gutter-md">
              <div class="col-12">
                <q-input
                  v-model="editingTask.description"
                  label="任务描述"
                  type="textarea"
                  outlined
                  autogrow
                />
              </div>
            </div>

            <!-- 收货任务特定字段 -->
            <template v-if="editingTask.task_type === 'receiving'">
              <div class="row q-col-gutter-md">
                <div class="col-12 col-md-6">
                  <q-select
                    v-model="editingTask.reference_id"
                    :options="purchaseOrderOptions"
                    label="采购订单"
                    outlined
                    emit-value
                    map-options
                  />
                </div>
                <div class="col-12 col-md-6">
                  <q-input
                    v-model="editingTask.expected_quantity"
                    label="预期数量"
                    type="number"
                    outlined
                  />
                </div>
              </div>
            </template>

            <!-- 拣货任务特定字段 -->
            <template v-if="editingTask.task_type === 'picking'">
              <div class="row q-col-gutter-md">
                <div class="col-12 col-md-6">
                  <q-select
                    v-model="editingTask.reference_id"
                    :options="salesOrderOptions"
                    label="销售订单"
                    outlined
                    emit-value
                    map-options
                  />
                </div>
              </div>
            </template>

            <!-- 上架任务特定字段 -->
            <template v-if="editingTask.task_type === 'putaway'">
              <div class="row q-col-gutter-md">
                <div class="col-12 col-md-6">
                  <q-select
                    v-model="editingTask.product_id"
                    :options="productOptions"
                    label="产品"
                    outlined
                    emit-value
                    map-options
                  />
                </div>
                <div class="col-12 col-md-6">
                  <q-input
                    v-model="editingTask.quantity"
                    label="数量"
                    type="number"
                    outlined
                  />
                </div>
              </div>
              <div class="row q-col-gutter-md">
                <div class="col-12 col-md-6">
                  <q-select
                    v-model="editingTask.source_location_id"
                    :options="locationOptions"
                    label="源位置"
                    outlined
                    emit-value
                    map-options
                  />
                </div>
                <div class="col-12 col-md-6">
                  <q-select
                    v-model="editingTask.destination_location_id"
                    :options="locationOptions"
                    label="目标位置"
                    outlined
                    emit-value
                    map-options
                  />
                </div>
              </div>
            </template>

            <!-- 盘点任务特定字段 -->
            <template v-if="editingTask.task_type === 'inventory_count'">
              <div class="row q-col-gutter-md">
                <div class="col-12 col-md-6">
                  <q-select
                    v-model="editingTask.zone_id"
                    :options="zoneOptions"
                    label="区域"
                    outlined
                    emit-value
                    map-options
                  />
                </div>
                <div class="col-12 col-md-6">
                  <q-select
                    v-model="editingTask.count_type"
                    :options="[
                      { label: '周期盘点', value: 'cycle' },
                      { label: '全面盘点', value: 'full' },
                      { label: '抽样盘点', value: 'sample' }
                    ]"
                    label="盘点类型"
                    outlined
                    emit-value
                    map-options
                  />
                </div>
              </div>
            </template>

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

    <!-- 任务分配对话框 -->
    <q-dialog v-model="assignDialog" persistent>
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">分配任务</div>
          <div class="text-subtitle2">{{ selectedTask?.task_type_label }} - {{ selectedTask?.description }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="assignTask" class="q-gutter-md">
            <q-select
              v-model="assignedUser"
              :options="userOptions"
              label="分配给"
              :rules="[val => !!val || '请选择用户']"
              outlined
              emit-value
              map-options
            />

            <q-input
              v-model="assignmentNote"
              label="备注"
              type="textarea"
              outlined
              autogrow
            />

            <div class="row">
              <div class="col-12 flex justify-end">
                <q-btn flat label="取消" color="primary" v-close-popup />
                <q-btn type="submit" label="分配" color="primary" :loading="assigning" />
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 任务详情对话框 -->
    <q-dialog v-model="detailsDialog" persistent maximized>
      <q-card>
        <q-card-section class="row items-center">
          <div class="text-h6">任务详情</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-separator />

        <q-card-section class="q-pa-md" style="max-height: 80vh" scroll>
          <div class="row q-col-gutter-md">
            <div class="col-12 col-md-6">
              <q-card flat bordered>
                <q-card-section>
                  <div class="text-h6">基本信息</div>
                </q-card-section>
                <q-separator />
                <q-list>
                  <q-item>
                    <q-item-section>
                      <q-item-label caption>任务编号</q-item-label>
                      <q-item-label>{{ selectedTask?.id }}</q-item-label>
                    </q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section>
                      <q-item-label caption>任务类型</q-item-label>
                      <q-item-label>{{ selectedTask?.task_type_label }}</q-item-label>
                    </q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section>
                      <q-item-label caption>状态</q-item-label>
                      <q-item-label>
                        <q-badge :color="getStatusColor(selectedTask?.status)">
                          {{ getStatusLabel(selectedTask?.status) }}
                        </q-badge>
                      </q-item-label>
                    </q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section>
                      <q-item-label caption>优先级</q-item-label>
                      <q-item-label>
                        <q-badge :color="getPriorityColor(selectedTask?.priority)">
                          {{ getPriorityLabel(selectedTask?.priority) }}
                        </q-badge>
                      </q-item-label>
                    </q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section>
                      <q-item-label caption>仓库</q-item-label>
                      <q-item-label>{{ selectedTask?.warehouse_name }}</q-item-label>
                    </q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section>
                      <q-item-label caption>描述</q-item-label>
                      <q-item-label>{{ selectedTask?.description }}</q-item-label>
                    </q-item-section>
                  </q-item>
                </q-list>
              </q-card>
            </div>

            <div class="col-12 col-md-6">
              <q-card flat bordered>
                <q-card-section>
                  <div class="text-h6">时间信息</div>
                </q-card-section>
                <q-separator />
                <q-list>
                  <q-item>
                    <q-item-section>
                      <q-item-label caption>创建时间</q-item-label>
                      <q-item-label>{{ selectedTask?.created_at }}</q-item-label>
                    </q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section>
                      <q-item-label caption>截止日期</q-item-label>
                      <q-item-label>{{ selectedTask?.due_date || '无' }}</q-item-label>
                    </q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section>
                      <q-item-label caption>开始时间</q-item-label>
                      <q-item-label>{{ selectedTask?.started_at || '未开始' }}</q-item-label>
                    </q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section>
                      <q-item-label caption>完成时间</q-item-label>
                      <q-item-label>{{ selectedTask?.completed_at || '未完成' }}</q-item-label>
                    </q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section>
                      <q-item-label caption>分配给</q-item-label>
                      <q-item-label>{{ selectedTask?.assigned_to_name || '未分配' }}</q-item-label>
                    </q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section>
                      <q-item-label caption>创建人</q-item-label>
                      <q-item-label>{{ selectedTask?.created_by_name }}</q-item-label>
                    </q-item-section>
                  </q-item>
                </q-list>
              </q-card>
            </div>
          </div>

          <div class="row q-col-gutter-md q-mt-md">
            <div class="col-12">
              <q-card flat bordered>
                <q-card-section>
                  <div class="text-h6">任务历史</div>
                </q-card-section>
                <q-separator />
                <q-list>
                  <q-item v-for="(history, index) in taskHistory" :key="index">
                    <q-item-section avatar>
                      <q-icon :name="getHistoryIcon(history.action)" :color="getHistoryColor(history.action)" />
                    </q-item-section>
                    <q-item-section>
                      <q-item-label>{{ history.action_label }}</q-item-label>
                      <q-item-label caption>{{ history.created_at }} - {{ history.user_name }}</q-item-label>
                      <q-item-label caption v-if="history.notes">{{ history.notes }}</q-item-label>
                    </q-item-section>
                  </q-item>
                </q-list>
              </q-card>
            </div>
          </div>

          <div class="row q-col-gutter-md q-mt-md" v-if="taskItems.length > 0">
            <div class="col-12">
              <q-card flat bordered>
                <q-card-section>
                  <div class="text-h6">任务项目</div>
                </q-card-section>
                <q-separator />
                <q-table
                  :rows="taskItems"
                  :columns="itemColumns"
                  row-key="id"
                  :pagination="{rowsPerPage: 0}"
                  flat
                  bordered
                >
                  <template v-slot:body-cell-status="props">
                    <q-td :props="props">
                      <q-badge :color="getItemStatusColor(props.value)">
                        {{ getItemStatusLabel(props.value) }}
                      </q-badge>
                    </q-td>
                  </template>
                </q-table>
              </q-card>
            </div>
          </div>
        </q-card-section>

        <q-separator />

        <q-card-actions align="right">
          <q-btn flat label="关闭" color="primary" v-close-popup />
          <q-btn color="primary" icon="edit" label="编辑" @click="openTaskDialog(selectedTask)" 
            v-if="canEditTask(selectedTask)" v-close-popup />
          <q-btn color="primary" icon="assignment_ind" label="分配" @click="openAssignDialog(selectedTask)" 
            v-if="canAssignTask(selectedTask)" v-close-popup />
          <q-btn color="positive" icon="play_arrow" label="开始" @click="startTask(selectedTask)" 
            v-if="canStartTask(selectedTask)" v-close-popup />
          <q-btn color="negative" icon="cancel" label="取消" @click="cancelTask(selectedTask)" 
            v-if="canCancelTask(selectedTask)" v-close-popup />
          <q-btn color="positive" icon="check" label="完成" @click="completeTask(selectedTask)" 
            v-if="canCompleteTask(selectedTask)" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script>
import { defineComponent, ref, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import { taskAPI, warehouseAPI, userAPI, productAPI } from 'src/services/api'
import { useAuthStore } from 'src/stores/auth'

export default defineComponent({
  name: 'TasksPage',

  setup() {
    const $q = useQuasar()
    const authStore = useAuthStore()
    const currentUser = computed(() => authStore.currentUser)
    const isAdmin = computed(() => authStore.isAdmin)

    // 任务列表相关
    const tasks = ref([])
    const loading = ref(false)
    const pagination = ref({
      sortBy: 'created_at',
      descending: true,
      page: 1,
      rowsPerPage: 10,
      rowsNumber: 0
    })
    const filter = ref({
      warehouse: null,
      status: null,
      type: null
    })

    // 选项数据
    const warehouses = ref([])
    const users = ref([])
    const products = ref([])
    const locations = ref([])
    const zones = ref([])
    const purchaseOrders = ref([])
    const salesOrders = ref([])

    // 任务编辑相关
    const taskDialog = ref(false)
    const editingTask = ref({
      task_type: '',
      warehouse_id: null,
      priority: 'medium',
      due_date: null,
      description: '',
      reference_id: null,
      expected_quantity: null,
      product_id: null,
      quantity: null,
      source_location_id: null,
      destination_location_id: null,
      zone_id: null,
      count_type: null
    })
    const saving = ref(false)

    // 任务分配相关
    const assignDialog = ref(false)
    const selectedTask = ref(null)
    const assignedUser = ref(null)
    const assignmentNote = ref('')
    const assigning = ref(false)

    // 任务详情相关
    const detailsDialog = ref(false)
    const taskHistory = ref([])
    const taskItems = ref([])

    const columns = [
      { name: 'id', align: 'left', label: '任务编号', field: 'id', sortable: true },
      { name: 'task_type_label', align: 'left', label: '任务类型', field: 'task_type_label', sortable: true },
      { name: 'description', align: 'left', label: '描述', field: 'description', sortable: false },
      { name: 'warehouse_name', align: 'left', label: '仓库', field: 'warehouse_name', sortable: true },
      { name: 'status', align: 'center', label: '状态', field: 'status', sortable: true },
      { name: 'priority', align: 'center', label: '优先级', field: 'priority', sortable: true },
      { name: 'assigned_to_name', align: 'left', label: '分配给', field: 'assigned_to_name', sortable: true },
      { name: 'created_at', align: 'left', label: '创建时间', field: 'created_at', sortable: true },
      { name: 'actions', align: 'center', label: '操作', field: 'actions', sortable: false }
    ]

    const itemColumns = [
      { name: 'product_name', align: 'left', label: '产品', field: 'product_name', sortable: true },
      { name: 'product_sku', align: 'left', label: 'SKU', field: 'product_sku', sortable: true },
      { name: 'quantity', align: 'right', label: '数量', field: 'quantity', sortable: true },
      { name: 'completed_quantity', align: 'right', label: '已完成数量', field: 'completed_quantity', sortable: true },
      { name: 'source_location', align: 'left', label: '源位置', field: 'source_location', sortable: true },
      { name: 'destination_location', align: 'left', label: '目标位置', field: 'destination_location', sortable: true },
      { name: 'status', align: 'center', label: '状态', field: 'status', sortable: true }
    ]

    const statusOptions = [
      { label: '待分配', value: 'pending' },
      { label: '已分配', value: 'assigned' },
      { label: '进行中', value: 'in_progress' },
      { label: '已完成', value: 'completed' },
      { label: '已取消', value: 'cancelled' }
    ]

    const taskTypeOptions = [
      { label: '收货', value: 'receiving' },
      { label: '上架', value: 'putaway' },
      { label: '拣货', value: 'picking' },
      { label: '补货', value: 'replenishment' },
      { label: '盘点', value: 'inventory_count' },
      { label: '移库', value: 'movement' },
      { label: '其他', value: 'other' }
    ]

    const priorityOptions = [
      { label: '低', value: 'low' },
      { label: '中', value: 'medium' },
      { label: '高', value: 'high' },
      { label: '紧急', value: 'urgent' }
    ]

    const warehouseOptions = computed(() => {
      return warehouses.value.map(warehouse => ({
        label: warehouse.name,
        value: warehouse.id
      }))
    })

    const userOptions = computed(() => {
      return users.value.map(user => ({
        label: user.username,
        value: user.id
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

    const zoneOptions = computed(() => {
      return zones.value.map(zone => ({
        label: zone.name,
        value: zone.id
      }))
    })

    const purchaseOrderOptions = computed(() => {
      return purchaseOrders.value.map(po => ({
        label: `${po.number} - ${po.supplier_name}`,
        value: po.id
      }))
    })

    const salesOrderOptions = computed(() => {
      return salesOrders.value.map(so => ({
        label: `${so.number} - ${so.customer_name}`,
        value: so.id
      }))
    })

    const fetchTasks = async () => {
      loading.value = true
      try {
        const params = {}
        if (filter.value.warehouse) params.warehouse_id = filter.value.warehouse
        if (filter.value.status) params.status = filter.value.status
        if (filter.value.type) params.task_type = filter.value.type
        
        const response = await taskAPI.getTasks(params)
        tasks.value = response.data
      } catch (error) {
        console.error('获取任务列表失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取任务列表失败',
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
      }
    }

    const fetchUsers = async () => {
      try {
        const response = await userAPI.getUsers()
        users.value = response.data
      } catch (error) {
        console.error('获取用户列表失败:', error)
      }
    }

    const fetchProducts = async () => {
      try {
        const response = await productAPI.getProducts()
        products.value = response.data
      } catch (error) {
        console.error('获取产品列表失败:', error)
      }
    }

    const fetchLocations = async (warehouseId) => {
      try {
        const response = await warehouseAPI.getLocations(warehouseId)
        locations.value = response.data
      } catch (error) {
        console.error('获取位置列表失败:', error)
      }
    }

    const fetchZones = async (warehouseId) => {
      try {
        const response = await warehouseAPI.getZones(warehouseId)
        zones.value = response.data
      } catch (error) {
        console.error('获取区域列表失败:', error)
      }
    }

    const fetchPurchaseOrders = async () => {
      try {
        // 假设API支持获取采购订单
        const response = await taskAPI.getPurchaseOrders()
        purchaseOrders.value = response.data
      } catch (error) {
        console.error('获取采购订单失败:', error)
      }
    }

    const fetchSalesOrders = async () => {
      try {
        // 假设API支持获取销售订单
        const response = await taskAPI.getSalesOrders()
        salesOrders.value = response.data
      } catch (error) {
        console.error('获取销售订单失败:', error)
      }
    }

    const resetFilters = () => {
      filter.value = {
        warehouse: null,
        status: null,
        type: null
      }
      fetchTasks()
    }

    const getStatusColor = (status) => {
      switch (status) {
        case 'pending': return 'grey'
        case 'assigned': return 'blue'
        case 'in_progress': return 'orange'
        case 'completed': return 'positive'
        case 'cancelled': return 'negative'
        default: return 'grey'
      }
    }

    const getStatusLabel = (status) => {
      switch (status) {
        case 'pending': return '待分配'
        case 'assigned': return '已分配'
        case 'in_progress': return '进行中'
        case 'completed': return '已完成'
        case 'cancelled': return '已取消'
        default: return '未知'
      }
    }

    const getPriorityColor = (priority) => {
      switch (priority) {
        case 'low': return 'green'
        case 'medium': return 'blue'
        case 'high': return 'orange'
        case 'urgent': return 'red'
        default: return 'blue'
      }
    }

    const getPriorityLabel = (priority) => {
      switch (priority) {
        case 'low': return '低'
        case 'medium': return '中'
        case 'high': return '高'
        case 'urgent': return '紧急'
        default: return '中'
      }
    }

    const getItemStatusColor = (status) => {
      switch (status) {
        case 'pending': return 'grey'
        case 'in_progress': return 'orange'
        case 'completed': return 'positive'
        case 'cancelled': return 'negative'
        default: return 'grey'
      }
    }

    const getItemStatusLabel = (status) => {
      switch (status) {
        case 'pending': return '待处理'
        case 'in_progress': return '进行中'
        case 'completed': return '已完成'
        case 'cancelled': return '已取消'
        default: return '未知'
      }
    }

    const getHistoryIcon = (action) => {
      switch (action) {
        case 'created': return 'add_circle'
        case 'assigned': return 'assignment_ind'
        case 'started': return 'play_circle'
        case 'completed': return 'check_circle'
        case 'cancelled': return 'cancel'
        case 'updated': return 'edit'
        default: return 'info'
      }
    }

    const getHistoryColor = (action) => {
      switch (action) {
        case 'created': return 'primary'
        case 'assigned': return 'blue'
        case 'started': return 'orange'
        case 'completed': return 'positive'
        case 'cancelled': return 'negative'
        case 'updated': return 'purple'
        default: return 'grey'
      }
    }

    const canEditTask = (task) => {
      if (!task) return false
      return isAdmin.value || 
        (task.status === 'pending' && task.created_by === currentUser.value?.id)
    }

    const canAssignTask = (task) => {
      if (!task) return false
      return isAdmin.value && task.status === 'pending'
    }

    const canStartTask = (task) => {
      if (!task) return false
      return task.status === 'assigned' && 
        (isAdmin.value || task.assigned_to === currentUser.value?.id)
    }

    const canCancelTask = (task) => {
      if (!task) return false
      return isAdmin.value && 
        ['pending', 'assigned', 'in_progress'].includes(task.status)
    }

    const canCompleteTask = (task) => {
      if (!task) return false
      return task.status === 'in_progress' && 
        (isAdmin.value || task.assigned_to === currentUser.value?.id)
    }

    const openTaskDialog = (task = null) => {
      if (task) {
        // 编辑现有任务
        editingTask.value = { ...task }
        
        // 如果是编辑模式，获取相关数据
        if (task.warehouse_id) {
          fetchLocations(task.warehouse_id)
          fetchZones(task.warehouse_id)
        }
      } else {
        // 创建新任务
        editingTask.value = {
          task_type: '',
          warehouse_id: null,
          priority: 'medium',
          due_date: null,
          description: '',
          reference_id: null,
          expected_quantity: null,
          product_id: null,
          quantity: null,
          source_location_id: null,
          destination_location_id: null,
          zone_id: null,
          count_type: null
        }
      }
      
      // 获取选项数据
      fetchPurchaseOrders()
      fetchSalesOrders()
      fetchProducts()
      
      taskDialog.value = true
    }

    const onTaskTypeChange = () => {
      // 根据任务类型重置特定字段
      if (editingTask.value.task_type === 'receiving') {
        editingTask.value.reference_id = null
        editingTask.value.expected_quantity = null
      } else if (editingTask.value.task_type === 'picking') {
        editingTask.value.reference_id = null
      } else if (editingTask.value.task_type === 'putaway') {
        editingTask.value.product_id = null
        editingTask.value.quantity = null
        editingTask.value.source_location_id = null
        editingTask.value.destination_location_id = null
      } else if (editingTask.value.task_type === 'inventory_count') {
        editingTask.value.zone_id = null
        editingTask.value.count_type = null
      }
    }

    const saveTask = async () => {
      saving.value = true
      try {
        const taskData = { ...editingTask.value }
        
        if (taskData.id) {
          // 更新现有任务
          await taskAPI.updateTask(taskData.id, taskData)
          $q.notify({
            color: 'positive',
            message: '任务更新成功',
            icon: 'check_circle'
          })
        } else {
          // 创建新任务
          await taskAPI.createTask(taskData)
          $q.notify({
            color: 'positive',
            message: '任务创建成功',
            icon: 'check_circle'
          })
        }
        
        taskDialog.value = false
        fetchTasks()
      } catch (error) {
        console.error('保存任务失败:', error)
        $q.notify({
          color: 'negative',
          message: '保存任务失败: ' + (error.response?.data?.error || error.message),
          icon: 'error'
        })
      } finally {
        saving.value = false
      }
    }

    const openAssignDialog = (task) => {
      selectedTask.value = task
      assignedUser.value = null
      assignmentNote.value = ''
      assignDialog.value = true
    }

    const assignTask = async () => {
      assigning.value = true
      try {
        await taskAPI.assignTask(selectedTask.value.id, assignedUser.value, assignmentNote.value)
        
        $q.notify({
          color: 'positive',
          message: '任务分配成功',
          icon: 'check_circle'
        })
        
        assignDialog.value = false
        fetchTasks()
      } catch (error) {
        console.error('分配任务失败:', error)
        $q.notify({
          color: 'negative',
          message: '分配任务失败: ' + (error.response?.data?.error || error.message),
          icon: 'error'
        })
      } finally {
        assigning.value = false
      }
    }

    const startTask = async (task) => {
      try {
        await taskAPI.startTask(task.id)
        
        $q.notify({
          color: 'positive',
          message: '任务已开始',
          icon: 'check_circle'
        })
        
        fetchTasks()
        
        // 如果详情对话框打开，刷新任务历史
        if (detailsDialog.value) {
          fetchTaskHistory(task.id)
        }
      } catch (error) {
        console.error('开始任务失败:', error)
        $q.notify({
          color: 'negative',
          message: '开始任务失败: ' + (error.response?.data?.error || error.message),
          icon: 'error'
        })
      }
    }

    const cancelTask = async (task) => {
      $q.dialog({
        title: '确认取消',
        message: '确定要取消此任务吗？',
        cancel: true,
        persistent: true
      }).onOk(async () => {
        try {
          await taskAPI.cancelTask(task.id)
          
          $q.notify({
            color: 'positive',
            message: '任务已取消',
            icon: 'check_circle'
          })
          
          fetchTasks()
          
          // 如果详情对话框打开，刷新任务历史
          if (detailsDialog.value) {
            fetchTaskHistory(task.id)
          }
        } catch (error) {
          console.error('取消任务失败:', error)
          $q.notify({
            color: 'negative',
            message: '取消任务失败: ' + (error.response?.data?.error || error.message),
            icon: 'error'
          })
        }
      })
    }

    const completeTask = async (task) => {
      try {
        await taskAPI.completeTask(task.id)
        
        $q.notify({
          color: 'positive',
          message: '任务已完成',
          icon: 'check_circle'
        })
        
        fetchTasks()
        
        // 如果详情对话框打开，刷新任务历史
        if (detailsDialog.value) {
          fetchTaskHistory(task.id)
        }
      } catch (error) {
        console.error('完成任务失败:', error)
        $q.notify({
          color: 'negative',
          message: '完成任务失败: ' + (error.response?.data?.error || error.message),
          icon: 'error'
        })
      }
    }

    const viewTaskDetails = async (task) => {
      selectedTask.value = task
      
      // 获取任务历史
      await fetchTaskHistory(task.id)
      
      // 获取任务项目
      await fetchTaskItems(task.id)
      
      detailsDialog.value = true
    }

    const fetchTaskHistory = async (taskId) => {
      try {
        const response = await taskAPI.getTaskHistory(taskId)
        taskHistory.value = response.data
      } catch (error) {
        console.error('获取任务历史失败:', error)
        taskHistory.value = []
      }
    }

    const fetchTaskItems = async (taskId) => {
      try {
        const response = await taskAPI.getTaskItems(taskId)
        taskItems.value = response.data
      } catch (error) {
        console.error('获取任务项目失败:', error)
        taskItems.value = []
      }
    }

    onMounted(() => {
      fetchTasks()
      fetchWarehouses()
      fetchUsers()
    })

    return {
      // 任务列表相关
      tasks,
      loading,
      pagination,
      filter,
      columns,
      fetchTasks,
      resetFilters,
      
      // 状态和优先级处理
      getStatusColor,
      getStatusLabel,
      getPriorityColor,
      getPriorityLabel,
      
      // 选项数据
      statusOptions,
      taskTypeOptions,
      priorityOptions,
      warehouseOptions,
      userOptions,
      productOptions,
      locationOptions,
      zoneOptions,
      purchaseOrderOptions,
      salesOrderOptions,
      
      // 任务编辑相关
      taskDialog,
      editingTask,
      saving,
      openTaskDialog,
      saveTask,
      onTaskTypeChange,
      
      // 任务分配相关
      assignDialog,
      selectedTask,
      assignedUser,
      assignmentNote,
      assigning,
      openAssignDialog,
      assignTask,
      
      // 任务操作相关
      canEditTask,
      canAssignTask,
      canStartTask,
      canCancelTask,
      canCompleteTask,
      startTask,
      cancelTask,
      completeTask,
      
      // 任务详情相关
      detailsDialog,
      taskHistory,
      taskItems,
      itemColumns,
      viewTaskDetails,
      getHistoryIcon,
      getHistoryColor,
      getItemStatusColor,
      getItemStatusLabel
    }
  }
})
</script>
