import router from './router'
import { Message } from 'element-ui'

const whiteList = ['/login'] // 白名单

router.beforeEach(async (to, from, next) => {
  const hasToken = localStorage.getItem('token')

  if (hasToken) {
    if (to.path === '/login') {
      // 已登录且要跳转的页面是登录页
      next({ path: '/' })
    } else {
      next()
    }
  } else {
    if (whiteList.indexOf(to.path) !== -1) {
      // 在免登录白名单中，直接进入
      next()
    } else {
      // 其他没有访问权限的页面将被重定向到登录页面
      Message.warning('请先登录')
      next(`/login?redirect=${to.path}`)
    }
  }
}) 