<template>
  <div class="ctd-container">
    <el-card class="upload-card">
      <div slot="header" class="card-header">
        <div class="header-left">
          <span class="page-title">文件上传</span>
          <el-tag type="info" size="small">支持PDF格式</el-tag>
        </div>
      </div>
      <el-upload
        class="upload-area"
        ref="upload"
        action=""
        :auto-upload="false"
        :file-list="fileList"
        :before-upload="beforeUpload"
        :on-change="handleChange"
        drag
      >
        <i class="el-icon-upload"></i>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <div class="el-upload__tip" slot="tip">只能上传PDF文件</div>
      </el-upload>
      <div class="upload-actions">
        <el-button type="primary" icon="el-icon-upload2" @click="submitUpload" :disabled="fileList.length === 0">
          上传到服务器
        </el-button>
      </div>
    </el-card>

    <el-card class="list-card">
      <div slot="header" class="card-header">
        <div class="header-left">
          <span class="page-title">审评文件列表</span>
          <el-tag type="info" class="total-count">共 {{ total }} 个文件</el-tag>
        </div>
        <div class="header-right">
          <el-button type="primary" icon="el-icon-refresh" @click="handleECTDFilter">刷新</el-button>
        </div>
      </div>

      <el-table
        :data="filteredECTDList"
        style="width:100%"
        border
        stripe
        highlight-current-row
        v-loading="loading"
      >
        <el-table-column prop="doc_classification" label="文档类别" width="120" align="center"></el-table-column>
        <el-table-column prop="doc_id" label="文档ID" width="180" show-overflow-tooltip></el-table-column>
        <el-table-column prop="file_name" label="文件名称" min-width="200" show-overflow-tooltip></el-table-column>
        <el-table-column prop="parse_status" label="解析状态" width="100" align="center">
          <template slot-scope="scope">
            <el-tag :type="scope.row.parse_status ? 'success' : 'info'" size="small">
              {{ scope.row.parse_status ? '已解析' : '未解析' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right" align="center">
          <template slot-scope="scope">
            <el-button
              size="mini"
              type="primary"
              icon="el-icon-s-operation"
              @click="handleParse(scope.row.doc_classification, scope.row.doc_id)"
              :disabled="!!scope.row.parse_status"
            >解析</el-button>
            <el-button
              size="mini"
              type="danger"
              icon="el-icon-delete"
              @click="handleDelete(scope.row.doc_id)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <pagination
        :total="total"
        :page.sync="listQuery.page"
        :limit.sync="listQuery.limit"
        @pagination="handleECTDFilter"
      />
    </el-card>

    <el-dialog
      title="解析进度"
      :visible.sync="showParseProgress"
      width="30%"
      center
      :close-on-click-modal="false"
      :show-close="false"
      class="progress-dialog"
    >
      <el-progress
        :percentage="parseProgress"
        :status="parseProgress === 100 ? 'success' : undefined"
        :stroke-width="20"
      ></el-progress>
      <div class="progress-text">{{ parseProgress }}%</div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="cancelParse">取消</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import Pagination from '@/components/Pagination'
import { io } from 'socket.io-client'

export default {
  name: 'CTD',
  components: {
    Pagination
  },
  data() {
    return {
      fileList: [],
      filteredECTDList: [],
      showParseProgress: false,
      parseProgress: 0,
      abortController: null,
      loading: false,
      total: 0,
      listQuery: {
        page: 1,
        limit: 10
      },
      socket: null
    }
  },
  created() {
    this.handleECTDFilter()
    this.initSocket()
  },
  beforeDestroy() {
    if (this.socket) {
      this.socket.disconnect()
    }
  },
  methods: {
    initSocket() {
      this.socket = io('/', {
        path: '/socket.io',
        transports: ['websocket', 'polling']
      })

      this.socket.on('connect', () => {
        console.log('WebSocket connected')
      })

      this.socket.on('disconnect', () => {
        console.log('WebSocket disconnected')
      })

      this.socket.on('parse_progress', (data) => {
        if (data.cur_section && data.total_section) {
          this.parseProgress = Math.round(
            (data.cur_section / data.total_section) * 100
          )
        }
      })
    },
    beforeUpload(file) {
      const isPDF = file.type === 'application/pdf'
      if (!isPDF) {
        this.$message.error('只能上传PDF文件!')
      }
      return isPDF
    },
    handleChange(file, fileList) {
      this.fileList = fileList
    },
    async submitUpload() {
      if (this.fileList.length === 0) {
        this.$message.warning('请选择要上传的文件')
        return
      }
      const formData = new FormData()
      formData.append('file', this.fileList[0].raw)
      formData.append('classification', 'eCTD')
      formData.append('affect_range', '')
      try {
        const response = await this.$http.post('/api/upload_file', formData)
        if (response.data.code === 200) {
          this.$message.success('上传成功')
          this.fileList = []
          this.handleECTDFilter()
        } else {
          this.$message.error(response.data.msg || '上传失败')
        }
      } catch (error) {
        console.error('上传文件失败:', error)
        this.$message.error('上传文件失败，请重试')
      }
    },
    async handleECTDFilter() {
      this.loading = true
      try {
        const response = await this.$http.get('/api/get_file_by_class/eCTD', {
          params: {
            page: this.listQuery.page,
            limit: this.listQuery.limit
          }
        })
        if (response.data.code === 200) {
          this.filteredECTDList = response.data.data.list.map(item => ({
            ...item,
            doc_classification: "eCTD"
          }))
          this.total = response.data.data.total
        }
      } catch (error) {
        console.error('获取CTD列表失败:', error)
        this.$message.error('获取CTD列表失败，请重试')
      } finally {
        this.loading = false
      }
    },
    async handleParse(docClassification, docId) {
      this.showParseProgress = true
      this.parseProgress = 0
      this.abortController = new AbortController()

      try {
        const response = await fetch(
          `/api/parse_ectd_stream/${docId}`,
          {
            method: 'GET',
            signal: this.abortController.signal
          }
        )

        if (!response.ok) {
          throw new Error(`HTTP错误! 状态码: ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder('utf-8')
        let buffer = ''
        let isReading = true

        while (isReading) {
          const { done, value } = await reader.read()
          if (done) {
            isReading = false
            break
          }

          buffer += decoder.decode(value, { stream: true })
          
          const lines = buffer.split('\n')
          for (let i = 0; i < lines.length - 1; i++) {
            const line = lines[i].trim()
            if (!line) continue

            try {
              const data = JSON.parse(line)
              console.log('流数据:', data)

              if (data.cur_section && data.total_section) {
                this.parseProgress = Math.round(
                  (data.cur_section / data.total_section) * 100
                )
              }

              if (data.error) {
                throw new Error(data.error)
              }
            } catch (err) {
              console.error('数据解析错误:', err)
              this.$message.error(`解析失败: ${err.message}`)
              this.abortController.abort()
              isReading = false
            }
          }
          buffer = lines[lines.length - 1]
        }

        this.$message.success('解析完成')
        this.handleECTDFilter()
      } catch (err) {
        if (err.name !== 'AbortError') {
          this.$message.error(`请求失败: ${err.message}`)
        }
      } finally {
        this.showParseProgress = false
        this.parseProgress = 0
        this.abortController = null
      }
    },
    cancelParse() {
      if (this.abortController) {
        this.abortController.abort()
      }
    },
    async handleDelete(docId) {
      try {
        await this.$confirm('确认删除该文件吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const response = await this.$http.post(`/api/delete_file/${docId}`)
        if (response.data.code === 200) {
          this.$message.success('删除成功')
          this.handleECTDFilter()
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除失败:', error)
          this.$message.error('删除失败，请重试')
        }
      }
    }
  }
}
</script>

<style scoped>
.ctd-container {
  padding: 20px;
  height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.upload-card,
.list-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2f3d;
}

.total-count {
  font-size: 13px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.upload-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.el-upload {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.el-upload-dragger {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.el-upload__text {
  margin-top: 16px;
  color: #606266;
}

.el-upload__text em {
  color: #409EFF;
  font-style: normal;
}

.upload-actions {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.el-table {
  margin-top: 16px;
  flex: 1;
}

.progress-dialog {
  text-align: center;
}

.progress-text {
  margin-top: 16px;
  font-size: 16px;
  color: #606266;
}

/* 自定义滚动条样式 */
.el-table__body-wrapper::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.el-table__body-wrapper::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

.el-table__body-wrapper::-webkit-scrollbar-track {
  background: #f0f0f0;
}
</style> 