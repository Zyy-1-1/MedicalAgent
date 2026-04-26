# Medical Diagnosis Multi-Agent System

基于 **AutoGen** + **LangChain** 的多智能体协作医疗诊断系统。使用 **AutoGen AssistantAgent** 构建各角色智能体，**LangChain** 管理 Prompt 模板和结构化输出解析，**GraphRAG**（知识图谱）提供医学知识检索，临时内存管理会话。

> 免责声明：本系统仅供学习和技术参考，所有 AI 生成内容不构成医疗建议。请务必咨询持牌医疗专业人士。

---

## 项目架构

```
MedicalAgent/
├── .env                              # API Key 与服务配置
├── backend/
│   ├── main.py                       # FastAPI 入口 + CORS
│   ├── config.py                     # 环境变量配置
│   ├── requirements.txt              # Python 依赖
│   ├── agents/
│   │   ├── base.py                   # AutoGen LLM 配置 + 智能体执行器 + LangChain 解析器
│   │   ├── triage.py                 # 分诊智能体（AutoGen AssistantAgent）
│   │   ├── symptom_analyzer.py       # 症状分析智能体（AutoGen AssistantAgent）
│   │   ├── diagnosis.py              # 诊断智能体（AutoGen AssistantAgent）
│   │   ├── treatment.py              # 治疗建议智能体（AutoGen AssistantAgent）
│   │   ├── chat_agent.py             # 对话智能体（LangChain + GraphRAG）
│   │   └── orchestrator.py           # 多智能体顺序编排器（替代 LangGraph）
│   ├── rag/
│   │   └── __init__.py               # 医学知识图谱 + GraphRAG 检索器
│   ├── memory/
│   │   └── __init__.py               # 临时内存会话管理（零持久化）
│   ├── models/
│   │   └── __init__.py               # Pydantic 数据模型
│   └── routers/
│       ├── chat.py                   # 会话与聊天 API
│       └── diagnosis.py              # 诊断 API
└── frontend/
    ├── package.json
    ├── vite.config.js                # API 代理（:5173 → :8000）
    └── src/
        ├── main.js
        ├── App.vue                   # 医疗主题头部
        ├── api/index.js              # Axios API 客户端
        ├── views/Home.vue            # 三栏布局
        └── components/
            ├── PatientForm.vue       # 患者信息表单
            ├── ChatPanel.vue         # 聊天 + 诊断面板
            └── DiagnosisResult.vue   # 诊断结果展示
```

---

## 核心功能

### AutoGen 多智能体系统

系统使用 **AutoGen**（Microsoft 的多智能体对话框架）构建 4 个角色专精的 AssistantAgent：

| 智能体 | 角色 | 职责 |
|--------|------|------|
| `TriageAgent` | 分诊护士 | 评估紧急程度，建议就诊科室 |
| `SymptomAnalyst` | 症状分析师 | 提取关键症状，列出可能疾病 |
| `Diagnostician` | 诊断医师 | 综合症状 + 图检索知识 → 诊断 |
| `TreatmentAdvisor` | 治疗顾问 | 开治疗计划（措施、用药、生活建议） |

每个智能体是 `autogen.AssistantAgent` 实例，拥有独立的 **system message** 和 **LLM 配置**，通过 `ConversableAgent(UserProxy)` 发起单轮对话调用。

#### 调用机制

```python
# agents/base.py
_user_proxy = ConversableAgent("UserProxy", llm_config=False, human_input_mode="NEVER")

async def run_agent(agent: AssistantAgent, message: str) -> str:
    result = await _user_proxy.a_initiate_chat(
        recipient=agent,
        message=message,
        max_turns=1,       # 单轮：发消息 → 收回复 → 结束
    )
    return result.chat_history[-1]["content"]
```

### 顺序诊断流水线（替代 LangGraph）

不使用 LangGraph StateGraph，改用**简单顺序编排**：

```
START
  │
  ├─ Step 1: TriageAgent ───────────── AutoGen 智能体 #1
  │     输出 → { urgency, recommended_action, specialty }
  │
  ├─ Step 2: SymptomAnalyst ────────── AutoGen 智能体 #2
  │     输出 → { key_symptoms[], possible_conditions[], requires_emergency }
  │
  ├─ Step 3: GraphRAG Retrieval ────── 图遍历（非 LLM）
  │     输出 → 知识图谱 Top-3 文档 + 格式化上下文
  │
  ├─ Step 4: Diagnostician ─────────── AutoGen 智能体 #3
  │     输入 = 症状 + 患者信息 + GraphRAG 上下文
  │     输出 → { primary_diagnosis, differential_diagnoses[], confidence, reasoning }
  │
  ├─ Step 5: TreatmentAdvisor ──────── AutoGen 智能体 #4
  │     输入 = 诊断结果 + 症状 + 患者信息 + GraphRAG 上下文
  │     输出 → { immediate_actions[], medications[], lifestyle[], follow_up }
  │
  └─ Step 6: Compile ───────────────── 纯 Python 拼接
        输出 → Markdown 回复
```

