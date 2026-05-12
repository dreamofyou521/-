from genre_library_manager import genre_lib
import streamlit as st
import re
import json
import time
from openai import OpenAI
import ui_controller

# --- 常量配置 ---
DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_API_KEY = "ollama"
DEFAULT_MODEL_NAME = "qwen2.5:latest"

client = OpenAI(base_url=DEFAULT_BASE_URL, api_key=DEFAULT_API_KEY)










# --- 核心功能函数 ---

def _call_llm_for_json(prompt):
    """通用 LLM 调用函数，返回 JSON"""
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是一个专业的叙事结构分析师和创意生成器。请只输出 JSON 数据。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"} 
        )
        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        st.error(f"LLM 调用失败: {e}")
        st.caption("提示: 请检查 Ollama 是否正在运行，以及模型名称是否正确。")
        return None

def extract_genre_from_text(sample_text: str):
    """调用 LLM 自动提取小说片段的流派特征"""
    prompt = f"""
    深入分析以下小说片段的文风、情感基调、常见套路和核心特征。
    请提取并生成一份高质量的流派预设（Genre Profile），帮助生成引擎完美复刻这种风格。
    必须返回 JSON 格式，包含以下字段：
    - "name": 流派的具体名称（如"克苏鲁修仙"、“赛博朋克黑客”、“古龙风武侠”）。
    - "id": 简短的纯英文小写ID，可带下划线（如"cthulhu_cult"）。
    - "system_prompt": 扮演这类小说家的 System Prompt，详细描述该流派文风的语言节奏、感官描写风格、句式长短偏好（不少于100字）。
    - "network_prompt": 该流派的情节推进规律，用于指导大纲节点生成（如"典型的套路包括：拍卖会打脸、跌入悬崖获得奇遇、隐秘组织干涉"）。
    
    小说片段参考：
    {sample_text}
    """
    return _call_llm_for_json(prompt)

def _merge_future_events(current_net, future_events):
    """合并预测的未来事件，处理 ID 冲突"""
    existing_ids = {n['id'] for n in current_net.get('nodes', [])}
    timestamp = int(time.time())
    
    id_mapping = {}
    valid_new_nodes = []
    
    for node in future_events.get('nodes', []):
        original_id = node['id']
        if original_id in existing_ids:
            new_id = f"{original_id}_{timestamp}"
            id_mapping[original_id] = new_id
            node['id'] = new_id
        valid_new_nodes.append(node)
        
    valid_new_edges = []
    for edge in future_events.get('edges', []):
        edge['source'] = id_mapping.get(edge['source'], edge['source'])
        edge['target'] = id_mapping.get(edge['target'], edge['target'])
        valid_new_edges.append(edge)

    current_net['nodes'].extend(valid_new_nodes)
    current_net['edges'].extend(valid_new_edges)
    return current_net, len(valid_new_nodes)

def verify_and_summarize_network(network, raw_record):
    """使用 LLM 核查事件网络的准确性，并将其精炼为高质量的中文大纲描述"""
    network_json = json.dumps(network, ensure_ascii=False, indent=2)
    sentences = raw_record.get("sentences", []) if isinstance(raw_record, dict) else []
    raw_text = " ".join(sentences)[:1500] if sentences else str(raw_record)[:1500]
    
    prompt = f"""
    你是一个严谨的事件库建设专家与本土化翻译大师。
    以下是通过基础算法提取出的“初步事件网络”，以及相对应的原始文本片段全集或缩略版本。
    
    【原始上下文参考】：
    {raw_text}
    
    【初步事件网络】：
    {network_json}
    
    【你的任务】：
    1. **精准度核实与修正 (Accuracy Verification)**：仔细检查原文本，验证事件的触发词是否准确捕捉了核心动作与含意。如果初步提取有误（比如名词当动词、主客体倒置、或是英文生硬翻译），你必须修复节点名称 (label) 和描述 (description)。
    2. **全中文精炼优化 (Chinese Localization)**：将所有的事件名称、描述和连线标签统一转换为自然、流畅且不失原文精度的中文。
    3. **查证总结报告 (Verification Report)**：写一段详实的核查日志（查证总结报告）。你需要向用户说明：原始事件是否准确？你纠正了哪些错漏？整体讲述的故事大意是什么？
    
    务必返回一个合法的 JSON 对象，不包含任何外部 Markdown。
    【核心警告】：不允许使用省略号！你必须在 `nodes` 和 `edges` 数组中返回全部汉化并修正后的事件节点对象和连线对象（包含 id, label, description, type, source, target 等所有原始层级字段）。若数组为空，将导致系统崩溃！
    格式如下：
    {{
      "verification_report": "核查日志与中文故事大意...",
      "nodes": [ {{ "id": "1", "label": "晨练", "description": "进行晨跑", "type": "event" }} ],
      "edges": [ {{ "source": "1", "target": "2", "label": "随后", "relation_type": "temporal" }} ]
    }}
    """
    return _call_llm_for_json(prompt)

