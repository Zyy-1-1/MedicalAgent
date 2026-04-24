# Medical Diagnosis Multi-Agent System

基于大语言模型的多智能体协作医疗诊断系统，集成 RAG 医学知识检索与记忆管理功能。

> 免责声明：本系统仅供学习和技术参考，所有 AI 生成内容不构成医疗建议。请务必咨询持牌医疗专业人士。

## 项目架构

```
MedicalAgent/
├── .env                              # API Key 与服务配置
├── backend/
│   ├── main.py                       # FastAPI 入口
│   ├── config.py                     # 环境变量配置
│   ├── requirements.txt              # Python 依赖
│   ├── agents/
│   │   ├── base.py                   # LLM 客户端封装
│   │   ├── triage.py                 # 分诊智能体
│   │   ├── symptom_analyzer.py       # 症状分析智能体
│   │   ├── diagnosis.py              # 诊断智能体
│   │   ├── treatment.py              # 治疗建议智能体
│   │   ├── chat_agent.py             # 对话智能体
│   │   └── orchestrator.py           # 多智能体调度编排器
│   ├── rag/
│   │   └── __init__.py               # 医学知识库 + 检索引擎
│   ├── memory/
│   │   ├── __init__.py               # 会话记忆（内存 + JSON 持久化）
│   │   └── patient_history.py        # 患者历史档案
│   ├── models/
│   │   └── __init__.py               # Pydantic 数据模型
│   └── routers/
│       ├── chat.py                   # 会话与聊天 API
│       └── diagnosis.py              # 诊断 API
└── frontend/
    ├── package.json
    ├── vite.config.js                # 含 API 代理配置
    └── src/
        ├── main.js
        ├── App.vue
        ├── api/index.js              # Axios API 客户端
        ├── views/Home.vue            # 三栏主布局
        └── components/
            ├── PatientForm.vue       # 患者信息表单
            ├── ChatPanel.vue         # 聊天 + 诊断面板
            └── DiagnosisResult.vue   # 诊断结果展示
```

## 核心功能

### 多智能体协作 Pipeline

当用户点击"智能诊断"时，系统按序调度 5 个专业智能体：

| 步骤 | 智能体 | 职责 |
|------|--------|------|
| 1 | 分诊 Agent | 评估紧急程度（低/中/高/紧急），建议就诊科室 |
| 2 | 症状分析 Agent | 提取关键症状，列出可能疾病 |
| 3 | RAG 检索 | 从医学知识库检索相关参考资料 |
| 4 | 诊断 Agent | 综合症状 + RAG上下文 → 初步诊断 + 鉴别诊断 |
| 5 | 治疗建议 Agent | 紧急措施、用药参考、生活方式建议、随访计划 |

### RAG 医学知识检索

- 内置 12 大类常见疾病知识库（感冒、流感、高血压、糖尿病、偏头痛等）
- 关键词匹配 + 语义相似度评分
- 检索结果注入 Agent Prompt 提供医学依据

### Memory 记忆系统

- **短期记忆**：会话内对话历史，注入 LLM 上下文窗口
- **长期记忆**：JSON 文件持久化存储会话记录与患者历史
- **患者档案**：支持按患者 ID 追踪多次诊断历史

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

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/sessions` | 创建会话 |
| GET | `/api/sessions/{id}` | 获取会话信息 |
| POST | `/api/chat` | 发送聊天消息 |
| POST | `/api/diagnosis` | 执行多智能体诊断 |

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
  "references": [{ "content": "...", "source": "Influenza", "relevance": 0.85 }]
}
```

## 技术栈

- **后端**：Python 3.10+ / FastAPI / OpenAI SDK / Pydantic
- **前端**：Vue 3 / Element Plus / Axios / Vite
- **LLM**：兼容 OpenAI API 格式的大语言模型