与 LangGraph 方案的关键区别：

| 特性 | LangGraph | AutoGen 顺序流水线 |
|------|-----------|-------------------|
| 状态管理 | `StateGraph(TypedDict)` 全局状态 | Python dict 手动传递 |
| 节点 | 函数节点 | AutoGen AssistantAgent |
| 图编译 | `graph.compile()` 构建 DAG | 无编译，直接执行 |
| 灵活性 | 支持条件边、循环、并行 | 固定顺序，简单直接 |
| 心智负担 | 需要理解图概念 | 纯函数调用，易于调试 |

### GraphRAG 知识图谱检索

**80+ 节点** + **200+ 关系边** 的医学知识图谱：

| 节点类型 | 数量 | 示例 |
|----------|------|------|
| Disease | 12 | 感冒、流感、高血压、糖尿病 |
| Symptom | 36+ | 头痛、发热、咳嗽、乏力 |
| Treatment | 18+ | 休息、补水、抗生素治疗 |
| Medication | 18+ | 对乙酰氨基酚、二甲双胍 |
| Category | 8 | 呼吸系统、心血管 |

**检索流程**：关键词匹配 → BFS 图遍历（深度 2）→ 距离加权排序 → Top-K 输出

### LangChain Prompt 与结构化输出

智能体虽由 AutoGen 驱动，但 **LangChain** 负责两件事：

1. **`PydanticOutputParser`** — 解析智能体输出的 JSON 为 Pydantic 模型，含三级兜底：
   - LangChain 解析器 → 手动 JSON 解析 → 默认值
2. **`ChatOpenAI`** — 用于 `chat_agent.py` 的多轮对话场景（需要 `MessagesPlaceholder`）

### 临时内存管理

- **会话记忆**：`ChatMessageHistory` 存储对话历史，限制最近 10 轮
- **零持久化**：所有数据仅在内存中，应用重启后自动清除
- **无文件写入**：不生成任何数据文件

---

## 关键技术栈

| 层次 | 技术 |
|------|------|
| **智能体框架** | AutoGen (pyautogen) — AssistantAgent + ConversableAgent |
| **Prompt 管理** | LangChain — ChatPromptTemplate、PydanticOutputParser |
| **LLM 调用** | LangChain ChatOpenAI + AutoGen LLM config（统一接入 OpenAI API） |
| **知识检索** | GraphRAG — 内存知识图谱 + BFS 图遍历 |
| **Web 框架** | FastAPI + Pydantic |
| **前端** | Vue 3 + Element Plus + Axios |
| **会话记忆** | ChatMessageHistory（临时内存） |

---

## 文件结构速览

### 智能体文件

| 文件 | 导出的关键内容 | 职责 |
|------|---------------|------|
| `agents/base.py` | `get_autogen_llm_config()`, `run_agent()`, `parse_json_response()`, `get_llm()`, `get_parser()` | 共享工具函数 |
| `agents/triage.py` | `triage_agent` (AssistantAgent), `async triage()` | 分诊评估 |
| `agents/symptom_analyzer.py` | `analysis_agent` (AssistantAgent), `async analyze()` | 症状分析 |
| `agents/diagnosis.py` | `diagnosis_agent` (AssistantAgent), `async diagnose()` | 诊断推理 |
| `agents/treatment.py` | `treatment_agent` (AssistantAgent), `async recommend()` | 治疗建议 |
| `agents/chat_agent.py` | `async handle_chat()` | 自由对话 |
| `agents/orchestrator.py` | `async run_diagnosis_pipeline()` | 6 步顺序编排 |

### API 路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/sessions` | 创建会话 |
| GET | `/api/sessions/{id}` | 获取会话信息 |
| POST | `/api/chat` | 发送聊天消息 |
| POST | `/api/diagnosis` | 执行多智能体诊断 |

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

## 诊断请求示例

```bash
curl -X POST http://localhost:8000/api/diagnosis \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test123",
    "symptoms": "头痛、发烧38.5度、全身酸痛已持续2天",
    "duration": "2天",
    "severity_level": "medium",
    "patient_info": {
      "age": 35,
      "gender": "male",
      "medical_history": "无重大病史"
    }
  }'
```

## 诊断响应结构

```json
{
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
    "follow_up": "如症状加重或持续超过7天，请复诊",
    "disclaimer": "本内容为AI生成的医疗信息仅供参考..."
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