def extract_event_network(input_text, author_context=None):
    """调用本地 LLM 提取事件网络"""
    
    # --- 新增：极速处理特定格式的学术数据集 JSON (如 ACE05/ERE 格式) ---
    try:
        data = json.loads(input_text)
        if isinstance(data, dict) and "sentences" in data and ("event_mentions" in data or "events" in data):
            # 极速解析模式：直接将 event_mentions/events 转换为 nodes，完全跳过 LLM 提取，实现秒级出图
            nodes = []
            edges = []
            
            sentences = data.get("sentences", [])
            event_mentions = data.get("event_mentions") or data.get("events", [])
            
            # 标准化 event_mentions 结构
            standardized_events = []
            for i, em in enumerate(event_mentions):
                if 'mention' in em and isinstance(em['mention'], list) and len(em['mention']) > 0:
                    # 处理带有 mention 列表的格式
                    mention_data = em['mention'][0]
                    standardized_events.append({
                        "id": em.get("id", str(i)),
                        "trigger_word": mention_data.get("trigger_word", "Event"),
                        "type": em.get("type", "event"),
                        "sent_id": mention_data.get("sent_id", 0),
                        "offset": mention_data.get("offset", [0,0])
                    })
                else:
                    # 处理原始格式
                    standardized_events.append({
                        "id": em.get("id", str(i)),
                        "trigger_word": em.get("trigger_word", "Event"),
                        "type": em.get("type", "event"),
                        "sent_id": em.get("sent_id", 0),
                        "offset": em.get("offset", [0,0])
                    })
            
            # 按句子ID和偏移量排序，恢复时间线顺序
            standardized_events.sort(key=lambda x: (x.get("sent_id", 0), x.get("offset", [0,0])[0]))
            
            # 为了防止图谱过大导致前端卡顿，最多保留 35 个核心事件
            if len(standardized_events) > 35:
                standardized_events = standardized_events[:35]
                
            # 建立 ID 到节点的映射，方便后续添加关系
            node_ids = set()
                
            for i, em in enumerate(standardized_events):
                node_id = em.get("id", str(i))
                trigger = em.get("trigger_word", "Event")
                event_type = em.get("type", "event")
                sent_id = em.get("sent_id", 0)
                
                desc = sentences[sent_id] if sent_id < len(sentences) else trigger
                
                # 简单映射事件类型到图谱节点类型
                node_type = "event"
                event_type_lower = event_type.lower()
                if any(kw in event_type_lower for kw in ["attack", "die", "hostile", "conflict", "kill", "terrorism", "massacre"]):
                    node_type = "conflict"
                elif any(kw in event_type_lower for kw in ["end", "release", "liberation", "rescue"]):
                    node_type = "resolution"
                elif any(kw in event_type_lower for kw in ["plan", "prepare", "getready", "statement"]):
                    node_type = "setup"
                
                nodes.append({
                    "id": node_id,
                    "label": trigger,
                    "description": f"[{event_type}] {desc[:40]}...",
                    "type": node_type,
                    "salience": 8 if node_type in ["conflict", "resolution"] else 5
                })
                node_ids.add(node_id)
                
            # 尝试从数据集中提取显式关系
            temporal_rels = data.get("temporal_relations", {})
            causal_rels = data.get("causal_relations", {})
            
            has_explicit_edges = False
            
            # 处理时间关系
            if isinstance(temporal_rels, dict):
                for rel_type, pairs in temporal_rels.items():
                    if isinstance(pairs, list):
                        for pair in pairs:
                            if len(pair) == 2 and pair[0] in node_ids and pair[1] in node_ids:
                                edges.append({
                                    "source": pair[0],
                                    "target": pair[1],
                                    "label": rel_type,
                                    "relation_type": "temporal"
                                })
                                has_explicit_edges = True
                                
            # 处理因果关系
            if isinstance(causal_rels, dict):
                for rel_type, pairs in causal_rels.items():
                    if isinstance(pairs, list):
                        for pair in pairs:
                            if len(pair) == 2 and pair[0] in node_ids and pair[1] in node_ids:
                                edges.append({
                                    "source": pair[0],
                                    "target": pair[1],
                                    "label": rel_type,
                                    "relation_type": "causal"
                                })
                                has_explicit_edges = True
            
            # 如果没有显式关系，则回退到基于句子顺序的隐式关系构建
            if not has_explicit_edges:
                for i in range(1, len(standardized_events)):
                    em = standardized_events[i]
                    prev_em = standardized_events[i-1]
                    node_id = em.get("id", str(i))
                    prev_node_id = prev_em.get("id", str(i-1))
                    
                    if prev_em.get("sent_id") == em.get("sent_id"):
                        edges.append({
                            "source": prev_node_id,
                            "target": node_id,
                            "label": "同句关联",
                            "relation_type": "concurrent"
                        })
                    else:
                        edges.append({
                            "source": prev_node_id,
                            "target": node_id,
                            "label": "时间顺承",
                            "relation_type": "temporal"
                        })
                        
            if nodes:
                return {"nodes": nodes, "edges": edges}
            
    except Exception:
        pass
    # ------------------------------------------

    context_prompt = ""
    if author_context:
        target_audience = author_context.get('target_audience', {})
        audience_desc = f"目标读者：{target_audience.get('age', '全年龄')}，偏好：{target_audience.get('preference', '无')}"
        
        context_prompt = f"""
    【作者设定参考】：
    - 人物关系：{author_context.get('characters', '未指定')}
    - 世界观：{author_context.get('world_setting', '未指定')}
    - 【MirrorStories 策略】：请确保提取的事件和描述符合以下受众的阅读习惯和兴趣点：
      {audience_desc}
    请在提取事件时，参考上述设定，确保事件描述与人物性格和世界观保持一致，并吸引目标读者。
        """

    prompt = f"""
    你是一个专业的自然语言处理（NLP）专家和知识图谱构建师。请分析以下文本，精准抽取核心事件，并构建结构化的“事件网络”。
    
    【核心理论指导：基于本体和论元的事件抽取 (Ontology & Argument-based Extraction)】
    为了确保抽取的精准度，请严格遵循“先思考，后输出”的原则。你必须在 JSON 的 `reasoning_step` 字段中先进行多步推理，然后再输出节点和边。

    【抽取规范（Schema-Guided）】
    1. 推理步骤 (reasoning_step)：
       - 实体消解：识别文本中的核心实体，并明确代词（他/她/它）的具体指代。
       - 触发词提取：找出代表核心动作的“触发词”（动词/动名词）。
       - 逻辑梳理：分析这些动作之间的先后顺序和因果关系。
    2. 事件节点 (Nodes)：
       - 必须基于明确的“触发词”来定义事件。请提取 5 到 15 个最核心的事件，避免过度碎片化。
       - label：事件的精简核心概括（3-6个字，如“刺杀国王”、“发现密室”）。
       - description：客观准确的事件描述（不超过20字）。
       - arguments：提取该事件的核心论元，必须包含 subject(施事/主体), object(受事/客体), time(时间,若有), location(地点,若有)。
       - type：严格从以下类别中选择：setup(铺垫), conflict(冲突), climax(高潮), resolution(结局), investigation(调查), discovery(发现), event(普通事件)。
       - salience：事件对整体剧情的重要性（1-10的整数）。
    3. 事件关系 (Edges)：
       - 必须精准识别事件之间的逻辑关联，避免过度推断。
       - relation_type：严格从以下类别选择：causal(因果关系-A导致B), temporal(时间顺承-A发生后B发生), concurrent(并发关系-A与B同时发生)。
       - label：精简的关系描述（如“导致”、“随后”、“同时”）。

    【少样本示例 (Few-Shot Example)】
    输入文本："2023年，李明在图书馆发现了一本古老的魔法书。他打开书后，不小心释放了一个恶魔。恶魔随后摧毁了整个小镇。"
    输出 JSON:
    {{
      "reasoning_step": "1. 实体：李明，魔法书，恶魔，小镇。'他'指代李明。2. 触发词：发现，打开/释放，摧毁。3. 逻辑：发现 -> 释放 -> 摧毁。",
      "nodes": [
        {{ "id": "1", "label": "发现魔法书", "description": "李明在图书馆找到古书", "arguments": {{"subject": "李明", "object": "魔法书", "time": "2023年", "location": "图书馆"}}, "type": "discovery", "salience": 7 }},
        {{ "id": "2", "label": "释放恶魔", "description": "李明打开书释放了恶魔", "arguments": {{"subject": "李明", "object": "恶魔", "time": "未知", "location": "图书馆"}}, "type": "conflict", "salience": 9 }},
        {{ "id": "3", "label": "摧毁小镇", "description": "恶魔将小镇完全摧毁", "arguments": {{"subject": "恶魔", "object": "小镇", "time": "随后", "location": "小镇"}}, "type": "climax", "salience": 10 }}
      ],
      "edges": [
        {{ "source": "1", "target": "2", "label": "导致", "relation_type": "causal" }},
        {{ "source": "2", "target": "3", "label": "随后", "relation_type": "temporal" }}
      ]
    }}

    【当前任务】
    输入文本："{input_text}"
    {context_prompt}
    
    请严格遵循上述规范和 JSON 格式，不要输出任何 Markdown 标记（如 ```json），直接输出合法的 JSON 对象。
    """
    return _call_llm_for_json(prompt)

