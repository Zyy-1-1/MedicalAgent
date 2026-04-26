# Medical Diagnosis Multi-Agent System

基于 **LangChain** + **LangGraph** 的多智能体协作医疗诊断系统，采用 **GraphRAG**（知识图谱检索增强生成）进行医学知识检索，临时内存管理会话。

> 免责声明：本系统仅供学习和技术参考，所有 AI 生成内容不构成医疗建议。请务必咨询持牌医疗专业人士。

---

## 项目架构

```
MedicalAgent/
├── .env                              # API Key 与服务配置
├── backend/
│   ├── main.py                       # FastAPI 入口
│   ├── config.py                     # 环境变量配置
│   ├── requirements.txt              # Python 依赖
│   ├── agents/
│   │   ├── base.py                   # LangChain ChatOpenAI + 结构化输出
│   │   ├── triage.py                 # 分诊智能体
│   │   ├── symptom_analyzer.py       # 症状分析智能体
│   │   ├── diagnosis.py              # 诊断智能体
│   │   ├── treatment.py              # 治疗建议智能体
│   │   ├── chat_agent.py             # 对话智能体（含 GraphRAG 检索）
│   │   └── orchestrator.py           # LangGraph 状态图编排器
│   ├── rag/
│   │   └── __init__.py               # 医学知识图谱 + GraphRAG 检索器
│   ├── memory/
│   │   └── __init__.py               # 临时内存会话管理
│   ├── models/
│   │   └── __init__.py               # Pydantic 数据模型
│   └── routers/
│       ├── chat.py                   # 会话与聊天 API
│       └── diagnosis.py              # 诊断 API
└── frontend/
    ├── package.json
    ├── vite.config.js                # API 代理配置
    └── src/
        ├── main.js                   # Vue 应用入口
        ├── App.vue                   # 根组件（医疗主题头部）
        ├── api/index.js              # Axios API 客户端
        ├── views/Home.vue            # 三栏布局
        └── components/
            ├── PatientForm.vue       # 患者信息表单
            ├── ChatPanel.vue         # 聊天 + 诊断面板
            └── DiagnosisResult.vue   # 诊断结果展示
```

---

## 核心功能

### GraphRAG 知识图谱检索

系统构建了包含 **12 类疾病**、**36+ 症状**、**18+ 治疗措施**、**18+ 药物** 等 **80+ 节点** 及 **200+ 关系边** 的医学知识图谱：

| 节点类型 | 数量 | 示例 |
|----------|------|------|
| 疾病 (Disease) | 12 | 感冒、流感、高血压、糖尿病 |
| 症状 (Symptom) | 36+ | 头痛、发热、咳嗽、乏力 |
| 治疗 (Treatment) | 18+ | 休息、补水、抗生素治疗 |
| 药物 (Medication) | 18+ | 对乙酰氨基酚、二甲双胍 |
| 分类 (Category) | 8 | 呼吸系统、心血管、消化系统 |

**检索流程**：
1. 中英文关键词匹配 → 图节点定位
2. BFS 图遍历（深度 2）→ 发现关联知识
3. 图距离加权排序 → Top-K 文档输出

### LangGraph 多智能体诊断流程

```
START → triage → symptom_analysis → graphrag_retrieval → diagnosis → treatment → compile → END
```

| 节点 | 职责 | 技术 |
|------|------|------|
| triage | 评估紧急程度（低/中/高/紧急），建议就诊科室 | LangChain `with_structured_output` |
| symptom_analysis | 提取关键症状，列出可能疾病 | LangChain `with_structured_output` |
| graphrag_retrieval | 从医学知识图谱检索相关参考 | 图遍历检索器（BaseRetriever） |
| diagnosis | 综合症状 + GraphRAG 上下文 → 诊断 | LangChain `with_structured_output` |
| treatment | 紧急措施、用药参考、生活建议、随访 | LangChain `with_structured_output` |
| compile | 结构化结果 → Markdown 响应 | Python |

### 临时内存管理

- **会话记忆**：`ChatMessageHistory` 存储对话历史，限制最近 10 轮
- **零持久化**：所有数据仅在内存中，应用重启后自动清除
- **无文件写入**：不生成任何数据文件，保护患者隐私

### AI 医疗助手对话

- 支持多轮自由对话
- 自动检索相关知识图谱节点作为上下文
- 基于对话历史理解病情连续变化

---

## 快速开始

### 1. 配置环境

编辑 `.env` 文件：

```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

支持的 LLM 服务商：OpenAI、DeepSeek、以及其他兼容 OpenAI API 格式的服务。

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

API 文档访问：http://localhost:8000/docs

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问：http://localhost:5173

---

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/sessions` | 创建会话 |
| GET | `/api/sessions/{id}` | 获取会话信息 |
| POST | `/api/chat` | 发送聊天消息 |
| POST | `/api/diagnosis` | 执行 LangGraph 多智能体诊断 |

### 诊断请求示例

```json
POST /api/diagnosis
{
  "session_id": "abc123",
  "symptoms": "头痛、发烧38.5度、全身酸痛已持续2天",
  "duration": "2天",
  "severity_level": "medium",
  "patient_info": {
    "age": 35,
    "gender": "male",
    "medical_history": "无重大病史"
  }
}
```

### 诊断响应示例

```json
{
  "session_id": "abc123",
  "triage": {
    "urgency": "medium",
    "recommended_action": "建议1-2日内前往内科就诊",
    "specialty": "内科"
  },
  "symptom_analysis": {
    "key_symptoms": ["头痛", "发热", "全身酸痛"],
    "possible_conditions": ["流行性感冒", "上呼吸道感染", "COVID-19"],
    "requires_emergency": false
  },
  "diagnosis": {
    "primary_diagnosis": "流行性感冒",
    "differential_diagnoses": ["上呼吸道感染", "COVID-19"],
    "confidence": "moderate",
    "reasoning": "患者症状符合流感典型表现：高热伴全身酸痛..."
  },
  "treatment": {
    "immediate_actions": ["充分休息", "多饮水", "物理降温"],
    "medications": ["对乙酰氨基酚", "布洛芬"],
    "lifestyle_recommendations": ["保持室内通风", "清淡饮食"],
    "follow_up": "如症状加重或持续超过7天，请复诊"
  },
  "references": [
    {
      "content": "流感是由流感病毒引起的高度传染性呼吸道疾病...",
      "source": "Influenza",
      "source_cn": "流行性感冒",
      "type": "disease",
      "relevance": 0.85
    }
  ]
}
```

---

## 技术栈

- **后端**：Python 3.10+ / FastAPI / LangChain / LangGraph / langchain-openai / Pydantic
- **前端**：Vue 3 (Composition API) / Element Plus / Axios / Vite
- **检索**：GraphRAG（内存知识图谱 + BFS 图遍历）
- **记忆**：临时内存会话（无持久化）
- **LLM**：兼容 OpenAI API 格式的大语言模型
