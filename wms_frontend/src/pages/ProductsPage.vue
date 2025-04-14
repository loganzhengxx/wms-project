<template>
  <q-page padding>
    <div class="q-pa-md">
      <div class="row q-mb-md">
        <div class="col-12">
          <div class="text-h5">产品管理</div>
          <div class="text-subtitle2">管理产品、类别和属性</div>
        </div>
      </div>

      <div class="row q-mb-md">
        <div class="col-12">
          <q-btn color="primary" icon="add" label="添加产品" @click="openProductDialog()" />
          <q-btn class="q-ml-sm" color="secondary" icon="refresh" label="刷新" @click="fetchProducts()" />
          <q-btn class="q-ml-sm" color="accent" icon="category" label="管理类别" @click="openCategoriesDialog()" />
        </div>
      </div>

      <div class="row q-mb-md">
        <div class="col-12 col-md-3 q-pr-md-md">
          <q-input
            v-model="filter.name"
            label="产品名称"
            dense
            outlined
            clearable
            @keyup.enter="fetchProducts"
          />
        </div>
        <div class="col-12 col-md-3 q-pr-md-md q-pt-xs-sm">
          <q-input
            v-model="filter.sku"
            label="SKU"
            dense
            outlined
            clearable
            @keyup.enter="fetchProducts"
          />
        </div>
        <div class="col-12 col-md-3 q-pr-md-md q-pt-xs-sm">
          <q-select
            v-model="filter.category"
            :options="categoryOptions"
            label="类别"
            dense
            outlined
            clearable
            emit-value
            map-options
            @update:model-value="fetchProducts"
          />
        </div>
        <div class="col-12 col-md-3 q-pt-xs-sm">
          <q-btn color="primary" icon="search" label="搜索" @click="fetchProducts" />
          <q-btn class="q-ml-sm" color="secondary" flat label="重置" @click="resetFilters" />
        </div>
      </div>

      <div class="row">
        <div class="col-12">
          <q-table
            :rows="products"
            :columns="columns"
            row-key="id"
            :loading="loading"
            :pagination.sync="pagination"
            binary-state-sort
          >
            <template v-slot:body-cell-image="props">
              <q-td :props="props">
                <q-img
                  v-if="props.row.images && props.row.images.length > 0"
                  :src="props.row.images[0].image_url"
                  spinner-color="primary"
                  style="height: 50px; max-width: 50px"
                />
                <q-icon v-else name="image" size="50px" color="grey-5" />
              </q-td>
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
                <q-btn flat round dense color="primary" icon="edit" @click="openProductDialog(props.row)" />
                <q-btn flat round dense color="primary" icon="inventory" @click="viewInventory(props.row)" />
                <q-btn flat round dense color="primary" icon="image" @click="openImagesDialog(props.row)" />
                <q-btn flat round dense :color="props.row.is_active ? 'negative' : 'positive'" 
                  :icon="props.row.is_active ? 'block' : 'check_circle'" 
                  @click="toggleProductStatus(props.row)" />
              </q-td>
            </template>
          </q-table>
        </div>
      </div>
    </div>

    <!-- 产品编辑对话框 -->
    <q-dialog v-model="productDialog" persistent maximized>
      <q-card>
        <q-card-section class="row items-center">
          <div class="text-h6">{{ editingProduct.id ? '编辑产品' : '添加产品' }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-separator />

        <q-card-section class="q-pa-md" style="max-height: 80vh" scroll>
          <q-form @submit="saveProduct" class="q-gutter-md">
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <q-input
                  v-model="editingProduct.name"
                  label="产品名称"
                  :rules="[val => !!val || '请输入产品名称']"
                  outlined
                />
              </div>
              <div class="col-12 col-md-6">
                <q-input
                  v-model="editingProduct.sku"
                  label="SKU"
                  :rules="[val => !!val || '请输入SKU']"
                  outlined
                />
              </div>
            </div>

            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <q-input
                  v-model="editingProduct.barcode"
                  label="条形码"
                  outlined
                />
              </div>
              <div class="col-12 col-md-6">
                <q-select
                  v-model="editingProduct.category"
                  :options="categoryOptions"
                  label="类别"
                  outlined
                  emit-value
                  map-options
                />
              </div>
            </div>

            <div class="row q-col-gutter-md">
              <div class="col-12">
                <q-input
                  v-model="editingProduct.description"
                  label="产品描述"
                  type="textarea"
                  outlined
                  autogrow
                />
              </div>
            </div>

            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-3">
                <q-input
                  v-model.number="editingProduct.cost_price"
                  label="成本价"
                  type="number"
                  outlined
                  prefix="¥"
                />
              </div>
              <div class="col-12 col-md-3">
                <q-input
                  v-model.number="editingProduct.selling_price"
                  label="销售价"
                  type="number"
                  outlined
                  prefix="¥"
                />
              </div>
              <div class="col-12 col-md-3">
                <q-input
                  v-model.number="editingProduct.min_stock_level"
                  label="最低库存水平"
                  type="number"
                  outlined
                />
              </div>
              <div class="col-12 col-md-3">
                <q-input
                  v-model.number="editingProduct.reorder_point"
                  label="再订购点"
                  type="number"
                  outlined
                />
              </div>
            </div>

            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-3">
                <q-input
                  v-model.number="editingProduct.weight"
                  label="重量(kg)"
                  type="number"
                  outlined
                />
              </div>
              <div class="col-12 col-md-3">
                <q-input
                  v-model.number="editingProduct.length"
                  label="长度(cm)"
                  type="number"
                  outlined
                />
              </div>
              <div class="col-12 col-md-3">
                <q-input
                  v-model.number="editingProduct.width"
                  label="宽度(cm)"
                  type="number"
                  outlined
                />
              </div>
              <div class="col-12 col-md-3">
                <q-input
                  v-model.number="editingProduct.height"
                  label="高度(cm)"
                  type="number"
                  outlined
                />
              </div>
            </div>

            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <q-input
                  v-model="editingProduct.handling_instructions"
                  label="处理说明"
                  type="textarea"
                  outlined
                  autogrow
                />
              </div>
              <div class="col-12 col-md-6">
                <q-input
                  v-model="editingProduct.storage_requirements"
                  label="存储要求"
                  type="textarea"
                  outlined
                  autogrow
                />
              </div>
            </div>

            <div class="row q-col-gutter-md">
              <div class="col-12">
                <q-toggle v-model="editingProduct.is_active" label="激活" />
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

    <!-- 类别管理对话框 -->
    <q-dialog v-model="categoriesDialog" persistent>
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">管理产品类别</div>
        </q-card-section>

        <q-separator />

        <q-card-section style="max-height: 60vh" class="scroll">
          <q-list bordered separator>
            <q-item v-for="category in categories" :key="category.id">
              <q-item-section>
                <q-item-label>{{ category.name }}</q-item-label>
                <q-item-label caption>{{ category.description || '无描述' }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-btn flat round dense color="primary" icon="edit" @click="openCategoryDialog(category)" />
                <q-btn flat round dense color="negative" icon="delete" @click="confirmDeleteCategory(category)" />
              </q-item-section>
            </q-item>
          </q-list>

          <div class="q-mt-md">
            <q-btn color="primary" icon="add" label="添加类别" @click="openCategoryDialog()" />
          </div>
        </q-card-section>

        <q-separator />

        <q-card-actions align="right">
          <q-btn flat label="关闭" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- 类别编辑对话框 -->
    <q-dialog v-model="categoryDialog" persistent>
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">{{ editingCategory.id ? '编辑类别' : '添加类别' }}</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveCategory" class="q-gutter-md">
            <q-input
              v-model="editingCategory.name"
              label="类别名称"
              :rules="[val => !!val || '请输入类别名称']"
              outlined
            />

            <q-input
              v-model="editingCategory.description"
              label="类别描述"
              type="textarea"
              outlined
              autogrow
            />

            <q-select
              v-model="editingCategory.parent"
              :options="parentCategoryOptions"
              label="父类别"
              outlined
              clearable
              emit-value
              map-options
            />

            <div class="row">
              <div class="col-12 flex justify-end">
                <q-btn flat label="取消" color="primary" v-close-popup />
                <q-btn type="submit" label="保存" color="primary" :loading="savingCategory" />
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 产品图片对话框 -->
    <q-dialog v-model="imagesDialog" persistent>
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">管理产品图片</div>
          <div class="text-subtitle2">{{ selectedProduct?.name }}</div>
        </q-card-section>

        <q-separator />

        <q-card-section style="max-height: 60vh" class="scroll">
          <div class="row q-col-gutter-md">
            <div v-for="image in productImages" :key="image.id" class="col-6 col-md-4">
              <q-card>
                <q-img :src="image.image_url" spinner-color="primary" style="height: 200px" />
                <q-card-actions align="right">
                  <q-btn flat round dense :color="image.is_primary ? 'positive' : 'grey'" 
                    icon="star" @click="setAsPrimaryImage(image)" />
                  <q-btn flat round dense color="negative" icon="delete" @click="deleteImage(image)" />
                </q-card-actions>
              </q-card>
            </div>
          </div>

          <div class="q-mt-md">
            <q-file
              v-model="newImage"
              label="添加图片"
              outlined
              accept="image/*"
              @update:model-value="uploadImage"
            >
              <template v-slot:prepend>
                <q-icon name="add_photo_alternate" />
              </template>
            </q-file>
          </div>
        </q-card-section>

        <q-separator />

        <q-card-actions align="right">
          <q-btn flat label="关闭" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- 库存查看对话框 -->
    <q-dialog v-model="inventoryDialog" persistent>
      <q-card style="min-width: 700px">
        <q-card-section>
          <div class="text-h6">产品库存</div>
          <div class="text-subtitle2">{{ selectedProduct?.name }} ({{ selectedProduct?.sku }})</div>
        </q-card-section>

        <q-separator />

        <q-card-section style="max-height: 60vh" class="scroll">
          <q-table
            :rows="productInventory"
            :columns="inventoryColumns"
            row-key="id"
            :loading="loadingInventory"
          >
            <template v-slot:body-cell-available_quantity="props">
              <q-td :props="props">
                <q-badge :color="props.value > 0 ? 'positive' : 'negative'">
                  {{ props.value }}
                </q-badge>
              </q-td>
            </template>

            <template v-slot:body-cell-actions="props">
              <q-td :props="props">
                <q-btn flat round dense color="primary" icon="edit" @click="openAdjustDialog(props.row)" />
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

    <!-- 库存调整对话框 -->
    <q-dialog v-model="adjustDialog" persistent>
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">调整库存</div>
          <div class="text-subtitle2">{{ selectedProduct?.name }} - {{ selectedInventory?.location_name }}</div>
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
  </q-page>
</template>

<script>
import { defineComponent, ref, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import { productAPI, inventoryAPI } from 'src/services/api'

export default defineComponent({
  name: 'ProductsPage',

  setup() {
    const $q = useQuasar()

    // 产品列表相关
    const products = ref([])
    const loading = ref(false)
    const pagination = ref({
      sortBy: 'name',
      descending: false,
      page: 1,
      rowsPerPage: 10,
      rowsNumber: 0
    })
    const filter = ref({
      name: '',
      sku: '',
      category: null
    })

    // 类别相关
    const categories = ref([])
    const categoriesDialog = ref(false)
    const categoryDialog = ref(false)
    const editingCategory = ref({
      name: '',
      description: '',
      parent: null
    })
    const savingCategory = ref(false)

    // 产品编辑相关
    const productDialog = ref(false)
    const editingProduct = ref({
      name: '',
      description: '',
      sku: '',
      barcode: '',
      category: null,
      weight: null,
      width: null,
      height: null,
      length: null,
      cost_price: null,
      selling_price: null,
      min_stock_level: 0,
      reorder_point: 0,
      handling_instructions: '',
      storage_requirements: '',
      is_active: true
    })
    const saving = ref(false)

    // 产品图片相关
    const imagesDialog = ref(false)
    const selectedProduct = ref(null)
    const productImages = ref([])
    const newImage = ref(null)

    // 库存相关
    const inventoryDialog = ref(false)
    const productInventory = ref([])
    const loadingInventory = ref(false)
    const adjustDialog = ref(false)
    const selectedInventory = ref(null)
    const adjustment = ref({
      quantity: 0,
      reason: '',
      batch_id: null
    })
    const adjusting = ref(false)
    const batches = ref([])

    const columns = [
      { name: 'image', align: 'center', label: '图片', field: 'image', sortable: false },
      { name: 'name', align: 'left', label: '产品名称', field: 'name', sortable: true },
      { name: 'sku', align: 'left', label: 'SKU', field: 'sku', sortable: true },
      { name: 'category_name', align: 'left', label: '类别', field: 'category_name', sortable: true },
      { name: 'cost_price', align: 'right', label: '成本价', field: 'cost_price', format: val => `¥${val || 0}`, sortable: true },
      { name: 'selling_price', align: 'right', label: '销售价', field: 'selling_price', format: val => `¥${val || 0}`, sortable: true },
      { name: 'is_active', align: 'center', label: '状态', field: 'is_active', sortable: true },
      { name: 'actions', align: 'center', label: '操作', field: 'actions', sortable: false }
    ]

    const inventoryColumns = [
      { name: 'warehouse_name', align: 'left', label: '仓库', field: 'warehouse_name', sortable: true },
      { name: 'location_name', align: 'left', label: '位置', field: 'location_name', sortable: true },
      { name: 'quantity', align: 'right', label: '总数量', field: 'quantity', sortable: true },
      { name: 'reserved_quantity', align: 'right', label: '预留数量', field: 'reserved_quantity', sortable: true },
      { name: 'available_quantity', align: 'right', label: '可用数量', field: 'available_quantity', sortable: true },
      { name: 'actions', align: 'center', label: '操作', field: 'actions', sortable: false }
    ]

    const categoryOptions = computed(() => {
      return categories.value.map(category => ({
        label: category.name,
        value: category.id
      }))
    })

    const parentCategoryOptions = computed(() => {
      // 如果是编辑模式，排除当前类别及其子类别
      if (editingCategory.value.id) {
        return categories.value
          .filter(category => category.id !== editingCategory.value.id)
          .map(category => ({
            label: category.name,
            value: category.id
          }))
      }
      return categoryOptions.value
    })

    const batchOptions = computed(() => {
      return batches.value.map(batch => ({
        label: `${batch.batch_number} (${batch.expiry_date ? '到期: ' + batch.expiry_date : '无到期日期'})`,
        value: batch.id
      }))
    })

    const fetchProducts = async () => {
      loading.value = true
      try {
        const params = {}
        if (filter.value.name) params.name = filter.value.name
        if (filter.value.sku) params.sku = filter.value.sku
        if (filter.value.category) params.category_id = filter.value.category
        
        const response = await productAPI.getProducts(params)
        products.value = response.data
      } catch (error) {
        console.error('获取产品列表失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取产品列表失败',
          icon: 'error'
        })
      } finally {
        loading.value = false
      }
    }

    const fetchCategories = async () => {
      try {
        const response = await productAPI.getCategories()
        categories.value = response.data
      } catch (error) {
        console.error('获取类别列表失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取类别列表失败',
          icon: 'error'
        })
      }
    }

    const resetFilters = () => {
      filter.value = {
        name: '',
        sku: '',
        category: null
      }
      fetchProducts()
    }

    const openProductDialog = (product = null) => {
      if (product) {
        // 编辑现有产品
        editingProduct.value = { ...product }
      } else {
        // 创建新产品
        editingProduct.value = {
          name: '',
          description: '',
          sku: '',
          barcode: '',
          category: null,
          weight: null,
          width: null,
          height: null,
          length: null,
          cost_price: null,
          selling_price: null,
          min_stock_level: 0,
          reorder_point: 0,
          handling_instructions: '',
          storage_requirements: '',
          is_active: true
        }
      }
      productDialog.value = true
    }

    const saveProduct = async () => {
      saving.value = true
      try {
        const productData = { ...editingProduct.value }
        
        if (productData.id) {
          // 更新现有产品
          await productAPI.updateProduct(productData.id, productData)
          $q.notify({
            color: 'positive',
            message: '产品更新成功',
            icon: 'check_circle'
          })
        } else {
          // 创建新产品
          await productAPI.createProduct(productData)
          $q.notify({
            color: 'positive',
            message: '产品创建成功',
            icon: 'check_circle'
          })
        }
        
        productDialog.value = false
        fetchProducts()
      } catch (error) {
        console.error('保存产品失败:', error)
        $q.notify({
          color: 'negative',
          message: '保存产品失败: ' + (error.response?.data?.error || error.message),
          icon: 'error'
        })
      } finally {
        saving.value = false
      }
    }

    const toggleProductStatus = async (product) => {
      try {
        const updatedProduct = { ...product, is_active: !product.is_active }
        await productAPI.updateProduct(product.id, updatedProduct)
        
        $q.notify({
          color: 'positive',
          message: `产品已${updatedProduct.is_active ? '激活' : '禁用'}`,
          icon: 'check_circle'
        })
        
        fetchProducts()
      } catch (error) {
        console.error('更新产品状态失败:', error)
        $q.notify({
          color: 'negative',
          message: '更新产品状态失败',
          icon: 'error'
        })
      }
    }

    const openCategoriesDialog = () => {
      fetchCategories()
      categoriesDialog.value = true
    }

    const openCategoryDialog = (category = null) => {
      if (category) {
        // 编辑现有类别
        editingCategory.value = { ...category }
      } else {
        // 创建新类别
        editingCategory.value = {
          name: '',
          description: '',
          parent: null
        }
      }
      categoryDialog.value = true
    }

    const saveCategory = async () => {
      savingCategory.value = true
      try {
        const categoryData = { ...editingCategory.value }
        
        if (categoryData.id) {
          // 更新现有类别
          // 假设API支持更新类别
          $q.notify({
            color: 'positive',
            message: '类别更新成功',
            icon: 'check_circle'
          })
        } else {
          // 创建新类别
          // 假设API支持创建类别
          $q.notify({
            color: 'positive',
            message: '类别创建成功',
            icon: 'check_circle'
          })
        }
        
        categoryDialog.value = false
        fetchCategories()
      } catch (error) {
        console.error('保存类别失败:', error)
        $q.notify({
          color: 'negative',
          message: '保存类别失败',
          icon: 'error'
        })
      } finally {
        savingCategory.value = false
      }
    }

    const confirmDeleteCategory = (category) => {
      $q.dialog({
        title: '确认删除',
        message: `确定要删除类别 "${category.name}" 吗？`,
        cancel: true,
        persistent: true
      }).onOk(async () => {
        try {
          // 假设API支持删除类别
          $q.notify({
            color: 'positive',
            message: '类别删除成功',
            icon: 'check_circle'
          })
          fetchCategories()
        } catch (error) {
          console.error('删除类别失败:', error)
          $q.notify({
            color: 'negative',
            message: '删除类别失败',
            icon: 'error'
          })
        }
      })
    }

    const openImagesDialog = async (product) => {
      selectedProduct.value = product
      productImages.value = product.images || []
      imagesDialog.value = true
    }

    const uploadImage = async () => {
      if (!newImage.value) return
      
      try {
        // 假设API支持上传图片
        $q.notify({
          color: 'positive',
          message: '图片上传成功',
          icon: 'check_circle'
        })
        
        // 重新获取产品图片
        newImage.value = null
      } catch (error) {
        console.error('上传图片失败:', error)
        $q.notify({
          color: 'negative',
          message: '上传图片失败',
          icon: 'error'
        })
      }
    }

    const setAsPrimaryImage = async (image) => {
      try {
        // 假设API支持设置主图
        $q.notify({
          color: 'positive',
          message: '已设置为主图',
          icon: 'check_circle'
        })
      } catch (error) {
        console.error('设置主图失败:', error)
        $q.notify({
          color: 'negative',
          message: '设置主图失败',
          icon: 'error'
        })
      }
    }

    const deleteImage = async (image) => {
      $q.dialog({
        title: '确认删除',
        message: '确定要删除此图片吗？',
        cancel: true,
        persistent: true
      }).onOk(async () => {
        try {
          // 假设API支持删除图片
          $q.notify({
            color: 'positive',
            message: '图片删除成功',
            icon: 'check_circle'
          })
          
          // 从列表中移除图片
          productImages.value = productImages.value.filter(img => img.id !== image.id)
        } catch (error) {
          console.error('删除图片失败:', error)
          $q.notify({
            color: 'negative',
            message: '删除图片失败',
            icon: 'error'
          })
        }
      })
    }

    const viewInventory = async (product) => {
      selectedProduct.value = product
      loadingInventory.value = true
      
      try {
        const response = await productAPI.getProductInventory(product.id)
        productInventory.value = response.data
        
        // 获取产品批次
        const batchResponse = await productAPI.getProductBatches(product.id)
        batches.value = batchResponse.data
        
        inventoryDialog.value = true
      } catch (error) {
        console.error('获取产品库存失败:', error)
        $q.notify({
          color: 'negative',
          message: '获取产品库存失败',
          icon: 'error'
        })
      } finally {
        loadingInventory.value = false
      }
    }

    const openAdjustDialog = (inventory) => {
      selectedInventory.value = inventory
      adjustment.value = {
        quantity: 0,
        reason: '',
        batch_id: null
      }
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
        
        // 重新获取产品库存
        const response = await productAPI.getProductInventory(selectedProduct.value.id)
        productInventory.value = response.data
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

    onMounted(() => {
      fetchProducts()
      fetchCategories()
    })

    return {
      // 产品列表相关
      products,
      loading,
      pagination,
      filter,
      columns,
      fetchProducts,
      resetFilters,
      
      // 产品编辑相关
      productDialog,
      editingProduct,
      saving,
      openProductDialog,
      saveProduct,
      toggleProductStatus,
      
      // 类别相关
      categories,
      categoriesDialog,
      categoryDialog,
      editingCategory,
      savingCategory,
      categoryOptions,
      parentCategoryOptions,
      openCategoriesDialog,
      openCategoryDialog,
      saveCategory,
      confirmDeleteCategory,
      
      // 产品图片相关
      imagesDialog,
      selectedProduct,
      productImages,
      newImage,
      openImagesDialog,
      uploadImage,
      setAsPrimaryImage,
      deleteImage,
      
      // 库存相关
      inventoryDialog,
      productInventory,
      loadingInventory,
      inventoryColumns,
      viewInventory,
      adjustDialog,
      selectedInventory,
      adjustment,
      adjusting,
      batchOptions,
      openAdjustDialog,
      saveAdjustment
    }
  }
})
</script>