def analyze_missing_arguments(network):
    """分析并补全事件网络节点中缺失的关键论元（主体/客体/时间/地点）"""
    network_json = json.dumps(network, ensure_ascii=False, indent=2)
    prompt = f"""
    你是一位细致入微的叙事分析师与设定补充专家。请深度审查以下事件网络，找出在事件描述或标签中缺失了关键结构化论元（主体 Subject、客体 Object、时间 Time、地点 Location）的“空洞”节点。
    
    【分析与修复重点】：
    1. 主体与客体缺失：事件描述“发生了爆炸”缺乏主体和客体，需补充为（例如）“‘创世纪’安保队伍的追踪无人机对K的藏身处发生爆炸”。
    2. 时间与地点模糊：如果连续事件间缺少明确的场景转换，请为它们指定合理的、富有文学氛围的具体时间或地点（如“午夜时分”、“废弃的霓虹下水道”）。
    3. 细节填充原则：根据上下文节点或角色的合理推演，提供具体的、可落地的补齐信息，而不要只是生成占位符。
    
    【当前事件网络】：
    {network_json}
    
    【行动指南】：
    1. 遍历所有 `nodes`，将你在推理后生成的新细节直接整合覆写进 `description`，让节点的描述变得有血有肉。
    2. 如果原节点名称过于抽象，也可略加修饰更新 `label`。
    3. 必须生成详细的 `audit_report`，具体列出哪些节点原先缺乏什么维度，你是如何推理并为其补全细节的。
    4. 保持原有的 `edges` 不变，或者如果由于地点/时间的变更导致逻辑改变，也可以微调。
    
    请严格返回一个合法的 JSON 对象。【重要警告】：不允许使用省略号 `[...]`，你必须在 `nodes` 和 `edges` 数组中返回全部完整的节点和连线对象（必须包含原有的所有字段和补充的 arguments）！格式必须如下：
    {{
      "audit_report": "🔹 节点2：原本缺失发生地点，结合下文推理，在描述中补充了‘地下黑市诊所’。\\n🔹 节点5：缺乏动作客体，现明确为‘黑客解密了CEO的终端数据’...",
      "nodes": [ {{ "id": "1", "label": "紧急治疗", "description": "进行伤口包扎", "arguments": {{"subject":"医生", "location":"地下诊所"}}, "type": "event" }} ],
      "edges": [ {{ "source": "1", "target": "2", "label": "随后", "relation_type": "temporal" }} ]
    }}
    """
    return _call_llm_for_json(prompt)

def refine_temporal_to_causal(network):
    """分析 temporal (时间顺延) 的边，如果蕴含强因果逻辑，将其进阶为 causal 关系"""
    network_json = json.dumps(network, ensure_ascii=False, indent=2)
    prompt = f"""
    你是一位逻辑严密的剧情解构专家。请深度审查以下事件网络中的事件边 (edges)。
    现有的关系类型 (relation_type) 包括 'causal'（因果）、'temporal'（时间顺延）和 'probabilistic'（概率/可能）。
    
    【分析与升级重点】：
    1. 寻找伪装的 causal：很多目前标记为 'temporal' 甚至没写清楚类型的边，只要存在明确的“导致”、“引发”、“作为前置条件”的剧情逻辑（如：节点A“潜入大楼”-> 节点B“触发警报”），就应当被升级为 'causal'。
    2. 精炼 relationship label：对于被升级或原本描述泛泛的边，根据起因和结果重新提炼一个具体且具有说服力（逻辑上可以成立）的文字标签，例如把“之后”修改为“因为侵入内部系统引起安保注意”。
    3. 合理推断：利用节点中的 description 相互对比，提供强有力的 justification 进行更深层的推理。
    
    【当前事件网络】：
    {network_json}
    
    【行动指南】：
    1. 遍历所有 `edges`，着重检查 'temporal' 类型的边。如果你认为它们不仅是时间上的先后顺序，更是情节推动的因果关系，将其 `relation_type` 改为 'causal'。
    2. 将原有的边描述（如果存在）替换为准确且合乎逻辑的论述文字。并补充一个对原因进行深刻总结的标签到 `label` 字段。
    3. 必须生成详细的 `audit_report`，明确指出你升级了哪些边，以及升级的逻辑推理原因。
    4. 保持 `nodes` 不变（可直接返回原样）。
    
    请严格返回一个合法的 JSON 对象。【重要警告】：不允许使用省略号 `[...]`，你必须在 `nodes` 和 `edges` 数组中返回全部完整的节点和连线对象！格式必须如下：
    {{
      "audit_report": "🔹 边 (ID: 1 -> ID: 2)：原为 temporal，现升级为 causal。判断理由：角色A在节点1获得关键道具，节点2直接使用了该道具破局，具有强制因果。...",
      "nodes": [ {{ "id": "1", "label": "获取道具", "description": "拿到钥匙", "type": "event" }} ],
      "edges": [ {{ "source": "1", "target": "2", "label": "导致破门", "relation_type": "causal" }} ]
    }}
    """
    return _call_llm_for_json(prompt)

def predict_future_events(current_network, author_context=None):
    """调用本地 LLM 预测未来可能发生的事件"""
    network_json = json.dumps(current_network, ensure_ascii=False, indent=2)
    
    context_prompt = ""
    if author_context:
        target_audience = author_context.get('target_audience', {})
        audience_desc = f"目标读者：{target_audience.get('age', '全年龄')}，偏好：{target_audience.get('preference', '无')}"

        context_prompt = f"""
    【作者设定参考】：
    - 人物关系：{author_context.get('characters', '未指定')}
    - 世界观：{author_context.get('world_setting', '未指定')}
    - 【MirrorStories 策略】：预测的未来事件应能够引起以下受众的共鸣或兴趣：
      {audience_desc}
        """

    prompt = f"""
    基于当前的事件网络，预测接下来可能发生的 3-5 个“未来事件”。
    
    当前事件网络 (JSON):
    {network_json}
    
    {context_prompt}
    
    任务：
    1. 根据因果逻辑和人物性格，推演后续发展。
    2. 生成新的事件节点，并标记其发生概率（likelihood）。
    3. 定义新事件与现有事件的连接关系。
    4. 新事件的 ID 请从 "future_1" 开始编号。
    
    请务必只返回一个合法的 JSON 对象，格式如下：
    {{
      "nodes": [
        {{ "id": "future_1", "label": "预测事件名", "description": "描述...", "type": "prediction", "likelihood": "80%", "salience": 7 }}
      ],
      "edges": [
        {{ "source": "现有事件ID", "target": "future_1", "label": "可能导致", "relation_type": "probabilistic" }}
      ]
    }}
    """
    return _call_llm_for_json(prompt)

