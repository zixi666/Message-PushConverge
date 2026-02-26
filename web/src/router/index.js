import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../components/Layout.vue'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import ChannelList from '../views/channels/ChannelList.vue'
import TaskList from '../views/tasks/TaskList.vue'
import TaskDetail from '../views/tasks/TaskDetail.vue'
import SendMessage from '../views/message/SendMessage.vue'
import LogList from '../views/logs/LogList.vue'
// 删除 Statistics 的导入

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: Dashboard,
      },
      {
        path: 'channels',
        name: 'Channels',
        component: ChannelList,
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: TaskList,
      },
      {
        path: 'tasks/:id',
        name: 'TaskDetail',
        component: TaskDetail,
      },
      {
        path: 'send',
        name: 'SendMessage',
        component: SendMessage,
      },
      {
        path: 'logs',
        name: 'Logs',
        component: LogList,
      },
      // 删除了 Statistics 路由
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router