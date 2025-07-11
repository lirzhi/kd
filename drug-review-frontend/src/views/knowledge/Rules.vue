<template>
  <div class="rules-container">
    <el-card class="rules-card">
      <div class="card-header">
        <div class="header-title">
          <span class="page-title">审评规则</span>
        </div>
        <div class="header-left">
          <el-select v-model="selectedSection1" filterable clearable placeholder="请选择一级章节" style="width:180px;margin-right:10px" @change="onSection1Change">
            <el-option v-for="item in sectionOptions" :key="item.section_id" :label="item.section_name + '（' + item.section_id + '）'" :value="item.section_id" />
          </el-select>
          <el-select v-model="selectedSection2" filterable clearable placeholder="请选择二级章节" style="width:180px" :disabled="!selectedSection1" @change="onSection2Change">
            <el-option
              v-for="item in getChildrenSections(selectedSection1)"
              :key="item.section_id"
              :label="item.section_name + '（' + item.section_id + '）'"
              :value="item.section_id"
            />
          </el-select>
        </div>

        <div class="header-right">
          <el-button type="primary" @click="showAddDialog = true">添加规则</el-button>
        </div>
      </div>
      <el-table :data="tableList" border style="width: 100%" v-loading="loading">
        <el-table-column prop="section_id" label="章节ID" width="150" align="center" />
        <el-table-column prop="section_name" label="章节名称" width="200" align="center" />
        <el-table-column prop="requirement" label="审评规则" min-width="300" align="left">
          <template slot-scope="scope">
            <div class="requirement-cell">{{ scope.row.requirement }}</div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center">
          <template slot-scope="scope">
            <el-button size="mini" @click="editRule(scope.$index, scope.row)">修改</el-button>
            <el-button size="mini" type="danger" @click="deleteRule(scope.$index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    <!-- 添加规则弹窗 -->
    <el-dialog title="添加规则" :visible.sync="showAddDialog">
      <el-input v-model="addRuleContent" type="textarea" rows="5" placeholder="请输入规则内容" />
      <div slot="footer">
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addRule">确定</el-button>
      </div>
    </el-dialog>
    <!-- 修改规则弹窗 -->
    <el-dialog title="修改规则" :visible.sync="showEditDialog">
      <el-input v-model="editRuleContent" type="textarea" rows="5" placeholder="请输入规则内容" />
      <div slot="footer">
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEditRule">确定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ectdSectionList } from './ectd-section.js'

export default {
  name: 'ReviewRules',
  data() {
    return {
      sectionOptions: [],
      selectedSection1: '',
      selectedSection2: '',
      requirementList: [],
      tableList: [],
      loading: false,
      showAddDialog: false,
      addRuleContent: '',
      showEditDialog: false,
      editRuleContent: '',
      editRuleIndex: null
    }
  },
  created() {
    this.sectionOptions = ectdSectionList
    console.log('ectdSectionList:', this.sectionOptions)
  },
  methods: {
    getChildrenSections(section1Id) {
      const parent = this.sectionOptions.find(item => item.section_id === section1Id)
      return parent && parent.children_sections ? parent.children_sections : []
    },
    onSection1Change() {
      this.selectedSection2 = ''
      this.requirementList = []
      this.tableList = []
    },
    async onSection2Change() {
      if (!this.selectedSection2) {
        this.requirementList = []
        this.tableList = []
        return
      }
      this.loading = true
      try {
        const params = { section_id: this.selectedSection2 }
        const response = await fetch(`/api/get_principle_content`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params)
        })
        const res = await response.json()
        let requirements = []
        if (res.code === 200) {
          if (typeof res.data === 'string') {
            try {
              requirements = JSON.parse(res.data)
            } catch { requirements = [res.data] }
          } else if (Array.isArray(res.data)) {
            requirements = res.data
          }
          this.requirementList = requirements
          this.syncTableList()
        } else {
          this.$message.error(res.message || '加载规则失败')
        }
      } catch (e) {
        this.$message.error('加载规则失败')
      } finally {
        this.loading = false
      }
    },
    editRule(index, row) {
      this.editRuleIndex = index;
      this.editRuleContent = row.requirement;
      this.showEditDialog = true;
    },
    async saveEditRule() {
      if (!this.editRuleContent.trim()) return this.$message.warning('请输入内容');
      this.$set(this.requirementList, this.editRuleIndex, this.editRuleContent.trim());
      await this.syncRules();
      this.showEditDialog = false;
    },
    async deleteRule(index) {
      this.requirementList.splice(index, 1);
      await this.syncRules();
    },
    async addRule() {
      if (!this.addRuleContent.trim()) return this.$message.warning('请输入内容');
      this.requirementList.push(this.addRuleContent.trim());
      await this.syncRules();
      this.showAddDialog = false;
      this.addRuleContent = '';
    },
    async syncRules() {
      const params = {
        section_id: this.selectedSection2,
        content: this.requirementList
      };
      const response = await fetch(`/api/set_principle_content`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      const res = await response.json();
      if (res.code === 200) {
        this.$message.success('操作成功');
        this.syncTableList();
      } else {
        this.$message.error(res.message || '操作失败');
      }
    },
    syncTableList() {
      const parent = this.sectionOptions.find(item => item.section_id === this.selectedSection1)
      const child = parent && parent.children_sections
        ? parent.children_sections.find(c => c.section_id === this.selectedSection2)
        : null
      const section_id = this.selectedSection2
      const section_name = child ? child.section_name : ''
      this.tableList = this.requirementList.map(req => ({
        section_id,
        section_name,
        requirement: req
      }))
    }
  }
}
</script>

<style lang="scss" scoped>
.rules-container {
  padding: 20px;
  height: 100%;
  box-sizing: border-box;
}

.rules-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 10px 20px 10px;
  position: relative;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-title {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  width: 200px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #1f2f3d;
  letter-spacing: 2px;
}

.header-right {
  display: flex;
  align-items: center;
}

.el-table {
  margin-top: 16px;
}

.el-dialog {
  .el-form {
    padding: 20px;
  }
  .el-textarea {
    width: 100%;
  }
}

.dialog-footer {
  text-align: right;
  padding: 20px;
}

.requirement-cell {
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.8;
  font-size: 15px;
  padding: 6px 0;
}

.el-table .el-button {
  margin-right: 8px;
}

.el-table .el-button:last-child {
  margin-right: 0;
}
</style>