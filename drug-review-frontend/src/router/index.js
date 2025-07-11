import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)

import Layout from '@/layout'

export const constantRoutes = [
  {
    path: '/login',
    component: () => import('@/views/login/index'),
    hidden: true
  },
  {
    path: '/',
    component: Layout,
    redirect: '/knowledge/laws',
    children: [
      {
        path: 'knowledge',
        component: { render: h => h('router-view') },
        meta: { title: '知识库管理', icon: 'el-icon-s-management' },
        children: [
          {
            path: 'laws',
            name: 'Laws',
            component: () => import('@/views/knowledge/Laws'),
            meta: { title: '法律法规' }
          },
          {
            path: 'guidence',
            name: 'Guidence',
            component: () => import('@/views/knowledge/Guidence'),
            meta: { title: '指导原则' }
          },
          {
            path: 'regulations',
            name: 'Regulations',
            component: () => import('@/views/knowledge/Regulations'),
            meta: { title: '制度规范' }
          },
          {
            path: 'qa',
            name: 'QA',
            component: () => import('@/views/knowledge/QA'),
            meta: { title: '问答数据' }
          },
          {
            path: 'pharmacy',
            name: 'Pharmacy',
            component: () => import('@/views/knowledge/Pharmacy'),
            meta: { title: '药典数据' }
          },
          {
            path: 'rules',
            name: 'Rules',
            component: () => import('@/views/knowledge/Rules'),
            meta: { title: '审评规则' }
          }
        ]
      },
      {
        path: 'project',
        component: { render: h => h('router-view') },
        meta: { title: '审评项目管理', icon: 'el-icon-s-order' },
        children: [
          {
            path: 'documents',
            name: 'Documents',
            component: () => import('@/views/project/Documents'),
            meta: { title: '审评资料' }
          },
          {
            path: 'report/:id',
            name: 'Report',
            component: () => import('@/views/project/Report'),
            meta: { title: '审评报告' },
            hidden: true
          }
        ]
      }
    ]
  }
]

const createRouter = () => new Router({
  mode: 'history',
  scrollBehavior: () => ({ y: 0 }),
  routes: constantRoutes
})

const router = createRouter()

export function resetRouter() {
  const newRouter = createRouter()
  router.matcher = newRouter.matcher
}

export default router 