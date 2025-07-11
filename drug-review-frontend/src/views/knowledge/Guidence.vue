<template>
    <div class="knowledge-container">
      <el-container>
        <!-- 右侧内容 -->
        <el-main>
          <el-card class="knowledge-card">
            <div slot="header" class="card-header">
              <div class="header-left">
                <span class="page-title">指导原则</span>
                <el-tag type="info" class="total-count">共 {{ total }} 条记录</el-tag>
              </div>
              <div class="header-right">
                <el-button type="primary" icon="el-icon-plus" @click="handleAdd">新增知识</el-button>
                <el-button type="primary" icon="el-icon-refresh" @click="handleRefresh">刷新</el-button>
              </div>
            </div>
            <div class="table-scroll-area">
              <el-table
                :data="fileList"
                style="width:100%"
                border
                stripe
                highlight-current-row
                v-loading="loading"
              >
                <el-table-column prop="file_name" label="文件名" min-width="200" show-overflow-tooltip></el-table-column>
                <el-table-column prop="doc_classification" label="知识类型" width="120" align="center">
                  <template slot-scope="scope">
                    <el-tag>{{ scope.row.doc_classification }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="doc_id" label="文件id" width="180" align="center"></el-table-column>
                <el-table-column prop="create_time" label="上传时间" width="180" align="center"></el-table-column>
                <el-table-column prop="parse_status" label="解析状态" width="120" align="center">
                  <template slot-scope="scope">
                    <el-tag :type="getParseStatusType(scope.row.doc_id)">
                      {{ getParseStatusText(scope.row.doc_id) }}
                      <i v-if="parsingDocId === scope.row.doc_id" class="el-icon-loading"></i>
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="180" fixed="right" align="center">
                  <template slot-scope="scope">
                    <el-button
                      size="mini"
                      type="primary"
                      icon="el-icon-refresh"
                      :disabled="scope.row.parse_status === 1 || parsingDocId === scope.row.doc_id"
                      @click="handleParse(scope.row.doc_classification, scope.row.doc_id)"
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
            </div>
            <pagination
              :total="total"
              :page.sync="listQuery.page"
              :limit.sync="listQuery.limit"
              @pagination="getFileList"
              class="pagination"
            />
          </el-card>
        </el-main>
      </el-container>

      <!-- 新增知识对话框 -->
      <el-dialog
        title="新增知识"
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
          class="knowledge-form"
        >
          <el-form-item label="知识类型" prop="classification">
            <el-input 
              v-model="form.classification" 
              placeholder="指导原则"
              disabled
            ></el-input>
          </el-form-item>
          <el-form-item label="作用范围" prop="affect_range">
            <el-input v-model="form.affect_range" placeholder="请输入作用范围"></el-input>
          </el-form-item>
          <el-form-item label="文件" prop="file">
            <el-upload
              class="upload-demo"
              drag
              action="#"
              :auto-upload="false"
              :on-change="handleFileChange"
              :file-list="fileList"
            >
              <i class="el-icon-upload"></i>
              <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
            </el-upload>
          </el-form-item>
        </el-form>
        <div slot="footer" class="dialog-footer">
          <el-button @click="dialogVisible = false">取 消</el-button>
          <el-button type="primary" @click="handleUpload" :loading="uploading">上 传</el-button>
        </div>
      </el-dialog>
    </div>
  </template>

  <script>
  import Pagination from '@/components/Pagination'
  const CATEGORY = '指导原则'

  export default {
    name: 'Guidence',
    components: {
      Pagination
    },
    data() {
      return {
        loading: false,
        fileList: [],
        total: 0,
        listQuery: {
          page: 1,
          limit: 10
        },
        dialogVisible: false,
        form: {
          classification: CATEGORY,
          affect_range: '',
          file: null
        },
        rules: {
          affect_range: [
            { required: true, message: '请输入作用范围', trigger: 'blur' }
          ],
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
        parsingDocId: null
      }
    },
    created() {
      this.getFileList()
    },
    methods: {
      async getFileList() {
        this.loading = true
        try {
          const response = await this.$http.get(`/api/get_file_by_class/${CATEGORY}`, {
            params: {
              page: this.listQuery.page,
              limit: this.listQuery.limit
            }
          })
          if (response.data.code === 200) {
            this.fileList = response.data.data.list
            this.total = response.data.data.total
            console.log(this.fileList)
          }
        } catch (error) {
          console.error('获取文件列表失败:', error)
          this.$message.error('获取文件列表失败，请重试')
        } finally {
          this.loading = false
        }
      },
      handleRefresh() {
        this.getFileList()
      },
      handleAdd() {
        this.form = {
          classification: CATEGORY,
          affect_range: '',
          file: null
        }
        this.fileList = []
        this.uploadFile = null
        this.dialogVisible = true
        this.$nextTick(() => {
          this.$refs.form.clearValidate()
        })
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
            this.getFileList()
          }
        } catch (error) {
          if (error !== 'cancel') {
            console.error('删除失败:', error)
            this.$message.error('删除失败，请重试')
          }
        }
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
        formData.append('classification', this.form.classification)
        formData.append('affect_range', this.form.affect_range)
        
        try {
          const response = await this.$http.post('/api/upload_file', formData)
          if (response.data.code === 200) {
            this.$message.success('文件上传成功')
            this.dialogVisible = false

            // 设置正在解析的文件ID
            this.parsingDocId = response.data.data.doc_id
            await this.getFileList()

            // 等待1秒后开始解析
            setTimeout(() => {
              this.handleParse(this.form.classification, this.parsingDocId)
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
      async handleParse(docClassification, docId) {
        this.parsingDocId = docId
        try {
          const response = await this.$http.post(`/api/add_to_kd/${docId}`)
          if (response.data.code === 200) {
            this.$message.success('解析完成')
            // 解析完成后刷新列表
            await this.getFileList()
          } else {
            this.$message.error(response.data.msg || '解析失败')
          }
        } catch (error) {
          console.error('解析失败:', error)
          this.$message.error('解析失败，请重试')
        } finally {
          this.parsingDocId = null
        }
      },
      getParseStatusText(docId) {
        if (this.parsingDocId && this.parsingDocId === docId) {
          return '正在解析'
        }
        const file = this.fileList.find(f => f.doc_id === docId)
        if (file) {
          return file.parse_status === 1 ? '已解析' : '未解析'
        }
        return '未解析'
      },
      getParseStatusType(docId) {
        if (this.parsingDocId && this.parsingDocId === docId) {
          return 'warning'
        }
        const file = this.fileList.find(f => f.doc_id === docId)
        if (file) {
          return file.parse_status === 1 ? 'success' : 'info'
        }
        return 'info'
      }
    }
  }
  </script>
  
  <style lang="scss" scoped>
  .knowledge-container {
    height: 100vh;
    box-sizing: border-box;
    overflow: hidden;
  
    .el-container {
      height: 100%;
      overflow: hidden;
    }
  
    .el-aside {
      background-color: #fff;
      border-right: 1px solid #e6e6e6;
      height: 100%;
      overflow: hidden;
      
      .type-menu {
        border-right: none;
      }
    }
    
    .el-main {
      padding: 0px 10px 10px 10px;
      height: 100%;
      overflow: hidden;
  
      .knowledge-card {
        height: 100%;
        display: flex;
        flex-direction: column;
        overflow: hidden;
  
        .card-header {
          flex-shrink: 0;
        }
  
        .table-scroll-area {
          flex: 1 1 0;
          min-height: 0;
          overflow-y: auto;
          margin-bottom: 0;
        }
  
        .el-table {
          min-height: 100%;
        }
  
        .pagination {
          flex-shrink: 0;
          background: #fff;
          padding: 10px 0 0 0;
          text-align: right;
        }
      }
    }
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .header-left {
        display: flex;
        align-items: center;
        
        .page-title {
          font-size: 18px;
          font-weight: bold;
          margin-right: 10px;
        }
      }
    }
    
    .knowledge-form {
      .upload-demo {
        width: 100%;
      }
    }
  }
  </style> 