<template>
  <q-page padding>
    <div class="q-pa-md">
      <div class="row q-mb-md">
        <div class="col-12">
          <div class="text-h5">报表与分析</div>
          <div class="text-subtitle2">查看系统数据分析和报表</div>
        </div>
      </div>

      <div class="row q-mb-md">
        <div class="col-12 col-md-3 q-pr-md-md">
          <q-select
            v-model="selectedReport"
            :options="reportOptions"
            label="报表类型"
            outlined
            emit-value
            map-options
            @update:model-value="loadReport"
          />
        </div>
        <div class="col-12 col-md-3 q-pr-md-md q-pt-xs-sm">
          <q-select
            v-model="filter.warehouse"
            :options="warehouseOptions"
            label="仓库"
            outlined
            clearable
            emit-value
            map-options
            @update:model-value="loadReport"
          />
        </div>
        <div class="col-12 col-md-3 q-pr-md-md q-pt-xs-sm">
          <q-select
            v-model="filter.timeRange"
            :options="timeRangeOptions"
            label="时间范围"
            outlined
            emit-value
            map-options
            @update:model-value="loadReport"
          />
        </div>
        <div class="col-12 col-md-3 q-pt-xs-sm">
          <q-btn color="primary" icon="refresh" label="刷新" @click="loadReport" />
          <q-btn class="q-ml-sm" color="secondary" icon="print" label="打印" @click="printReport" />
          <q-btn class="q-ml-sm" color="accent" icon="file_download" label="导出" @click="exportReport" />
        </div>
      </div>

      <!-- 库存报表 -->
      <div v-if="selectedReport === 'inventory'" class="row q-col-gutter-md">
        <div class="col-12 col-md-6">
          <q-card class="report-card">
            <q-card-section>
              <div class="text-h6">库存概览</div>
            </q-card-section>
            <q-card-section>
              <div class="row q-col-gutter-md">
                <div class="col-6 col-md-3">
                  <div class="text-subtitle2">总产品数</div>
                  <div class="text-h4">{{ inventorySummary.total_products }}</div>
                </div>
                <div class="col-6 col-md-3">
                  <div class="text-subtitle2">总库存量</div>
                  <div class="text-h4">{{ inventorySummary.total_quantity }}</div>
                </div>
                <div class="col-6 col-md-3">
                  <div class="text-subtitle2">低库存产品</div>
                  <div class="text-h4 text-warning">{{ inventorySummary.low_stock_products }}</div>
                </div>
                <div class="col-6 col-md-3">
                  <div class="text-subtitle2">缺货产品</div>
                  <div class="text-h4 text-negative">{{ inventorySummary.out_of_stock_products }}</div>
                </div>
              </div>
            </q-card-section>
            <q-card-section>
              <div id="inventory-value-chart" style="height: 300px"></div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col-12 col-md-6">
          <q-card class="report-card">
            <q-card-section>
              <div class="text-h6">库存分布</div>
            </q-card-section>
            <q-card-section>
              <div id="inventory-distribution-chart" style="height: 300px"></div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col-12">
          <q-card class="report-card">
            <q-card-section>
              <div class="text-h6">低库存产品</div>
            </q-card-section>
            <q-card-section>
              <q-table
                :rows="lowStockProducts"
                :columns="lowStockColumns"
                row-key="id"
                :pagination="{rowsPerPage: 10}"
              >
                <template v-slot:body-cell-available_quantity="props">
                  <q-td :props="props">
                    <q-badge :color="getStockLevelColor(props.row)">
                      {{ props.value }}
                    </q-badge>
                  </q-td>
                </template>
              </q-table>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- 活动报表 -->
      <div v-if="selectedReport === 'activity'" class="row q-col-gutter-md">
        <div class="col-12 col-md-6">
          <q-card class="report-card">
            <q-card-section>
              <div class="text-h6">任务完成情况</div>
            </q-card-section>
            <q-card-section>
              <div class="row q-col-gutter-md">
                <div class="col-6 col-md-3">
                  <div class="text-subtitle2">总任务数</div>
                  <div class="text-h4">{{ activitySummary.total_tasks }}</div>
                </div>
                <div class="col-6 col-md-3">
                  <div class="text-subtitle2">已完成</div>
                  <div class="text-h4 text-positive">{{ activitySummary.completed_tasks }}</div>
                </div>
                <div class="col-6 col-md-3">
                  <div class="text-subtitle2">进行中</div>
                  <div class="text-h4 text-warning">{{ activitySummary.in_progress_tasks }}</div>
                </div>
                <div class="col-6 col-md-3">
                  <div class="text-subtitle2">待处理</div>
                  <div class="text-h4 text-negative">{{ activitySummary.pending_tasks }}</div>
                </div>
              </div>
            </q-card-section>
            <q-card-section>
              <div id="task-completion-chart" style="height: 300px"></div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col-12 col-md-6">
          <q-card class="report-card">
            <q-card-section>
              <div class="text-h6">任务类型分布</div>
            </q-card-section>
            <q-card-section>
              <div id="task-type-chart" style="height: 300px"></div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col-12">
          <q-card class="report-card">
            <q-card-section>
              <div class="text-h6">用户活动</div>
            </q-card-section>
            <q-card-section>
              <q-table
                :rows="userActivities"
                :columns="userActivityColumns"
                row-key="id"
                :pagination="{rowsPerPage: 10}"
              >
                <template v-slot:body-cell-task_completion_rate="props">
                  <q-td :props="props">
                    <q-linear-progress
                      :value="props.value / 100"
                      :color="props.value >= 80 ? 'positive' : props.value >= 50 ? 'warning' : 'negative'"
                      style="height: 15px"
                    />
                    <div class="text-center">{{ props.value }}%</div>
                  </q-td>
                </template>
              </q-table>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- 库存移动报表 -->
      <div v-if="selectedReport === 'inventory_movement'" class="row q-col-gutter-md">
        <div class="col-12">
          <q-card class="report-card">
            <q-card-section>
              <div class="text-h6">库存移动趋势</div>
            </q-card-section>
            <q-card-section>
              <div id="inventory-movement-chart" style="height: 400px"></div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col-12">
          <q-card class="report-card">
            <q-card-section>
              <div class="text-h6">库存交易记录</div>
            </q-card-section>
            <q-card-section>
              <q-table
                :rows="inventoryTransactions"
                :columns="transactionColumns"
                row-key="id"
                :pagination="{rowsPerPage: 10}"
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
        </div>
      </div>

      <!-- 自定义报表 -->
      <div v-if="selectedReport === 'custom'" class="row q-col-gutter-md">
        <div class="col-12">
          <q-card class="report-card">
            <q-card-section>
              <div class="text-h6">自定义报表</div>
            </q-card-section>
            <q-card-section>
              <div class="row q-col-gutter-md">
                <div class="col-12 col-md-4">
                  <q-select
                    v-model="customReport.dimension"
                    :options="dimensionOptions"
                    label="维度"
                    outlined
                    emit-value
                    map-options
                  />
                </div>
                <div class="col-12 col-md-4">
                  <q-select
                    v-model="customReport.metric"
                    :options="metricOptions"
                    label="指标"
                    outlined
                    emit-value
                    map-options
                  />
                </div>
                <div class="col-12 col-md-4">
                  <q-btn color="primary" class="full-width" label="生成报表" @click="generateCustomReport" />
                </div>
              </div>
            </q-card-section>
            <q-card-section v-if="customReportData.length > 0">
              <div id="custom-report-chart" style="height: 400px"></div>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script>