def audit_and_fix_event_network(network):
    """调用 LLM 审查并修复事件网络的逻辑漏洞"""
    network_json = json.dumps(network, ensure_ascii=False, indent=2)
    prompt = f"""
    你是一位极其严苛的资深故事溯源编辑与逻辑审查专家。请对以下事件网络进行深度的【逻辑连贯性分析】。你需要找出隐匿在因果关系（causal）和时间顺序（temporal）中的深层“逻辑矛盾”和“情节断裂”，并实施修复。

    【深度优先审查重点】：
    1. 状态矛盾与时空错位 (State Contradictions)：
       - 角色生死/状态矛盾：角色在节点A身受重伤或已绝望/死亡，却在没有铺垫的情况下正常参与了后续节点B。
       - 资源/条件矛盾：在节点A中已被销毁/消耗的关键物品，在节点B又被使用；或某个计划的前提条件尚未达成，后续事件就直接触发了。
       - 修复要求：允许修改节点的 `description`（如将其改为“带伤强行突围”），或新增一两个“缓冲过渡节点”（如“黑市医生抢救”/“暗中收集资源”）来弥合状态缺口。
    2. 孤立事件与剧情碎片 (Isolated Events)：
       - 检查所有节点的入度（即：是被哪些节点导致的）和出度（即：导致了哪些节点）。
       - 缺乏前置原因的“天降”事件必须连向一个合理的起因，或将其设定为铺垫(setup)。
       - 缺乏后续影响的节点（无果而终）必须连向相关的后续情节，或作为结局节点。
       - 修复要求：为所有孤立节点建立合理的关联边 (edges)。
    3. 循环悖论 (Circular Causality)：A发生导致B，B又倒回去导致A，形成逻辑死循环，必须打破并理顺因果流向。
    4. 动机缺失 (Lacking Motivation)：冲突节点发生得过于突然，请为突发冲突链接必要的铺垫节点，或者修改相关描述增强人物动机。
    
    【当前事件网络】：
    {network_json}
    
    【行动指南】：
    1. 请全面地审查、重构和修复 `edges` 中的连接。
    2. 你可以更新、增加或微调 `nodes`。
    3. 生成详细的 `audit_report` (中文)，分点说明你做了哪些具体改动（如新增了什么边，修复了哪两个节点间的状态矛盾）。若网络本身极度完美，也需要说明你的检查项。
    
    请严格返回一个合法的 JSON 对象。【重要警告】：不允许使用省略号 `[...]`，你必须在 `nodes` 和 `edges` 数组中返回全部且完整的节点和连线对象（即使你完全没有进行修改，也请全部原样输出）！格式必须如下：
    {{
      "audit_report": "1. 状态矛盾修复：修正了节点3在重伤后无缝战斗的矛盾，新增了‘紧急治疗’节点。2. 孤立事件修复：节点5此前无来源，现已将节点2设为其前置起因...",
      "nodes": [ {{ "id": "1", "label": "紧急治疗", "description": "进行伤口包扎", "type": "event" }} ],
      "edges": [ {{ "source": "1", "target": "2", "label": "导致", "relation_type": "causal" }} ]
    }}
    """
    return _call_llm_for_json(prompt)

def parse_fast_outline_text(text: str):
    nodes = []
    edges = []
    # 匹配: [1] 标题: 描述 (类型) <- 来源
    pattern = re.compile(r'^\[(.+?)\]\s*([^:]+):\s*(.*?)(?:\s*\(([^)]+)\))?(?:\s*<-\s*(.+))?$')
    for line in text.split('\n'):
        line = line.strip()
        if not line: continue
        m = pattern.match(line)
        if m:
            nid, label, desc, ntype, sources = m.groups()
            ntype = ntype.strip().lower() if ntype else "event"
            salience = 8 if ntype in ["conflict", "climax"] else (7 if ntype == "resolution" else 5)
            nodes.append({
                "id": str(nid).strip(),
                "label": label.strip(),
                "description": f"[{ntype}] {desc.strip()}",
                "type": ntype,
                "salience": salience
            })
            if sources:
                for src in sources.split(','):
                    src = src.strip()
                    if src:
                        edges.append({
                            "source": src,
                            "target": str(nid).strip(),
                            "relation_type": "causal",
                            "label": "导致"
                        })
    return {"nodes": nodes, "edges": edges}

def generate_random_event_network(category, complexity, theme, background, randomness, show_probability):
    """调用本地 LLM 随机生成事件网络"""
    complexity_desc = {
        "简单 (Simple)": "包含3-5个核心事件，单线叙事。",
        "中等 (Medium)": "包含6-10个事件，双线交织。",
        "复杂 (Complex)": "包含10-15个事件，多线网状结构。",
        "史诗 (Epic)": "包含15+个事件，宏大叙事，涉及多个阵营。"
    }
    
    randomness_desc = {
        "低 (Low)": "逻辑严密，常规发展。",
        "中 (Medium)": "包含1-2个意外转折。",
        "高 (High)": "充满反转，情节跌宕起伏。"
    }

    prob_instruction = ""
    if show_probability:
        prob_instruction = "在每个节点的 description 中，包含该事件发生的概率（例如：'发生概率: 80%'）。"

    prompt = f"""
    请作为一个创意事件生成器，构建一个“事件网络”。
    
    【生成参数】：
    - **类别**: {category}
    - **复杂程度**: {complexity} ({complexity_desc.get(complexity, "")})
    - **主题/关键词**: {theme}
    - **背景设定**: {background}
    - **随机性/意外度**: {randomness} ({randomness_desc.get(randomness, "")})
    
    【任务】：
    1. 构思一系列相互关联的事件（节点）。简要标记它们（3-5个字）并提供详细描述。
    2. {prob_instruction}
    3. 定义事件之间的因果或时间关系（边）。
    4. 对事件进行分类（铺垫 setup、冲突 conflict、高潮 climax、结局 resolution、调查 investigation、发现 discovery 或普通事件 event）。
    
    请务必只返回一个合法的 JSON 对象，不要包含 Markdown 格式（如 ```json ... ```），格式如下：
    {{
      "nodes": [
        {{ "id": "1", "label": "事件名称", "description": "详细描述... (发生概率: 80%)", "type": "setup" }}
      ],
      "edges": [
        {{ "source": "1", "target": "2", "label": "导致/引发" }}
      ]
    }}
    """
    return _call_llm_for_json(prompt)

def generate_image_prompts(network, style, tone, author_context=None):
    """调用本地 LLM 为关键事件生成图像提示词 (多模态支持)"""
    # 筛选出关键事件 (如 climax, conflict, discovery)
    key_events = [n for n in network.get('nodes', []) if n.get('type') in ['climax', 'conflict', 'discovery', 'prediction']]
    if not key_events:
        key_events = network.get('nodes', [])[:5] # 如果没有特定类型，取前5个
        
    events_json = json.dumps(key_events, ensure_ascii=False, indent=2)
    
    audience_instruction = ""
    if author_context:
        target_audience = author_context.get('target_audience', {})
        audience_instruction = f"目标受众：{target_audience.get('age', '全年龄')}，偏好：{target_audience.get('preference', '无')}。请确保画面风格适合该受众（例如：儿童则色彩鲜艳，成人则更具艺术感）。"
    
    prompt = f"""
    基于以下关键事件，为每个事件生成一个详细的 AI 绘画提示词 (Midjourney/Stable Diffusion 格式)。
    
    事件列表 (JSON):
    {events_json}
    
    【要求】：
    1. 风格：{style}
    2. 氛围：{tone}
    3. {audience_instruction}
    4. 提示词结构：[主体描述], [环境/背景], [艺术风格/媒介], [光影/色彩], [画质修饰词]
    5. 请为每个事件返回一个提示词，并用英文撰写提示词 (因为绘画模型通常对英文支持更好)，但附带中文说明。
    
    请务必只返回一个合法的 JSON 对象，格式如下：
    {{
      "prompts": [
        {{ "event_id": "1", "event_label": "事件名", "prompt_en": "A cyberpunk detective standing in rain...", "description_cn": "赛博朋克侦探站在雨中..." }}
      ]
    }}
    """
    return _call_llm_for_json(prompt)

