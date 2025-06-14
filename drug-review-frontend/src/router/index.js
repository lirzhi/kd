import Vue from 'vue'
import VueRouter from 'vue-router'
import Main from '../views/Main.vue'
import ReportManagement from '../views/Report.vue'
import RequirementsManagement from '../views/Requirements.vue'
import CTD from '../views/CTD.vue'
import KnowledgeManagement from '../views/Knowledge.vue'

// 确保VueRouter只初始化一次
if (!Vue.prototype.$router) {
  Vue.use(VueRouter)
}

let OriginPush = VueRouter.prototype.push;
let OriginReplace = VueRouter.prototype.replace;
VueRouter.prototype.push = function (location, resolve, reject) {
    if (resolve && reject) {
        OriginPush.call(this, location, resolve, reject);
    }
    else {
        OriginPush.call(this, location, () => { }, () => { });
    }
}
VueRouter.prototype.replace = function (location, resolve, reject) {
    if (resolve && reject) {
        OriginReplace.call(this, location, resolve, reject);
    }
    else {
        OriginReplace.call(this, location, () => { }, () => { });
    }
}

const routes = [
  {
    path: '/',
    component: Main,
    redirect: '/report',
    children: [
      {
        path: '/report',
        name: 'ReportManagement',
        component: ReportManagement,
        meta: { title: '审评报告' }
      },
      {
        path: '/requirements',
        name: 'RequirementsManagement',
        component: RequirementsManagement,
        meta: { title: '审评要求' }
      },
      {
        path: '/ctd',
        name: 'CTD',
        component: CTD,
        meta: { title: 'CTD管理' }
      },
      {
        path: '/knowledge',
        name: 'KnowledgeManagement',
        component: KnowledgeManagement,
        meta: { title: '知识库管理' }
      }
    ]
  }
]

const router = new VueRouter({
  routes
})

export default router 