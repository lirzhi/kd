<template>
  <div class="knowledge-container">
    <el-card class="upload-card">
      <div slot="header" class="card-header">
        <div class="header-left">
          <span class="page-title">文件上传</span>
          <el-tag type="info" size="small">支持PDF、Word格式</el-tag>
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
        <div class="el-upload__tip" slot="tip">支持PDF、Word格式文件</div>
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
          <span class="page-title">知识库管理</span>
          <el-tag type="info" class="total-count">共 {{ total }} 条记录</el-tag>
        </div>
        <div class="header-right">
          <el-button type="primary" icon="el-icon-refresh" @click="handleRefresh">刷新</el-button>
        </div>
      </div>

      <el-table
        :data="knowledgeList"
        style="width:100%"
        border
        stripe
        highlight-current-row
        v-loading="loading"
      >
        <el-table-column prop="doc_id" label="文档ID" width="180" show-overflow-tooltip></el-table-column>
        <el-table-column prop="file_name" label="文件名称" min-width="200" show-overflow-tooltip></el-table-column>
        <el-table-column prop="doc_type" label="文档类型" width="120" align="center"></el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="180" align="center"></el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template slot-scope="scope">
            <el-button
              size="mini"
              type="primary"
              icon="el-icon-view"
              @click="handleView(scope.row)"
            >查看</el-button>
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
        @pagination="getKnowledgeList"
      />
    </el-card>

    <el-dialog
      title="文档内容"
      :visible.sync="dialogVisible"
      width="70%"
      center
      :close-on-click-modal="false"
      class="content-dialog"
    >
      <div v-if="selectedDoc" class="doc-content">
        <div class="doc-header">
          <h3>{{ selectedDoc.file_name }}</h3>
          <el-tag size="small" type="info">{{ selectedDoc.doc_type }}</el-tag>
        </div>
        <div class="content-display markdown-body" v-html="formattedContent"></div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import Pagination from '@/components/Pagination'

export default {
  name: 'KnowledgeManagement',
  components: {
    Pagination
  },
  data() {
    return {
      knowledgeList: [],
      fileList: [],
      dialogVisible: false,
      selectedDoc: null,
      loading: false,
      total: 0,
      listQuery: {
        page: 1,
        limit: 10
      }
    }
  },
  computed: {
    formattedContent() {
      if (!this.selectedDoc) return ''
      return this.$marked.parse(this.selectedDoc.content || '')
    }
  },
  created() {
    this.getKnowledgeList()
  },
  methods: {
    beforeUpload(file) {
      const isValidType = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type)
      if (!isValidType) {
        this.$message.error('只能上传PDF或Word文件!')
      }
      return isValidType
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
      formData.append('classification', 'knowledge')
      formData.append('affect_range', '')
      try {
        const response = await this.$http.post('/api/upload_file', formData)
        if (response.data.code === 200) {
          this.$message.success('上传成功')
          this.fileList = []
          this.getKnowledgeList()
        } else {
          this.$message.error(response.data.msg || '上传失败')
        }
      } catch (error) {
        console.error('上传文件失败:', error)
        this.$message.error('上传文件失败，请重试')
      }
    },
    async getKnowledgeList() {
      this.loading = true
      try {
        const response = await this.$http.get('/api/get_file_classification', {
          params: {
            page: this.listQuery.page,
            limit: this.listQuery.limit
          }
        })
        if (response.data.code === 200) {
          this.knowledgeList = response.data.data.list
          this.total = response.data.data.total
        }
      } catch (error) {
        console.error('获取知识库列表失败:', error)
        this.$message.error('获取知识库列表失败，请重试')
      } finally {
        this.loading = false
      }
    },
    handleRefresh() {
      this.getKnowledgeList()
    },
    handleView(doc) {
      this.selectedDoc = doc
      this.dialogVisible = true
    },
    async handleDelete(docId) {
      try {
        await this.$confirm('确认删除该文档吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const response = await this.$http.post(`/api/delete_file/${docId}`)
        if (response.data.code === 200) {
          this.$message.success('删除成功')
          this.getKnowledgeList()
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
.knowledge-container {
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

.doc-content {
  padding: 20px;
}

.doc-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.doc-header h3 {
  margin: 0;
  font-size: 18px;
  color: #1f2f3d;
}

.content-display {
  margin-top: 20px;
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  max-height: 60vh;
  overflow-y: auto;
  background-color: #fafafa;
}

/* 自定义滚动条样式 */
.content-display::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.content-display::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

.content-display::-webkit-scrollbar-track {
  background: #f0f0f0;
}

/* Markdown样式 */
.markdown-body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  line-height: 1.6;
  color: #24292e;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body p {
  margin-top: 0;
  margin-bottom: 16px;
}

.markdown-body code {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 3px;
}

.markdown-body pre {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 3px;
}

.markdown-body table {
  display: block;
  width: 100%;
  overflow: auto;
  border-spacing: 0;
  border-collapse: collapse;
}

.markdown-body table th,
.markdown-body table td {
  padding: 6px 13px;
  border: 1px solid #dfe2e5;
}

.markdown-body table tr {
  background-color: #fff;
  border-top: 1px solid #c6cbd1;
}

.markdown-body table tr:nth-child(2n) {
  background-color: #f6f8fa;
}
</style> 