def extract_network_from_nlp_jsonl(record_dict):
    """专门用于将 NLP 数据集格式转换为中文事件网络（纯 Python 极速模式，100% 结构准确，0 延迟）"""
    
    if not isinstance(record_dict, dict):
        st.error("解析 NLP 数据集记录失败：传入的记录不是一个有效的字典结构。")
        return {"nodes": [], "edges": []}

    sentences = record_dict.get("sentences")
    events = record_dict.get("events") or record_dict.get("event_mentions")

    if sentences is None or events is None:
        st.error("解析 NLP 数据集记录失败：记录中缺失 'sentences' 或 'events'/'event_mentions' 关键字段。")
        return {"nodes": [], "edges": []}

    if not isinstance(sentences, list) or not isinstance(events, list):
        st.error("解析 NLP 数据集记录失败：'sentences' 或 'events' 的格式不正确，应为列表 (list) 类型。")
        return {"nodes": [], "edges": []}

    if len(sentences) == 0 and len(events) == 0:
        st.warning("提示：该记录的 'sentences' 和 'events' 内容均为空。")
        return {"nodes": [], "edges": []}

    # 建立极速本地映射，完全替代大模型翻译
    rel_zh_map = {
        "BEFORE": "发生在...之前",
        "AFTER": "发生在...之后",
        "SIMULTANEOUS": "同时发生",
        "INCLUDES": "时间包含",
        "IS_INCLUDED": "被包含于",
        "PRECONDITION": "前提条件",
        "CAUSES": "导致了",
        "EFFECT": "产生了结果"
    }
    
    def map_event_type(raw_type):
        raw = raw_type.lower()
        if any(k in raw for k in ['attack', 'die', 'injure', 'conflict', 'kill', 'massacre', 'terrorism', 'arrest', 'jail', 'crash']):
            return 'conflict'
        if any(k in raw for k in ['end', 'release', 'pardon', 'acquit', 'resolve', 'finish']):
            return 'resolution'
        if any(k in raw for k in ['plan', 'prepare', 'statement', 'declare', 'meet', 'phone', 'contact', 'transport', 'movement', 'transfer']):
            return 'setup'
        if any(k in raw for k in ['discover', 'find', 'investigate', 'trial', 'sue', 'inspect', 'charge', 'sentence']):
            return 'investigation'
        return 'event'

    # 1. Python 精准提取结构 (100% 准确，毫秒级)
    standardized_events = []
    for i, em in enumerate(events):
        if isinstance(em, dict):
            if 'mention' in em and isinstance(em['mention'], list) and len(em['mention']) > 0:
                mention_data = em['mention'][0]
                
                # 提取 arguments
                arguments = []
                if 'argument' in em and isinstance(em['argument'], list):
                    for arg in em['argument']:
                        if isinstance(arg, dict):
                            arg_role = arg.get('role', '元素')
                            arg_text = arg.get('text', '')
                            if 'mention' in arg and isinstance(arg['mention'], list) and len(arg['mention']) > 0:
                                arg_text = arg['mention'][0].get('text', arg_text)
                            if arg_text:
                                arguments.append({"role": arg_role, "text": arg_text})
                
                standardized_events.append({
                    "id": em.get("id", str(i)),
                    "trigger_word": mention_data.get("trigger_word", "Event"),
                    "type": em.get("type", "event"),
                    "sent_id": mention_data.get("sent_id", 0),
                    "arguments": arguments
                })
            else:
                standardized_events.append({
                    "id": em.get("id", str(i)),
                    "trigger_word": em.get("trigger_word", "Event"),
                    "type": em.get("type", "event"),
                    "sent_id": em.get("sent_id", 0),
                    "arguments": []
                })
                
    # 限制节点数量，避免过于庞大的 NLP集（例如上百个节点）拖垮前端图形渲染
    if len(standardized_events) > 60:
        standardized_events = standardized_events[:60]
        st.toast("数据集记录的节点过多，为了保证渲染速度，已保留前60个核心事件。", icon="⚠️")
        
    raw_nodes = []
    node_ids = set()
    for em in standardized_events:
        node_id = em["id"]
        sent_id = em["sent_id"]
        raw_trigger = em["trigger_word"]
        raw_type = em["type"]
        
        desc = sentences[sent_id] if sent_id < len(sentences) else raw_trigger
        
        # 使用 Markdown 加粗原词，帮助用户在句子中快速定位触发词
        if raw_trigger in desc:
            desc = desc.replace(raw_trigger, f"**{raw_trigger}**")
            
        mapped_type = map_event_type(raw_type)
        salience = 8 if mapped_type == 'conflict' else (7 if mapped_type == 'resolution' else 5)
        
        raw_nodes.append({
            "id": node_id,
            "label": raw_trigger,  # 保留原始触发词保证数据真实、准确
            "description": f"[{raw_type}] {desc}",
            "type": mapped_type,
            "salience": salience
        })
        node_ids.add(node_id)
        
    raw_edges = []
    temporal_rels = record_dict.get("temporal_relations", {})
    causal_rels = record_dict.get("causal_relations", {})
    has_explicit_edges = False
    
    if isinstance(temporal_rels, dict):
        for rel_type, pairs in temporal_rels.items():
            if isinstance(pairs, list):
                label_zh = rel_zh_map.get(rel_type.upper(), f"时间: {rel_type}")
                for pair in pairs:
                    if len(pair) == 2 and pair[0] in node_ids and pair[1] in node_ids:
                        raw_edges.append({"source": pair[0], "target": pair[1], "relation_type": "temporal", "label": label_zh})
                        has_explicit_edges = True
                        
    if isinstance(causal_rels, dict):
        for rel_type, pairs in causal_rels.items():
            if isinstance(pairs, list):
                label_zh = rel_zh_map.get(rel_type.upper(), f"因果: {rel_type}")
                for pair in pairs:
                    if len(pair) == 2 and pair[0] in node_ids and pair[1] in node_ids:
                        raw_edges.append({"source": pair[0], "target": pair[1], "relation_type": "causal", "label": label_zh})
                        has_explicit_edges = True
                        
    if not has_explicit_edges:
        for i in range(1, len(standardized_events)):
            prev = standardized_events[i-1]
            curr = standardized_events[i]
            rel = "concurrent" if prev["sent_id"] == curr["sent_id"] else "temporal"
            lbl = "同句关联" if rel == "concurrent" else "时间顺承"
            raw_edges.append({"source": prev["id"], "target": curr["id"], "relation_type": rel, "label": lbl})
            
    return {"nodes": raw_nodes, "edges": raw_edges}

