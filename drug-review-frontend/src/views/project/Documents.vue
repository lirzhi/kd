<template>
  <div class="ctd-container">
    <el-card class="list-card">
      <div slot="header" class="card-header">
        <div class="header-left">
          <span class="page-title">审评项目列表</span>
          <el-tag type="info" class="total-count">共 {{ total }} 个文件</el-tag>
        </div>
        <div class="header-right">
          <el-button type="primary" icon="el-icon-plus" @click="handleAdd">新增项目</el-button>
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
        <el-table-column prop="file_name" label="文档名称" min-width="200" show-overflow-tooltip></el-table-column>
        <el-table-column prop="parse_status" label="解析状态" width="120" align="center">
          <template slot-scope="scope">
            <el-tag :type="getParseStatusType(scope.row.doc_id)">
              {{ getParseStatusText(scope.row.doc_id) }}
              <span v-if="parsingDocId === scope.row.doc_id">
                ({{ parseProgress }}%)
                <i class="el-icon-loading"></i>
              </span>
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="review_status" label="审评状态" width="100" align="center">
          <template slot-scope="scope">
            <el-tag :type="scope.row.review_status === 1 ? 'success' : 'info'">
              {{ scope.row.review_status === 1 ? '已审评' : '未审评' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="350" fixed="right" align="center">
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
              :type="scope.row.review_status === 1 ? 'success' : 'primary'"
              :icon="scope.row.review_status === 1 ? 'el-icon-view' : 'el-icon-edit'"
              @click="handleReport(scope.row)"
            >
              {{ scope.row.review_status === 1 ? '查看报告' : '生成报告' }}
            </el-button>
            
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
      title="新增资料"
      :visible.sync="dialogVisible"
      width="50%"
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
    >
      <el-form
        ref="form"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="upload-form"
      >
        <el-form-item label="文件" prop="file">
          <el-upload
            class="upload-demo"
            drag
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            :before-upload="beforeUpload"
          >
            <i class="el-icon-upload"></i>
            <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
            <div class="el-upload__tip" slot="tip">只能上传PDF文件</div>
          </el-upload>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading">上 传</el-button>
      </div>
    </el-dialog>

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

export default {
  name: 'Documents',
  components: {
    Pagination
  },
  data() {
    return {
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
      dialogVisible: false,
      form: {
        file: null
      },
      rules: {
        file: [
          { 
            required: true, 
            message: '请上传文件', 
            trigger: 'change',
            validator: (rule, value, callback) => {
              if (!this.uploadFile) {
                callback(new Error('请上传文件'))
              } else {
                callback()
              }
            }
          }
        ]
      },
      uploading: false,
      uploadFile: null,
      parsingDocId: null,
      fileList: []
    }
  },
  created() {
    this.handleECTDFilter()
  },
  methods: {
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
      this.parsingDocId = docId
      this.parseProgress = 0
      this.abortController = new AbortController()

      try {
        const response = await fetch(
          `/api/parse_ectd_stream/${docId}`,
          {
            method: 'GET',
            signal: this.abortController.signal,
            headers: {
              'Accept': 'text/event-stream',
              'Cache-Control': 'no-cache',
              'Connection': 'keep-alive'
            }
          }
        )

        if (!response.ok) {
          throw new Error(`HTTP错误! 状态码: ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder('utf-8')
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) {
            console.log('流读取完成')
            break
          }

          buffer += decoder.decode(value, { stream: true })
          
          const lines = buffer.split('\n')
          for (let i = 0; i < lines.length - 1; i++) {
            const line = lines[i].trim()
            if (!line) continue

            try {
              const data = JSON.parse(line)
              console.log('解析数据:', data)

              if (data.cur_section && data.total_section) {
                // 更新进度
                this.parseProgress = Math.round(
                  (data.cur_section / data.total_section) * 100
                )
                console.log('当前进度:', this.parseProgress)
              }

              if (data.error) {
                throw new Error(data.error)
              }
            } catch (err) {
              console.error('数据解析错误:', err)
              this.$message.error(`解析失败: ${err.message}`)
              this.abortController.abort()
            }
          }
          buffer = lines[lines.length - 1]
        }

        // 解析完成后刷新列表
        this.$message.success('解析完成')
        await this.handleECTDFilter()
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('解析失败:', err)
          this.$message.error(`解析失败: ${err.message}`)
        }
      } finally {
        this.parsingDocId = null
        this.parseProgress = 0
        this.abortController = null
        // 确保在完成后刷新列表
        await this.handleECTDFilter()
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
    },
    handleAdd() {
      this.form = {
        file: null
      }
      this.fileList = []
      this.uploadFile = null
      this.dialogVisible = true
      this.$nextTick(() => {
        this.$refs.form.clearValidate()
      })
    },
    handleFileChange(file) {
      this.uploadFile = file.raw
      this.fileList = [file]
      this.form.file = file.raw
      this.$refs.form.validateField('file')
    },
    handleDialogClosed() {
      this.$refs.form.resetFields()
      this.fileList = []
      this.uploadFile = null
      this.uploading = false
    },
    async handleUpload() {
      if (!this.uploadFile) {
        this.$message.warning('请选择要上传的文件')
        return
      }
      
      try {
        const valid = await this.$refs.form.validate()
        if (!valid) {
          return
        }
      } catch (error) {
        console.error('表单验证失败:', error)
        return
      }
      
      this.uploading = true
      const formData = new FormData()
      formData.append('file', this.uploadFile)
      formData.append('classification', 'eCTD')
      formData.append('affect_range', '')
      
      try {
        const response = await this.$http.post('/api/upload_file', formData)
        if (response.data.code === 200) {
          this.$message.success('文件上传成功')
          this.dialogVisible = false
          
          this.parsingDocId = response.data.data.doc_id
          
          await this.handleECTDFilter()
          
          setTimeout(() => {
            this.handleParse('eCTD', this.parsingDocId)
          }, 1000)
        } else {
          this.$message.error(response.data.msg || '文件上传失败')
        }
      } catch (error) {
        console.error('文件上传失败:', error)
        this.$message.error('文件上传失败，请重试')
      } finally {
        this.uploading = false
      }
    },
    getParseStatusText(docId) {
      if (this.parsingDocId && this.parsingDocId === docId) {
        return '正在解析'
      }
      const file = this.filteredECTDList.find(f => f.doc_id === docId)
      if (file) {
        return file.parse_status ? '已解析' : '未解析'
      }
      return '未解析'
    },
    getParseStatusType(docId) {
      if (this.parsingDocId && this.parsingDocId === docId) {
        return 'warning'
      }
      const file = this.filteredECTDList.find(f => f.doc_id === docId)
      if (file) {
        return file.parse_status ? 'success' : 'info'
      }
      return 'info'
    },
    beforeUpload(file) {
      const isPDF = file.type === 'application/pdf'
      if (!isPDF) {
        this.$message.error('只能上传PDF文件!')
      }
      return isPDF
    },
    handleReport(row) {
      this.$router.push({
        name: 'Report',
        params: { id: row.doc_id },
        query: { 
          fileName: row.file_name,
          reviewStatus: row.review_status
        }
      })
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

.upload-form {
  .upload-demo {
    width: 100%;
  }
}
</style> 