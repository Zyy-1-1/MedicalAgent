"""
基于知识图谱的医学知识检索系统（GraphRAG）

使用内存知识图谱进行实体关系建模与图遍历检索，替代传统关键词匹配 RAG。
"""
from typing import Optional
from collections import defaultdict
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun

# ── 节点类型 ──
DISEASE = "disease"
SYMPTOM = "symptom"
TREATMENT = "treatment"
MEDICATION = "medication"
CATEGORY = "category"

# ── 关系类型 ──
HAS_SYMPTOM = "has_symptom"
INDICATES = "indicates"
TREATED_BY = "treated_by"
MEDICATION_FOR = "medication_for"
BELONGS_TO = "belongs_to"
HAS_RISK_FACTOR = "has_risk_factor"
HAS_TREATMENT = "has_treatment"

# ── 关系权重 ──
EDGE_WEIGHTS = {
    HAS_SYMPTOM: 1.0,
    INDICATES: 0.9,
    TREATED_BY: 0.8,
    MEDICATION_FOR: 0.7,
    BELONGS_TO: 0.5,
    HAS_RISK_FACTOR: 0.6,
    HAS_TREATMENT: 0.75,
}


class GraphNode:
    __slots__ = ("id", "name", "name_cn", "type", "content", "keywords")

    def __init__(self, id: str, name: str, name_cn: str, type: str,
                 content: str, keywords: list[str] | None = None):
        self.id = id
        self.name = name
        self.name_cn = name_cn
        self.type = type
        self.content = content
        self.keywords = keywords or []


class GraphEdge:
    __slots__ = ("source", "target", "relation", "weight")

    def __init__(self, source: str, target: str, relation: str, weight: float = 1.0):
        self.source = source
        self.target = target
        self.relation = relation
        self.weight = weight


