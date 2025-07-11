<template>
  <div class="report-container">
    <el-breadcrumb separator="/" class="breadcrumb">
      <el-breadcrumb-item :to="{ path: '/project/documents' }">审评项目</el-breadcrumb-item>
      <el-breadcrumb-item>{{ documentInfo.file_name }}审评报告</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card class="report-card">
      <div slot="header" class="card-header">
        <div class="header-left">
          <span class="page-title">{{ documentInfo.file_name }}</span>
          <el-tag type="info" size="small">文档ID: {{ documentInfo.doc_id }}</el-tag>
        </div>
        <div class="header-right">
          <!-- <el-button 
            type="warning" 
            icon="el-icon-check" 
            @click="handleConfirmReview"
            style="margin-right: 8px;"
          >确定审评</el-button> -->
          <el-dropdown @command="handleExport">
            <el-button type="primary" icon="el-icon-document">
              导出报告<i class="el-icon-arrow-down el-icon--right"></i>
            </el-button>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item command="word">导出Word</el-dropdown-item>
              <!-- <el-dropdown-item command="pdf" disabled>导出PDF（暂不支持）</el-dropdown-item> -->
            </el-dropdown-menu>
          </el-dropdown>
        </div>
      </div>

      <div class="section-selector">
        <el-select
          v-model="selectedSection"
          placeholder="请选择章节"
          clearable
          filterable
          style="width: 300px"
          @change="handleSectionChange"
        >
          <el-option label="全部" value="all" />
          <el-option
            v-for="section in sectionOptions"
            :key="section"
            :label="section"
            :value="section"
          />
        </el-select>
        
        <template v-if="!isReviewed">
          <el-button
            type="success"
            icon="el-icon-document"
            :loading="generatingFull"
            @click="handleGenerateFullReport"
          >生成报告</el-button>
        </template>
        <template v-else>
          <el-button
            v-if="selectedSection === 'all'"
            type="success"
            icon="el-icon-refresh"
            :loading="generatingFull"
            @click="handleGenerateFullReport"
          >重新生成完整报告</el-button>
          <el-button
            v-if="selectedSection !== 'all'"
            type="primary"
            icon="el-icon-refresh"
            :loading="generating"
            @click="handleGenerateSectionReport"
          >重新生成章节结论</el-button>
        </template>
      </div>

      <el-progress 
        v-if="generatingFull" 
        :percentage="reportProgress" 
        :status="reportStatus === 'failed' ? 'exception' : ''"
      ></el-progress>

      <div class="content-container">
        <div class="original-content">
          <div class="content-header">
            <h3>原始资料</h3>
          </div>
          <div class="content-body" style="padding:0;">
            <iframe
              v-if="pdfUrl"
              :src="pdfUrl"
              width="100%"
              height="600px"
              style="border:none;"
            ></iframe>
            <div v-else style="text-align:center;color:#aaa;padding:40px 0;">暂无PDF文件</div>
          </div>
        </div>
        <div class="report-content">
          <div class="content-header">
            <h3>审评报告</h3>
            <div class="header-actions">
              <el-button
                v-if="!isEditing"
                type="text"
                icon="el-icon-edit"
                @click="handleEdit"
              >编辑</el-button>
              <el-button
                v-if="isEditing"
                type="text"
                icon="el-icon-check"
                @click="handleSave"
              >保存</el-button>
            </div>
          </div>
          <div class="content-body">
            <div v-if="isEditing" class="edit-area">
              <el-input
                type="textarea"
                v-model="reportContent"
                :rows="20"
                resize="none"
              />
            </div>
            <div v-else class="markdown-body" v-html="formattedReportContent"></div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'ReportGeneration',
  data() {
    return {
      documentInfo: {},
      selectedSection: 'all',
      sectionOptions: [],
      originalContent: '',
      reportContent: '',
      generating: false,
      generatingFull: false,
      isReviewed: false,
      isEditing: false,
      originalReportContent: '',
      pdfUrl: '',
      reportProgress: 0,
      reportStatus: 'pending',
      statusCheckInterval: null
    }
  },
  computed: {
    formattedOriginalContent() {
      if (!this.originalContent) return ''
      
      // 如果内容是JSON字符串，尝试解析
      try {
        const content = typeof this.originalContent === 'string' 
          ? JSON.parse(this.originalContent) 
          : this.originalContent
        
        // 如果内容是数组，转换为字符串
        if (Array.isArray(content)) {
          return this.$marked.parse(content.join('\n\n'))
        }
        
        // 如果内容是对象，获取content字段
        if (typeof content === 'object' && content.content) {
          return this.$marked.parse(content.content)
        }
        
        // 其他情况直接解析
        return this.$marked.parse(this.originalContent)
      } catch (e) {
        // 如果解析失败，直接返回原始内容
        return this.$marked.parse(this.originalContent)
      }
    },
    formattedReportContent() {
      return this.$marked.parse(this.reportContent || '')
    }
  },
  created() {
    this.getSectionList(this.$route.params.id)
    this.getDocumentInfo()
    this.isReviewed = this.$route.query.reviewStatus == 1
    this.getFullReport()
    this.getOriginalFileContent()
    this.setPdfUrl()
  },
  methods: {
    async getDocumentInfo() {
      try {
        // 获取文档基本信息
        const response = await this.$http.post('/api/get_document_info', {
          doc_id: this.$route.params.id
        })
        
        if (response.data.code === 200) {
          this.documentInfo = response.data.data
          // 获取章节列表
        }
      } catch (error) {
        console.error('获取文档信息失败:', error)
        this.$message.error('获取文档信息失败，请重试')
      }
    },
    async getSectionList(docId) {
      try {
        const response = await this.$http.post(`/api/get_ectd_sections/${docId}`)
        if (response.data.code === 200) {
          this.sectionOptions = response.data.data
        }
      } catch (error) {
        console.error('获取章节列表失败:', error)
        this.$message.error('获取章节列表失败，请重试')
      }
    },
    
    async handleSectionChange() {
      if (!this.selectedSection) {
        this.reportContent = ''
        return
      }

      try {
        if (this.selectedSection === 'all') {
          await this.getFullReport()
        } else {
          await this.getSectionReport(this.selectedSection)
        }
      } catch (error) {
        console.error('获取内容失败:', error)
        this.$message.error('获取内容失败，请重试')
      }
    },
    async handleGenerateSectionReport() {
      if (!this.selectedSection) {
        this.$message.warning('请选择章节')
        return
      }

      this.generating = true
      try {
        const response = await this.$http.post('/api/review_section', {
          doc_id: this.$route.params.id,
          section_id: this.selectedSection,
          content: this.originalContent
        })
        
        if (response.data.code === 200) {
          this.reportContent = response.data.data.report_content
          // 更新审评状态
          await this.$http.post('/api/update_review_status', {
            doc_id: this.$route.params.id,
            status: 1
          })
          this.$message.success('章节报告生成成功')
        }
      } catch (error) {
        console.error('生成章节报告失败:', error)
        this.$message.error('生成章节报告失败，请重试')
      } finally {
        this.generating = false
      }
    },
    async handleGenerateFullReport() {
      this.generatingFull = true
      this.reportProgress = 0
      this.reportStatus = 'pending'
      
      try {
        // 开始生成报告
        const response = await this.$http.post('/api/review_all_section', {
          doc_id: this.$route.params.id
        })
        
        if (response.data.code === 200) {
          // 开始轮询状态
          this.startStatusCheck()
        }
      } catch (error) {
        console.error('生成完整报告失败:', error)
        this.$message.error('生成完整报告失败，请重试')
        this.generatingFull = false
      }
    },
    async handleExport(type) {
      if (type !== 'word') {
        this.$message.warning('当前仅支持Word导出');
        return;
      }
      try {
        const response = await this.$http.post('/api/export_report', {
          doc_id: this.$route.params.id,
          export_type: type
        }, { 
          responseType: 'blob',
          timeout: 300000 // 设置5分钟超时
        })
        
        // 从响应头中获取文件名
        const contentDisposition = response.headers['content-disposition']
        let filename = `${this.documentInfo.file_name}_报告.${type === 'word' ? 'docx' : 'pdf'}`
        
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename="(.+)"/)
          if (filenameMatch) {
            filename = decodeURIComponent(filenameMatch[1])
          }
        }
        
        // 根据类型设置正确的MIME类型
        const mimeType = type === 'word' 
          ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
          : 'application/pdf'
        
        // 检查响应数据
        if (!response.data || response.data.size === 0) {
          throw new Error('导出文件为空')
        }
        
        const blob = new Blob([response.data], { type: mimeType })
        
        // 创建下载链接
        const link = document.createElement('a')
        link.href = window.URL.createObjectURL(blob)
        link.download = filename
        
        // 触发下载
        document.body.appendChild(link)
        link.click()
        
        // 清理
        document.body.removeChild(link)
        window.URL.revokeObjectURL(link.href)
        
        this.$message.success(`${type === 'word' ? 'Word' : 'PDF'}报告导出成功`)
      } catch (error) {
        if (error.response && error.response.data) {
          // 尝试解析后端返回的json
          const reader = new FileReader();
          reader.onload = () => {
            try {
              const res = JSON.parse(reader.result);
              this.$message.error(res.message || '导出报告失败，请重试');
            } catch {
              this.$message.error('导出报告失败，请重试');
            }
          };
          reader.readAsText(error.response.data);
        } else {
          this.$message.error(`导出报告失败: ${error.message || '请重试'}`);
        }
      }
    },
    async getFullReport() {
      try {
        const response = await this.$http.post('/api/get_report', {
          doc_id: this.$route.params.id
        })
        
        if (response.data.code === 200) {
          this.reportContent = response.data.data.content
        }
      } catch (error) {
        console.error('获取完整报告失败:', error)
        this.$message.error('获取完整报告失败，请重试')
      }
    },
    async getSectionReport(sectionId) {
      try {
        const response = await this.$http.post('/api/get_report_by_section', {
          doc_id: this.$route.params.id,
          section_id: sectionId
        })
        
        if (response.data.code === 200) {
          this.reportContent = response.data.data
        }
      } catch (error) {
        console.error('获取章节报告失败:', error)
        this.$message.error('获取章节报告失败，请重试')
      }
    },
    async handleViewReport() {
      if (this.selectedSection === 'all') {
        await this.getFullReport()
      } else {
        await this.getSectionReport(this.selectedSection)
      }
    },
    async handleEdit() {
      this.originalReportContent = this.reportContent
      this.isEditing = true
    },
    async handleSave() {
      try {
        const response = await this.$http.post('/api/set_report_content', {
          doc_id: this.$route.params.id,
          section_id: this.selectedSection === 'all' ? 'all' : this.selectedSection,
          content: this.reportContent
        })
        
        if (response.data.code === 200) {
          this.$message.success('保存成功')
          this.isEditing = false
        }
      } catch (error) {
        console.error('保存失败:', error)
        this.$message.error('保存失败，请重试')
      }
    },
    async handleConfirmReview() {
      try {
        const response = await this.$http.post('/api/update_review_status', {
          doc_id: this.$route.params.id,
          status: 1
        })
        
        if (response.data.code === 200) {
          this.isReviewed = true
          this.$message.success('审评状态已更新')
        }
      } catch (error) {
        console.error('更新审评状态失败:', error)
        this.$message.error('更新审评状态失败，请重试')
      }
    },
    async getOriginalFileContent() {
      try {
        const response = await this.$http.post('/api/get_original_file_content', {
          doc_id: this.$route.params.id
        })
        
        if (response.data.code === 200) {
          this.originalContent = response.data.data.content
        }
      } catch (error) {
        console.error('获取原始文件内容失败:', error)
        this.$message.error('获取原始文件内容失败，请重试')
      }
    },
    setPdfUrl() {
      this.pdfUrl = `/api/pdf_view/${this.$route.params.id}`
    },
    startStatusCheck() {
      // 清除可能存在的旧定时器
      if (this.statusCheckInterval) {
        clearInterval(this.statusCheckInterval)
      }
      
      // 每2秒检查一次状态
      this.statusCheckInterval = setInterval(async () => {
        try {
          const response = await this.$http.get(`/api/get_report_status/${this.$route.params.id}`)
          const status = response.data.data
          
          this.reportProgress = status.progress
          this.reportStatus = status.status
          
          if (status.status === 'completed') {
            // 报告生成完成
            clearInterval(this.statusCheckInterval)
            this.generatingFull = false
            this.isReviewed = true
            await this.getFullReport() // 获取生成的报告内容
            this.$message.success('完整报告生成成功')
          } else if (status.status === 'failed') {
            // 报告生成失败
            clearInterval(this.statusCheckInterval)
            this.generatingFull = false
            this.$message.error(status.message || '生成报告失败')
          }
        } catch (error) {
          console.error('检查报告状态失败:', error)
          clearInterval(this.statusCheckInterval)
          this.generatingFull = false
          this.$message.error('检查报告状态失败')
        }
      }, 2000)
    }
  },
  beforeDestroy() {
    // 组件销毁前清除定时器
    if (this.statusCheckInterval) {
      clearInterval(this.statusCheckInterval)
    }
  }
}
</script>

