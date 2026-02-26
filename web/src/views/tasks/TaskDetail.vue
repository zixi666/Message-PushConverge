<template>
  <div class="task-detail">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-button type="primary" link @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回
            </el-button>
            <span class="title">任务详情 - {{ taskName }}</span>
          </div>
          <div class="header-right">
            <el-button type="primary" @click="handleAddIns">新增实例</el-button>
          </div>
        </div>
      </template>

      <el-table :data="insList" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="120" />
        <el-table-column prop="way_name" label="渠道名称" />
        <el-table-column prop="way_type" label="渠道类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.way_type === 'dtalk' ? 'primary' : 'success'">
              {{ row.way_type === 'dtalk' ? '钉钉' : '飞书' }}
            </el-tag>
          </template>
        </el-table-column>
        <!-- @MODIFIED: 内容类型固定为文本，不再显示Markdown选项 -->
        <el-table-column prop="content_type" label="内容类型" width="120">
          <template #default>
            <el-tag type="info">文本</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="enable" label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.enable"
              :active-value="1"
              :inactive-value="0"
              @change="(val) => handleEnableChange(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_on" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_on) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" link @click="handleDeleteIns(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增实例对话框 -->
    <el-dialog
      v-model="insDialog.visible"
      title="新增实例"
      width="400px"
      @close="handleInsDialogClose"
    >
      <el-form
        ref="insFormRef"
        :model="insForm"
        :rules="insRules"
        label-width="80px"
      >
        <el-form-item label="选择渠道" prop="way_id">
          <el-select
            v-model="insForm.way_id"
            placeholder="请选择渠道"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="item in channels"
              :key="item.id"
              :label="`${item.name} (${item.type === 'dtalk' ? '钉钉' : '飞书'})`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>

        <!-- @MODIFIED: 内容类型固定为文本，隐藏选择项 -->
        <el-form-item label="内容类型" prop="content_type" v-if="false">
          <el-radio-group v-model="insForm.content_type">
            <el-radio value="text">文本</el-radio>
          </el-radio-group>
        </el-form-item>
        <!-- @NEW: 显示固定提示 -->
        <el-alert
          type="info"
          :closable="false"
          show-icon
          title="当前仅支持文本消息"
          style="margin-top: 10px;"
        />
      </el-form>
      <template #footer>
        <el-button @click="insDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitIns" :loading="submitting">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import request from '../../utils/request'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const taskId = route.params.id

const loading = ref(false)
const taskName = ref('')
const insList = ref([])
const channels = ref([])

const insDialog = reactive({
  visible: false,
})

const insForm = reactive({
  task_id: taskId,
  way_id: '',
  content_type: 'text',  // @NOTE: 固定为text
})

// @MODIFIED: 简化验证规则，只需要渠道
const insRules = {
  way_id: [
    { required: true, message: '请选择渠道', trigger: 'change' },
  ],
  // content_type 不再需要验证
}

const insFormRef = ref()
const submitting = ref(false)

const fetchTaskDetail = async () => {
  loading.value = true
  try {
    const res = await request.get(`/sendtasks/ins/gettask?id=${taskId}`)
    taskName.value = res.data.name
    insList.value = res.data.ins_data
  } catch (error) {
    console.error('获取任务详情失败:', error)
    ElMessage.error('获取任务详情失败')
    router.push('/tasks')
  } finally {
    loading.value = false
  }
}

const fetchChannels = async () => {
  try {
    const res = await request.get('/sendways/list?page=1&page_size=100')
    channels.value = res.data.list
  } catch (error) {
    console.error('获取渠道列表失败:', error)
  }
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const goBack = () => {
  router.push('/tasks')
}

const handleAddIns = () => {
  insDialog.visible = true
}

const handleEnableChange = async (row, val) => {
  try {
    await request.post(`/sendtasks/ins/update_enable?id=${row.id}&enable=${val}`)
    ElMessage.success('状态更新成功')
  } catch (error) {
    console.error('更新状态失败:', error)
    row.enable = val === 1 ? 0 : 1 // 回滚
  }
}

const handleDeleteIns = (row) => {
  ElMessageBox.confirm('确认删除该实例吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await request.post(`/sendtasks/ins/delete?id=${row.id}`)
      ElMessage.success('删除成功')
      fetchTaskDetail()
    } catch (error) {
      console.error('删除失败:', error)
    }
  })
}

const handleInsDialogClose = () => {
  insForm.way_id = ''
  insForm.content_type = 'text'
  insFormRef.value?.clearValidate()
}

const handleSubmitIns = async () => {
  if (!insFormRef.value) return

  await insFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        // @NOTE: content_type 固定为 text，不需要单独传递
        const submitData = {
          task_id: insForm.task_id,
          way_id: insForm.way_id,
          content_type: 'text'  // 固定为text
        }
        await request.post('/sendtasks/ins/add', submitData)
        ElMessage.success('新增成功')
        insDialog.visible = false
        fetchTaskDetail()
      } catch (error) {
        console.error('提交失败:', error)
      } finally {
        submitting.value = false
      }
    }
  })
}

onMounted(() => {
  fetchTaskDetail()
  fetchChannels()
})
</script>

<style scoped>
.task-detail {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right {
  display: flex;
  align-items: center;
}

.title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

/* 可选：让返回按钮和标题有更好的间距 */
.header-left .el-button {
  margin-right: 4px;
}
</style>