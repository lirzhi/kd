
// 创建Vue实例
new Vue({
    el: '#app',
    data() {
        return {
            chapters: [
                { label: '3.3.1', value: '3.3.1' },
                { label: '3.3.2', value: '3.3.2' }
            ],
            content:"",
            report:"",
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
                classfication:"",
                affectRange:""
            },
            fileList:[],
            ectdList:[],
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
        this.initChapters();
        this.fetchData();
    },
    watch: {
        selectedChapterIndex() {
        this.loadSources()
        }
    },
    methods: {
        // 初始化章节数据
        initChapters() {
            this.chapters = this.chapters.map(chapter => ({
                ...chapter,
                content: chapter.content || '暂无内容',
                conclusion: {
                    content: '暂无结论',
                    references: [],
                    experiences: [],
                    rawData: null
                }
            }));
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
        async handleUpload(file) {
            const formData = new FormData();
            formData.append('file', file.raw);
            formData.append('category', 'clinical'); // 示例附加参数

            try {
                const res = await this.$http.post('http://127.0.0.1:5000/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
                });
                
                if (res.status === 201) {
                this.$message.success('上传成功');
                }
            } catch (error) {
                this.handleApiError(error, '文件上传失败');
            }
        },
        //解析ectd
        async parseECTD(row){

        },
        // 确认删除
        confirmDelete(row) {
            this.$confirm('确定删除该文档吗？', '提示', {
            type: 'warning'
            }).then(async () => {
            await this.deleteECTD(row.doc_id);
            });
        },

        // 执行删除
        async deleteECTD(docId) {
            try {
            // const res = await this.$http.delete(`/api/ectd/${docId}`);
            if (res.data.code === 200) {
                this.$message.success('删除成功');
                // this.fetchECTDList();
            }
            } catch (error) {
            this.$message.error('删除失败');
            }
        },

        // 生成章节结论
        async fetchData() {
            try {
                const response = await fetch('http://127.0.0.1:5000/test_single_review', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                });
                
                const data = await response.json();
                if (data.code === 200) {
                    this.results = data.data;
                    this.content = this.results.content;
                }
            } catch (error) {
                console.error('生成结论失败:', error);
                this.$message.error('结论生成失败，请重试');
            }
        },

        // 生成章节结论
        async generateReport(index) {
            try {
                this.isGenerating = true
                this.streamContent = ""
                    
                // 初始化SSE连接
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
            try {
                const chapter = this.chapters[index];
                const response = await fetch('http://127.0.0.1:5000/test', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({content: chapter.content})
                });
                
                const data = await response.json();
                if (data.code === 200) {
                    this.$set(this.chapters, index, {
                        ...chapter,
                        conclusion: {
                            content: data.data.final_report,
                            references: data.data.final_reference || [],
                            experiences: chapter.conclusion.experiences,
                            rawData: data.data
                        }
                    });
                    this.$message.success(`第${chapter.label}章结论生成成功`);
                }
            } catch (error) {
                console.error('生成结论失败:', error);
                this.$message.error('结论生成失败，请重试');
            }
        },

        // 重新生成结论
        async regenerate() {
            try {
                const chapter = this.chapters[0]; // 假设只重新生成第一个章节的结论
                const tempData = {
                    content: chapter.content,
                    original_report: chapter.conclusion.content,
                    content_split_reference_list: chapter.conclusion.references,
                    final_experience: chapter.conclusion.experiences,
                    content_split_conclusion_list: chapter.conclusion.rawData?.content_split_report_list || []
                };

                const response = await fetch('http://127.0.0.1:5000/regenerate_report', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ content: tempData })
                });

                const data = await response.json();
                if (data.code === 200) {
                    this.$set(this.chapters, 0, {
                        ...chapter,
                        conclusion: {
                            ...chapter.conclusion,
                            content: data.data.report,
                            rawData: {
                                ...chapter.conclusion.rawData,
                                final_report: data.data.report
                            }
                        }
                    });
                    this.$message.success(`第${chapter.label}章结论重新生成成功`);
                }
            } catch (error) {
                console.error('重新生成失败:', error);
                this.$message.error('重新生成失败，请重试');
            }
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
        showUploadDialog(){
            this.uploadDialogVisible = true;
        },

        // 切换搜索框显示
        toggleSearch() {
            this.showSearch = !this.showSearch;
        },

        // 执行搜索
        doSearch() {
            // 模拟搜索逻辑
            this.$message.info(`搜索内容: ${this.searchQuery}`);
        },
        handleMenuSelect(index) {
            // 处理菜单选择
            if(index === '3') {
                this.showUploadDialog();
                // 跳转审批记录页面
            }
        },
        // 搜索来源
        async searchSources() {
        if (!this.sourceSearchQuery.trim()) {
            this.filteredSources = [...this.sources]
            return
        }

        try {
            const response = await this.$http.post('/sources/search', {
            query: this.sourceSearchQuery,
            chapter: this.selectedChapterIndex + 1
            })
            
            if (response.data.code === 200) {
            this.filteredSources = response.data.data
            }
        } catch (error) {
            this.$message.error('搜索失败')
        }
        },

        // 删除来源
        async deleteSource(index) {
        try {
            await this.$http.delete(`/sources/${this.filteredSources[index].id}`)
            this.filteredSources.splice(index, 1)
            this.sources = this.sources.filter(
            s => s.id !== this.filteredSources[index].id
            )
            this.$message.success('删除成功')
        } catch (error) {
            this.$message.error('删除失败')
        }
        },

        // 初始化来源数据
        async loadSources() {
        try {
            const response = await this.$http.get(`/sources/${this.selectedChapterIndex}`)
            if (response.data.code === 200) {
            this.sources = response.data.data
            this.filteredSources = [...this.sources]
            }
        } catch (error) {
            this.$message.error('加载来源数据失败')
        }
        },
        //上传文件
        submitUpload() {
            // this.$refs.upload.submit();
            const file = fileList[0].raw;
            const classfication = this.uploadForm.classfication;
            const affectRange = this.uploadForm.affectRange;

        },
        handleRemove(file, fileList) {
            console.log(file, fileList);
        },
        handlePreview(file) {
            console.log(file);
        },
        // 状态显示格式化
        statusType(status) {
            const statusMap = {
            1: 'info',   // 上传中
            2: 'success', // 可解析
            3: 'danger'   // 已失效
            };
            return statusMap[status] || 'info';
        },

        statusText(status) {
            const textMap = {
            1: '已上传',
            2: '可解析',
            3: '已失效'
            };
            return textMap[status] || '未知状态';
        }
    },
    }
);
