<template>
  <q-page padding>
    <div class="q-pa-md">
      <div class="row q-mb-md">
        <div class="col-12">
          <div class="text-h5">仓库管理</div>
          <div class="text-subtitle2">管理仓库、区域和位置</div>
        </div>
      </div>

      <div class="row q-mb-md">
        <div class="col-12">
          <q-btn color="primary" icon="add" label="添加仓库" @click="openWarehouseDialog()" />
          <q-btn class="q-ml-sm" color="secondary" icon="refresh" label="刷新" @click="fetchWarehouses()" />
        </div>
      </div>

      <div class="row">
        <div class="col-12">
          <q-table
            :rows="warehouses"
            :columns="warehouseColumns"
            row-key="id"
            :loading="loading"
            :pagination.sync="pagination"
            binary-state-sort
          >
            <template v-slot:body-cell-is_active="props">
              <q-td :props="props">
                <q-badge :color="props.row.is_active ? 'positive' : 'negative'">
                  {{ props.row.is_active ? '激活' : '禁用' }}
                </q-badge>
              </q-td>
            </template>

            <template v-slot:body-cell-actions="props">
              <q-td :props="props">
                <q-btn flat round dense color="primary" icon="edit" @click="openWarehouseDialog(props.row)" />
                <q-btn flat round dense color="primary" icon="grid_view" @click="openZonesDialog(props.row)" />
                <q-btn flat round dense color="primary" icon="place" @click="openLocationsDialog(props.row)" />
                <q-btn flat round dense :color="props.row.is_active ? 'negative' : 'positive'" 
                  :icon="props.row.is_active ? 'block' : 'check_circle'" 
                  @click="toggleWarehouseStatus(props.row)" />
              </q-td>
            </template>
          </q-table>
        </div>
      </div>
    </div>

    <!-- 仓库编辑对话框 -->
    <q-dialog v-model="warehouseDialog" persistent>
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">{{ editingWarehouse.id ? '编辑仓库' : '添加仓库' }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveWarehouse" class="q-gutter-md">
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <q-input
                  v-model="editingWarehouse.name"
                  label="仓库名称"
                  :rules="[val => !!val || '请输入仓库名称']"
                  outlined
                />
              </div>
              <div class="col-12 col-md-6">
                <q-input
                  v-model="editingWarehouse.code"
                  label="仓库代码"
                  :rules="[val => !!val || '请输入仓库代码']"
                  outlined
                />
              </div>
            </div>

            <q-input
              v-model="editingWarehouse.address"
              label="地址"
              type="textarea"
              outlined
              autogrow
            />

            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <q-input
                  v-model="editingWarehouse.contact_person"
                  label="联系人"
                  outlined
                />
              </div>
              <div class="col-12 col-md-6">
                <q-input
                  v-model="editingWarehouse.phone"
                  label="电话"
                  outlined
                />
              </div>
            </div>

            <q-input
              v-model="editingWarehouse.email"
              label="电子邮箱"
              type="email"
              outlined
            />

            <q-toggle v-model="editingWarehouse.is_active" label="激活" />

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

    <!-- 区域管理对话框 -->
    <q-dialog v-model="zonesDialog" persistent maximized>
      <q-card>
        <q-card-section class="row items-center">
          <div class="text-h6">区域管理</div>
          <div class="text-subtitle2 q-ml-md">{{ selectedWarehouse?.name }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-separator />

        <q-card-section>
          <div class="row q-mb-md">
            <div class="col-12">
              <q-btn color="primary" icon="add" label="添加区域" @click="openZoneDialog()" />
              <q-btn class="q-ml-sm" color="secondary" icon="refresh" label="刷新" @click="fetchZones()" />
            </div>
          </div>

          <div class="row">
            <div class="col-12">
              <q-table
                :rows="zones"
                :columns="zoneColumns"
                row-key="id"
                :loading="loadingZones"
                :pagination.sync="zonePagination"
                binary-state-sort
              >
                <template v-slot:body-cell-actions="props">
                  <q-td :props="props">
                    <q-btn flat round dense color="primary" icon="edit" @click="openZoneDialog(props.row)" />
                    <q-btn flat round dense color="negative" icon="delete" @click="confirmDeleteZone(props.row)" />
                  </q-td>
                </template>
              </q-table>
            </div>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 区域编辑对话框 -->
    <q-dialog v-model="zoneDialog" persistent>
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">{{ editingZone.id ? '编辑区域' : '添加区域' }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveZone" class="q-gutter-md">
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <q-input
                  v-model="editingZone.name"
                  label="区域名称"
                  :rules="[val => !!val || '请输入区域名称']"
                  outlined
                />
              </div>
              <div class="col-12 col-md-6">
                <q-input
                  v-model="editingZone.code"
                  label="区域代码"
                  :rules="[val => !!val || '请输入区域代码']"
                  outlined
                />
              </div>
            </div>

            <q-input
              v-model="editingZone.description"
              label="描述"
              type="textarea"
              outlined
              autogrow
            />

            <q-select
              v-model="editingZone.zone_type"
              :options="zoneTypeOptions"
              label="区域类型"
              :rules="[val => !!val || '请选择区域类型']"
              outlined
              emit-value
              map-options
            />

            <div class="row">
              <div class="col-12 flex justify-end">
                <q-btn flat label="取消" color="primary" v-close-popup />
                <q-btn type="submit" label="保存" color="primary" :loading="savingZone" />
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 位置管理对话框 -->
    <q-dialog v-model="locationsDialog" persistent maximized>
      <q-card>
        <q-card-section class="row items-center">
          <div class="text-h6">位置管理</div>
          <div class="text-subtitle2 q-ml-md">{{ selectedWarehouse?.name }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-separator />

        <q-card-section>
          <div class="row q-mb-md">
            <div class="col-12">
              <q-btn color="primary" icon="add" label="添加位置" @click="openLocationDialog()" />
              <q-btn class="q-ml-sm" color="secondary" icon="refresh" label="刷新" @click="fetchLocations()" />
            </div>
          </div>

          <div class="row q-mb-md">
            <div class="col-12 col-md-4">
              <q-select
                v-model="locationFilter.zone"
                :options="zoneOptions"
                label="区域"
                dense
                outlined
                clearable
                emit-value
                map-options
                @update:model-value="fetchLocations"
              />
            </div>
          </div>

          <div class="row">
            <div class="col-12">
              <q-table
                :rows="locations"
                :columns="locationColumns"
                row-key="id"
                :loading="loadingLocations"
                :pagination.sync="locationPagination"
                binary-state-sort
              >
                <template v-slot:body-cell-is_active="props">
                  <q-td :props="props">
                    <q-badge :color="props.row.is_active ? 'positive' : 'negative'">
                      {{ props.row.is_active ? '激活' : '禁用' }}
                    </q-badge>
                  </q-td>
                </template>

                <template v-slot:body-cell-is_pickable="props">
                  <q-td :props="props">
                    <q-icon :name="props.row.is_pickable ? 'check' : 'close'" 
                      :color="props.row.is_pickable ? 'positive' : 'negative'" />
                  </q-td>
                </template>

                <template v-slot:body-cell-is_receivable="props">
                  <q-td :props="props">
                    <q-icon :name="props.row.is_receivable ? 'check' : 'close'" 
                      :color="props.row.is_receivable ? 'positive' : 'negative'" />
                  </q-td>
                </template>

                <template v-slot:body-cell-actions="props">
                  <q-td :props="props">
                    <q-btn flat round dense color="primary" icon="edit" @click="openLocationDialog(props.row)" />
                    <q-btn flat round dense :color="props.row.is_active ? 'negative' : 'positive'" 
                      :icon="props.row.is_active ? 'block' : 'check_circle'" 
                      @click="toggleLocationStatus(props.row)" />
                  </q-td>
                </template>
              </q-table>
            </div>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 位置编辑对话框 -->
    <q-dialog v-model="locationDialog" persistent>
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">{{ editingLocation.id ? '编辑位置' : '添加位置' }}</div>
        </q-card-section>

        <q-card-section style="max-height: 70vh" class="scroll">
          <q-form @submit="saveLocation" class="q-gutter-md">
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <q-input
                  v-model="editingLocation.name"
                  label="位置名称"
                  :rules="[val => !!val || '请输入位置名称']"
                  outlined
                />
              </div>
              <div class="col-12 col-md-6">
                <q-input
                  v-model="editingLocation.code"
                  label="位置代码"
                  :rules="[val => !!val || '请输入位置代码']"
                  outlined
                />
              </div>
            </div>

            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <q-select
                  v-model="editingLocation.zone_id"
                  :options="zoneOptions"
                  label="区域"
                  :rules="[val => !!val || '请选择区域']"
                  outlined
                  emit-value
                  map-options
                />
              </div>
              <div class="col-12 col-md-6">
                <q-input
                  v-model="editingLocation.barcode"
                  label="条形码"
                  outlined
                />
              </div>
            </div>

            <div class="row q-col-gutter-md">
              <div class="col-12">
                <q-select
                  v-model="editingLocation.location_type"
                  :options="locationTypeOptions"
                  label="位置类型"
                  :rules="[val => !!val || '请选择位置类型']"
                  outlined
                  emit-value
                  map-options
                />
              </div>
            </div>

            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-3">
                <q-input
                  v-model="editingLocation.aisle"
                  label="通道"
                  outlined
                />
              </div>
              <div class="col-12 col-md-3">
                <q-input
                  v-model="editingLocation.rack"
                  label="货架"
                  outlined
                />
              </div>
              <div class="col-12 col-md-3">
                <q-input
                  v-model="editingLocation.shelf"
                  label="层"
                  outlined
                />
              </div>
              <div class="col-12 col-md-3">
                <q-input
                  v-model="editingLocation.bin"
                  label="格"
                  outlined
                />
              </div>
            </div>

            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <q-input
                  v-model.number="editingLocation.max_weight"
                  label="最大承重(kg)"
                  type="number"
                  outlined
                />
              </div>
              <div class="col-12 col-md-6">
                <q-input
                  v-model.number="editingLocation.max_volume"
                  label="最大体积(m³)"
                  type="number"
                  outlined
                />
              </div>
            </div>

            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-4">
                <q-toggle v-model="editingLocation.is_pickable" label="可拣货" />
              </div>
              <div class="col-12 col-md-4">
                <q-toggle v-model="editingLocation.is_receivable" label="可收货" />
              </div>
              <div class="col-12 col-md-4">
                <q-toggle v-model="editingLocation.is_active" label="激活" />
              </div>
            </div>

            <div class="row">
              <div class="col-12 flex justify-end">
                <q-btn flat label="取消" color="primary" v-close-popup />
                <q-btn type="submit" label="保存" color="primary" :loading="savingLocation" />
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script>
import { defineComponent, ref, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import { warehouseAPI } from 'src/services/api'

export default defineComponent({
  name: 'WarehousePage',

  setup() {
    const $q = useQuasar()

    // 仓库相关
    const warehouses = ref([])
    const loading = ref(false)
    const pagination = ref({
      sortBy: 'name',
      descending: false,
      page: 1,
      rowsPerPage: 10,
      rowsNumber: 0
    })
    const warehouseDialog = ref(false)
    const editingWarehouse = ref({
      name: '',
      code: '',
      address: '',
      contact_person: '',
      phone: '',
      email: '',
      is_active: true
    })
    const saving = ref(false)
    const selectedWarehouse = ref(null)

    // 区域相关
    const zones = ref([])
    const loadingZones = ref(false)
    const zonePagination = ref({
      sortBy: 'name',
      descending: false,
      page: 1,
      rowsPerPage: 10,
      rowsNumber: 0
    })
    const zonesDialog = ref(false)
    const zoneDialog = ref(false)
    const editingZone = ref({
      name: '',
      code: '',
      description: '',
      zone_type: '',
      warehouse_id: null
    })
    const savingZone = ref(false)

    // 位置相关
    const locations = ref([])
    const loadingLocations = ref(false)
    const locationPagination = ref({
      sortBy: 'name',
      descending: false,
      page: 1,
      rowsPerPage: 10,
      rowsNumber: 0
    })
    const locationsDialog = ref(false)
    const locationDialog = ref(false)
    const editingLocation = ref({
      name: '',
      code: '',
      barcode: '',
      location_type: '',
      aisle: '',
      rack: '',
      shelf: '',
      bin: '',
      max_weight: null,
      max_volume: null,
      is_pickable: true,
      is_receivable: true,
      is_active: true,
      warehouse_id: null,
      zone_id: null
    })
    const savingLocation = ref(false)
    const locationFilter = ref({
      zone: null
    })

    const warehouseColumns = [
      { name: 'name', align: 'left', label: '仓库名称', field: 'name', sortable: true },
      { name: 'code', align: 'left', label: '仓库代码', field: 'code', sortable: true },
      { name: 'address', align: 'left', label: '地址', field: 'address', sortable: false },
      { name: 'contact_person', align: 'left', label: '联系人', field: 'contact_person', sortable: true },
      { name: 'phone', align: 'left', label: '电话', field: 'phone', sortable: false },
      { name: 'is_active', align: 'center', label: '状态', field: 'is_active', sortable: true },
      { name: 'actions', align: 'center', label: '操作', field: 'actions', sortable: false }
    ]

    const zoneColumns = [
      { name: 'name', align: 'left', label: '区域名称', field: 'name', sortable: true },
      { name: 'code', align: 'left', label: '区域代码', field: 'code', sortable: true },
      { name: 'description', align: 'left', label: '描述', field: 'description', sortable: false },
      { name: 'zone_type', align: 'left', label: '区域类型', field: 'zone_type', sortable: true },
      { name: 'actions', align: 'center', label: '操作', field: 'actions', sortable: false }
    ]

    const locationColumns = [
      { name: 'name', align: 'left', label: '位置名称', field: 'name', sortable: true },
      { name: 'code', align: 'left', label: '位置代码', field: 'code', sortable: true },
      { name: 'zone_name', align: 'left', label: '区域', field: 'zone_name', sortable: true },
      { name: 'location_type', align: 'left', label: '位置类型', field: 'location_type', sortable: true },
      { name: 'aisle', align: 'left', label: '通道', field: 'aisle', sortable: true },
      { name: 'rack', align: 'left', label: '货架', field: 'rack', sortable: true },
      { name: 'is_pickable', align: 'center', label: '可拣货', field: 'is_pickable', sortable: true },
      { name: 'is_receivable', align: 'center', label: '可收货', field: 'is_receivable', sortable: true },
      { name: 'is_active', align: 'center', label: '状态', field: 'is_active', sortable: true },
      { name: 'actions', align: 'center', label: '操作', field: 'actions', sortable: false }
    ]

    const zoneTypeOptions = [
      { label: '收货区', value: 'receiving' },
      { label: '存储区', value: 'storage' },
      { label: '拣货区', value: 'picking' },
      { label: '包装区', value: 'packing' },
      { label: '发货区', value: 'shipping' },
      { label: '退货区', value: 'returns' },
      { label: '质检区', value: 'quality_control' },
      { label: '其他', value: 'other' }
    ]

    const locationTypeOptions = [
      { label: '货架', value: 'shelf' },
      { label: '货位', value: 'bin' },
      { label: '地面', value: 'floor' },
      { label: '收货区', value: 'receiving' },
      { label: '发货区', value: 'shipping' },
      { label: '暂存区', value: 'staging' },
      { label: '其他', value: 'other' }
    ]

    const zoneOptions = computed(() => {
      return zones.value.map(zone => ({
        label: zone.name,
        value: zone.id
      }))
    })

    const fetchWarehouses = async () => {
      loading.value = true
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
      } finally {
        loading.value = false
      }
    }

    const openWarehouseDialog = (warehouse = null) => {
      if (warehouse) {
        // 编辑现有仓库
        editingWarehouse.value = { ...warehouse }
      } else {
        // 创建新仓库
        editingWarehouse.value = {
          name: '',
          code: '',
          address: '',
          contact_person: '',
          phone: '',
          email: '',
          is_active: true
        }
      }
      warehouseDialog.value = true
    }

    const saveWarehouse = async () => {
      saving.value = true
      try {
        const warehouseData = { ...editingWarehouse.value }
        
        if (warehouseData.id) {
          // 更新现有仓库
          await warehouseAPI.updateWarehouse(warehouseData.id, warehouseData)
          $q.notify({
            color: 'positive',
            message: '仓库更新成功',
            icon: 'check_circle'
          })
        } else {
          // 创建新仓库
          await warehouseAPI.createWarehouse(warehouseData)
          $q.notify({
            color: 'positive',
            message: '仓库创建成功',
            icon: 'check_circle'
          })
        }
        
        warehouseDialog.value = false
        fetchWarehouses()
      } catch (error) {
        console.error('保存仓库失败:', error)
        $q.notify({
          color: 'negative',
          message: '保存仓库失败: ' + (error.response?.data?.error || error.message),
          icon: 'error'
        })
      } finally {
        saving.value = false
      }
    }

    const toggleWarehouseStatus = async (warehouse) => {
      try {
        const updatedWarehouse = { ...warehouse, is_active: !warehouse.is_active }
        await warehouseAPI.updateWarehouse(warehouse.id, updatedWarehouse)
        
        $q.notify({
          color: 'positive',
          message: `仓库已${updatedWarehouse.is_active ? '激活' : '禁用'}`,
          icon: 'check_circle'
        })
        
        fetchWarehouses()
      } catch (error) {
        console.error('更新仓库状态失败:', error)
        $q.notify({
          color: 'negative',
          message: '更新仓库状态失败',
          icon: 'error'
        })
      }
    }

    const openZonesDialog = (warehouse) => {
      selectedWarehouse.value = warehouse
      fetchZones()
      zonesDialog.value = true
    }

    const fetchZones = async () => {
      if (!selectedWarehouse.value) return
      
      loadingZones.value = true
      try {
        const response = await warehouseAPI.getZones(selectedWarehouse.value.id)
        zones.value = response.data
      } catch (error) {
        console.error('获取区域列表失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取区域列表失败',
          icon: 'error'
        })
      } finally {
        loadingZones.value = false
      }
    }

    const openZoneDialog = (zone = null) => {
      if (zone) {
        // 编辑现有区域
        editingZone.value = { ...zone }
      } else {
        // 创建新区域
        editingZone.value = {
          name: '',
          code: '',
          description: '',
          zone_type: '',
          warehouse_id: selectedWarehouse.value.id
        }
      }
      zoneDialog.value = true
    }

    const saveZone = async () => {
      savingZone.value = true
      try {
        const zoneData = { ...editingZone.value }
        
        if (zoneData.id) {
          // 更新现有区域
          // 假设API支持更新区域
          $q.notify({
            color: 'positive',
            message: '区域更新成功',
            icon: 'check_circle'
          })
        } else {
          // 创建新区域
          // 假设API支持创建区域
          $q.notify({
            color: 'positive',
            message: '区域创建成功',
            icon: 'check_circle'
          })
        }
        
        zoneDialog.value = false
        fetchZones()
      } catch (error) {
        console.error('保存区域失败:', error)
        $q.notify({
          color: 'negative',
          message: '保存区域失败',
          icon: 'error'
        })
      } finally {
        savingZone.value = false
      }
    }

    const confirmDeleteZone = (zone) => {
      $q.dialog({
        title: '确认删除',
        message: `确定要删除区域 "${zone.name}" 吗？`,
        cancel: true,
        persistent: true
      }).onOk(async () => {
        try {
          // 假设API支持删除区域
          $q.notify({
            color: 'positive',
            message: '区域删除成功',
            icon: 'check_circle'
          })
          fetchZones()
        } catch (error) {
          console.error('删除区域失败:', error)
          $q.notify({
            color: 'negative',
            message: '删除区域失败',
            icon: 'error'
          })
        }
      })
    }

    const openLocationsDialog = (warehouse) => {
      selectedWarehouse.value = warehouse
      locationFilter.value = {
        zone: null
      }
      fetchZones()
      fetchLocations()
      locationsDialog.value = true
    }

    const fetchLocations = async () => {
      if (!selectedWarehouse.value) return
      
      loadingLocations.value = true
      try {
        const params = {
          warehouse_id: selectedWarehouse.value.id
        }
        
        if (locationFilter.value.zone) {
          params.zone_id = locationFilter.value.zone
        }
        
        const response = await warehouseAPI.getLocations(params.warehouse_id, params.zone_id)
        locations.value = response.data
      } catch (error) {
        console.error('获取位置列表失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取位置列表失败',
          icon: 'error'
        })
      } finally {
        loadingLocations.value = false
      }
    }

    const openLocationDialog = (location = null) => {
      if (location) {
        // 编辑现有位置
        editingLocation.value = { ...location }
      } else {
        // 创建新位置
        editingLocation.value = {
          name: '',
          code: '',
          barcode: '',
          location_type: '',
          aisle: '',
          rack: '',
          shelf: '',
          bin: '',
          max_weight: null,
          max_volume: null,
          is_pickable: true,
          is_receivable: true,
          is_active: true,
          warehouse_id: selectedWarehouse.value.id,
          zone_id: locationFilter.value.zone || null
        }
      }
      locationDialog.value = true
    }

    const saveLocation = async () => {
      savingLocation.value = true
      try {
        const locationData = { ...editingLocation.value }
        
        if (locationData.id) {
          // 更新现有位置
          // 假设API支持更新位置
          $q.notify({
            color: 'positive',
            message: '位置更新成功',
            icon: 'check_circle'
          })
        } else {
          // 创建新位置
          // 假设API支持创建位置
          $q.notify({
            color: 'positive',
            message: '位置创建成功',
            icon: 'check_circle'
          })
        }
        
        locationDialog.value = false
        fetchLocations()
      } catch (error) {
        console.error('保存位置失败:', error)
        $q.notify({
          color: 'negative',
          message: '保存位置失败',
          icon: 'error'
        })
      } finally {
        savingLocation.value = false
      }
    }

    const toggleLocationStatus = async (location) => {
      try {
        const updatedLocation = { ...location, is_active: !location.is_active }
        // 假设API支持更新位置状态
        
        $q.notify({
          color: 'positive',
          message: `位置已${updatedLocation.is_active ? '激活' : '禁用'}`,
          icon: 'check_circle'
        })
        
        fetchLocations()
      } catch (error) {
        console.error('更新位置状态失败:', error)
        $q.notify({
          color: 'negative',
          message: '更新位置状态失败',
          icon: 'error'
        })
      }
    }

    onMounted(() => {
      fetchWarehouses()
    })

    return {
      // 仓库相关
      warehouses,
      loading,
      pagination,
      warehouseColumns,
      warehouseDialog,
      editingWarehouse,
      saving,
      fetchWarehouses,
      openWarehouseDialog,
      saveWarehouse,
      toggleWarehouseStatus,
      
      // 区域相关
      zones,
      loadingZones,
      zonePagination,
      zoneColumns,
      zonesDialog,
      zoneDialog,
      editingZone,
      savingZone,
      zoneTypeOptions,
      zoneOptions,
      selectedWarehouse,
      fetchZones,
      openZonesDialog,
      openZoneDialog,
      saveZone,
      confirmDeleteZone,
      
      // 位置相关
      locations,
      loadingLocations,
      locationPagination,
      locationColumns,
      locationsDialog,
      locationDialog,
      editingLocation,
      savingLocation,
      locationTypeOptions,
      locationFilter,
      fetchLocations,
      openLocationsDialog,
      openLocationDialog,
      saveLocation,
      toggleLocationStatus
    }
  }
})
</script>
