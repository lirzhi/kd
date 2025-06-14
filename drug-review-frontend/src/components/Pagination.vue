<template>
  <div class="pagination-container">
    <el-pagination
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
      :current-page="currentPage"
      :page-sizes="[10, 20, 50, 100]"
      :page-size="pageSize"
      layout="total, sizes, prev, pager, next, jumper"
      :total="total"
      background
    >
    </el-pagination>
  </div>
</template>

<script>
export default {
  name: 'PaginationComponent',
  props: {
    total: {
      type: Number,
      required: true
    },
    page: {
      type: Number,
      default: 1
    },
    limit: {
      type: Number,
      default: 10
    }
  },
  data() {
    return {
      currentPage: this.page,
      pageSize: this.limit
    }
  },
  watch: {
    page(val) {
      this.currentPage = val
    },
    limit(val) {
      this.pageSize = val
    }
  },
  methods: {
    handleSizeChange(val) {
      this.$emit('update:limit', val)
      this.$emit('pagination', { page: this.currentPage, limit: val })
    },
    handleCurrentChange(val) {
      this.$emit('update:page', val)
      this.$emit('pagination', { page: val, limit: this.pageSize })
    }
  }
}
</script>

<style scoped>
.pagination-container {
  padding: 20px 0;
  text-align: right;
}
</style> 