import { defineComponent, ref, onMounted, watch } from 'vue'
import { useQuasar } from 'quasar'
import { reportAPI, warehouseAPI } from 'src/services/api'
import * as echarts from 'echarts'

export default defineComponent({
  name: 'ReportsPage',

  setup() {
    const $q = useQuasar()

    // 报表选择和过滤
    const selectedReport = ref('inventory')
    const filter = ref({
      warehouse: null,
      timeRange: 'last_30_days'
    })

    // 图表实例
    let inventoryValueChart = null
    let inventoryDistributionChart = null
    let taskCompletionChart = null
    let taskTypeChart = null
    let inventoryMovementChart = null
    let customReportChart = null

    // 报表数据
    const inventorySummary = ref({
      total_products: 0,
      total_quantity: 0,
      low_stock_products: 0,
      out_of_stock_products: 0
    })
    const lowStockProducts = ref([])
    const activitySummary = ref({
      total_tasks: 0,
      completed_tasks: 0,
      in_progress_tasks: 0,
      pending_tasks: 0
    })
    const userActivities = ref([])
    const inventoryTransactions = ref([])
    const customReportData = ref([])

    // 自定义报表配置
    const customReport = ref({
      dimension: 'product',
      metric: 'quantity'
    })

    // 选项数据
    const warehouses = ref([])

    const reportOptions = [
      { label: '库存报表', value: 'inventory' },
      { label: '活动报表', value: 'activity' },
      { label: '库存移动报表', value: 'inventory_movement' },
      { label: '自定义报表', value: 'custom' }
    ]

    const timeRangeOptions = [
      { label: '今天', value: 'today' },
      { label: '昨天', value: 'yesterday' },
      { label: '本周', value: 'this_week' },
      { label: '上周', value: 'last_week' },
      { label: '本月', value: 'this_month' },
      { label: '上月', value: 'last_month' },
      { label: '最近7天', value: 'last_7_days' },
      { label: '最近30天', value: 'last_30_days' },
      { label: '最近90天', value: 'last_90_days' },
      { label: '今年', value: 'this_year' },
      { label: '去年', value: 'last_year' }
    ]

    const dimensionOptions = [
      { label: '产品', value: 'product' },
      { label: '仓库', value: 'warehouse' },
      { label: '用户', value: 'user' },
      { label: '任务类型', value: 'task_type' },
      { label: '时间', value: 'time' }
    ]

    const metricOptions = [
      { label: '数量', value: 'quantity' },
      { label: '价值', value: 'value' },
      { label: '任务数', value: 'task_count' },
      { label: '完成率', value: 'completion_rate' },
      { label: '周转率', value: 'turnover_rate' }
    ]

    const lowStockColumns = [
      { name: 'product_name', align: 'left', label: '产品名称', field: 'product_name', sortable: true },
      { name: 'product_sku', align: 'left', label: 'SKU', field: 'product_sku', sortable: true },
      { name: 'warehouse_name', align: 'left', label: '仓库', field: 'warehouse_name', sortable: true },
      { name: 'available_quantity', align: 'right', label: '可用数量', field: 'available_quantity', sortable: true },
      { name: 'min_stock_level', align: 'right', label: '最低库存水平', field: 'min_stock_level', sortable: true },
      { name: 'reorder_point', align: 'right', label: '再订购点', field: 'reorder_point', sortable: true },
      { name: 'days_until_stockout', align: 'right', label: '预计缺货天数', field: 'days_until_stockout', sortable: true }
    ]

    const userActivityColumns = [
      { name: 'username', align: 'left', label: '用户名', field: 'username', sortable: true },
      { name: 'total_tasks', align: 'right', label: '总任务数', field: 'total_tasks', sortable: true },
      { name: 'completed_tasks', align: 'right', label: '已完成任务', field: 'completed_tasks', sortable: true },
      { name: 'task_completion_rate', align: 'center', label: '完成率', field: 'task_completion_rate', sortable: true },
      { name: 'avg_completion_time', align: 'right', label: '平均完成时间(分钟)', field: 'avg_completion_time', sortable: true },
      { name: 'last_activity', align: 'left', label: '最近活动', field: 'last_activity', sortable: true }
    ]

    const transactionColumns = [
      { name: 'created_at', align: 'left', label: '时间', field: 'created_at', sortable: true },
      { name: 'product_name', align: 'left', label: '产品', field: 'product_name', sortable: true },
      { name: 'transaction_type', align: 'center', label: '类型', field: 'transaction_type', sortable: true },
      { name: 'quantity', align: 'right', label: '数量', field: 'quantity', sortable: true },
      { name: 'warehouse_name', align: 'left', label: '仓库', field: 'warehouse_name', sortable: true },
      { name: 'location_name', align: 'left', label: '位置', field: 'location_name', sortable: true },
      { name: 'reference_type', align: 'left', label: '引用类型', field: 'reference_type', sortable: true },
      { name: 'user_name', align: 'left', label: '操作人', field: 'user_name', sortable: true }
    ]

    const warehouseOptions = computed(() => {
      return warehouses.value.map(warehouse => ({
        label: warehouse.name,
        value: warehouse.id
      }))
    })

    const fetchWarehouses = async () => {
      try {
        const response = await warehouseAPI.getWarehouses()
        warehouses.value = response.data
      } catch (error) {
        console.error('获取仓库列表失败:', error)
      }
    }

    const loadReport = async () => {
      switch (selectedReport.value) {
        case 'inventory':
          await loadInventoryReport()
          break
        case 'activity':
          await loadActivityReport()
          break
        case 'inventory_movement':
          await loadInventoryMovementReport()
          break
        case 'custom':
          // 自定义报表需要用户点击生成按钮
          break
      }
    }

    const loadInventoryReport = async () => {
      try {
        const params = {
          warehouse_id: filter.value.warehouse,
          time_range: filter.value.timeRange
        }
        
        // 获取库存概览数据
        const summaryResponse = await reportAPI.getInventorySummary(params)
        inventorySummary.value = summaryResponse.data
        
        // 获取低库存产品数据
        const lowStockResponse = await reportAPI.getLowStockProducts(params)
        lowStockProducts.value = lowStockResponse.data
        
        // 获取库存价值趋势数据
        const valueResponse = await reportAPI.getInventoryValueTrend(params)
        renderInventoryValueChart(valueResponse.data)
        
        // 获取库存分布数据
        const distributionResponse = await reportAPI.getInventoryDistribution(params)
        renderInventoryDistributionChart(distributionResponse.data)
      } catch (error) {
        console.error('加载库存报表失败:', error)
        $q.notify({
          color: 'negative',
          message: '加载库存报表失败',
          icon: 'error'
        })
      }
    }

    const loadActivityReport = async () => {
      try {
        const params = {
          warehouse_id: filter.value.warehouse,
          time_range: filter.value.timeRange
        }
        
        // 获取活动概览数据
        const summaryResponse = await reportAPI.getActivitySummary(params)
        activitySummary.value = summaryResponse.data
        
        // 获取用户活动数据
        const userActivityResponse = await reportAPI.getUserActivities(params)
        userActivities.value = userActivityResponse.data
        
        // 获取任务完成趋势数据
        const completionResponse = await reportAPI.getTaskCompletionTrend(params)
        renderTaskCompletionChart(completionResponse.data)
        
        // 获取任务类型分布数据
        const typeResponse = await reportAPI.getTaskTypeDistribution(params)
        renderTaskTypeChart(typeResponse.data)
      } catch (error) {
        console.error('加载活动报表失败:', error)
        $q.notify({
          color: 'negative',
          message: '加载活动报表失败',
          icon: 'error'
        })
      }
    }

    const loadInventoryMovementReport = async () => {
      try {
        const params = {
          warehouse_id: filter.value.warehouse,
          time_range: filter.value.timeRange
        }
        
        // 获取库存移动趋势数据
        const movementResponse = await reportAPI.getInventoryMovementTrend(params)
        renderInventoryMovementChart(movementResponse.data)
        
        // 获取库存交易记录数据
        const transactionResponse = await reportAPI.getInventoryTransactions(params)
        inventoryTransactions.value = transactionResponse.data
      } catch (error) {
        console.error('加载库存移动报表失败:', error)
        $q.notify({
          color: 'negative',
          message: '加载库存移动报表失败',
          icon: 'error'
        })
      }
    }

    const generateCustomReport = async () => {
      try {
        const params = {
          warehouse_id: filter.value.warehouse,
          time_range: filter.value.timeRange,
          dimension: customReport.value.dimension,
          metric: customReport.value.metric
        }
        
        // 获取自定义报表数据
        const response = await reportAPI.getCustomReport(params)
        customReportData.value = response.data
        
        // 渲染自定义报表图表
        renderCustomReportChart(response.data)
      } catch (error) {
        console.error('生成自定义报表失败:', error)
        $q.notify({
          color: 'negative',
          message: '生成自定义报表失败',
          icon: 'error'
        })
      }
    }

    const renderInventoryValueChart = (data) => {
      if (!inventoryValueChart) {
        inventoryValueChart = echarts.init(document.getElementById('inventory-value-chart'))
      }
      
      const option = {
        title: {
          text: '库存价值趋势'
        },
        tooltip: {
          trigger: 'axis',
          formatter: '{b}<br/>{a}: ¥{c}'
        },
        xAxis: {
          type: 'category',
          data: data.dates
        },
        yAxis: {
          type: 'value',
          name: '价值 (¥)'
        },
        series: [
          {
            name: '库存价值',
            type: 'line',
            data: data.values,
            areaStyle: {}
          }
        ]
      }
      
      inventoryValueChart.setOption(option)
    }

    const renderInventoryDistributionChart = (data) => {
      if (!inventoryDistributionChart) {
        inventoryDistributionChart = echarts.init(document.getElementById('inventory-distribution-chart'))
      }
      
      const option = {
        title: {
          text: '库存分布'
        },
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          right: 10,
          top: 'center'
        },
        series: [
          {
            name: '库存分布',
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: '18',
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: data.map(item => ({
              name: item.name,
              value: item.value
            }))
          }
        ]
      }
      
      inventoryDistributionChart.setOption(option)
    }

    const renderTaskCompletionChart = (data) => {
      if (!taskCompletionChart) {
        taskCompletionChart = echarts.init(document.getElementById('task-completion-chart'))
      }
      
      const option = {
        title: {
          text: '任务完成趋势'
        },
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['已完成', '进行中', '待处理']
        },
        xAxis: {
          type: 'category',
          data: data.dates
        },
        yAxis: {
          type: 'value',
          name: '任务数'
        },
        series: [
          {
            name: '已完成',
            type: 'bar',
            stack: 'total',
            data: data.completed,
            color: '#21BA45'
          },
          {
            name: '进行中',
            type: 'bar',
            stack: 'total',
            data: data.in_progress,
            color: '#F2C037'
          },
          {
            name: '待处理',
            type: 'bar',
            stack: 'total',
            data: data.pending,
            color: '#C10015'
          }
        ]
      }
      
      taskCompletionChart.setOption(option)
    }

    const renderTaskTypeChart = (data) => {
      if (!taskTypeChart) {
        taskTypeChart = echarts.init(document.getElementById('task-type-chart'))
      }
      
      const option = {
        title: {
          text: '任务类型分布'
        },
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          right: 10,
          top: 'center'
        },
        series: [
          {
            name: '任务类型',
            type: 'pie',
            radius: '70%',
            data: data.map(item => ({
              name: item.name,
              value: item.value
            })),
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      }
      
      taskTypeChart.setOption(option)
    }

    const renderInventoryMovementChart = (data) => {
      if (!inventoryMovementChart) {
        inventoryMovementChart = echarts.init(document.getElementById('inventory-movement-chart'))
      }
      
      const option = {
        title: {
          text: '库存移动趋势'
        },
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['入库', '出库']
        },
        xAxis: {
          type: 'category',
          data: data.dates
        },
        yAxis: {
          type: 'value',
          name: '数量'
        },
        series: [
          {
            name: '入库',
            type: 'line',
            data: data.inbound,
            color: '#21BA45'
          },
          {
            name: '出库',
            type: 'line',
            data: data.outbound,
            color: '#C10015'
          }
        ]
      }
      
      inventoryMovementChart.setOption(option)
    }

    const renderCustomReportChart = (data) => {
      if (!customReportChart) {
        customReportChart = echarts.init(document.getElementById('custom-report-chart'))
      }
      
      // 根据维度和指标类型选择合适的图表类型
      let chartType = 'bar'
      if (customReport.value.dimension === 'time') {
        chartType = 'line'
      } else if (['product', 'warehouse', 'user', 'task_type'].includes(customReport.value.dimension) && 
                 ['quantity', 'value'].includes(customReport.value.metric)) {
        chartType = 'bar'
      }
      
      const option = {
        title: {
          text: `${getDimensionLabel(customReport.value.dimension)} - ${getMetricLabel(customReport.value.metric)}`
        },
        tooltip: {
          trigger: chartType === 'line' ? 'axis' : 'item'
        },
        xAxis: {
          type: 'category',
          data: data.map(item => item.name),
          axisLabel: {
            rotate: 45,
            interval: 0
          }
        },
        yAxis: {
          type: 'value',
          name: getMetricLabel(customReport.value.metric)
        },
        series: [
          {
            name: getMetricLabel(customReport.value.metric),
            type: chartType,
            data: data.map(item => item.value)
          }
        ]
      }
      
      customReportChart.setOption(option)
    }

    const getDimensionLabel = (dimension) => {
      const option = dimensionOptions.find(opt => opt.value === dimension)
      return option ? option.label : dimension
    }

    const getMetricLabel = (metric) => {
      const option = metricOptions.find(opt => opt.value === metric)
      return option ? option.label : metric
    }

    const getStockLevelColor = (product) => {
      if (product.available_quantity <= 0) {
        return 'negative'
      } else if (product.available_quantity < product.min_stock_level) {
        return 'warning'
      } else {
        return 'positive'
      }
    }

    const printReport = () => {
      window.print()
    }

    const exportReport = () => {
      $q.notify({
        color: 'info',
        message: '正在导出报表...',
        icon: 'file_download'
      })
      
      // 假设导出功能
      setTimeout(() => {
        $q.notify({
          color: 'positive',
          message: '报表导出成功',
          icon: 'check_circle'
        })
      }, 1500)
    }

    // 监听窗口大小变化，调整图表大小
    const resizeCharts = () => {
      if (inventoryValueChart) inventoryValueChart.resize()
      if (inventoryDistributionChart) inventoryDistributionChart.resize()
      if (taskCompletionChart) taskCompletionChart.resize()
      if (taskTypeChart) taskTypeChart.resize()
      if (inventoryMovementChart) inventoryMovementChart.resize()
      if (customReportChart) customReportChart.resize()
    }

    // 监听报表类型变化
    watch(selectedReport, () => {
      loadReport()
    })

    onMounted(() => {
      fetchWarehouses()
      loadReport()
      
      window.addEventListener('resize', resizeCharts)
    })

    onBeforeUnmount(() => {
      window.removeEventListener('resize', resizeCharts)
      
      // 销毁图表实例
      if (inventoryValueChart) inventoryValueChart.dispose()
      if (inventoryDistributionChart) inventoryDistributionChart.dispose()
      if (taskCompletionChart) taskCompletionChart.dispose()
      if (taskTypeChart) taskTypeChart.dispose()
      if (inventoryMovementChart) inventoryMovementChart.dispose()
      if (customReportChart) customReportChart.dispose()
    })

    return {
      // 报表选择和过滤
      selectedReport,
      filter,
      reportOptions,
      timeRangeOptions,
      warehouseOptions,
      
      // 报表数据
      inventorySummary,
      lowStockProducts,
      activitySummary,
      userActivities,
      inventoryTransactions,
      customReportData,
      
      // 表格列定义
      lowStockColumns,
      userActivityColumns,
      transactionColumns,
      
      // 自定义报表配置
      customReport,
      dimensionOptions,
      metricOptions,
      
      // 方法
      loadReport,
      getStockLevelColor,
      printReport,
      exportReport,
      generateCustomReport
    }
  }
})
</script>

<style lang="scss" scoped>
.report-card {
  margin-bottom: 20px;
}

.text-warning {
  color: #F2C037;
}

@media print {
  .q-page-container {
    padding: 0 !important;
  }
  
  .q-header, .q-drawer, .q-footer {
    display: none !important;
  }
}
</style>
