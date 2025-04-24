const SERVER_HOST = '127.0.0.1'
const SERVER_PORT = '5000'
// 配置 marked 全局选项
marked.setOptions({
    breaks: true,       // 将换行符转换为 <br>（关键配置）
    sanitize: false,    // 允许原始 HTML（若需要保留特殊格式）
    mangle: false,      // 禁用自动生成锚点链接
    headerIds: false,   // 禁用自动生成 header ID
    gfm: true,          // 启用 GitHub Flavored Markdown 模式
    smartLists: true // 自动优化列表缩进
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
- **试药与试剂选择** 
 - 使用甲醇作为溶剂进行溶解度测试是合理的，因为甲醇是一种常用的有机溶剂，广泛应用于药物溶解性研究。 
 - 水作为对照溶剂也符合常规检测标准，因为水是最常见的生物相关介质之一，其溶解性数据对于评估药物的生物利用度至关重要。
- **仪器与设备选择** 
 - 所用仪器如秒表、电子分析天平（万分之一）、容量瓶、量筒等均为通用且高精度设备，能够满足溶解度测试的需求。 
 - 具塞刻度试管的设计有助于确保实验过程中样品与溶剂混合的均匀性和密封性，减少外界环境对实验结果的影响。
- **操作方法合理性** 
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
            isSearchLoading:false,
            searchLoadingText:"正在努力搜索中...",
            searchResults: [], // 搜索结果
            referenceData: {},       // 文档引用数据
            selectedDocId: null,     // 当前选中的文档ID
            selectedDocContent:null,// 当前选中的文档内容
            eventSource:null,
            // 新增数据项
            displayReport: "",      // 实际显示的内容
            typewriterInterval: null,
            charIndex: 0,
            typingSpeed: 50 ,        // 打字速度（毫秒/字符）
            selectedChapterIndex: 0,
            expDialogVisible: false,
            uploadDialogVisible: false,
            kdDialogVisible: false,
            uploadForm:{
                classification:"",
                affect_range:""

            },
            dialogHeight: `${window.innerHeight * 0.66}px`, // 弹窗高度
            filteredECTDList:[],
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

            selectedExpSection1:'',
            selectedExpSection2:'',
            newExperience: '',
            experiences: [
                // "结构确证项目应全面，应能充分证明原料药的平面结构与立体结构。",
                // "结合文献调研信息以及工艺开发研究，具有多晶型、溶剂化物或水合物等多种物理形态的，应进行相关确证",
                // "并且关注原料药批间晶型一致性以及放置过程的晶型稳定性等。 "
                "1.依据相关指导原则简述各主要质量控制项目（如有关物质、异构体、残留溶剂、含量等）的分析方法筛选与确定的过程，并与现行版国内外药典收载方法参数列表对比。如有研究但未列入质量标准的项目，需一并提供分析方法描述、限度等。 ",
      "2.有关物质：简述分析方法筛选依据，明确色谱条件筛选所用样品（明确已知杂质信息，也可以采用粗品/粗品母液、合理设计降解试验样品等）及纯度，筛选项目及评价指标、考察结果等。如适用，列表对比自拟方法与药典方法检出能力（建议采用影响因素试验样品或加速试验样品、合理设计降解试验样品等），自拟方法的分离检出能力应不低于药典标准。提供专属性典型图谱（如系统适用性图谱、混合杂质对照品图谱等）。用表格形式表示：|有关物质|拟定注册标准|ChP（版本号）|BP（版本号）|USP（版本号）|EP（版本号）|其他|\n|方法|\n|色谱柱|\n|流动相及洗脱程序|\n|流速|\n|柱温|\n|检测波长|\n|进样体积|\n|稀释剂|\n|供试品溶液浓度|\n|对照（品）溶液浓度|\n|……|\n|定量方式",
      "3.如适用，请提供有关物质自拟方法与药典方法检出结果对比。",
      "4.研究但未订入标准的项目：参照中国药典格式提供各项目的分析方法。 ",
      "5.质量标准各项目分析方法的建立均应具有依据。",
      "6.有关物质分析方法筛选时，应在杂质谱分析全面的基础上，结合相关文献，科学选择分析方法。可以在原料药中加入限度浓度的已知杂质，证明拟定的有关物质分析方法可以单独分离目标杂质和/或使杂质与主成分有效分离；也可以采用含适量杂质的样品（如粗品或粗品母液、适当降解样品、稳定性末期样品等），对色谱条件进行比较优选研究，根据对杂质的检出能力选择适宜的色谱条件，建立有关物质分析方法。对于已有药典标准收载的，应结合原料药工艺路线分析药典标准分析方法的适用性，拟定的有关物质分析方法分离检出能力和杂质控制要求应不低于药典标准。", 
      "7.同时，需关注稳定性考察期间总杂增加与含量下降的匹配性，如出现不匹配情况，需关注有关物质与含量测定分析方法的专属性、杂质校正因子影响等，必要时优化分析方法。"
            ],
            requireFileList:[],
            requireList:[],
            requireFilteredList: [], 
            isSourceView: false,
            sourceSearchQuery: '', // 来源搜索关键词
            sources: [], // 原始来源数据
            filteredSources: [], // 过滤后的来源数据
            isStepView: false,
            filteredSteps: [
                
              ],// 过滤后的来源数据
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
            // return marked.parse(window.raw_report|| '');
        },
        markedContent(){
            return marked.parse(this.formatMarkdown(this.content) || '');
            // return marked.parse(this.formatMarkdown(window.raw_content) || '');
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
                const response = await fetch(`http://${SERVER_HOST}:${SERVER_PORT}/get_ectd_sections/${docId}`, {
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
                    const response = await fetch(`http://${SERVER_HOST}:${SERVER_PORT}/get_ectd_content/${docKey}`, {
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
            this.eventSource = new EventSource(`http://${SERVER_HOST}:${SERVER_PORT}/stream_logs`);
            this.eventSource.onmessage = (e) => {
                
                const msg = JSON.parse(e.data);
                console.log('Received log:', msg);
                const { task, data } = JSON.parse(e.data)
                this.streamContent = `[${task}] ${data}\n`
                console.log('Received log:', this.streamContent);
                this.filteredSteps.push(this.streamContent)
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
            this.uploadForm.classification = "",
            this.uploadForm.affect_range = ""
            this.getClassification();
        },
        showKDDialog(){
            this.kdDialogVisible = true;
            this.uploadForm.classification = "",
            this.uploadForm.affect_range = ""
            this.getClassification();
        },
        //上传文件
        async submitUpload() {
            const formData = new FormData();
            const file = this.fileList[0];
            console.log("file为",file.raw)
            formData.append('file', file.raw);
            const classification = this.showUploadDialog?'eCTD':this.uploadForm.classification;
            const affect_range = this.uploadForm.affect_range;
            formData.append('classification', classification);
            formData.append('affect_range', affect_range);
            console.log("formData为",formData)
            try {
                const response = await fetch(`http://${SERVER_HOST}:${SERVER_PORT}/upload_file`,  {
                    
                    method: 'POST',
                    body: formData, // 注意：不要手动设置 Content-Type
                });
                 res = await response.json();
                 console.log("res.data为：",res)
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
        // 过滤ectd列表
        async handleECTDFilter() {
            const classification = 'eCTD';
            console.log("classification:",classification)
            try {
                const response = await fetch(`http://${SERVER_HOST}:${SERVER_PORT}/get_file_by_class/${classification}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                });
                
                const res = await response.json();
                console.log("data为：",res)
                if (res.code === 200) {
                    // 添加分类字段到每个条目
                    this.filteredECTDList = res.data.map(item => ({
                        ...item,
                        doc_classification: classification // 注意字段名与表格列prop对应
                    }));
                    console.log("处理后数据：", this.filteredECTDList);
                }
            } catch (error) {
                console.error('获取eCTD列表失败:', error);
                this.$message.error('获取eCTD列表失败，请重试');
            } 
            
        },
        //获取类别
        async getClassification() {
            // 调用后端接口获取章节列表
            try {
                const response = await fetch(`http://${SERVER_HOST}:${SERVER_PORT}/get_file_classification`, {
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
            if(this.uploadDialogVisible == true) this.selectedCategory='eCTD';
            const classification = this.selectedCategory;
            console.log("classification:",classification)
            try {
                const response = await fetch(`http://${SERVER_HOST}:${SERVER_PORT}/get_file_by_class/${classification}`, {
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
                const response = await fetch(`http://${SERVER_HOST}:${SERVER_PORT}/get_ectd_info_list`, {
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
        //       const response = await fetch(`http://${SERVER_HOST}:${SERVER_PORT}//parse_ectd/${docId}`, {
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
        handleParseSSEComplete(){
            this.showParseProgress = false;
            if(this.eventSourceParse) {
                this.eventSourceParse.close()
            }
            this.handleFilter();
            this.handleECTDFilter();

        },
        //解析eCTD
        async handleEctdParse(docId) {
                this.showParseProgress = true;
                this.parseProgress = 0;
                this.abortController = new AbortController();
            
                try {
                const response = await fetch(
                    `http://${SERVER_HOST}:${SERVER_PORT}/parse_ectd_stream/${docId}`,
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
              const response = await fetch(`http://${SERVER_HOST}:${SERVER_PORT}/add_to_kd/${docId}`, {
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
              
              const response = await fetch(`http://${SERVER_HOST}:${SERVER_PORT}/delete_ectd/${docId}`, {
                method: 'POST',
            });
              const res = await response.json();
              console.log("res为：",res)
              
              if (res.code === 200) {
                this.$message.success('删除成功');
                if(this.uploadDialogVisible == true) await this.handleECTDFilter();
                else await this.handleFilter();
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
            const params = {
                content:this.content,
                content_section:this.selectedSection,
                review_require_list:this.experiences

            }
            console.log("params:",params)
            try {
                const response = await fetch(`http://${SERVER_HOST}:${SERVER_PORT}/review_text`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(params)
                });
                console.log("response:",response)
                
                const res = await response.json();
                console.log("res:",res)

                if (res.code === 200) {
                    this.results = res.data;
                    console.log("this.results:",this.results)
                    this.results.review_result_list = this.results.review_result_list
                    .filter(item => item && item.conclusion && item.conclusion.content && item.conclusion.content) // 过滤掉空元素
                    console.log("this.results.review_result_list:",this.results.review_result_list)
                    this.report = this.results.review_result_list
                    .filter(item => item && item.conclusion && item.conclusion.content && item.conclusion.content) // 过滤掉空元素
                    .map(item => item.conclusion.content) // 提取每个 conclusion.content
                    .join('\n\n'); // 用两个换行符拼接每个结论，确保段落之间有清晰的分隔
                    const text = this.formatMarkdown(this.report)

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
                // 保留原始换行符，避免过早替换导致结构丢失
            text = text
            // 1. 标准化换行符（统一为 \n）
            .replace(/\r\n/g, '\n')
            .replace(/\r/g, '\n')

            // 2. 处理标题格式（保证标题前后空行）
            .replace(/(\n|^)(#{1,6} )/g, '\n\n$2')  // 标题前空行
            .replace(/(\n#{1,6}.*?)(\n)(?=\S)/g, '$1\n\n') // 标题后空行

            // 3. 处理列表项（统一使用 - 符号）
            .replace(/(\n|^)\s*(\d+)\./g, '\n-')    // 有序转无序
            .replace(/(\n- [^\n]+)(\n+)(?=- )/g, '$1\n') // 列表项间空行
            .replace(/(\n- .+?)(\n)(?=\S)/g, '$1  \n')   // 列表内换行

            // 4. 处理段落结构
            .replace(/(\n\n)([^\n#-])/g, '\n\n$2')  // 段落前空行
            .replace(/([^\n])(\n)([^\n#-])/g, '$1  \n$3') // 段内换行

            // 5. 清理多余空行和空格
            .replace(/\n{3,}/g, '\n\n')    // 最多保留两个空行
            .replace(/ +/g, ' ')           // 合并连续空格
            .replace(/(^\s+|\s+$)/g, '');  // 去除首尾空格

            return text;
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
            this.isStepView = false;
            this.results.review_result_list = this.results.review_result_list
                    .filter(item => item && item.conclusion && item.conclusion.content && item.conclusion.content) // 过滤掉空元素
                    console.log("this.results.review_result_list:",this.results.review_result_list)
            this.filteredSources = this.results.review_require_list.map((item, index) => ({
                review_require: item,
                // review_result: this.results.review_result_list[index].conclusion.content || ''
              }))
              console.log("this.filteredSources:",this.filteredSources)
        },
         // 删除来源
         async deleteSource(index) {
            this.filteredSources.splice(index, 1)
        
        },

        // 显示结论来源
        showStep() {
            this.isStepView = true;
            this.isSourceView = false;
              console.log("this.filteredSources:",this.filteredSources)
        },
         // 删除来源
         async deleteStep(index) {
            this.filteredSources.splice(index, 1)
        
        },

        // 返回主页面
        backToMain() {
            this.isSourceView = false;
            this.isStepView = false;
        },
        //经验管理
        // 显示经验管理弹窗
        showExpDialog() {
            this.expDialogVisible = true;
        },

        handleExpFilter(){

        },

        // 添加经验
        async addExperience() {
            if (this.newExperience.trim()) {
                const newExperience = this.newExperience
                this.experiences.push({newExperience});
                this.newExperience = '';
            }
            // const params={
            //     parent_section:this.selectedExpSection1,
            //     section_id:this.selectedExpSection2,
            //     requirement:this.newExperience
            // }
            // try {
            //     const response = await fetch(`http://${SERVER_HOST}:${SERVER_PORT}/add_requirement`, {
            //       method: 'POST',
            //       body:params
            //   });
            //     const res = await response.json();
            //     console.log("res为：",res)  
            //     if (res.code === 200) {
            //       this.$message.success('添加要求成功');
            //       await this.handleFilter();
            //     } else {
            //       this.$message.error(res.error);
            //     }
            //   } finally {
             
            //   }
        },

        // 删除经验
        deleteExperience(sectionId) {
            
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
        async performSearch() {
            this.isSearchLoading = true ;
            if (this.searchKeyword.trim()) {
                const formData = new FormData();
                formData.append('query',this.searchKeyword)
                
                try { 
                    const response = await fetch(`http://${SERVER_HOST}:${SERVER_PORT}/search_by_query`, {
                        method: 'POST',
                        body: formData
                    });
                    const res = await response.json();
                    console.log("res为：",res)
                    
                    if (res.code === 200) {
                        this.$message.success('搜素成功');
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
        
        // handleBallClick() {
        // this.isExpanded = !this.isExpanded;
        // },
        
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
            // 处理菜单选择
            if(index === '4') {
                this.showKDDialog();
                // 跳转审批记录页面
            }
        },
        // 搜索来源
        async searchSources() {
        
        },
        // 初始化来源数据
        async loadSources() {
        
        },
        //审评要求
        //上传审评要求
         async requireSubmitUpload(){
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
                const response = await fetch(`http://${SERVER_HOST}:${SERVER_PORT}/upload_file`,  {
                    
                    method: 'POST',
                    body: formData, // 注意：不要手动设置 Content-Type
                });
                 res = await response.json();
                 console.log("res.data为：",res)
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
        requireHandleChange(file, fileList) {
            this.requireFileList=fileList;
            console.log("fileList 为：",fileList )
        },
        requireBeforeUpload(file) {
            this.requireFileLis.push(file)
            console.log("fileList 为：",fileList )
            return false; // 阻止默认上传行为
        },
        //删除文件列表里的文件
        requireHandleRemove(file, fileList) {
            this.requireFileList=fileList;//删除文件列表
            this.$message({
                message: '文件删除成功',
                type: 'info'
            });
        },
    },
}
    
);
