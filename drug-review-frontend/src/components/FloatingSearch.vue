<template>
  <div class="floating-search-container" @click.stop>
    <div
      class="floating-ball"
      :class="{ expanded: isExpanded }"
      @click="handleBallClick"
      @mousedown="startDrag"
      ref="ball"
      :style="ballStyle"
    >
      <i v-if="!isExpanded" class="el-icon-search search-icon"></i>
      <transition name="el-zoom-in-center">
        <div v-if="isExpanded" class="search-panel">
          <el-card class="search-card">
            <el-loading :loading="isSearchLoading" :text="searchLoadingText" spinner="el-icon-loading" background="rgba(255,255,255,0.9)">
              <div class="input-container">
                <el-input
                  ref="searchInput"
                  v-model="searchKeyword"
                  placeholder="请输入搜索内容"
                  class="custom-input"
                  @keyup.enter.native="performSearch"
                  :loading="isSearchLoading"
                >
                  <el-button slot="append" type="primary" icon="el-icon-search" @click="performSearch"/>
                </el-input>
              </div>
              <div class="results-container">
                <el-card class="merged-results" v-if="mergedContent">
                  <h3>搜索结果：</h3>
                  <div class="merged-content">{{ mergedContent }}</div>
                </el-card>
                <el-card class="reference-table" v-if="referenceList.length">
                  <el-table :data="referenceList" style="width:100%" max-height="300">
                    <el-table-column prop="doc_id" label="文档ID" width="80"/>
                    <el-table-column prop="file_name" label="文件名" width="120"/>
                    <el-table-column prop="page_id" label="页码/索引" width="80"/>
                    <el-table-column prop="classification" label="分类" width="80"/>
                    <el-table-column label="操作" width="80">
                      <template slot-scope="scope">
                        <el-button type="text" size="mini" @click="showReferenceContent(scope.row)">查看内容</el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                  <div v-if="selectedDocContent" class="reference-content">
                    <h4>文档内容：</h4>
                    <el-input type="textarea" :value="selectedDocContent" :rows="6" resize="none" class="content-box"/>
                  </div>
                </el-card>
              </div>
            </el-loading>
          </el-card>
        </div>
      </transition>
    </div>
  </div>
</template>

<script>
const SERVER_HOST = '127.0.0.1'
const SERVER_PORT = '5000'

export default {
  name: 'FloatingSearch',
  data() {
    return {
      isExpanded: false, // 控制搜索框展开状态
      searchKeyword: "", // 搜索关键词
      isSearchLoading: false,
      searchLoadingText: "正在努力搜索中...",
      searchResults: [], // 搜索结果
      referenceData: {}, // 文档引用数据
      selectedDocContent: null, // 当前选中的文档内容
      // 拖拽相关
      isDragging: false,
      dragOffset: { x: 0, y: 0 },
      ballPosition: { x: 40, y: 40 }, // 初始位置
    }
  },
  computed: {
    ballStyle() {
      return {
        left: `${this.ballPosition.x}px`,
        top: `${this.ballPosition.y}px`,
      }
    },
    // 合并所有搜索结果内容
    mergedContent() {
      return this.searchResults.map(item => item.content).join("\n\n");
    },
    // 将 reference 对象转换为数组
    referenceList() {
      return Object.entries(this.referenceData).map(([doc_id, value]) => ({
        doc_id,
        ...value
      }));
    }
  },
  mounted() {
    console.log('FloatingSearch component mounted')
    document.addEventListener('click', this.clickOutsideHandler)
    document.addEventListener('mousemove', this.handleMouseMove)
    document.addEventListener('mouseup', this.handleMouseUp)
    
    // 从localStorage恢复位置
    const savedPosition = localStorage.getItem('floatingSearchPosition')
    if (savedPosition) {
      this.ballPosition = JSON.parse(savedPosition)
    }
    
    // 确保悬浮球可见
    this.$nextTick(() => {
      console.log('FloatingSearch ball position:', this.ballPosition)
      console.log('FloatingSearch ball element:', this.$refs.ball)
    })
  },
  beforeDestroy() {
    document.removeEventListener('click', this.clickOutsideHandler)
    document.removeEventListener('mousemove', this.handleMouseMove)
    document.removeEventListener('mouseup', this.handleMouseUp)
  },
  methods: {
    // 切换搜索框状态
    toggleSearch() {
      this.isExpanded = !this.isExpanded;
      if (this.isExpanded) {
        this.$nextTick(() => {
          this.$refs.searchInput && this.$refs.searchInput.focus();
        });
      }
    },
    // 处理悬浮球点击
    handleBallClick(event) {
      if (!this.isExpanded && !this.isDragging) {
        this.toggleSearch();
      }
    },
    // 点击外部关闭
    clickOutsideHandler(event) {
      if (this.isExpanded && !event.target.closest('.floating-search-container')) {
        this.toggleSearch();
        this.resetSearch();
      }
    },
    // 拖拽相关方法
    startDrag(event) {
      if (this.isExpanded) return // 展开状态下不允许拖拽
      
      this.isDragging = true
      const rect = this.$refs.ball.getBoundingClientRect()
      this.dragOffset = {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top
      }
      event.preventDefault()
    },
    handleMouseMove(event) {
      if (!this.isDragging) return
      
      const newX = event.clientX - this.dragOffset.x
      const newY = event.clientY - this.dragOffset.y
      
      // 限制在视窗范围内
      const maxX = window.innerWidth - 56
      const maxY = window.innerHeight - 56
      
      this.ballPosition = {
        x: Math.max(0, Math.min(newX, maxX)),
        y: Math.max(0, Math.min(newY, maxY))
      }
      
      // 保存位置到localStorage
      localStorage.setItem('floatingSearchPosition', JSON.stringify(this.ballPosition))
    },
    handleMouseUp() {
      this.isDragging = false
    },
    // 执行搜索 - 完全按照test.js的逻辑
    async performSearch() {
      this.isSearchLoading = true;
      if (this.searchKeyword.trim()) {
        const formData = new FormData();
        formData.append('query', this.searchKeyword)
        
        try { 
        const response = await fetch(`http://${SERVER_HOST}:${SERVER_PORT}/search_by_query`, {
          method: 'POST',
          body: formData
          });
          const res = await response.json();
          console.log("res为：", res)
          
        if (res.code === 200) {
            this.$message.success('搜索成功');
            this.isSearchLoading = false; 
            this.searchResults = res.data.response; // 设置搜索结果
            this.referenceData = res.data.reference; // 设置参考文档信息
        } else {
            this.$message.error(res.error);
          }
        } catch (error) {
          this.$message.error('搜索失败');
        }
      }
    },
    showReferenceContent(row) {
      this.selectedDocContent = row.content;
    },
    resetSearch() {
      this.searchKeyword = ''
      this.searchResults = []
      this.referenceData = {}
      this.selectedDocContent = null
    }
  }
}
</script>