def generate_stylized_text_stream(network, style, tone, author_context, target_word_count, pov, reference_text=None):
    """调用本地 LLM 生成风格化文本，并使用流式输出"""
    network_json = json.dumps(network, ensure_ascii=False, indent=2)
    
    # 构建作者设定提示词
    context_prompt = ""
    if author_context:
        target_audience = author_context.get('target_audience', {})
        audience_desc = f"目标读者：{target_audience.get('age', '全年龄')}，偏好：{target_audience.get('preference', '无')}"

        context_prompt = f"""
    【作者设定约束】：
    请严格遵循以下人物设定和世界观进行写作，确保角色行为符合人设（Character Consistency）：
    - 人物小传与关系：
    {author_context.get('characters', '未指定')}
    
    - 世界观背景：
    {author_context.get('world_setting', '未指定')}

    - 【MirrorStories 策略】：请调整叙事口吻、词汇选择和节奏，以最大程度地吸引以下受众：
      {audience_desc}
      (例如：若读者是儿童，使用简单词汇；若读者是硬核科幻迷，增加技术细节描述。)
        """
        
    reference_prompt = ""
    if reference_text and reference_text.strip():
        reference_prompt = f"""
    【⚠️强约束：文风镜像克隆（Style Cloning）】：
    用户提供了一段参考文本。你必须**像素级模仿**参考文本的文锋、句式结构、修辞风格、以及叙事节奏。将参考文本的"灵魂"完美地迁移到本次的创作中。
    
    参考文本如下：
    \"\"\"
    {reference_text.strip()}
    \"\"\"
        """

    prompt = f"""
    你是一位荣获茅盾文学奖的殿堂级小说家。你精通各种文学流派，擅长运用细腻的笔触、深邃的隐喻和极具张力的场景描写。你拒绝平庸的叙事，只创作具有极高文学价值的艺术品。
    
    请基于以下事件网络结构，创作一篇完整、连贯、富有文采的正式文章/小说。
    
    事件网络 (JSON):
    {network_json}
    
    {context_prompt}
    {reference_prompt}
    
    【核心约束：多维感官极限放大（视觉/听觉/触觉/嗅觉）】
    - 对于 'conflict' (冲突) 节点：必须穿插极端高强度的感官细节。
      * 视觉（光影、色彩）：例如利刃上折射的刺眼冷光、迅速漫开的暗红血迹、昏暗环境中的残影。
      * 听觉（声音、震动）：例如耳膜边缘的轰鸣音、沉重的喘息、金属对撞的尖利刺耳声、地面传来的震颤。
      * 触觉（温度、质感）：例如如同针扎般的冰冷空气、黏腻而发烫的汗水、粗糙且刮骨的地面摩擦感。
      * 嗅觉（气味）：例如空气中浓烈的铁锈味（血腥）、火药燃烧后的焦糊味、或雨水与泥土混合的生冷气息。
      结合多种感官，深入刻画人物在瞬间的内心挣扎、生存本能的恐惧或狂乱的战意。
    - 对于 'climax' (高潮) 节点：使用极具扩张力的长句或急促的短句交替，将人物的灵魂剖白、潜意识闪回，与上述四种极致的感官碎影彻底融合。让读者通过人物的五官，体验一种失重般、几乎窒息的顶级沉浸感和文学感染力。

    【AI小说生成前沿技术约束（极细致的沉浸感优化）】
    为了彻底打破 AI 生成通用的“总结性流水账”通病，你必须完全采用以下专业写作坊的核心原则：
    1. **【场景化展开与实时感 (Scene-By-Scene Expansion)】**：绝对禁止一笔带过。将每一个核心事件节点铺设为一个【实时的视听场景】。必须写出动作的前置、爆发和余波。
    2. **【终极原则：展示，不要告知 (Show, Don't Tell)】**：不要告诉我“他很害怕”，要向我展示“他掌心渗出冷汗，瞳孔在昏暗的车厢内无规则地剧烈跳动”。用物理反应、环境反馈和下意识动作代替情绪的名词。
    3. **【穿插高能对白 (Dialogue and Subtext)】**：不要完全依靠旁白推进剧情。引入具有锋芒的直接对话。在对白中埋入潜台词，并通过对话时的微动作（诸如：摩挲打火机、眼神的躲闪、呼吸的停顿）来拉扯张力。
    4. **【多维感官锚点 (Sensory Anchors)】**：为每一个新场景建立至少两个以上的感官锚点（除了视觉）。增加诸如：机油的刺鼻味、喉咙泛起的血腥味、远处沉闷的雷声、指尖触碰粗糙金属的冷冽感。

    常规写作要求：
    1. **结构化与连贯性**：严格遵循事件网络的因果逻辑（Edges），但必须将其无缝融入到自然的故事流中。
    2. **节奏控制与细节分配（极其重要）**：
       - 根据事件类型（Type）精细控制描写深度，严格执行上述【核心约束：细节描写与感官张力】。
       - 对于 'setup' (铺垫) 节点：需交代清前因后果，以氛围渲染为主。
       - 根据显著性（Salience 1-10）：分数越高的事件，请分配绝对优势的笔墨。
    3. **文学性与美感**：
       - **修辞手法**：大量使用比喻、拟人、隐喻等高级修辞，避免直白的流水账。
       - **环境与人物交融**：让天气、光影、环境音等元素折射人物的内心状态。
    4. **风格与基调**：
       - 写作风格： "{style}"
       - 情感基调： "{tone}"
       - 叙事视角： "{pov}"
    5. **【核心字数约束】**： 
       - 你的输出字数必须严格达到 **{target_word_count} 字** 左右。
       - 如果目标字数较长，请充分展开环境描写、人物心理活动、对话和动作细节。
       - 如果目标字数较短，请精炼语言，加快叙事节奏，只保留核心情节。
    6. **【文章完整性强制指令】**：
       - 输出必须是一篇**结构完整的正式小说/文章**，包含引人入胜的开头、连贯的主体和完整的结尾。
       - **绝对禁止**使用“1. 2. 3.”等列表格式，**绝对禁止**写成大纲、流水账或碎片化的草稿。
       - 所有的事件必须用优美的文学语言无缝串联。
       - 请使用中文进行写作。
       - **关键要求**：请将所有事件自然地融入故事情节中，不要在文中留下任何类似 [ID: xxx] 的标记或编号。
    
    现在开始写作。
    """
    
    try:
        current_model = DEFAULT_MODEL_NAME
        
        response = client.chat.completions.create(
            model=current_model,
            messages=[
                {"role": "system", "content": "你是一位殿堂级小说家。你拒绝输出任何列表或大纲，只输出连贯、优美、充满细节的文学作品。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        st.error(f"生成文本失败: {e}")
        yield ""

def main():
    if "story_history" not in st.session_state:
        st.session_state["story_history"] = []
    # --- Streamlit UI 布局 ---

    st.set_page_config(page_title="EventWeaver | 智能事件网络", page_icon="🕸️", layout="wide", initial_sidebar_state="expanded")
    ui_controller.inject_custom_css()


    # --- 渲染侧边栏并获取配置 ---
    author_context = ui_controller.render_sidebar()

    # 注入特色流派库特征
    active_genre_id = st.session_state.get('active_genre_id')
    if active_genre_id:
        g = genre_lib.get_genre_by_id(active_genre_id)
        if g:
            author_context['world_setting'] = f"【所选小说流派: {g['name']}】\n{g.get('system_prompt', '')}\n(网络事件构建指导: {g.get('network_prompt', '')})\n\n" + author_context.get('world_setting', '')

    # --- 主界面 ---
    if 'network' not in st.session_state or not st.session_state['network']:
        # 阶段 1：数据输入与生成
        ui_controller.render_hero_section()
        
        st.markdown('<h3 style="text-align: center; margin-bottom: 2rem; color: var(--text-secondary);">选择数据源开始溯源</h3>', unsafe_allow_html=True)
        
        tab_text, tab_json, tab_jsonl, tab_random = st.tabs([
            "📖 文本大纲", "✍️ 极速录入", "📁 数据集解析", "🧠 灵感大爆炸 (TNO/Galgame)"
        ])
        
        with tab_text:
            input_text, submit_btn = ui_controller.render_text_extraction_mode()
            if submit_btn:
                with st.status("🧠 正在连接本地认知引擎分析情节...", expanded=True) as status:
                    st.write("解析自然语言并提取核心节点...")
                    network_data = extract_event_network(input_text, author_context)
                    if network_data:
                        st.session_state['network'] = network_data
                        status.update(label="情节逻辑拓扑构建完成！", state="complete", expanded=False)
                        st.balloons()
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        status.update(label="解析失败，请检查模型运行状态。", state="error")
                        
        with tab_json:
            input_content, submit_btn = ui_controller.render_event_network_input_mode()
            if submit_btn:
                try:
                    # 尝试普通 JSON
                    network_data = json.loads(input_content)
                    if "nodes" in network_data and "edges" in network_data:
                        st.session_state['network'] = network_data
                        st.toast("JSON 大纲解析成功！", icon="✅")
                        st.balloons()
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("JSON 格式错误：必须包含 'nodes' 和 'edges' 字段。")
                except json.JSONDecodeError:
                    # 如果不是 JSON，尝试极速文本解析
                    with st.status("⚡ 正在启动极速本地解析引擎...", expanded=True) as status:
                        start_time = time.time()
                        st.write("映射语法结构到拓扑节点...")
                        network_data = parse_fast_outline_text(input_content)
                        if network_data and network_data.get("nodes"):
                            elapsed = time.time() - start_time
                            st.session_state['network'] = network_data
                            status.update(label=f"解析成功！(耗时 {elapsed:.3f} 秒，共 {len(network_data['nodes'])} 节点)", state="complete", expanded=False)
                            st.balloons()
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            status.update(label="解析失败：格式不匹配", state="error")
                            st.error("无法解析输入内容，请检查大纲是否严格按照 `[ID] 标题: 描述 (类型) <- 来源` 的格式编写。")
                            
        with tab_jsonl:
            selected_record_str, submit_btn = ui_controller.render_jsonl_import_mode()
            if submit_btn and selected_record_str:
                try:
                    record = json.loads(selected_record_str)
                    if isinstance(record, dict):
                        if "nodes" in record and "edges" in record:
                            with st.status("🤖 提取到图谱数据，正在验证精准度与中文转写...", expanded=True) as status:
                                st.write("调用大模型进行二次核实...")
                                verified_data = verify_and_summarize_network(record, record)
                                if verified_data and "nodes" in verified_data:
                                    st.session_state['network'] = {"nodes": verified_data["nodes"], "edges": verified_data.get("edges", [])}
                                    st.session_state['verification_report'] = verified_data.get("verification_report", "查证完毕：原始数据准确。")
                                    status.update(label="结构验证与优化完成！", state="complete", expanded=False)
                                    st.balloons()
                                else:
                                    st.session_state['network'] = record
                                    status.update(label="核查超时，已加载原始数据。", state="complete", expanded=False)
                                time.sleep(1.5)
                                st.rerun()
                        elif "sentences" in record or "event_mentions" in record:
                            with st.status("⚡ 启用极速离线解析引擎提取核心事件...", expanded=True) as status:
                                st.write("对齐实体并重构关联图谱...")
                                network_data = extract_network_from_nlp_jsonl(record)
                                if network_data and network_data.get("nodes"):
                                    st.write("🧠 唤醒大模型进行全中文翻译与精准度查证...")
                                    verified_data = verify_and_summarize_network(network_data, record)
                                    if verified_data and "nodes" in verified_data:
                                        st.session_state['network'] = {"nodes": verified_data["nodes"], "edges": verified_data.get("edges", [])}
                                        st.session_state['verification_report'] = verified_data.get("verification_report", "查证完毕：提取准确。")
                                        status.update(label="智能解析与查证完成！", state="complete", expanded=False)
                                        st.balloons()
                                    else:
                                        st.session_state['network'] = network_data
                                        status.update(label="大模型查证失败，保留初步解析结果。", state="complete", expanded=False)
                                    time.sleep(1.5)
                                    st.rerun()
                                elif network_data:
                                    status.update(label="警告：未提取到事件节点", state="error")
                                    st.warning("解析完成，但未能提取到任何事件节点或数据格式不符合要求。")
                                else:
                                    status.update(label="解析失败", state="error")
                                    st.error("解析失败，请检查数据格式。")
                        else:
                            with st.status("🤖 记录非标准图谱格式，启动智能推理与查证...", expanded=True) as status:
                                network_data = extract_event_network(json.dumps(record, ensure_ascii=False), author_context)
                                if network_data:
                                    st.write("🧠 正在核查事件精准度并生成全中文大纲...")
                                    verified_data = verify_and_summarize_network(network_data, record)
                                    if verified_data and "nodes" in verified_data:
                                        st.session_state['network'] = {"nodes": verified_data["nodes"], "edges": verified_data.get("edges", [])}
                                        st.session_state['verification_report'] = verified_data.get("verification_report", "查证完毕：推断准确。")
                                        status.update(label="智能解析与查证完成！", state="complete", expanded=False)
                                        st.balloons()
                                    else:
                                        st.session_state['network'] = network_data
                                        status.update(label="初次推断完成，但深层查证超时。", state="complete", expanded=False)
                                    time.sleep(1.5)
                                    st.rerun()
                                else:
                                    status.update(label="解析失败", state="error")
                                    st.error("智能解析失败，请检查数据格式。")
                    else:
                        st.error("选中的记录不是有效的字典格式。")
                except json.JSONDecodeError:
                    st.error("选中的记录不是有效的 JSON 格式。")
                    
        with tab_random:
            category, complexity, theme, background, randomness, show_probability, submit_btn = ui_controller.render_random_generation_mode()
            if submit_btn:
                with st.status("🌌 正在从混沌中织造新的因果网络...", expanded=True) as status:
                    st.write("配置大模型参数并随机采样世界线...")
                    
                    # 注入激活的流派库
                    active_genre_id = st.session_state.get('active_genre_id')
                    extended_bg = background
                    if active_genre_id:
                        g = genre_lib.get_genre_by_id(active_genre_id)
                        if g:
                             st.toast(f"随机生成将遵循 {g['name']} 特征库约束！", icon="📚")
                             extended_bg = f"【流派核心设定: {g['name']}】\n{g.get('system_prompt', '')}\n【网络生成方向指导】: {g.get('network_prompt', '')}\n\n{background}"
                             
                    network_data = generate_random_event_network(category, complexity, theme, extended_bg, randomness, show_probability)
                    if network_data:
                        st.session_state['network'] = network_data
                        status.update(label="随机事件网络生成并收敛完毕！", state="complete", expanded=False)
                        st.balloons()
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        status.update(label="生成失败", state="error")

    else:
        # 阶段 2：仪表盘与创作台
        st.markdown('<div class="dashboard-title">🕸️ 事件图谱工作台</div>', unsafe_allow_html=True)
        
        if 'verification_report' in st.session_state and st.session_state['verification_report']:
            st.info(f"**大模型查证摘要：**\n\n{st.session_state['verification_report']}", icon="💡")
            
        # 顶部指标卡片
        nodes_count = len(st.session_state['network'].get('nodes', []))
        edges_count = len(st.session_state['network'].get('edges', []))
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("事件节点 (Nodes)", nodes_count)
        col_m2.metric("关联边 (Edges)", edges_count)
        col_m3.metric("当前状态", "已生成故事" if st.session_state.get('story') else "待创作")
        with col_m4:
            st.write("")
            if st.button("⚠️ 清除并返回首页", use_container_width=True):
                st.session_state['network'] = None
                st.session_state['story'] = None
                st.session_state['story_history'] = []
                st.session_state['verification_report'] = None
                st.rerun()
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        tab_graph, tab_story, tab_edit, tab_raw, tab_knowledge = st.tabs([
            "🌌 时空图谱", "📝 AI 故事工坊", "✏️ 逻辑修剪", "💻 潜行数据", "📚 语料与微调"
        ])
        
        with tab_graph:
            predict_clicked = ui_controller.render_graph_tab(st.session_state['network'])
            if predict_clicked:
                with st.status("🔮 正在深入可能性的分支推演未来...", expanded=True) as status:
                    st.write("调用本地认知模型执行时间线拓展...")
                    future_events = predict_future_events(st.session_state['network'], author_context)
                    if future_events:
                        st.session_state['network'], new_count = _merge_future_events(st.session_state['network'], future_events)
                        status.update(label=f"推演成功！已拓展 {new_count} 个未来节点", state="complete", expanded=False)
                        st.snow()
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        status.update(label="推演失败，已抵达当前世界线的观测极限。", state="error")
                        
        with tab_story:
            scol1, scol2 = st.columns([1, 2])
            with scol1:
                style, tone, pov, target_word_count, reference_text, generate_btn = ui_controller.render_style_controls()
                
            with scol2:
                if generate_btn:
                    status_placeholder = st.empty()
                    status_placeholder.info("⏳ 正在连线大模型创作长篇小说中...（文本正逐句流式输出，请耐心等待直到出现完毕提示）")
                    try:
                        # 检查是否有激活的小说流派库
                        active_genre_id = st.session_state.get('active_genre_id')
                        extended_author_context = author_context.copy() if author_context else {}
                        extended_reference = reference_text or ""
                        
                        if active_genre_id:
                            g = genre_lib.get_genre_by_id(active_genre_id)
                            if g:
                                st.toast(f"正在应用 {g['name']} 特征库！", icon="📚")
                                if not extended_reference and g.get('reference_text'):
                                    extended_reference = g.get('reference_text')
                                    
                        stream = generate_stylized_text_stream(st.session_state['network'], style, tone, extended_author_context, target_word_count, pov, extended_reference)
                        full_story = st.write_stream(stream)
                        
                        st.session_state['story'] = full_story
                        st.session_state['story_history'].append({
                            "content": full_story,
                            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "style": style,
                            "tone": tone
                        })
                        status_placeholder.success("✅ 小说已生成完毕！为您重新排版中...")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error("生成过程中发生错误。")
                elif st.session_state.get('story'):
                    if st.session_state.get('restored_story_trigger'):
                        st.toast("⏪ 历史版本已恢复！", icon="✅")
                        st.session_state['restored_story_trigger'] = False
                        
                    gen_prompts_clicked = ui_controller.render_story_tab(st.session_state.get('story'), st.session_state.get('image_prompts'))
                    if gen_prompts_clicked:
                        with st.status("🎨 正在提取视觉特征生成多模态提示词...", expanded=True) as status:
                            prompts_data = generate_image_prompts(st.session_state['network'], style, tone, author_context)
                            if prompts_data:
                                st.session_state['image_prompts'] = prompts_data
                                status.update(label="关键帧绘画提示词构建完成", state="complete", expanded=False)
                                st.rerun()
                            else:
                                status.update(label="提示词构建失败", state="error")
                else:
                    st.info("👈 请在左侧配置写作风格并点击“生成正文草稿”按钮。")
                    
        with tab_edit:
            if st.session_state.get('network_saved_trigger'):
                st.toast("网络结构已更新！请切换回“交互式图谱”查看。", icon="💾")
                st.balloons()
                st.session_state['network_saved_trigger'] = False
                
            audit_clicked, analyze_args_clicked, refine_edges_clicked = ui_controller.render_edit_network_tab(st.session_state['network'])
            
            if audit_clicked:
                with st.status("🕵️ 正在由 AI 架构师执行严密的逻辑审计...", expanded=True) as status:
                    st.write("检测剧情连续性漏洞并尝试自动修复...")
                    fixed_network = audit_and_fix_event_network(st.session_state['network'])
                    if fixed_network and "nodes" in fixed_network:
                        st.session_state['network'] = {
                            "nodes": fixed_network["nodes"], 
                            "edges": fixed_network.get("edges", [])
                        }
                        report = fixed_network.get('audit_report', '逻辑清晰，暂未发现结构性漏洞。')
                        status.update(label="逻辑审查与自修复闭环完成！", state="complete", expanded=False)
                        st.success(f"**审查报告**:\n{report}")
                        # Allow user to see the success message for 3 seconds before reload
                        time.sleep(3)
                        st.rerun()
                    else:
                        status.update(label="逻辑修复执行失败", state="error")
                        
            if analyze_args_clicked:
                with st.status("🔎 正在进行深层文本溯源与论元拓扑补齐...", expanded=True) as status:
                    st.write("提取并关联潜在的人、事、时、地核心论元...")
                    enriched_network = analyze_missing_arguments(st.session_state['network'])
                    if enriched_network and "nodes" in enriched_network:
                        st.session_state['network'] = {
                            "nodes": enriched_network["nodes"],
                            "edges": enriched_network.get("edges", [])
                        }
                        report = enriched_network.get('audit_report', '当前拓扑论元饱和，状态良好。')
                        status.update(label="关键论元分析与结构补齐完成！", state="complete", expanded=False)
                        st.success(f"**操作报告**:\n{report}")
                        time.sleep(3)
                        st.rerun()
                    else:
                        status.update(label="论元分析过程异常中断", state="error")

            if refine_edges_clicked:
                with st.status("🔗 正在执行高能因果关系深度重构...", expanded=True) as status:
                    st.write("剥离时间表象，重塑强因果链接网络...")
                    refined_network = refine_temporal_to_causal(st.session_state['network'])
                    if refined_network and "edges" in refined_network:
                        st.session_state['network'] = {
                            "nodes": refined_network.get("nodes", st.session_state['network'].get('nodes')),
                            "edges": refined_network["edges"]
                        }
                        report = refined_network.get('audit_report', '底层因果关系处于最优化状态。')
                        status.update(label="因果脉络精炼与边缘升级完成！", state="complete", expanded=False)
                        st.success(f"**操作报告**:\n{report}")
                        time.sleep(3)
                        st.rerun()
                    else:
                        status.update(label="连接升维失败", state="error")
                        
        with tab_raw:
            ui_controller.render_json_tab(st.session_state['network'])

        with tab_knowledge:
            ui_controller.render_knowledge_tab()


if __name__ == "__main__":
    main()