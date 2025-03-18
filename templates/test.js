// 配置 marked 全局选项
marked.setOptions({
    breaks: true,       // 将换行符转换为 <br>（关键配置）
    sanitize: false,    // 允许原始 HTML（若需要保留特殊格式）
    mangle: false,      // 禁用自动生成锚点链接
    headerIds: false,   // 禁用自动生成 header ID
    gfm: true           // 启用 GitHub Flavored Markdown 模式
  });
// 创建Vue实例
new Vue({
    el: '#app',
    
    data() {
        return {
            markdownText : `## 检测方法合理性说明

                ### 已知信息

                根据提供的待审评内容，检测方法主要涉及水中和甲醇中溶解度的测定。检测步骤明确，包括试药与试剂的选择、仪器与设备的使用以及操作方法的详细描述。

                ### 方法合理性分析

                1. **试药与试剂选择**
                - 使用甲醇作为溶剂进行溶解度测试是合理的，因为甲醇是一种常用的有机溶剂，广泛应用于药物溶解性研究。
                - 水作为对照溶剂也符合常规检测标准，因为水是最常见的生物相关介质之一，其溶解性数据对于评估药物的生物利用度至关重要。

                2. **仪器与设备选择**
                - 所用仪器如秒表、电子分析天平（万分之一）、容量瓶、量筒等均为通用且高精度设备，能够满足溶解度测试的需求。
                - 具塞刻度试管的设计有助于确保实验过程中样品与溶剂混合的均匀性和密封性，减少外界环境对实验结果的影响。

                3. **操作方法合理性**
                - 实验采用“强力振摇30秒”的方式模拟实际溶解过程，符合《中国药典》等相关规范中关于溶解度测定的操作要求。
                - 测试条件（25℃±2℃）也符合药物溶解度研究的标准温度范围，能够反映药物在接近人体生理条件下的溶解性能。
                - 通过间隔时间记录溶解情况（每5分钟观察一次），并持续观察30分钟，确保了实验数据的准确性和可靠性。

                综上所述，该检测方法具有科学性和合理性，符合相关行业标准和实际需求。

                ### 参考依据

                - 检测方法参考了《中国药典》中关于溶解度测定的相关规定。
                - 操作细节符合常规药物溶解度研究的技术要求。`,
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
            eventSourceParse:null,//解析
            abortController:null,
            parseProgress:0,
            showParseProgress:false,
            ectdList:[],//文件列表
            sectionList: [],    // 章节列表
            selectedDoc: '',     // 当前选中的文档ID
            selectedSection: '' ,// 当前选中的章节ID
            newExperience: '',
            experiences: [],
            sourceSearchQuery: '', // 来源搜索关键词
            sources: [], // 原始来源数据
            filteredSources: [], // 过滤后的来源数据
            searchContents:"",//搜素
            filteredSearchList:[],
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
        parseProgress(){

        }      
    },
    computed:{
        progressStatus() {
            return this.parseProgress === 100 ? 'success' : 'primary'
          },
        // 将 Markdown 文本转换为 HTML
        // Markdown 编译计算属性
        compiledMarkdown() {
            return marked.parse(this.formatMarkdown(this.displayReport) || '');
        }
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
                
                if (res.data.status === 1) {
                  this.$message.success('上传成功');
                  this.fileList = [];
                  console.log("res.data为：",res.data)
                //   this.getEctdList();
                  this.handleFilter();
                }
                else{
                    this.$message.error(res.data.msg);

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
        //   async handleParse(docId) {
        //     try {
              
        //       console.log("docId为：",docId)
        //       const response = await fetch(`http://127.0.0.1:5000//parse_ectd/${docId}`, {
        //         method: 'POST',
        //     });
        //       const res = await response.json();
        //       console.log("res为：",res)
              
        //       if (res.code === 200) {
        //         this.$message.success('解析成功');
        //         await this.getEctdList();
        //         await this.handleFilter();
        //       } else {
        //         this.$message.error(res.error);
        //       }
        //     } finally {
           
        //     }
        //   },
        async handleParse(docClassification,docId){
            console.log("docId为：",docId);
            if(docClassification == 'eCTD') this.handleEctdParse(docId);
            else this.handleFileParse(docId);
        },
        //解析进度
        async handleEctdParseSSE(docId){
            this.showParseProgress = true;

            // if(this.eventSourceParse) {
            //     this.eventSourceParse = null
            // }
            // this.eventSourceParse = new EventSource(`http://127.0.0.1:5000/parse_ectd_stream/${docId}`);
            // this.eventSourceParse.onmessage = (e) => {
                
            //     const msg = JSON.parse(e.data);
            //     console.log('Received log:', msg);
            //     const { cur_section, total_section } = msg
            //     this.parseLoading = cur_section / total_section *100;
            //     // 自动滚动到底部
            //     // this.$nextTick(() => {
            //     //     const textarea = document.getElementById('streamConsole')
            //     //     if(textarea) {
            //     //         textarea.scrollTop = textarea.scrollHeight
            //     //     }
            //     // })
            // };
            // if (cur_section === total_section) {
            //     this.handleParseSSEComplete()
            // }

            // this.eventSourceParse.onerror = (e) => {
            //     console.error('SSE error:', e)
            //     this.handleParseSSEComplete()
            // }
            // this.eventSourceParse.onerror = (e) => {
            //     console.error('Error:', e);
            //     this.eventSourceParse.close();
            // };

        },
        handleParseSSEComplete(){
            this.showParseProgress = false;
            if(this.eventSourceParse) {
                this.eventSourceParse.close()
            }
            this.handleFilter();

        },
        //解析eCTD
        async handleEctdParse(docId) {
                this.showParseProgress = true;
                this.parseProgress = 0;
                this.abortController = new AbortController();
            
                try {
                const response = await fetch(
                    `http://127.0.0.1:5000/parse_ectd_stream/${docId}`,
                    {
                    method: 'GET',
                    signal: this.abortController.signal
                    }
                );
            
                if (!response.ok) {
                    throw new Error(`HTTP错误! 状态码: ${response.status}`);
                }
            
                const reader = response.body.getReader();
                const decoder = new TextDecoder('utf-8');
                let buffer = '';
            
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
            
                    buffer += decoder.decode(value, { stream: true });
                    
                    // 处理可能包含多个JSON对象的块
                    const lines = buffer.split('\n');
                    for (let i = 0; i < lines.length - 1; i++) {
                    const line = lines[i].trim();
                    if (!line) continue;
            
                    try {
                        const data = JSON.parse(line);
                        console.log('流数据:', data);
            
                        // 更新进度
                        if (data.cur_section && data.total_section) {
                        this.parseProgress = Math.round(
                            (data.cur_section / data.total_section) * 100
                        );
                        }
            
                        // 错误处理
                        if (data.error) {
                        throw new Error(data.error);
                        }
                    } catch (err) {
                        console.error('数据解析错误:', err);
                        this.$message.error(`解析失败: ${err.message}`);
                        this.abortController.abort();
                    }
                    }
                    buffer = lines[lines.length - 1]; // 保留不完整数据
                }
            
                // 完成处理
                this.$message.success('解析完成');
                await this.getEctdList();
                await this.handleFilter();
                } catch (err) {
                if (err.name !== 'AbortError') {
                    this.$message.error(`请求失败: ${err.message}`);
                }
                } finally {
                this.showParseProgress = false;
                this.abortController = null;
                }
          },
          // 取消解析
            cancelParse() {
                if (this.abortController) {
                this.abortController.abort();
                }
            },
          //解析非eCTD文件
          async handleFileParse(docId) {
            try {
              const response = await fetch(`http://127.0.0.1:5000/add_to_kd/${docId}`, {
                method: 'POST',
            });
              const res = await response.json();
              console.log("res为：",res)  
              if (res.code === 200) {
                this.$message.success('解析成功');
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
                    const text = this.formatMarkdown(this.markdownText)

                    this.startTypewriterEffect();
                    console.log("this.report:",this.report)
                    console.log("text:",text)
                }
            } catch (error) {
                console.error('生成结论失败:', error);
                this.$message.error('结论生成失败，请重试');
            }
        },
        formatMarkdown(text) {
              // 1. 去除多余的空格和换行符
    text = text.replace(/\s+/g, ' ').trim();

    // 2. 将多个空格替换为单个空格
    text = text.replace(/ +/g, ' ');

    // 3. 修复标题格式（确保各级标题前后有空行）
    // 先处理三级标题
    text = text.replace(/(### .+)/g, '\n\n$1\n\n');
    // 再处理二级标题
    text = text.replace(/(## .+)/g, '\n\n$1\n\n');
    // 最后处理一级标题
    text = text.replace(/(# .+)/g, '\n\n$1\n\n');

    // 4. 修复列表项格式（确保列表项前有换行）
    text = text.replace(/(\d+\.\s+)/g, '\n$1'); // 有序列表
    text = text.replace(/(-\s+)/g, '\n$1');     // 无序列表

    // 5. 修复列表项内部的换行（确保列表项内部的换行是两个空格）
    text = text.replace(/(\n\s*-\s+[^\n]+)\s+/g, '$1  \n'); // 无序列表
    text = text.replace(/(\n\s*\d+\.\s+[^\n]+)\s+/g, '$1  \n'); // 有序列表

    // 6. 修复段落换行（确保段落之间有空行）
    text = text.replace(/(\n{2,})/g, '\n\n');

    // 7. 去除多余的空行
    text = text.replace(/\n{3,}/g, '\n\n');

    // 8. 修复标题下的内容换行（确保标题和内容之间有空行）
    text = text.replace(/(\n##+ .+\n)([^#])/g, '$1\n$2');

    // 9. 修复标题下的列表项换行（确保标题和列表项之间有空行）
    text = text.replace(/(\n##+ .+\n)(\d+\.\s+|-\s+)/g, '$1\n$2');

    // 10. 修复段落内的多余空格（确保段落内没有多余的空格）
    text = text.replace(/(\n\s+)([^-\d])/g, '\n$2');

    return text.trim();
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
            this.filteredSources = this.results.review_require_list.map((item, index) => ({
                review_require: item,
                review_result: this.results.review_result_list[index].conclusion.content || ''
              }))
        },
         // 删除来源
         async deleteSource(index) {
            this.filteredSources.splice(index, 1)
        
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
        // 初始化来源数据
        async loadSources() {
        
        },
    },
    }
);
