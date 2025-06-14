<template>
  <div class="report-container">
    <div class="doc-selector">
      <el-row type="flex" align="middle" :gutter="20">
        <el-col :span="8">
          <el-select v-model="selectedDoc" placeholder="请选择文档" class="doc-select" @change="handleDocChange" filterable>
            <el-option v-for="doc in filteredEctdList" :key="doc.doc_id" :label="doc.file_name" :value="doc.doc_id"/>
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-select v-model="selectedSection" placeholder="请选择章节" class="doc-select" :disabled="!selectedDoc" filterable>
            <el-option v-for="sectionId in sectionList" :key="sectionId" :label="sectionId" :value="sectionId"/>
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" :disabled="!selectedSection" @click="getContent">查看</el-button>
        </el-col>
      </el-row>
    </div>

    <el-row class="card-container" :gutter="20">
      <el-col v-if="!isSourceView && !isStepView" :span="12">
        <el-card class="content-card" style="margin-top: 0;">
          <div class="text-editor-container">
            <el-input type="textarea" v-model="content" :rows="35" placeholder="输入章节内容" class="rounded-editor"/>
          </div>
        </el-card>
      </el-col>

      <el-col v-else-if="!isStepView" :span="12">
        <el-card class="content-card" style="height: 80vh; overflow-y: auto;margin-top: 0px;">
          <el-button type="danger" @click="backToMain" style="margin-bottom:10px">返回</el-button>
          <div class="source-list">
            <el-card v-for="(source, index) in filteredSources" :key="index" class="source-item">
              <div class="source-header">
                <span class="source-title">指导原则 {{ index + 1 }}</span>
                <el-button type="danger" icon="el-icon-delete" circle @click="deleteSource(index)"/>
              </div>
              <div class="source-content">
                <el-input type="textarea" :value="source.review_require" :rows="3" readonly class="requirement-box"/>
              </div>
            </el-card>
          </div>
        </el-card>
      </el-col>

      <el-col v-else :span="12">
        <el-card style="height: 80vh; overflow-y: auto;">
          <el-button type="danger" @click="backToMain" style="margin-bottom: 10px;">返回</el-button>
          <el-card style="margin-top: 0px;">
            <div v-if="filteredSteps && filteredSteps.length > 0">
              <div v-for="(step, index) in filteredSteps" :key="index" style="padding: 5px 0; border-bottom: 1px solid #eee;">
                {{ step }}
              </div>
            </div>
            <div v-else style="color: #999; text-align: center; padding: 10px;">
              暂无数据
            </div>
          </el-card>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="conclusion-card">
          <div slot="header" class="report-header">
            <span>审评报告</span>
            <div>
              <el-button type="primary" @click="generateSectionReport" style="margin-left: 10px;">生成章节报告</el-button>
              <el-button type="primary" @click="generateFinalReport" style="margin-left: 10px;">生成完整报告</el-button>
              <el-button type="info" @click="showStep">生成过程</el-button>
              <el-button type="danger" @click="exportReport">导出报告</el-button>
            </div>
          </div>
          <div class="conclusion-display">
            <el-card class="report-card" v-loading="loading" element-loading-text="正在生成报告...">
              <div v-html="compiledMarkdown" style="height: 60vh; overflow-y: auto;" class="rounded-display markdown-render"></div>
            </el-card>
          </div>
          <div class="stream-display" :style="{marginTop: '20px'}">
            <el-input type="textarea" :value="streamContent" :rows="2" readonly class="dynamic-console" id="streamConsole"/>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div class="search-container" @click.stop>
      <div class="search-ball" :class="{ 'expanded': isExpanded }" @click="handleBallClick">
        <i v-if="!isExpanded" class="el-icon-search search-icon"></i>
        <transition name="el-zoom-in-center">
          <div v-if="isExpanded" class="search-box">
            <el-card class="search-wrapper">
              <el-loading :active="isSearchLoading" :text="searchLoadingText" spinner="el-icon-loading" background="rgba(255, 255, 255, 0.9)">
                <div class="input-container">
                  <el-input ref="searchInput" v-model="searchKeyword" placeholder="请输入搜索内容" class="custom-input" 
                    @keyup.enter.native="performSearch" :loading="isSearchLoading">
                    <el-button slot="append" type="primary" icon="el-icon-search search-icon" @click="performSearch"/>
                  </el-input>
                </div>
                <div class="results-container">
                  <el-card class="merged-results">
                    <h3>搜索结果：</h3>
                    <div class="merged-content">{{ mergedContent }}</div>
                  </el-card>
                  <el-card class="reference-table">
                    <el-table :data="referenceList" style="width:100%" max-height="400">
                      <el-table-column prop="doc_id" label="文档ID" width="auto"></el-table-column>
                      <el-table-column prop="file_name" label="文件名" width="auto"></el-table-column>
                      <el-table-column prop="page_id" label="页码/索引" width="auto"></el-table-column>
                      <el-table-column prop="classification" label="分类" width="auto"></el-table-column>
                      <el-table-column label="操作" width="120">
                        <template slot-scope="scope">
                          <el-button type="text" @click="showReferenceContent(scope.row)">查看内容</el-button>
                        </template>
                      </el-table-column>
                    </el-table>
                    <div v-if="selectedDocContent" class="reference-content">
                      <h4>文档内容：</h4>
                      <el-input type="textarea" :value="selectedDocContent" :rows="8" resize="none" class="content-box"/>
                    </div>
                  </el-card>
                </div>
              </el-loading>
            </el-card>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ReportManagement',
  data() {
    return {
      content: '',
      selectedDoc: '',
      selectedSection: '',
      ectdList: [],
      sectionList: [],
      isSourceView: false,
      isStepView: false,
      filteredSources: [],
      filteredSteps: [],
      isExpanded: false,
      searchKeyword: '',
      isSearchLoading: false,
      searchLoadingText: '正在努力搜索中...',
      searchResults: [],
      referenceData: {},
      selectedDocId: null,
      selectedDocContent: null,
      streamContent: '',
      displayReport: '',
      dialogVisible: false,
      loading: false,
      total: 0,
      listQuery: {
        page: 1,
        limit: 10
      },
      reportContent: ''
    }
  },
  computed: {
    filteredEctdList() {
      return Array.isArray(this.ectdList) ? this.ectdList : []
    },
    compiledMarkdown() {
      return this.$marked.parse(this.formatMarkdown(this.displayReport) || '')
    },
    mergedContent() {
      return this.searchResults.map(item => item.content).join('\n\n')
    },
    referenceList() {
      return Object.entries(this.referenceData).map(([doc_id, value]) => ({
        doc_id,
        ...value
      }))
    }
  },
  created() {
    this.getEctdList()
  },
  methods: {
    async getEctdList() {
      this.loading = true
      try {
        const response = await this.$http.get('/api/get_ectd_info_list', {
          params: {
            page: this.listQuery.page,
            limit: this.listQuery.limit
          }
        })
        if (response.data.code === 200) {
          this.ectdList = response.data.data.list || []
          this.total = response.data.data.total || 0
        }
      } catch (error) {
        console.error('获取eCTD列表失败:', error)
        this.$message.error('获取eCTD列表失败，请重试')
      } finally {
        this.loading = false
      }
    },
    async handleDocChange(docId) {
      this.selectedSection = ''
      try {
        await this.getSectionId(docId)
      } catch (error) {
        console.error('获取章节失败:', error)
      }
    },
    async getSectionId(docId) {
      try {
        const response = await this.$http.post(`/api/get_ectd_sections/${docId}`)
        if (response.data.code === 200) {
          this.sectionList = response.data.data
        }
      } catch (error) {
        console.error('获取章节列表失败:', error)
        this.$message.error('获取章节列表失败，请重试')
      }
    },
    async getContent() {
      if (this.selectedDoc && this.selectedSection) {
        const params = {
          doc_id: this.selectedDoc,
          section_id: this.selectedSection
        }
        try {
          const response = await this.$http.post('/api/get_ectd_content', params)
          if (response.data.code === 200) {
            const data = JSON.parse(response.data.data)
            this.content = data.content
          }
        } catch (error) {
          console.error('获取内容失败:', error)
        }
      }
    },
    formatMarkdown(text) {
      if (!text) return ''
      return text.replace(/\n/g, '\n\n')
    },
    async generateSectionReport() {
      if (!this.selectedDoc || !this.selectedSection) {
        this.$message.warning('请先选择文档和章节')
        return
      }

      this.loading = true
      try {
        const response = await this.$http.post('/api/generate_section_report', {
          doc_id: this.selectedDoc,
          section_id: this.selectedSection
        })

        if (response.data.code === 200) {
          this.$message.success('章节报告生成成功')
          this.content = response.data.data.content
          this.startTypewriterEffect()
        } else {
          this.$message.error(response.data.msg || '生成失败')
        }
      } catch (error) {
        console.error('生成章节报告失败:', error)
        this.$message.error('生成章节报告失败，请重试')
      } finally {
        this.loading = false
      }
    },
    async generateFinalReport() {
      if (!this.selectedDoc) {
        this.$message.warning('请先选择文档')
        return
      }
      
      this.loading = true
      try {
        const response = await this.$http.post('/api/generate_report', {
          doc_id: this.selectedDoc.doc_id
        })
        if (response.data.code === 200) {
          this.reportContent = response.data.data.report_content
          this.$message.success('报告生成成功')
        }
      } catch (error) {
        console.error('生成最终报告失败:', error)
        this.$message.error('生成报告失败，请重试')
      } finally {
        this.loading = false
      }
    },
    async exportReport() {
      if (!this.finalReport) {
        this.$message.warning('请先生成最终报告')
        return
      }

      try {
        const response = await this.$http.post('/api/export_report', {
          content: this.finalReport
        }, {
          responseType: 'blob'
        })

        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `审评报告_${new Date().toLocaleDateString()}.docx`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)

        this.$message.success('报告导出成功')
      } catch (error) {
        console.error('导出报告失败:', error)
        this.$message.error('导出报告失败，请重试')
      }
    },
    startTypewriterEffect() {
      if (this.typewriterInterval) {
        clearInterval(this.typewriterInterval)
      }

      this.displayReport = ''
      this.charIndex = 0
      const content = this.finalReport || this.content

      this.typewriterInterval = setInterval(() => {
        if (this.charIndex < content.length) {
          this.displayReport += content[this.charIndex]
          this.charIndex++
          this.scrollReportToBottom()
        } else {
          clearInterval(this.typewriterInterval)
        }
      }, this.typingSpeed)
    },
    scrollReportToBottom() {
      const container = document.querySelector('.content-display')
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },
    showStep() {
      this.isStepView = true
      this.isSourceView = false
    },
    backToMain() {
      this.isStepView = false
      this.isSourceView = false
    },
    handleBallClick(event) {
      event.stopPropagation()
      this.isExpanded = !this.isExpanded
    },
    async performSearch() {
      // 实现搜索逻辑
    },
    showReferenceContent(row) {
      this.selectedDocId = row.doc_id
      this.selectedDocContent = row.content || '暂无内容'
    },
    handleRefresh() {
      this.getEctdList()
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
          this.getEctdList()
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
.report-container {
  height: 100%;
}

.doc-selector {
  margin-bottom: 20px;
}

.card-container {
  height: calc(100vh - 180px);
}

.content-card,
.conclusion-card {
  height: 100%;
}

.text-editor-container {
  height: 100%;
}

.rounded-editor {
  height: 100%;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
}

.search-ball {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background-color: #409EFF;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.search-ball.expanded {
  width: 600px;
  height: 400px;
  border-radius: 8px;
}

.search-icon {
  color: white;
  font-size: 20px;
}

.search-box {
  width: 100%;
  height: 100%;
  padding: 20px;
}

.search-wrapper {
  height: 100%;
}

.input-container {
  margin-bottom: 20px;
}

.results-container {
  height: calc(100% - 60px);
  overflow-y: auto;
}

.merged-results,
.reference-table {
  margin-bottom: 20px;
}

.source-list {
  height: calc(100% - 50px);
  overflow-y: auto;
}

.source-item {
  margin-bottom: 10px;
}

.source-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.source-content {
  margin-top: 10px;
}

.requirement-box {
  width: 100%;
}

.markdown-render {
  padding: 20px;
}

.dynamic-console {
  font-family: monospace;
}
</style> 