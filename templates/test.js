// 创建Vue实例
new Vue({
    el: '#app',
    data() {
        return {
            content:"",
            report:"",
            isExpanded: false, // 控制搜索框展开状态
            searchKeyword: "", // 搜索关键词
            eventSource:null,
            // 新增数据项
            displayReport: "",      // 实际显示的内容
            typewriterInterval: null,
            charIndex: 0,
            typingSpeed: 50 ,        // 打字速度（毫秒/字符）
            selectedChapterIndex: 0,
            isSourceView: false,
            expDialogVisible: false,
            uploadDialogVisible: false,
            uploadForm:{
                classification:"",
                affect_range:""

            },
            dialogHeight: `${window.innerHeight * 0.66}px`, // 弹窗高度
            selectedCategory: '',      // 当前选中的分类
            categoryOptions: [],       // 分类选项
            filteredList: [],          // 过滤后的列表
            // 其他原有数据保持不变
            fileList:[],
            parseLoading:false,
            ectdList:[],//文件列表
            sectionList: [],    // 章节列表
            selectedDoc: '',     // 当前选中的文档ID
            selectedSection: '' ,// 当前选中的章节ID
            newExperience: '',
            experiences: [],
            sourceSearchQuery: '', // 来源搜索关键词
            sources: [], // 原始来源数据
            filteredSources: [], // 过滤后的来源数据
            isGenerating: false,
            streamContent: "",
            results: {
                content: "",
                review_require_list: [],
                search_plan_list: [],
                search_list: [],
                review_result_list: [],
                report_require_list: [],
                final_report: [{ report: { content: "" } }]
            }

        }
    },

    created() {
        this.getEctdList();
        // this.fetchData();
    },
    mounted(){
        /// 监听外部点击事件
        document.addEventListener('click', this.clickOutsideHandler);

    },
    beforeDestroy() {
        // 移除事件监听
        document.removeEventListener('click', this.clickOutsideHandler);
      },
    watch: {
       
    },
    methods: {
        // 初始化章节数据
        async handleDocChange(docId) {
            this.selectedSection = ''; // 清空之前选择的章节
            try {
             this.getSectionId(docId);
            } catch (error) {
              console.error('获取章节失败:', error);
            }
          },
      
          async getSectionId(docId) {
            // 调用后端接口获取章节列表
            try {
                const response = await fetch(`http://127.0.0.1:5000//get_ectd_sections/${docId}`, {
                    method: 'POST',
                });
                
                const res = await response.json();
                console.log("data为：",res)
                if (res.code === 200) {
                    this.sectionList = res.data;
                }
            } catch (error) {
                console.error('获取章节列表失败:', error);
                this.$message.error('获取章节列表失败，请重试');
            }

          },
      
          async handleView() {
            if (this.selectedDoc && this.selectedSection) {
              const docKey = `${this.selectedDoc}${this.selectedSection}`;
              console.log("docKey为:",docKey)
              try {
                await this.getContent(docKey);
              } catch (error) {
                console.error('获取内容失败:', error);
              }
            }
          },
          //获取章节内容
      
          async getContent() {
            if (this.selectedDoc && this.selectedSection) {
                const docKey = `${this.selectedDoc}${this.selectedSection}`;
                console.log("docKey为:",docKey)
                try {
                    const response = await fetch(`http://127.0.0.1:5000//get_ectd_content/${docKey}`, {
                        method: 'POST',
                    });
                    
                    const res = await response.json();
                    if (res.code === 200) {
                        // 解析data字段为JSON对象
                        const data = JSON.parse(res.data);
                        // 获取content字段
                        const content = data.content;
                        console.log("data为：",content)
                        this.content = content;
                    }
                } catch (error) {
                  console.error('获取内容失败:', error);
                }
              }  
          },

        initSSE(){
            if(this.eventSource) {
                this.eventSource = null
            }
            this.eventSource = new EventSource('http://127.0.0.1:5000/stream_logs');
            this.eventSource.onmessage = (e) => {
                
                const msg = JSON.parse(e.data);
                console.log('Received log:', msg);
                const { task, data } = JSON.parse(e.data)
                this.streamContent = `[${task}] ${data}\n`
                // 自动滚动到底部
                // this.$nextTick(() => {
                //     const textarea = document.getElementById('streamConsole')
                //     if(textarea) {
                //         textarea.scrollTop = textarea.scrollHeight
                //     }
                // })
            };
            this.eventSource.addEventListener('complete', () => {
                this.handleSSEComplete()
            })

            this.eventSource.onerror = (e) => {
                console.error('SSE error:', e)
                this.handleSSEComplete()
            }
            // this.eventSource.onerror = (e) => {
            //     console.error('Error:', e);
            //     this.eventSource.close();
            // };
        },
        handleSSEComplete() {
            this.fetchData();
            this.report = this.results.final_report[0].report.content;
            this.startTypewriterEffect();
            if(this.eventSource) {
                this.eventSource.close()
            }
            this.isGenerating = false
            
            // 将最终结果设置到报告内容
            // this.report = this.results.final_report[0].report.content
            this.streamContent = ""
        },
        //上传ectd文件
        // 文件上传方法
        showUploadDialog(){
            this.uploadDialogVisible = true;
            this.getClassification();
        },
        //上传文件
        async submitUpload() {
            const formData = new FormData();
            const file = this.fileList[0];
            console.log("file为",file.raw)
            formData.append('file', file.raw);
            const classification = this.uploadForm.classification;
            const affect_range = this.uploadForm.affect_range;
            formData.append('classification', classification);
            formData.append('affect_range', affect_range);
            console.log("formData为",formData)
            try {
                const res = await fetch('http://127.0.0.1:5000/upload_file',  {
                    
                    method: 'POST',
                    body: formData, // 注意：不要手动设置 Content-Type
                });
                
                if (res.status === 200) {
                  this.$message.success('上传成功');
                  this.fileList = [];
                //   this.getEctdList();
                //   this.handleFilter();
                }
            } catch (error) {
                this.$message.error('文件上传失败');
                console.log("error为：",error,)
            }
        },
        handlePreview(file,fileList){
            console.log("file为：",file)
        },
         //修改文件列表
        handleChange(file, fileList) {
            this.fileList = fileList;
            console.log("fileList 为：",fileList )
        },
        beforeUpload(file) {
            this.fileList.push(file);
            console.log("fileList 为：",fileList )
            return false; // 阻止默认上传行为
        },
        //删除文件列表里的文件
        handleRemove(file, fileList) {
            this.fileList = fileList; // 更新文件列表
            this.$message({
                message: '文件删除成功',
                type: 'info'
            });
        },
        //获取类别
        async getClassification() {
            // 调用后端接口获取章节列表
            try {
                const response = await fetch(`http://127.0.0.1:5000/get_file_classification`, {
                    method: 'POST',
                });
                
                const res = await response.json();
                console.log("data为：",res)
                if (res.code === 200) {
                    this.categoryOptions = res.data;
                }
            } catch (error) {
                console.error('获取类别列表失败:', error);
                this.$message.error('获取类别列表失败，请重试');
            }

          },
        // 过滤列表
        async handleFilter() {
            const classification = this.selectedCategory;
            console.log("classification:",classification)
            try {
                const response = await fetch(`http://127.0.0.1:5000/get_file_by_class/${classification}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                });
                
                const res = await response.json();
                console.log("data为：",res)
                if (res.code === 200) {
                    // 添加分类字段到每个条目
                    this.filteredList = res.data.map(item => ({
                        ...item,
                        doc_classification: classification // 注意字段名与表格列prop对应
                    }));
                    console.log("处理后数据：", this.filteredList);
                }
            } catch (error) {
                console.error('获取文件列表失败:', error);
                this.$message.error('获取文件列表失败，请重试');
            } 
            
        },
        //获取Ectd列表
        async getEctdList() {
            try {
                const response = await fetch('http://127.0.0.1:5000/get_ectd_info_list', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                });
                
                const res = await response.json();
                console.log("data为：",res)
                if (res.code === 200) {
                    this.ectdList = res.data;
                }
            } catch (error) {
                console.error('获取Ectd列表失败:', error);
                this.$message.error('获取Ectd列表失败，请重试');
            }
          },
          //无sse
          async handleParse(docId) {
            try {
              
              console.log("docId为：",docId)
              const response = await fetch(`http://127.0.0.1:5000//parse_ectd/${docId}`, {
                method: 'POST',
            });
              const res = await response.json();
              console.log("res为：",res)
              
              if (res.code === 200) {
                this.$message.success('解析成功');
                await this.getEctdList();
                await this.handleFilter();
              } else {
                this.$message.error(res.error);
              }
            } finally {
           
            }
          },
          async handleDelete(docId) {
            try {
              await this.$confirm('确认删除该文件？此操作不可恢复！', '警告', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
              });
              console.log("docId为：",docId)
              
              const response = await fetch(`http://127.0.0.1:5000/delete_ectd/${docId}`, {
                method: 'POST',
            });
              const res = await response.json();
              console.log("res为：",res)
              
              if (res.code === 200) {
                this.$message.success('删除成功');
                await this.handleFilter();
                await this.getEctdList();
              } else {
                this.$message.error(res.error);
              }
            } catch (error) {
              if (error !== 'cancel') {
                this.$message.error('删除失败');
              }
            }
          },

        // 生成章节结论
        async fetchData() {
            try {
                const response = await fetch('http://127.0.0.1:5000/test', {
                    method: 'POST',
                });
                
                const res = await response.json();
                if (res.code === 200) {
                    this.results = res.data;
                    console.log("this.results:",this.results)
                    this.report = this.results.final_report[0].report.content;
                    this.startTypewriterEffect();
                    console.log("this.report:",this.report)
                }
            } catch (error) {
                console.error('生成结论失败:', error);
                this.$message.error('结论生成失败，请重试');
            }
        },

        // 生成章节结论
        async generateReport() {
            try {
                this.isGenerating = true
                this.streamContent = "" 
                // 初始化SSE连接
                this.fetchData();
                this.initSSE()           
            } catch (error) {
                console.error('生成结论失败:', error);
                this.$message.error('结论生成失败，请重试');
            }
        },

        // 启动打字机效果
        startTypewriterEffect() {
            this.charIndex = 0;
            this.displayReport = "";
            
            if (this.typewriterInterval) {
                clearInterval(this.typewriterInterval);
            }
            
            this.typewriterInterval = setInterval(() => {
                if (this.charIndex < this.report.length) {
                    this.displayReport += this.report.charAt(this.charIndex);
                    this.charIndex++;
                    this.scrollReportToBottom();
                } else {
                    clearInterval(this.typewriterInterval);
                }
            }, this.typingSpeed);
        },

        // 保持滚动到底部
        scrollReportToBottom() {
            this.$nextTick(() => {
                const textarea = document.getElementById('finalReport');
                if(textarea) {
                    textarea.scrollTop = textarea.scrollHeight;
                }
            });
        },

        // 在组件销毁时清除定时器
        beforeDestroy() {
            this.closeSSE();
            if (this.typewriterInterval) {
                clearInterval(this.typewriterInterval);
            }
        },

        // 生成章节结论
        async generateConclusion(index) {
        },

        // 重新生成结论
        async regenerate() {  
        },

        // 显示结论来源
        showSource() {
            this.isSourceView = true;
            // 模拟获取结论来源数据
            this.sources = [
                { requirement: '要求1', conclusion: '结论1' },
                { requirement: '要求2', conclusion: '结论2' }
            ];
        },

        // 返回主页面
        backToMain() {
            this.isSourceView = false;
        },

        // 显示经验管理弹窗
        showExpDialog() {
            this.expDialogVisible = true;
        },

        // 添加经验
        addExperience() {
            if (this.newExperience.trim()) {
                this.experiences.push({ content: this.newExperience });
                this.newExperience = '';
            }
        },

        // 删除经验
        deleteExperience(index) {
            this.experiences.splice(index, 1);
        },
            // 显示上传文件弹窗
            showExpDialog() {
            this.expDialogVisible = true;
        },

        // 切换搜索框显示
        // toggleSearch() {
        //     this.showSearch = !this.showSearch;
        // },
        // 切换搜索框状态
            toggleSearch() {
                this.isExpanded = !this.isExpanded;
                if (this.isExpanded) {
                this.$nextTick(() => {
                    this.$refs.searchInput.focus();
                });
                }
            },
            // 处理悬浮球点击
            handleBallClick(event) {
                if (!this.isExpanded) {
                this.toggleSearch();
                }
            },
            // 执行搜索
            performSearch() {
                if (this.searchKeyword.trim()) {
                alert(`执行搜索：${this.searchKeyword}`);
                // 实际搜索逻辑...
                this.searchKeyword = '';
                }
            },
            // 点击外部关闭
            clickOutsideHandler(event) {
                if (this.isExpanded && !event.target.closest('.search-container')) {
                this.toggleSearch();
                }
            },
        // 执行搜索
        doSearch() {
            // 模拟搜索逻辑
            this.$message.info(`搜索内容: ${this.searchQuery}`);
        },
        handleMenuSelect(index) {
            if(index === '2'){
                this.showExpDialog();
            }
            // 处理菜单选择
            if(index === '3') {
                this.showUploadDialog();
                // 跳转审批记录页面
            }
        },
        // 搜索来源
        async searchSources() {
        
        },

        // 删除来源
        async deleteSource(index) {
        
        },

        // 初始化来源数据
        async loadSources() {
        
        },
    },
    }
);
