import Vue from 'vue'
import App from './App.vue'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
import axios from 'axios'
import {marked} from 'marked'
import router from './router'

Vue.use(ElementUI)

Vue.config.productionTip = false

// 配置axios
axios.interceptors.request.use(
  config => {
    // 在发送请求之前做些什么
    return config
  },
  error => {
    // 对请求错误做些什么
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

axios.interceptors.response.use(
  response => {
    // 对响应数据做点什么
    return response
  },
  error => {
    // 对响应错误做点什么
    if (error.response) {
      console.error('响应错误:', error.response.status, error.response.data)
    } else if (error.request) {
      console.error('请求错误:', error.request)
    } else {
      console.error('错误:', error.message)
    }
    return Promise.reject(error)
  }
)

Vue.prototype.$http = axios

// 配置marked
marked.setOptions({
  breaks: true,
  sanitize: false,
  mangle: false,
  headerIds: false,
  gfm: true,
  smartLists: true
})
Vue.prototype.$marked = marked

new Vue({
  router,
  render: h => h(App)
}).$mount('#app')
