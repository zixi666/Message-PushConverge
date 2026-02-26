<template>
  <div class="channel-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>渠道管理</span>
          <el-button type="primary" @click="handleAdd">新增渠道</el-button>
        </div>
      </template>

      <el-table :data="channels" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="120" />
        <el-table-column prop="name" label="渠道名称" />
        <!-- @NEW: 显示渠道类型 -->
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.type === 'dtalk' ? 'primary' : 'success'">
              {{ row.type === 'dtalk' ? '钉钉' : '飞书' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="access_token" label="AccessToken" min-width="200" show-overflow-tooltip />
        <el-table-column prop="has_secret" label="签名密钥" width="100">
          <template #default="{ row }">
            <el-tag :type="row.has_secret ? 'success' : 'info'" size="small">
              {{ row.has_secret ? '已设置' : '未设置' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_by" label="创建人" width="120" />
        <el-table-column prop="created_on" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_on) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleTest(row)">
              测试
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

    <!-- @MODIFIED: 新增/编辑渠道对话框 - 添加类型选择 -->
    <el-dialog
      v-model="dialog.visible"
      :title="dialog.title"
      width="500px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <!-- @NEW: 渠道类型选择 -->
        <el-form-item label="渠道类型" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio value="dtalk">
              <el-icon><Message /></el-icon>
              钉钉
            </el-radio>
            <el-radio value="feishu">
              <el-icon><Document /></el-icon>
              飞书
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="渠道名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入渠道名称" />
        </el-form-item>

        <!-- @MODIFIED: 根据类型显示不同的提示 -->
        <el-form-item label="AccessToken" prop="access_token">
          <el-input
            v-model="form.access_token"
            :placeholder="form.type === 'dtalk' ? '请输入钉钉机器人的AccessToken' : '请输入飞书机器人的AccessToken'"
            type="textarea"
            :rows="2"
          />
          <div class="form-tip" v-if="form.type === 'feishu'">
            <el-icon><InfoFilled /></el-icon>
            <span>例如：dae5d27b-325d-4f71-bf15-95d7bad4f3f6</span>
          </div>
        </el-form-item>

        <el-form-item label="签名密钥" prop="secret">
          <el-input
            v-model="form.secret"
            :placeholder="form.type === 'dtalk' ? '请输入钉钉机器人的Secret（可选）' : '请输入飞书机器人的Secret（可选）'"
            type="textarea"
            :rows="2"
          />
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>如果启用了签名验证，请输入密钥；否则留空</span>
          </div>
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
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Message, Document, InfoFilled } from '@element-plus/icons-vue'  // @NEW: 导入图标
import request from '../../utils/request'
import dayjs from 'dayjs'

const loading = ref(false)
const channels = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const dialog = reactive({
  visible: false,
  title: '新增渠道',
  type: 'add',
  id: '',
})

// @MODIFIED: 表单添加type字段
const form = reactive({
  type: 'dtalk',  // @NEW: 默认定钉
  name: '',
  access_token: '',
  secret: '',
})

// @MODIFIED: 动态验证规则
const rules = {
  type: [
    { required: true, message: '请选择渠道类型', trigger: 'change' },
  ],
  name: [
    { required: true, message: '请输入渠道名称', trigger: 'blur' },
  ],
  access_token: [
    { required: true, message: '请输入AccessToken', trigger: 'blur' },
  ],
  // secret 是可选字段，不需要验证规则
}

const formRef = ref()
const submitting = ref(false)

const fetchChannels = async () => {
  loading.value = true
  try {
    const res = await request.get('/sendways/list', {
      params: {
        page: page.value,
        page_size: pageSize.value,
      },
    })
    channels.value = res.data.list
    total.value = res.data.total
  } catch (error) {
    console.error('获取渠道列表失败:', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const handleSizeChange = (val) => {
  pageSize.value = val
  fetchChannels()
}

const handleCurrentChange = (val) => {
  page.value = val
  fetchChannels()
}

const handleAdd = () => {
  dialog.title = '新增渠道'
  dialog.type = 'add'
  dialog.id = ''
  form.type = 'dtalk'  // @NEW: 重置为钉钉
  dialog.visible = true
}

const handleEdit = (row) => {
  dialog.title = '编辑渠道'
  dialog.type = 'edit'
  dialog.id = row.id
  dialog.visible = true

  // @MODIFIED: 根据渠道类型解析auth数据
  form.type = row.type || 'dtalk'
  form.name = row.name
  form.access_token = row.access_token || ''
  form.secret = ''  // 不显示已设置的secret，出于安全考虑
}

const handleTest = async (row) => {
  try {
    await request.post(`/sendways/test?id=${row.id}`)
    ElMessage.success('测试消息发送成功')
  } catch (error) {
    console.error('测试失败:', error)
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确认删除渠道"${row.name}"吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await request.post(`/sendways/delete?id=${row.id}`)
      ElMessage.success('删除成功')
      fetchChannels()
    } catch (error) {
      console.error('删除失败:', error)
    }
  })
}

const handleDialogClose = () => {
  form.type = 'dtalk'
  form.name = ''
  form.access_token = ''
  form.secret = ''
  formRef.value?.clearValidate()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (dialog.type === 'add') {
          await request.post('/sendways/add', form)
          ElMessage.success('新增成功')
        } else {
          await request.post(`/sendways/edit?id=${dialog.id}`, form)
          ElMessage.success('编辑成功')
        }
        dialog.visible = false
        fetchChannels()
      } catch (error) {
        console.error('提交失败:', error)
      } finally {
        submitting.value = false
      }
    }
  })
}

// @NEW: 监听类型变化，更新placeholder等
watch(() => form.type, (newType) => {
  // 类型变化时的处理
})

onMounted(() => {
  fetchChannels()
})
</script>

<style scoped>
/* @NEW: 添加表单提示样式 */
.form-tip {
  margin-top: 5px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}

.form-tip .el-icon {
  font-size: 14px;
}

.channel-list {
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