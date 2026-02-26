<template>
  <div class="log-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>发送日志</span>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="任务名称">
          <el-input
            v-model="searchForm.name"
            placeholder="任务名称"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="任务ID">
          <el-input
            v-model="searchForm.task_id"
            placeholder="任务ID"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="成功" :value="1" />
            <el-option label="失败" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="searchForm.day"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="logs" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="task_id" label="任务ID" width="120" />
        <el-table-column prop="name" label="任务名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="caller_ip" label="调用IP" width="140" />
        <el-table-column prop="created_on" label="发送时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_on) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 日志详情对话框 -->
    <el-dialog v-model="logDialog.visible" title="发送详情" width="600px">
      <div class="log-detail">
        <pre>{{ logDialog.log }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import request from '../../utils/request'
import dayjs from 'dayjs'

const loading = ref(false)
const logs = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const searchForm = reactive({
  name: '',
  task_id: '',
  status: -1,
  day: '',
})

const logDialog = reactive({
  visible: false,
  log: '',
})

const fetchLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
    }

    if (searchForm.name) params.name = searchForm.name
    if (searchForm.task_id) params.task_id = searchForm.task_id
    if (searchForm.status >= 0) params.status = searchForm.status
    if (searchForm.day) params.day = searchForm.day

    const res = await request.get('/sendlogs/list', { params })
    logs.value = res.data.list
    total.value = res.data.total
  } catch (error) {
    console.error('获取日志列表失败:', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const handleSearch = () => {
  page.value = 1
  fetchLogs()
}

const handleReset = () => {
  searchForm.name = ''
  searchForm.task_id = ''
  searchForm.status = -1
  searchForm.day = ''
  page.value = 1
  fetchLogs()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  fetchLogs()
}

const handleCurrentChange = (val) => {
  page.value = val
  fetchLogs()
}

const viewDetail = (row) => {
  logDialog.log = row.log
  logDialog.visible = true
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.log-list {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

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