<template>
  <div class="task-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>任务管理</span>
          <el-button type="primary" @click="handleAdd">新增任务</el-button>
        </div>
      </template>

      <el-table :data="tasks" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="120" />
        <el-table-column prop="name" label="任务名称" />
        <el-table-column prop="created_by" label="创建人" width="120" />
        <el-table-column prop="created_on" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_on) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">
              详情
            </el-button>
            <el-button type="primary" link @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="danger" link @click="handleDelete(row)">
              删除
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

    <!-- 新增/编辑任务对话框 -->
    <el-dialog
      v-model="dialog.visible"
      :title="dialog.title"
      width="400px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入任务名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'
import dayjs from 'dayjs'

const router = useRouter()
const loading = ref(false)
const tasks = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const dialog = reactive({
  visible: false,
  title: '新增任务',
  type: 'add',
  id: '',
})

const form = reactive({
  name: '',
})

const rules = {
  name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
  ],
}

const formRef = ref()
const submitting = ref(false)

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await request.get('/sendtasks/list', {
      params: {
        page: page.value,
        page_size: pageSize.value,
      },
    })
    tasks.value = res.data.list
    total.value = res.data.total
  } catch (error) {
    console.error('获取任务列表失败:', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const handleSizeChange = (val) => {
  pageSize.value = val
  fetchTasks()
}

const handleCurrentChange = (val) => {
  page.value = val
  fetchTasks()
}

const handleAdd = () => {
  dialog.title = '新增任务'
  dialog.type = 'add'
  dialog.id = ''
  dialog.visible = true
}

const handleEdit = (row) => {
  dialog.title = '编辑任务'
  dialog.type = 'edit'
  dialog.id = row.id
  form.name = row.name
  dialog.visible = true
}

const viewDetail = (row) => {
  router.push(`/tasks/${row.id}`)
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确认删除任务"${row.name}"吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await request.post(`/sendtasks/delete?id=${row.id}`)
      ElMessage.success('删除成功')
      fetchTasks()
    } catch (error) {
      console.error('删除失败:', error)
    }
  })
}

const handleDialogClose = () => {
  form.name = ''
  formRef.value?.clearValidate()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (dialog.type === 'add') {
          await request.post('/sendtasks/add', form)
          ElMessage.success('新增成功')
        } else {
          await request.post(`/sendtasks/edit?id=${dialog.id}`, form)
          ElMessage.success('编辑成功')
        }
        dialog.visible = false
        fetchTasks()
      } catch (error) {
        console.error('提交失败:', error)
      } finally {
        submitting.value = false
      }
    }
  })
}

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.task-list {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>