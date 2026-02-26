<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20">
      <el-col :span="6" v-for="item in statsCards" :key="item.title">
        <el-card class="stats-card" :body-style="{ padding: '20px' }">
          <div class="stats-icon" :style="{ background: item.color + '20' }">
            <el-icon :size="24" :color="item.color">
              <component :is="item.icon" />
            </el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-title">{{ item.title }}</div>
            <div class="stats-value">{{ item.value }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第一行：发送趋势图 + 最近10条记录（横排） -->
    <el-row :gutter="24" class="mt-20">
      <!-- 发送趋势图 - 占18列 -->
      <el-col :span="18">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>发送趋势</span>
              <el-radio-group v-model="trendDays" size="small" @change="fetchStatistics">
                <el-radio-button :label="7">7天</el-radio-button>
                <el-radio-button :label="30">30天</el-radio-button>
                <el-radio-button :label="90">90天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <!-- 图表容器：高度提升到280px -->
          <div ref="trendChart" class="trend-chart" style="height: 280px"></div>
        </el-card>
      </el-col>

      <!-- 最近10条记录 - 占6列 -->
      <el-col :span="6">
        <el-card class="chart-card logs-card">
          <template #header>
            <div class="card-header">
              <span>最近10条发送记录</span>
              <el-button type="primary" link @click="router.push('/logs')">查看全部</el-button>
            </div>
          </template>
          <div class="recent-logs" v-loading="logsLoading">
            <div v-for="log in recentLogs" :key="log.id" class="log-item">
              <div class="log-header">
                <span class="log-name">{{ log.name }}</span>
                <el-tag :type="log.status === 1 ? 'success' : 'danger'" size="small">
                  {{ log.status === 1 ? '成功' : '失败' }}
                </el-tag>
              </div>
              <div class="log-footer">
                <span class="log-time">{{ formatDate(log.created_on) }}</span>
                <el-button type="primary" link size="small" @click="viewLogDetail(log)">
                  详情
                </el-button>
              </div>
            </div>
            <el-empty v-if="recentLogs.length === 0" description="暂无发送记录" :image-size="60" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 日志详情对话框 -->
    <el-dialog v-model="logDialog.visible" title="发送详情" width="600px">
      <div class="log-detail">
        <pre>{{ logDialog.log }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import request from '../utils/request'
import dayjs from 'dayjs'

const router = useRouter()
const trendDays = ref(30)

// 统计卡片数据
const statsCards = ref([
  { title: '今日成功', value: 0, icon: 'CircleCheck', color: '#67C23A' },
  { title: '今日失败', value: 0, icon: 'CircleClose', color: '#F56C6C' },
  { title: '今日总计', value: 0, icon: 'DataLine', color: '#409EFF' },
  { title: '历史总计', value: 0, icon: 'Histogram', color: '#E6A23C' },
])

// 任务列表
const tasks = ref([])
const selectedTask = ref('')
const taskStats = ref(null)

// 任务统计卡片
const taskStatCards = computed(() => {
  if (!taskStats.value) return []
  return [
    { label: '今日成功', value: taskStats.value.today_succ_num, class: 'success' },
    { label: '今日失败', value: taskStats.value.today_failed_num, class: 'danger' },
    { label: '今日总计', value: taskStats.value.today_total_num, class: '' },
    { label: '历史总计', value: taskStats.value.total_num, class: 'primary' },
  ]
})

// 最近日志
const recentLogs = ref([])
const logsLoading = ref(false)

// 图表实例
let trendChart = null
let pieChart = null
let taskChart = null

// 日志对话框
const logDialog = ref({
  visible: false,
  log: '',
})

// 获取全局统计
const fetchStatistics = async () => {
  try {
    const res = await request.get(`/statistic?days=${trendDays.value}`)
    const data = res.data

    statsCards.value[0].value = data.today_succ_num || 0
    statsCards.value[1].value = data.today_failed_num || 0
    statsCards.value[2].value = data.today_total_num || 0
    statsCards.value[3].value = data.total_num || 0

    await nextTick()
    updateCharts(data.daily_stats || [])
  } catch (error) {
    console.error('获取统计数据失败:', error)
    updateCharts([])
  }
}

// 获取任务列表
const fetchTasks = async () => {
  try {
    const res = await request.get('/sendtasks/list?page=1&page_size=100')
    tasks.value = res.data.list
  } catch (error) {
    console.error('获取任务列表失败:', error)
  }
}

// 获取任务统计
const fetchTaskStatistics = async () => {
  if (!selectedTask.value) {
    taskStats.value = null
    return
  }

  try {
    const res = await request.get(`/statistic/task?task_id=${selectedTask.value}&days=${trendDays.value}`)
    taskStats.value = res.data

    if (taskChart && taskStats.value.daily_stats) {
      const daily = taskStats.value.daily_stats
      const days = daily.map(item => item.day.slice(5))
      const successData = daily.map(item => item.succ_num)
      const failedData = daily.map(item => item.failed_num)

      taskChart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['成功', '失败'], show: true },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'category', data: days },
        yAxis: { type: 'value' },
        series: [
          { name: '成功', type: 'bar', data: successData, color: '#67C23A' },
          { name: '失败', type: 'bar', data: failedData, color: '#F56C6C' },
        ],
      })
    }
  } catch (error) {
    console.error('获取任务统计失败:', error)
  }
}