<style scoped>
.floating-search-container {
  position: fixed;
  z-index: 99999;
  user-select: none;
  pointer-events: none;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.floating-ball {
  position: absolute;
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #36cfc9 0%, #1890ff 100%);
  border-radius: 50%;
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: width 0.3s, height 0.3s, box-shadow 0.3s;
  overflow: visible;
  pointer-events: auto;
  z-index: 99999;
}

.floating-ball.expanded {
  width: 480px;
  height: 600px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(24, 144, 255, 0.25);
  background: #fff;
  align-items: flex-start;
  justify-content: flex-start;
  padding: 0;
}

.search-icon {
  font-size: 28px;
  color: #fff;
}

.search-panel {
  width: 100%;
  height: 100%;
  padding: 18px 18px 0 18px;
  box-sizing: border-box;
}

.search-card {
  box-shadow: none;
  background: transparent;
  border: none;
  padding: 0;
  height: 100%;
}

.input-container {
  margin-bottom: 12px;
}

.custom-input {
  width: 100%;
}

.custom-input >>> .el-input__inner {
  border-radius: 8px;
  border: 1px solid #dcdfe6;
}

.custom-input >>> .el-input-group__append {
  border-radius: 0 8px 8px 0;
  background: #409eff;
  border-color: #409eff;
}

.results-container {
  margin-top: 10px;
  height: calc(100% - 80px);
  overflow-y: auto;
}

.merged-results {
  margin-bottom: 10px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 8px;
}

.merged-results >>> .el-card__body {
  padding: 12px;
}

.merged-results h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #52c41a;
  font-weight: 600;
}

.merged-content {
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 13px;
  color: #333;
  line-height: 1.5;
  max-height: 120px;
  overflow-y: auto;
}

.reference-table {
  background: #f5f7fa;
  border: 1px solid #e6ebf5;
  border-radius: 8px;
}

.reference-table >>> .el-card__body {
  padding: 12px;
}

.reference-table >>> .el-table {
  font-size: 12px;
}

.reference-table >>> .el-table th {
  background: #fafafa;
  color: #606266;
  font-weight: 500;
  padding: 8px 0;
}

.reference-table >>> .el-table td {
  padding: 6px 0;
}

.reference-content {
  margin-top: 10px;
  border-top: 1px solid #e6ebf5;
  padding-top: 10px;
}

.reference-content h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #606266;
  font-weight: 600;
}

.content-box {
  width: 100%;
}

.content-box >>> .el-textarea__inner {
  font-size: 12px;
  line-height: 1.4;
  border-radius: 4px;
}

/* 滚动条样式 */
.results-container::-webkit-scrollbar {
  width: 6px;
}

.results-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.results-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.results-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.merged-content::-webkit-scrollbar {
  width: 4px;
}

.merged-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 2px;
}

.merged-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 2px;
}

.merged-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
