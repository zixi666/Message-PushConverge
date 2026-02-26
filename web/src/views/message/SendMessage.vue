<template>
  <div class="send-message">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>发送消息</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="send-form"
      >
        <!-- 选择任务 -->
        <el-form-item label="选择任务" prop="task_id">
          <el-select
            v-model="form.task_id"
            placeholder="请选择发送任务"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="item in tasks"
              :key="item.id"
              :label="`${item.name} (${item.id})`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>

        <!-- @MODIFIED: 简化标题字段，只有文本消息，不需要判断 -->
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入消息标题（可选）" />
        </el-form-item>

        <!-- @MODIFIED: 只保留文本内容输入框 -->
        <el-form-item label="内容" prop="text">
          <el-input
            v-model="form.text"
            type="textarea"
            :rows="8"
            placeholder="请输入要发送的文本内容"
          />
        </el-form-item>

        <!-- @REMOVED: 删除所有其他消息类型的模板 -->
        <!-- @功能暂时保留（可选，如果后端还支持@功能） -->
        <el-divider v-if="showAt">@ 设置</el-divider>

        <el-form-item v-if="showAt" label="@手机号">
          <el-select
            v-model="form.at_mobiles"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入手机号后回车"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item v-if="showAt" label="@用户ID">
          <el-select
            v-model="form.at_user_ids"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入用户ID后回车"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item v-if="showAt" label="@所有人">
          <el-switch v-model="form.is_at_all" />
        </el-form-item>

        <!-- 发送按钮 -->
        <el-form-item>
          <el-button
            type="primary"
            @click="handleSend"
            :loading="sending"
            size="large"
          >
            发送消息
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 发送结果 -->
      <el-card v-if="result.show" class="result-card" shadow="never">
        <template #header>
          <div class="result-header">
            <span>发送结果</span>
            <el-tag :type="result.status === 1 ? 'success' : 'danger'">
              {{ result.status === 1 ? '发送成功' : '部分失败' }}
            </el-tag>
          </div>
        </template>
        <pre class="result-log">{{ result.log }}</pre>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../../utils/request'

const tasks = ref([])

const form = reactive({
  task_id: '',
  title: '',
  text: '',
  // @REMOVED: 删除所有其他消息类型相关的字段
  // 保留@功能相关字段（如果后端还支持）
  at_mobiles: [],
  at_user_ids: [],
  is_at_all: false,
})

// @MODIFIED: 简化验证规则
const rules = {
  task_id: [
    { required: true, message: '请选择发送任务', trigger: 'change' },
  ],
  text: [
    { required: true, message: '请输入发送内容', trigger: 'blur' },
    { min: 1, max: 2000, message: '内容长度在1-2000个字符之间', trigger: 'blur' },
  ],
  // title 是可选字段，不需要验证
}

// @MODIFIED: 判断是否显示@功能（可以根据后端是否支持来决定）
const showAt = computed(() => {
  // 如果后端还支持@功能，这里返回true，否则返回false
  return false  // 暂时关闭@功能，因为后端已经简化
})

const formRef = ref()
const sending = ref(false)

const result = reactive({
  show: false,
  status: 0,
  log: '',
})

// 获取任务列表
const fetchTasks = async () => {
  try {
    const res = await request.get('/sendtasks/list?page=1&page_size=100')
    tasks.value = res.data.list
  } catch (error) {
    console.error('获取任务列表失败:', error)
  }
}

// 发送消息
const handleSend = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      sending.value = true
      try {
        // @MODIFIED: 只发送必要的字段
        const sendData = {
          task_id: form.task_id,
          title: form.title,
          text: form.text,
          // 如果后端还支持@功能，可以取消下面的注释
          // at_mobiles: form.at_mobiles,
          // at_user_ids: form.at_user_ids,
          // is_at_all: form.is_at_all,
        }

        const res = await request.post('/message/send', sendData)
        result.show = true
        result.status = res.data.status
        result.log = res.data.log

        if (res.data.status === 1) {
          ElMessage.success('发送成功')
        } else {
          ElMessage.warning('发送完成，但有失败记录')
        }
      } catch (error) {
        console.error('发送失败:', error)
      } finally {
        sending.value = false
      }
    }
  })
}

// 重置表单
const resetForm = () => {
  form.task_id = ''
  form.title = ''
  form.text = ''
  form.at_mobiles = []
  form.at_user_ids = []
  form.is_at_all = false
  result.show = false
  formRef.value?.clearValidate()
}

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.send-message {
  padding: 0;
}

.send-form {
  max-width: 800px;
}

.result-card {
  margin-top: 20px;
  background-color: #f5f7fa;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-log {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.5;
  max-height: 300px;
  overflow: auto;
}
</style>