class MedicalKnowledgeGraph:
    """内存医学知识图谱。支持中英文关键词匹配与 BFS 图遍历检索。"""

    def __init__(self):
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, list[GraphEdge]] = defaultdict(list)
        self._rev_edges: dict[str, list[GraphEdge]] = defaultdict(list)
        self._kw_index: dict[str, set[str]] = defaultdict(set)
        self._build()

    # ── 图构建 ──

    def _add_node(self, node: GraphNode):
        self._nodes[node.id] = node
        for kw in node.keywords:
            self._kw_index[kw.lower()].add(node.id)
        self._kw_index[node.name.lower()].add(node.id)
        self._kw_index[node.name_cn.lower()].add(node.id)

    def _add_edge(self, source: str, target: str, relation: str, weight: float | None = None):
        w = weight if weight is not None else EDGE_WEIGHTS.get(relation, 0.5)
        e = GraphEdge(source, target, relation, w)
        self._edges[source].append(e)
        self._rev_edges[target].append(e)

    # ── 检索接口 ──

    def find_nodes(self, query: str) -> set[str]:
        """根据查询文本匹配节点 ID。"""
        q = query.lower()
        matched: set[str] = set()
        for kw, ids in self._kw_index.items():
            if kw in q or q in kw:
                matched.update(ids)
        return matched

    def traverse(self, seed_ids: set[str], max_depth: int = 2) -> dict[str, float]:
        """BFS 遍历，返回 {node_id: score}。"""
        scores: dict[str, float] = defaultdict(float)

        for sid in seed_ids:
            if sid not in self._nodes:
                continue
            scores[sid] += 1.0  # 直接匹配满分

            visited = {sid}
            queue = [(sid, 0)]
            while queue:
                current, depth = queue.pop(0)
                if depth >= max_depth:
                    continue

                def _walk(edges, reverse: bool):
                    for e in edges:
                        neighbor = e.source if reverse else e.target
                        boost = 1.0 / (depth + 2) * e.weight
                        scores[neighbor] += boost
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append((neighbor, depth + 1))

                _walk(self._edges[current], False)
                _walk(self._rev_edges[current], True)

        return dict(scores)

    def get_node_scores(self, query: str, top_k: int = 3) -> list[tuple[str, float]]:
        """一站式检索：匹配 → 遍历 → 排序。"""
        seed = self.find_nodes(query)
        if not seed:
            return []
        scores = self.traverse(seed)
        # 按分数降序排列
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    def to_documents(self, ranked: list[tuple[str, float]]) -> list[tuple[Document, float]]:
        """将排序结果转为 Document。"""
        results = []
        for nid, score in ranked:
            node = self._nodes.get(nid)
            if not node:
                continue
            doc = Document(
                page_content=node.content,
                metadata={
                    "source": node.name,
                    "source_cn": node.name_cn,
                    "type": node.type,
                    "relevance": min(score / 3.0, 0.99),
                },
            )
            results.append((doc, score))
        return results

    # ── 构建知识图谱 ──

    def _build(self):
        """从结构化医学知识构建图谱。"""
        # fmt: off
        diseases = [
            {
                "id": "d_common_cold", "name": "Common Cold", "name_cn": "普通感冒",
                "content": "普通感冒是一种上呼吸道病毒性感染。症状包括流鼻涕、打喷嚏、喉咙痛、咳嗽和轻度发热。治疗以休息、补水和非处方药为主。大多数病例在7-10天内自行缓解。",
                "keywords": ["cold", "common cold", "感冒", "着凉", "受凉"],
                "symptoms": ["s_runny_nose", "s_sneezing", "s_sore_throat", "s_cough", "s_mild_fever"],
                "treatments": ["t_rest", "t_hydration", "t_otc"],
                "medications": ["m_acetaminophen", "m_ibuprofen", "m_decongestant"],
                "category": "c_respiratory", "risk_factors": [],
            },
            {
                "id": "d_influenza", "name": "Influenza", "name_cn": "流行性感冒",
                "content": "流感是由流感病毒引起的高度传染性呼吸道疾病。症状包括高热、全身酸痛、乏力、干咳和头痛。抗病毒药物在早期有效。建议每年接种疫苗预防。",
                "keywords": ["flu", "influenza", "流感", "甲流"],
                "symptoms": ["s_high_fever", "s_body_ache", "s_fatigue", "s_dry_cough", "s_headache", "s_chills"],
                "treatments": ["t_antiviral", "t_rest", "t_hydration"],
                "medications": ["m_oseltamivir", "m_acetaminophen", "m_ibuprofen"],
                "category": "c_respiratory", "risk_factors": ["r_elderly", "r_immunocompromised"],
            },
            {
                "id": "d_hypertension", "name": "Hypertension", "name_cn": "高血压",
                "content": "高血压是指血压持续读数为130/80 mmHg或更高的状况。常无症状。风险因素包括年龄、肥胖、高盐摄入和家族史。管理包括生活方式的改变和ACE抑制剂等药物。",
                "keywords": ["hypertension", "high blood pressure", "高血压", "血压高"],
                "symptoms": ["s_headache", "s_dizziness", "s_blurred_vision"],
                "treatments": ["t_lifestyle_change", "t_diet"],
                "medications": ["m_ace_inhibitor", "m_calcium_blocker", "m_diuretic"],
                "category": "c_cardiovascular", "risk_factors": ["r_obesity", "r_high_salt", "r_age"],
            },
            {
                "id": "d_diabetes", "name": "Type 2 Diabetes", "name_cn": "2型糖尿病",
                "content": "2型糖尿病是一种以胰岛素抵抗为特征的代谢性疾病。症状包括口渴、尿频、乏力、视力模糊和伤口愈合缓慢。管理包括饮食、运动、血糖监测和二甲双胍等药物。",
                "keywords": ["diabetes", "diabetic", "糖尿病", "血糖高", "糖"],
                "symptoms": ["s_thirst", "s_frequent_urination", "s_fatigue", "s_blurred_vision"],
                "treatments": ["t_diet", "t_exercise", "t_glucose_monitoring"],
                "medications": ["m_metformin", "m_insulin"],
                "category": "c_metabolic", "risk_factors": ["r_obesity", "r_age", "r_family_history"],
            },
            {
                "id": "d_migraine", "name": "Migraine", "name_cn": "偏头痛",
                "content": "偏头痛是一种神经系统疾病，引起剧烈头痛，常伴恶心、呕吐、畏光和畏声。诱因包括压力、特定食物、激素变化和睡眠紊乱。治疗包括止痛药、曲普坦类药物和预防性药物。",
                "keywords": ["migraine", "偏头痛", "头痛"],
                "symptoms": ["s_headache", "s_nausea", "s_light_sensitivity", "s_sound_sensitivity"],
                "treatments": ["t_rest", "t_avoid_triggers"],
                "medications": ["m_triptan", "m_ibuprofen", "m_acetaminophen"],
                "category": "c_neurological", "risk_factors": ["r_stress", "r_sleep"],
            },
            {
                "id": "d_gastroenteritis", "name": "Gastroenteritis", "name_cn": "肠胃炎",
                "content": "肠胃炎是胃和肠道的炎症，通常由病毒或细菌感染引起。症状包括腹泻、呕吐、腹部绞痛和恶心。治疗重点是补水和电解质补充。多数病例在数天内自愈。",
                "keywords": ["gastroenteritis", "stomach", "肠胃炎", "腹泻", "拉肚子"],
                "symptoms": ["s_diarrhea", "s_vomiting", "s_nausea", "s_abdominal_pain"],
                "treatments": ["t_rehydration", "t_electrolyte", "t_rest"],
                "medications": [],
                "category": "c_digestive", "risk_factors": [],
            },
            {
                "id": "d_pneumonia", "name": "Pneumonia", "name_cn": "肺炎",
                "content": "肺炎是肺部感染导致气囊发炎。症状包括咳痰、发热、寒战、呼吸急促和胸痛。细菌性肺炎用抗生素治疗。病毒性肺炎需要支持性护理。呼吸困难时需立即就医。",
                "keywords": ["pneumonia", "肺炎"],
                "symptoms": ["s_cough", "s_fever", "s_shortness_breath", "s_chest_pain", "s_chills"],
                "treatments": ["t_antibiotics", "t_supportive_care", "t_rest"],
                "medications": ["m_antibiotics"],
                "category": "c_respiratory", "risk_factors": ["r_elderly", "r_immunocompromised"],
            },
            {
                "id": "d_asthma", "name": "Asthma", "name_cn": "哮喘",
                "content": "哮喘是一种慢性呼吸系统疾病，伴有气道炎症。症状包括喘息、呼吸急促、胸闷和咳嗽（尤其在夜间或运动时）。管理包括吸入支气管扩张剂和皮质类固醇。避免已知触发因素。",
                "keywords": ["asthma", "哮喘", "气喘"],
                "symptoms": ["s_wheezing", "s_shortness_breath", "s_chest_tightness", "s_cough"],
                "treatments": ["t_inhaler", "t_avoid_triggers"],
                "medications": ["m_bronchodilator", "m_corticosteroid"],
                "category": "c_respiratory", "risk_factors": ["r_allergy", "r_exercise"],
            },
            {
                "id": "d_anxiety", "name": "Anxiety Disorders", "name_cn": "焦虑症",
                "content": "焦虑症涉及过度担忧和恐惧。身体症状包括心跳加速、出汗、颤抖、乏力和睡眠障碍。治疗结合心理治疗（CBT）和药物（SSRIs）。运动和冥想等生活方式调整有助于控制症状。",
                "keywords": ["anxiety", "anxious", "焦虑", "紧张", "恐慌"],
                "symptoms": ["s_rapid_heartbeat", "s_sweating", "s_trembling", "s_fatigue", "s_sleep_issues"],
                "treatments": ["t_cbt", "t_meditation", "t_exercise"],
                "medications": ["m_ssri"],
                "category": "c_mental_health", "risk_factors": ["r_stress", "r_family_history"],
            },
            {
                "id": "d_covid", "name": "COVID-19", "name_cn": "新型冠状病毒感染",
                "content": "COVID-19由SARS-CoV-2病毒引起。症状范围从轻度（发热、咳嗽、乏力、味嗅觉丧失）到重度（呼吸困难、胸痛）。预防包括疫苗接种、佩戴口罩和通风。高危患者可用抗病毒治疗（Paxlovid）。",
                "keywords": ["covid", "coronavirus", "新冠", "新型冠状病毒"],
                "symptoms": ["s_fever", "s_cough", "s_fatigue", "s_loss_smell", "s_loss_taste",
                           "s_shortness_breath", "s_chest_pain"],
                "treatments": ["t_antiviral", "t_supportive_care", "t_vaccination"],
                "medications": ["m_paxlovid", "m_acetaminophen"],
                "category": "c_respiratory", "risk_factors": ["r_elderly", "r_immunocompromised"],
            },
            {
                "id": "d_anemia", "name": "Anemia", "name_cn": "贫血",
                "content": "贫血是指健康红细胞不足的状况。常见类型为缺铁性贫血。症状包括乏力、虚弱、脸色苍白、呼吸短促、头晕和手脚冰凉。治疗取决于原因：补充铁剂、B12或处理基础疾病。",
                "keywords": ["anemia", "贫血", "气血不足"],
                "symptoms": ["s_fatigue", "s_weakness", "s_pale", "s_dizziness", "s_shortness_breath"],
                "treatments": ["t_diet", "t_supplement"],
                "medications": ["m_iron_supplement", "m_vitamin_b12"],
                "category": "c_blood", "risk_factors": [],
            },
            {
                "id": "d_eczema", "name": "Skin Allergy / Eczema", "name_cn": "皮肤过敏/湿疹",
                "content": "湿疹（特应性皮炎）引起红色、瘙痒、发炎的皮肤。触发因素包括过敏原、刺激物、压力和天气变化。管理包括保湿霜、外用皮质类固醇和避免触发因素。严重病例可能需要免疫调节剂或光疗。",
                "keywords": ["eczema", "rash", "skin", "湿疹", "皮肤过敏", "皮疹"],
                "symptoms": ["s_rash", "s_itching", "s_redness", "s_dry_skin"],
                "treatments": ["t_moisturizer", "t_avoid_triggers"],
                "medications": ["m_corticosteroid", "m_immunomodulator"],
                "category": "c_dermatology", "risk_factors": ["r_allergy", "r_stress"],
            },
        ]
        # fmt: on

        symptoms = {
            "s_headache": ("头痛", "headache", "头部疼痛"),
            "s_fever": ("发热", "fever", "体温升高"),
            "s_mild_fever": ("低热", "mild fever", "轻度发热"),
            "s_high_fever": ("高热", "high fever", "高烧"),
            "s_cough": ("咳嗽", "cough", "咳嗽症状"),
            "s_dry_cough": ("干咳", "dry cough", "无痰咳嗽"),
            "s_sore_throat": ("喉咙痛", "sore throat", "咽喉疼痛"),
            "s_runny_nose": ("流鼻涕", "runny nose", "鼻部分泌物"),
            "s_sneezing": ("打喷嚏", "sneezing", "喷嚏"),
            "s_body_ache": ("全身酸痛", "body ache", "肌肉疼痛"),
            "s_fatigue": ("乏力", "fatigue", "疲劳无力"),
            "s_dizziness": ("头晕", "dizziness", "眩晕"),
            "s_nausea": ("恶心", "nausea", "反胃想吐"),
            "s_vomiting": ("呕吐", "vomiting", "呕吐症状"),
            "s_diarrhea": ("腹泻", "diarrhea", "拉肚子"),
            "s_abdominal_pain": ("腹痛", "abdominal pain", "肚子疼"),
            "s_shortness_breath": ("呼吸急促", "shortness of breath", "气短"),
            "s_chest_pain": ("胸痛", "chest pain", "胸部疼痛"),
            "s_chest_tightness": ("胸闷", "chest tightness", "胸部压迫感"),
            "s_wheezing": ("喘息", "wheezing", "呼吸有哨音"),
            "s_blurred_vision": ("视力模糊", "blurred vision", "看不清楚"),
            "s_thirst": ("口渴", "thirst", "口干想喝水"),
            "s_frequent_urination": ("尿频", "frequent urination", "小便频繁"),
            "s_light_sensitivity": ("畏光", "light sensitivity", "怕光"),
            "s_sound_sensitivity": ("畏声", "sound sensitivity", "怕声音"),
            "s_rapid_heartbeat": ("心跳加速", "rapid heartbeat", "心慌"),
            "s_sweating": ("出汗", "sweating", "多汗"),
            "s_trembling": ("颤抖", "trembling", "发抖"),
            "s_sleep_issues": ("睡眠障碍", "sleep issues", "失眠"),
            "s_loss_smell": ("味觉丧失", "loss of smell", "闻不到味道"),
            "s_loss_taste": ("嗅觉丧失", "loss of taste", "尝不出味道"),
            "s_weakness": ("虚弱", "weakness", "无力"),
            "s_pale": ("脸色苍白", "pale", "面色苍白"),
            "s_rash": ("皮疹", "rash", "皮肤起疹"),
            "s_itching": ("瘙痒", "itching", "皮肤痒"),
            "s_redness": ("发红", "redness", "皮肤发红"),
            "s_dry_skin": ("皮肤干燥", "dry skin", "皮肤干"),
            "s_chills": ("寒战", "chills", "打冷颤"),
        }

        treatments = {
            "t_rest": ("休息", "rest", "充分休息，避免劳累"),
            "t_hydration": ("补水", "hydration", "多饮水保持水分"),
            "t_otc": ("非处方药", "OTC medication", "使用非处方药物缓解症状"),
            "t_antiviral": ("抗病毒治疗", "antiviral treatment", "抗病毒药物治疗"),
            "t_antibiotics": ("抗生素治疗", "antibiotics", "抗生素治疗细菌感染"),
            "t_supportive_care": ("支持性护理", "supportive care", "对症支持治疗"),
            "t_lifestyle_change": ("生活方式改变", "lifestyle change", "调整生活习惯"),
            "t_diet": ("饮食调整", "diet", "调整饮食结构"),
            "t_exercise": ("运动", "exercise", "规律体育锻炼"),
            "t_glucose_monitoring": ("血糖监测", "glucose monitoring", "定期监测血糖"),
            "t_avoid_triggers": ("避免诱因", "avoid triggers", "识别并避免诱发因素"),
            "t_rehydration": ("补液", "rehydration", "补充水分和电解质"),
            "t_electrolyte": ("电解质补充", "electrolyte", "补充电解质"),
            "t_inhaler": ("吸入治疗", "inhaler", "使用吸入装置给药"),
            "t_cbt": ("认知行为疗法", "CBT", "心理治疗"),
            "t_meditation": ("冥想", "meditation", "正念冥想放松"),
            "t_vaccination": ("疫苗接种", "vaccination", "接种疫苗预防"),
            "t_moisturizer": ("保湿", "moisturizer", "使用保湿产品"),
            "t_supplement": ("营养补充", "supplement", "补充营养素"),
        }

        medications = {
            "m_acetaminophen": ("对乙酰氨基酚", "Acetaminophen", "解热镇痛药"),
            "m_ibuprofen": ("布洛芬", "Ibuprofen", "非甾体抗炎药"),
            "m_decongestant": ("减充血剂", "Decongestant", "缓解鼻塞"),
            "m_oseltamivir": ("奥司他韦", "Oseltamivir", "抗流感病毒药"),
            "m_ace_inhibitor": ("ACE抑制剂", "ACE Inhibitor", "降压药"),
            "m_calcium_blocker": ("钙通道阻滞剂", "Calcium Channel Blocker", "降压药"),
            "m_diuretic": ("利尿剂", "Diuretic", "降压药"),
            "m_metformin": ("二甲双胍", "Metformin", "降糖药"),
            "m_insulin": ("胰岛素", "Insulin", "降糖药"),
            "m_triptan": ("曲普坦", "Triptan", "偏头痛特效药"),
            "m_bronchodilator": ("支气管扩张剂", "Bronchodilator", "缓解喘息"),
            "m_corticosteroid": ("皮质类固醇", "Corticosteroid", "抗炎药"),
            "m_ssri": ("SSRI", "SSRI", "抗抑郁焦虑药"),
            "m_paxlovid": ("Paxlovid", "Paxlovid", "抗新冠药"),
            "m_iron_supplement": ("铁剂", "Iron Supplement", "补铁"),
            "m_vitamin_b12": ("维生素B12", "Vitamin B12", "补充维生素"),
            "m_immunomodulator": ("免疫调节剂", "Immunomodulator", "调节免疫"),
            "m_antibiotics": ("抗生素", "Antibiotics", "抗菌药物"),
        }

        categories = {
            "c_respiratory": ("呼吸系统疾病", "Respiratory Diseases", "影响呼吸系统的疾病"),
            "c_cardiovascular": ("心血管疾病", "Cardiovascular Diseases", "影响心脏和血管的疾病"),
            "c_metabolic": ("代谢性疾病", "Metabolic Diseases", "影响代谢过程的疾病"),
            "c_neurological": ("神经系统疾病", "Neurological Diseases", "影响神经系统的疾病"),
            "c_digestive": ("消化系统疾病", "Digestive Diseases", "影响消化系统的疾病"),
            "c_mental_health": ("心理健康", "Mental Health", "心理健康相关"),
            "c_blood": ("血液疾病", "Blood Diseases", "影响血液的疾病"),
            "c_dermatology": ("皮肤疾病", "Dermatology", "皮肤相关疾病"),
        }

        risk_factors = {
            "r_elderly": ("老年人", "elderly", "年龄较大"),
            "r_immunocompromised": ("免疫功能低下", "immunocompromised", "免疫力弱"),
            "r_obesity": ("肥胖", "obesity", "体重超重"),
            "r_high_salt": ("高盐饮食", "high salt diet", "摄入盐分过多"),
            "r_age": ("年龄因素", "age", "年龄相关风险"),
            "r_family_history": ("家族史", "family history", "有家族遗传史"),
            "r_stress": ("压力", "stress", "精神压力大"),
            "r_sleep": ("睡眠不足", "sleep deprivation", "睡眠质量差"),
            "r_allergy": ("过敏体质", "allergy", "过敏史"),
            "r_exercise": ("运动诱发", "exercise-induced", "运动后加重"),
        }

        # 添加所有节点
        for d in diseases:
            self._add_node(GraphNode(d["id"], d["name"], d["name_cn"], DISEASE, d["content"], d["keywords"]))

        for sid, (cn, en, desc) in symptoms.items():
            self._add_node(GraphNode(sid, en, cn, SYMPTOM, desc, [cn, en]))

        for tid, (cn, en, desc) in treatments.items():
            self._add_node(GraphNode(tid, en, cn, TREATMENT, desc, [cn, en]))

        for mid, (cn, en, desc) in medications.items():
            self._add_node(GraphNode(mid, en, cn, MEDICATION, desc, [cn, en]))

        for cid, (cn, en, desc) in categories.items():
            self._add_node(GraphNode(cid, en, cn, CATEGORY, desc, [cn, en]))

        for rid, (cn, en, desc) in risk_factors.items():
            # 将风险因素作为症状节点或单独处理
            self._add_node(GraphNode(rid, en, cn, SYMPTOM, desc, [cn, en]))

        # 添加边（疾病关系）
        for d in diseases:
            did = d["id"]
            # 症状边
            for sid in d["symptoms"]:
                self._add_edge(did, sid, HAS_SYMPTOM)
                self._add_edge(sid, did, INDICATES)
            # 治疗边
            for tid in d["treatments"]:
                self._add_edge(did, tid, HAS_TREATMENT)
                self._add_edge(tid, did, TREATED_BY)
            # 药物边
            for mid in d["medications"]:
                self._add_edge(did, mid, MEDICATION_FOR)
                self._add_edge(mid, did, MEDICATION_FOR)
            # 分类边
            self._add_edge(did, d["category"], BELONGS_TO)
            self._add_edge(d["category"], did, BELONGS_TO)
            # 风险因素边
            for rid in d["risk_factors"]:
                self._add_edge(did, rid, HAS_RISK_FACTOR)

    # ── 上下文格式化 ──

    def format_context(self, ranked: list[tuple[str, float]], top_k: int = 3) -> str:
        """将图检索结果格式化为纯文本上下文。"""
        docs = self.to_documents(ranked)[:top_k]
        if not docs:
            return ""
        parts = ["[医学知识图谱参考]"]
        for i, (doc, score) in enumerate(docs):
            src = doc.metadata.get("source_cn", doc.metadata["source"])
            rel = doc.metadata["relevance"]
            parts.append(f"\n参考 {i+1}（{src}，相关度: {rel:.2f}）：\n{doc.page_content}")
        return "\n".join(parts)