// 获取最近日志
const fetchRecentLogs = async () => {
  logsLoading.value = true
  try {
    const res = await request.get('/sendlogs/list?page=1&page_size=10')
    recentLogs.value = res.data.list || []
  } catch (error) {
    console.error('获取最近日志失败:', error)
    recentLogs.value = []
  } finally {
    logsLoading.value = false
  }
}

// 更新图表
// 更新图表
const updateCharts = (dailyStats) => {
  if (!trendChart) {
    initCharts()
  }
  if (!trendChart) return

  const days = dailyStats?.map(item => item.day.slice(5)) || []
  const successData = dailyStats?.map(item => item.succ_num) || []
  const failedData = dailyStats?.map(item => item.failed_num) || []

  // 趋势图
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['成功', '失败'], top: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true }, // 增加底部空间，防止标签重叠
    xAxis: {
      type: 'category',
      data: days,
      axisLabel: {
        interval: 'auto', // 自动计算间隔，避免标签重叠
        rotate: 30,       // 标签旋转30度，节省空间
        hideOverlap: true // 隐藏重叠的标签
      }
    },
    yAxis: { type: 'value', min: 0 },
    series: [
      { name: '成功', type: 'line', data: successData, smooth: true, color: '#67C23A' },
      { name: '失败', type: 'line', data: failedData, smooth: true, color: '#F56C6C' },
    ],
    graphic: days.length === 0 ? [{
      type: 'text',
      left: 'center',
      top: 'center',
      style: {
        text: '暂无数据',
        fontSize: 14,
        fill: '#909399'
      }
    }] : []
  })
}

// 格式化日期
const formatDate = (date) => {
  return dayjs(date).format('MM-DD HH:mm')
}

// 查看日志详情
const viewLogDetail = (row) => {
  logDialog.value.log = row.log
  logDialog.value.visible = true
}

// 初始化图表
const initCharts = () => {
  const trendEl = document.querySelector('.trend-chart') || trendChartRef.value
  const pieEl = document.querySelector('.pie-chart')

  if (trendEl) {
    trendChart = echarts.init(trendEl)
  }
  if (pieEl) {
    pieChart = echarts.init(pieEl)
  }
}

const trendChartRef = ref(null)

onMounted(async () => {
  await nextTick()
  initCharts()

  fetchStatistics()
  fetchTasks()
  fetchRecentLogs()

  window.addEventListener('resize', () => {
    trendChart?.resize()
    pieChart?.resize()
    taskChart?.resize()
  })
})

onUnmounted(() => {
  trendChart?.dispose()
  pieChart?.dispose()
  taskChart?.dispose()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stats-card {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stats-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stats-info {
  flex: 1;
}

.stats-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stats-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.mt-20 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 最近日志卡片样式 */
.logs-card {
  height: 100%;
}

.logs-card :deep(.el-card__body) {
  /* 调整日志卡片内容高度，和图表卡片保持一致 */
  height: calc(100% - 60px);
  overflow-y: auto;
  padding: 15px;
}

.recent-logs {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.log-item {
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
  transition: all 0.3s;
}

.log-item:hover {
  background-color: #ecf5ff;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.log-name {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-time {
  font-size: 12px;
  color: #909399;
}

/* 图表卡片：统一高度为360px */
.chart-card {
  height: 360px;
}

/* 日志详情 */
.log-detail {
  max-height: 400px;
  overflow: auto;
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
}

.log-detail pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.5;
}
</style>