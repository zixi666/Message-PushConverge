<template>
  <div class="statistics">
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

    <el-row :gutter="20" class="mt-20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>发送趋势</span>
              <el-radio-group v-model="days" size="small" @change="fetchStatistics">
                <el-radio-button :label="7">7天</el-radio-button>
                <el-radio-button :label="30">30天</el-radio-button>
                <el-radio-button :label="90">90天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="trendChart" style="height: 400px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>今日发送分布</span>
            </div>
          </template>
          <div ref="pieChart" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>任务统计</span>
              <el-select
                v-model="selectedTask"
                placeholder="选择任务"
                filterable
                clearable
                @change="fetchTaskStatistics"
              >
                <el-option
                  v-for="item in tasks"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </div>
          </template>
          <div v-if="selectedTask">
            <div class="task-stats">
              <div class="task-stats-item">
                <div class="label">今日成功</div>
                <div class="value success">{{ taskStats.today_succ_num }}</div>
              </div>
              <div class="task-stats-item">
                <div class="label">今日失败</div>
                <div class="value danger">{{ taskStats.today_failed_num }}</div>
              </div>
              <div class="task-stats-item">
                <div class="label">今日总计</div>
                <div class="value">{{ taskStats.today_total_num }}</div>
              </div>
              <div class="task-stats-item">
                <div class="label">历史总计</div>
                <div class="value">{{ taskStats.total_num }}</div>
              </div>
            </div>
            <div ref="taskChart" style="height: 200px"></div>
          </div>
          <el-empty v-else description="请选择任务查看统计" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import request from '../../utils/request'

const days = ref(30)

const statsCards = ref([
  { title: '今日成功', value: 0, icon: 'CircleCheck', color: '#67C23A' },
  { title: '今日失败', value: 0, icon: 'CircleClose', color: '#F56C6C' },
  { title: '今日总计', value: 0, icon: 'DataLine', color: '#409EFF' },
  { title: '历史总计', value: 0, icon: 'Histogram', color: '#E6A23C' },
])

const tasks = ref([])
const selectedTask = ref('')
const taskStats = ref({
  today_succ_num: 0,
  today_failed_num: 0,
  today_total_num: 0,
  total_num: 0,
  daily_stats: [],
})

let trendChart = null
let pieChart = null
let taskChart = null

const fetchStatistics = async () => {
  try {
    const res = await request.get(`/statistic?days=${days.value}`)
    const data = res.data

    statsCards.value[0].value = data.today_succ_num
    statsCards.value[1].value = data.today_failed_num
    statsCards.value[2].value = data.today_total_num
    statsCards.value[3].value = data.total_num

    updateCharts(data.daily_stats)
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const fetchTasks = async () => {
  try {
    const res = await request.get('/sendtasks/list?page=1&page_size=100')
    tasks.value = res.data.list
  } catch (error) {
    console.error('获取任务列表失败:', error)
  }
}

const fetchTaskStatistics = async () => {
  if (!selectedTask.value) return

  try {
    const res = await request.get(`/statistic/task?task_id=${selectedTask.value}&days=${days.value}`)
    taskStats.value = res.data

    if (taskChart) {
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

const updateCharts = (dailyStats) => {
  if (!trendChart || !pieChart) return

  const days = dailyStats.map(item => item.day.slice(5))
  const successData = dailyStats.map(item => item.succ_num)
  const failedData = dailyStats.map(item => item.failed_num)

  // 趋势图
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['成功', '失败'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: days },
    yAxis: { type: 'value' },
    series: [
      { name: '成功', type: 'line', data: successData, smooth: true, color: '#67C23A' },
      { name: '失败', type: 'line', data: failedData, smooth: true, color: '#F56C6C' },
    ],
  })

  // 饼图
  pieChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left' },
    series: [
      {
        name: '今日发送',
        type: 'pie',
        radius: '50%',
        data: [
          { value: statsCards.value[0].value, name: '成功', itemStyle: { color: '#67C23A' } },
          { value: statsCards.value[1].value, name: '失败', itemStyle: { color: '#F56C6C' } },
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  })
}

const initCharts = () => {
  const trendEl = document.querySelector('.trend-chart')
  const pieEl = document.querySelector('.pie-chart')

  if (trendEl) {
    trendChart = echarts.init(trendEl)
  }
  if (pieEl) {
    pieChart = echarts.init(pieEl)
  }
}

onMounted(() => {
  fetchStatistics()
  fetchTasks()
  initCharts()

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
.statistics {
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

.task-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.task-stats-item {
  text-align: center;
}

.task-stats-item .label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.task-stats-item .value {
  font-size: 20px;
  font-weight: bold;
}

.task-stats-item .value.success {
  color: #67C23A;
}

.task-stats-item .value.danger {
  color: #F56C6C;
}
</style>