# ── 全局单例 ──
_knowledge_graph = MedicalKnowledgeGraph()


class GraphRetriever(BaseRetriever):
    """基于图遍历的医学知识检索器，实现 LangChain BaseRetriever 接口。"""

    graph: MedicalKnowledgeGraph = _knowledge_graph
    top_k: int = 3

    def __init__(self, top_k: int = 3, **kwargs):
        # BaseRetriever 是 Pydantic v2 模型，字段必须在 model 中声明
        super().__init__(top_k=top_k, graph=_knowledge_graph, **kwargs)

    def _get_relevant_documents(
        self, query: str, *, run_manager: Optional[CallbackManagerForRetrieverRun] = None
    ) -> list[Document]:
        ranked = self.graph.get_node_scores(query, top_k=self.top_k)
        docs = self.graph.to_documents(ranked)
        return [doc for doc, _ in docs]

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        """兼容旧接口：返回 dict 格式的结果。"""
        ranked = self.graph.get_node_scores(query, top_k=top_k)
        docs = self.graph.to_documents(ranked)
        return [
            {
                "content": doc.page_content,
                "source": doc.metadata["source"],
                "source_cn": doc.metadata["source_cn"],
                "type": doc.metadata["type"],
                "relevance": doc.metadata["relevance"],
            }
            for doc, _ in docs
        ]

    def get_context(self, query: str, top_k: int = 3) -> str:
        """将检索结果格式化为文本上下文。"""
        ranked = self.graph.get_node_scores(query, top_k=top_k)
        return self.graph.format_context(ranked, top_k=top_k)


retriever = GraphRetriever()