<style lang="scss" scoped>
.report-container {
  padding: 20px;
  height: 100%;
  box-sizing: border-box;
}

.breadcrumb {
  margin-bottom: 20px;
}

.report-card {
  height: 100%;
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

.section-selector {
  margin: 0 0;
  display: flex;
  gap: 16px;
  align-items: center;
  
  .el-cascader {
    width: 300px;
  }

  .el-button {
    display:flex;
    
    &.show {
      display: inline-flex;
    }
  }
}

.content-container {
  flex: 1;
  display: flex;
  gap: 20px;
  margin-top: 20px;
  min-height: 0;
}

.original-content,
.report-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  
  h3 {
    margin: 0;
    font-size: 16px;
    color: #1f2f3d;
  }
}

.content-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #fff;
  max-height: calc(100vh - 300px);
}

.edit-area {
  height: 100%;
  
  .el-textarea {
    height: 100%;
    
    ::v-deep .el-textarea__inner {
      height: 100%;
      min-height: 500px;
    }
  }
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

.pdf-content {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  
  .page-break {
    margin: 20px 0;
    border-top: 1px dashed #ccc;
  }
}

/* 优化报告内容显示样式 */
.report-content {
  .content-body {
    .markdown-body {
      h1, h2, h3, h4, h5, h6 {
        margin-top: 24px;
        margin-bottom: 16px;
        font-weight: 600;
        line-height: 1.25;
        color: #1f2f3d;
      }

      h1 { font-size: 2em; }
      h2 { font-size: 1.5em; }
      h3 { font-size: 1.25em; }
      h4 { font-size: 1em; }

      p {
        margin: 16px 0;
        line-height: 1.8;
      }

      ul, ol {
        padding-left: 2em;
        margin: 16px 0;
      }

      li {
        margin: 8px 0;
      }

      blockquote {
        margin: 16px 0;
        padding: 0 1em;
        color: #6a737d;
        border-left: 0.25em solid #dfe2e5;
      }

      code {
        padding: 0.2em 0.4em;
        margin: 0;
        font-size: 85%;
        background-color: rgba(27, 31, 35, 0.05);
        border-radius: 3px;
      }

      pre {
        padding: 16px;
        overflow: auto;
        font-size: 85%;
        line-height: 1.45;
        background-color: #f6f8fa;
        border-radius: 3px;
      }
    }
  }
}
</style> 