from genre_library_manager import genre_lib
import re
import json
import streamlit as st
import pandas as pd
from streamlit_agraph import agraph, Node, Edge, Config
from typing import Tuple, Dict, Any, List, Optional
import os
import base64

@st.cache_data
def get_base64_of_bin_file(bin_file):
    """读取本地文件并转换为 base64 编码"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def inject_custom_css():
    bg_style = ""
    # 检查是否存在用户自定义的背景图片
    for ext in ['jpg', 'png', 'jpeg', 'webp']:
        bg_path = f"assets/bg.{ext}"
        if os.path.exists(bg_path):
            img_b64 = get_base64_of_bin_file(bg_path)
            bg_style = f"""
            .stApp {{
                background-image: url("data:image/{ext};base64,{img_b64}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            /* 添加透明度使内容更易读 */
            .block-container {{
                background-color: rgba(255, 255, 255, 0.85); /* 半透明白色背景 */
                border-radius: 16px;
                padding: 2rem !important;
                margin-top: 2rem;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                backdrop-filter: blur(10px);
            }}
            @media (prefers-color-scheme: dark) {{
                .block-container {{
                    background-color: rgba(26, 22, 24, 0.85); /* 半透明深色背景 */
                }}
            }}
            """
            break

    st.markdown(f"""
    <style>
    {bg_style}
    /* ====== CSS 变量 ====== */
    :root {{
        --primary-color: #6366f1;      /* 工业感靛蓝 */
        --primary-hover: #4f46e5;      /* 深靛蓝 */
        --secondary-color: #f3f4f6;    /* 面板灰白 */
        --secondary-hover: #e5e7eb;    /* 面板灰悬停 */
        --text-primary: #111827;       /* 深黑灰，提供高对比度阅读 */
        --text-secondary: #4b5563;     /* 辅助灰 */
        --text-muted: #9ca3af;         /* 弱化灰 */
        --bg-base: #ffffff;
        --bg-surface: #f9fafb;         /* 极简卡片底色 */
        --border-color: #e5e7eb;       /* 浅边框 */
        --border-focus: #818cf8;       /* 蓝紫焦点边框 */
        
        --radius-sm: 6px;
        --radius-md: 8px;
        --radius-lg: 12px;
        --radius-xl: 16px;
        
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        
        --transition-fast: 0.15s ease-in-out;
        --transition-normal: 0.25s ease;
    }}

    /* ====== 深色主题适配 (仿各种写作软件黑暗模式) ====== */
    @media (prefers-color-scheme: dark) {{
        :root {{
            --primary-color: #818cf8;     /* 亮靛蓝 */
            --primary-hover: #6366f1;     
            --secondary-color: #1f2937;   /* 深层版块底色 */
            --secondary-hover: #374151;   
            --text-primary: #f9fafb;      
            --text-secondary: #d1d5db;    
            --text-muted: #6b7280;        
            --bg-base: #111827;           /* 深渊黑底色 */
            --bg-surface: #1f2937;        
            --border-color: #374151;      
            --border-focus: #818cf8;    
        }}
    }}

    /* ====== 排版与全局设置 ====== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: var(--text-primary);
    }}
    h1, h2, h3, h4, h5, h6 {{
        font-weight: 600 !important;
        letter-spacing: -0.02em;
        color: var(--text-primary);
    }}
    p, span, div {{
        color: var(--text-secondary);
    }}
    
    /* 隐藏 Streamlit 默认品牌标识 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* 主布局 */
    .block-container {{
        padding-top: 2.5rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }}
    
    /* ====== 巨幕区域 ====== */
    .hero-title {{
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--primary-color), #ffb6c1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        text-align: center;
        letter-spacing: -0.03em;
    }}
    .hero-subtitle {{
        font-size: 1.125rem;
        font-weight: 400;
        color: var(--text-muted);
        margin-bottom: 3.5rem;
        text-align: center;
        font-family: 'Comic Sans MS', 'Chalkboard SE', 'Marker Felt', sans-serif;
    }}

    /* ====== 容器与卡片 ====== */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-sm);
        transition: box-shadow var(--transition-normal);
        padding: 0.5rem; 
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
        box-shadow: var(--shadow-md);
    }}
    
    /* ====== 标签页 (分段控制风格) ====== */
    div[data-testid="stTabs"] {{
        background-color: transparent;
    }}
    div[data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background-color: var(--secondary-color);
        padding: 0.5rem;
        border-radius: var(--radius-lg);
        border: none;
        margin-bottom: 2rem;
    }}
    div[data-baseweb="tab"] {{
        background-color: transparent;
        border-radius: var(--radius-md);
        padding: 0.6rem 1.25rem;
        font-weight: 500;
        color: var(--text-secondary);
        border: none !important;
        transition: all var(--transition-fast);
    }}
    div[data-baseweb="tab"]:hover {{
        background-color: var(--secondary-hover);
        color: var(--text-primary);
    }}
    div[data-baseweb="tab"][aria-selected="true"] {{
        background-color: var(--bg-base);
        color: var(--text-primary);
        box-shadow: var(--shadow-sm);
        font-weight: 600;
    }}

    /* ====== 输入框 (文本, 文本域, 下拉框) ====== */
    div[data-testid="stTextInput"] input, 
    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="select"] > div {{
        background-color: var(--bg-base);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        color: var(--text-primary);
        transition: all var(--transition-fast);
    }}
    div[data-testid="stTextInput"] input:focus, 
    div[data-testid="stTextArea"] textarea:focus,
    div[data-baseweb="select"]:focus-within > div {{
        border-color: var(--border-focus);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
        background-color: var(--bg-base);
    }}
    
    /* ====== 展开面板 / 手风琴组件 ====== */
    div[data-testid="stExpander"] {{
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        background-color: var(--bg-surface);
        overflow: hidden;
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    div[data-testid="stExpander"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
        border-color: var(--primary-color);
    }}
    div[data-testid="stExpander"] summary {{
        background-color: var(--bg-surface);
        font-weight: 600;
        color: var(--text-primary);
        transition: background-color 0.3s ease;
    }}
    div[data-testid="stExpander"] summary:hover {{
        background-color: var(--secondary-color);
    }}

    /* ====== 按钮 ====== */
    /* 主要按钮 */
    @keyframes primary-pulse {{
      0% {{ box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.4); }}
      70% {{ box-shadow: 0 0 0 6px rgba(79, 70, 229, 0); }}
      100% {{ box-shadow: 0 0 0 0 rgba(79, 70, 229, 0); }}
    }}

    button[data-testid="baseButton-primary"] {{
        background: var(--primary-color) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        padding: 0.6rem 1.25rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3) !important;
        transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.2s ease !important;
        position: relative;
        overflow: hidden;
        animation: primary-pulse 2s infinite;
    }}
    button[data-testid="baseButton-primary"]::after {{
        content: '';
        position: absolute;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        pointer-events: none;
        background-image: radial-gradient(circle, #fff 10%, transparent 10.01%);
        background-repeat: no-repeat;
        background-position: 50%;
        transform: scale(10, 10);
        opacity: 0;
        transition: transform .5s, opacity 1s;
    }}
    button[data-testid="baseButton-primary"]:active::after {{
        transform: scale(0, 0);
        opacity: 0.3;
        transition: 0s;
    }}
    button[data-testid="baseButton-primary"]:hover {{
        background: var(--primary-hover) !important;
        box-shadow: 0 6px 15px -2px rgba(59, 130, 246, 0.5) !important;
        transform: translateY(-2px);
    }}
    button[data-testid="baseButton-primary"]:active {{
        transform: scale(0.97) translateY(0);
        box-shadow: 0 2px 4px -1px rgba(59, 130, 246, 0.3) !important;
    }}
    
    /* 次要按钮 */
    button[data-testid="baseButton-secondary"] {{
        background-color: var(--secondary-color) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-md) !important;
        font-weight: 500 !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative;
        overflow: hidden;
    }}
    button[data-testid="baseButton-secondary"]::after {{
        content: '';
        position: absolute;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        pointer-events: none;
        background-image: radial-gradient(circle, var(--primary-color) 10%, transparent 10.01%);
        background-repeat: no-repeat;
        background-position: 50%;
        transform: scale(10, 10);
        opacity: 0;
        transition: transform .5s, opacity 1s;
    }}
    button[data-testid="baseButton-secondary"]:active::after {{
        transform: scale(0, 0);
        opacity: 0.1;
        transition: 0s;
    }}
    button[data-testid="baseButton-secondary"]:hover {{
        background-color: var(--secondary-hover) !important;
        border-color: var(--primary-color) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    }}
    button[data-testid="baseButton-secondary"]:active {{
        transform: scale(0.97);
    }}
    
    /* ====== 数据框/数据编辑器覆写以优化显示效果 ====== */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {{
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        overflow: hidden;
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    [data-testid="stDataFrame"]:hover, [data-testid="stDataEditor"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        border-color: var(--primary-color);
    }}
    
    /* ====== 徽章样式 ====== */
    .st-emotion-cache-12awvrt {{
        border-radius: 4px;
        font-size: 0.8rem;
    }}
    </style>
    """, unsafe_allow_html=True)

def render_hero_section():
    st.markdown('<h1 class="hero-title">🔮 EventWeaver - 智能叙事引擎</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">专业级剧情拓扑设计工具 | 连接因果脉络，推演世界走向</p>', unsafe_allow_html=True)


def render_sidebar() -> Dict[str, Any]:
    """
    渲染侧边栏并返回配置信息。
    """
    with st.sidebar:
        st.header("🎨 工坊设定台")
        st.caption("定制属于你的核心设定，让 AI 懂你的灵感与脑洞。")
        
        with st.expander("👥 角色羁绊", expanded=True):
            character_info = st.text_area(
                "人物小传 & 关系网", 
                value="林警官：工作狂，逻辑缜密，但半年前因失误导致搭档殉职，一直被失眠困扰。\n周医生：死者的私人心理医生，温和有礼，却对死者生前的某些秘密避而不谈。\n赵助理：死者的得力助手，案发当晚声称自己在加班，表现得过于惊恐，似乎看到了不该看的东西。\n关系：林警官与死者曾是旧识，周医生似乎在刻意引导林警官的调查方向。",
                height=150,
                key="character_info_input",
                help="定义主要角色及其相互关系，AI 将在生成时保持人设一致性。"
            )
            
        with st.expander("🌍 世界观背景", expanded=True):
            world_setting = st.text_area(
                "故事舞台", 
                value="“灰雾镇”，一座常年被浓雾笼罩的偏远小镇。通讯信号时断时续，唯一的出山公路因泥石流被彻底封死。当地首富在紧闭的复古庄园书房内离奇死亡，门窗从内心反锁，唯一的钥匙就在死者口袋里——一个完美的密室杀人案。",
                height=100,
                key="world_setting_input"
            )

        with st.expander("🎯 目标读者", expanded=True):
            st.caption("定义目标受众以优化叙事策略")
            target_age = st.select_slider("目标年龄段", options=["儿童 (6-12)", "青少年 (13-18)", "青年 (19-35)", "中年 (36-60)", "全年龄"], value="青年 (19-35)")
            
            # 使用多选框提供预设标签
            default_tags = ["快节奏/网文风", "科幻/科技伦理"]
            tag_options = {
                "快节奏/网文风": "追求爽点、强冲突和剧情反转，减少冗长铺垫",
                "慢热/实体书风": "注重细节刻画、环境渲染与氛围烘托",
                "硬核推理": "喜爱伏笔、多重视角与严密逻辑，不把读者当傻子",
                "群像刻画": "看重多配角互动，配角智商在线，各有弧光",
                "情感驱动": "注重角色内心活动与人物间的深层羁绊",
                "科幻/科技伦理": "关注科技发展对人性的异化及哲学探讨"
            }
            
            selected_tags = st.multiselect(
                "偏好标签", 
                options=list(tag_options.keys()), 
                default=default_tags,
                help="选择能代表目标读者群体的标签"
            )
            
            # 显示选中标签的解释
            if selected_tags:
                tag_explanations = "".join([f"<li style='margin-bottom: 2px;'><b>{tag}</b>: {tag_options[tag]}</li>" for tag in selected_tags])
                st.markdown(f"<ul style='font-size: 0.85em; color: #555; padding-left: 1.5rem;'>{tag_explanations}</ul>", unsafe_allow_html=True)
            
            # 允许用户自定义补充
            custom_pref = st.text_input("补充偏好要求", value="", help="如有其他特殊要求可在此填写")
            
            # 组合最终的读者偏好字符串
            reader_preference = ", ".join(selected_tags)
            if custom_pref:
                reader_preference += f", {custom_pref}"

        author_context = {
            "characters": character_info,
            "world_setting": world_setting,
            "target_audience": {
                "age": target_age,
                "preference": reader_preference
            }
        }
        
        st.divider()
        st.markdown("<p style='font-size: 0.8rem; color: var(--text-muted); text-align: center'>Powered by EventWeaver AI | 纺织世界的每一条因果</p>", unsafe_allow_html=True)
        st.info("提示：您可以将背景图片命名为 `bg.jpg` 放置在项目根目录中的 `assets/` 文件夹下以自定义应用背景。")
        
        return author_context

def render_jsonl_import_mode() -> Tuple[Optional[str], bool]:
    """渲染 JSONL 文件导入模式"""
    st.markdown("### 📁 JSONL 文件导入")
    st.caption("由于系统运行在云端，无法直接读取您的本地 C 盘路径。请点击下方按钮上传您的 `test.jsonl` 文件。")
    
    selected_record_str = None
    submit_btn = False
    
    with st.container(border=True):
        uploaded_file = st.file_uploader("选择 JSONL 文件", type=['jsonl', 'json', 'txt'], help="请上传包含事件网络数据的 JSONL 文件")
        
        if uploaded_file is not None:
            try:
                content = uploaded_file.getvalue().decode("utf-8")
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                
                if lines:
                    st.success(f"成功读取文件，共 {len(lines)} 条记录。")
                    
                    selected_index = st.selectbox(
                        "选择要加载的记录", 
                        range(len(lines)), 
                        format_func=lambda x: f"记录 {x+1}: {lines[x][:60]}..."
                    )
                    
                    selected_record_str = lines[selected_index]
                    submit_btn = st.button("🚀 解析并加载选中记录", type="primary", use_container_width=True)
            except Exception as e:
                st.error(f"读取文件失败: {e}")
                
    return selected_record_str, submit_btn

def render_text_extraction_mode() -> Tuple[str, bool]:
    """渲染文本提取模式"""
    st.markdown("### 📖 文本大纲录入")
    st.caption("输入你的故事草稿、Galgame 剧情分支构想或 TNO 历史走向走向短文，AI 将为你梳理完整的事件时空结构。")
    
    with st.container(border=True):
        input_text = st.text_area("故事大纲 / 草稿", height=300, value="男主在放学后的旧校舍偶然撞见了正在咏唱魔法的同班同学绫音。为了掩盖秘密，绫音提出要清除男主相关的记忆。在此危机关头，男主觉醒了观测过去平行时空的能力...", label_visibility="collapsed", key="story_draft_input")
        submit_btn = st.button("🚀 提炼时空结构", type="primary", use_container_width=True)
        
    return input_text, submit_btn

def render_event_network_input_mode() -> Tuple[str, bool]:
    """渲染事件网络大纲录入模式"""
    st.markdown("### ✍️ 事件网络大纲录入 (极速版)")
    st.caption("使用极其简洁的纯文本语法，能够无延迟、高精度地解析 100+ 个节点。完全本地化，无需等待 AI。")
    
    default_text = """[1] 神秘电话: 李明在雨夜接到了神秘电话 (setup)
[2] 码头陷阱: 来到废弃码头发现只有打手 (conflict) <- 1
[3] 艰难突围: 利用地形优势艰难突围并受伤 (event) <- 2
[4] 幕后黑手: 发现这一切是老K的阴谋 (discovery) <- 3
[5] 医院疗伤: 在黑诊所内包扎伤口 (resolution) <- 3"""
    
    if 'event_network_draft' not in st.session_state:
        st.session_state['event_network_draft'] = default_text
        
    def load_100_nodes_example():
        try:
            with open(os.path.join(os.path.dirname(__file__), 'example_100_nodes.txt'), 'r', encoding='utf-8') as f:
                st.session_state['event_network_draft'] = f.read()
        except Exception as e:
            st.error(f"加载示例失败: {e}")

    with st.container(border=True):
        col1, col2 = st.columns([3, 2])
        col2.button("✨ 加载 100 节点赛博朋克示例", on_click=load_100_nodes_example, use_container_width=True)
            
        input_content = st.text_area("事件网络大纲结构", key="event_network_draft", height=350, label_visibility="collapsed", help="""语法说明：
[节点ID] 核心词/标题: 详细描述文本 (可选类型) <- 依赖的源节点ID (用逗号分隔)

类型可选: setup(铺垫), conflict(冲突), event(常规), discovery(发现), resolution(解决), climax(高潮)
""")
        submit_btn = st.button("🚀 极速解析结构", type="primary", use_container_width=True)
        
    return input_content, submit_btn

def render_random_generation_mode() -> Tuple[str, str, str, str, str, bool, bool]:
    """
    渲染随机生成模式 (重构版：Tag-based UI)
    """
    # 注入自定义 CSS 以实现极客感/卡片式布局
    st.markdown("""
    <style>
    /* 隐藏 Radio 默认圆圈，改为标签(Tag)样式 */
    div[role="radiogroup"] > label > div:first-of-type {
        display: none;
    }
    div[role="radiogroup"] {
        flex-direction: row;
        flex-wrap: wrap;
        gap: 10px;
    }
    div[role="radiogroup"] label {
        background-color: #f0f2f6;
        padding: 6px 16px;
        border-radius: 20px;
        border: 1px solid #e0e0e0;
        cursor: pointer;
        transition: all 0.2s;
    }
    div[role="radiogroup"] label:hover {
        background-color: #e0e2e6;
        border-color: #d0d0d0;
    }
    /* 选中状态 (Streamlit 内部类名可能会变，这里尝试通用选择器) */
    div[role="radiogroup"] label[data-baseweb="radio"] {
        background-color: #e0e2e6;
    }
    
    /* 预览框样式 */
    .prompt-preview {
        background-color: #1e1e1e;
        color: #00ff9d;
        font-family: 'Courier New', monospace;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #00ff9d;
        margin-bottom: 20px;
        font-size: 0.9rem;
    }
    .tag-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #666;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("### 🎲 随机灵感生成器")

    # --- 1. 实时预览区 (交互反馈) ---
    # 我们需要先定义变量才能显示预览，所以这里先占位，最后渲染
    preview_container = st.empty()

    # --- 2. 模块化选项卡 ---
    tab_core, tab_style, tab_params = st.tabs(["🧩 核心设定", "🎨 风格定义", "⚙️ 参数微调"])

    with tab_core:
        st.markdown('<div class="tag-label">事件类别</div>', unsafe_allow_html=True)
        category = st.radio("事件类别", 
            ["奇幻冒险", "科幻未来", "悬疑推理", "现代都市", "历史演义", "恐怖惊悚", "校园青春", "商业商战", "TNO事件", "Galgame/恋爱", "互动小说"], 
            horizontal=True, label_visibility="collapsed")
        
        st.markdown('<div class="tag-label" style="margin-top: 15px;">核心主题</div>', unsafe_allow_html=True)
        theme = st.text_input("核心主题", placeholder="例如：背叛, 时间旅行, 宝藏", label_visibility="collapsed")
        
        st.markdown('<div class="tag-label" style="margin-top: 15px;">世界观</div>', unsafe_allow_html=True)
        background = st.text_area("世界观", placeholder="例如：赛博朋克2077风格，由巨型企业统治的世界...", height=80, label_visibility="collapsed", key="world_bg_input")

    with tab_params:
        st.markdown('<div class="tag-label">复杂程度</div>', unsafe_allow_html=True)
        complexity = st.select_slider("复杂程度", 
            options=["简单", "中等", "复杂", "史诗"], value="中等", label_visibility="collapsed")
        
        st.markdown('<div class="tag-label" style="margin-top: 15px;">意外度</div>', unsafe_allow_html=True)
        randomness = st.radio("意外度", ["低", "中", "高"], index=1, horizontal=True, label_visibility="collapsed")
        
        st.markdown('<div class="tag-label" style="margin-top: 15px;">其他选项</div>', unsafe_allow_html=True)
        show_probability = st.toggle("显示发生概率", value=True)

    # 为了保持返回值一致，这里先返回 None 占位样式控制，稍后在主流程处理
    # 但根据原函数签名，我们需要返回 submit_btn
    # 这里我们把 submit_btn 放在最下面
    
    # 更新预览内容
    prompt_preview = f"生成一个 **[{category}]** 类型的事件网络，主题为 **[{theme if theme else '未指定'}]**。背景设定在 **[{background if background else '默认世界'}]**。结构复杂度为 **[{complexity}]**，包含 **[{randomness}]** 的意外转折。"
    preview_container.markdown(f'<div class="prompt-preview">>_ PROMPT_PREVIEW: {prompt_preview}</div>', unsafe_allow_html=True)

    st.write("")
    submit_btn = st.button("✨ 生成随机事件网络", type="primary", use_container_width=True)
    
    return category, complexity, theme, background, randomness, show_probability, submit_btn

def render_style_controls() -> Tuple[str, str, str, Tuple[int, int], str, bool]:
    """
    渲染风格和基调控制区域 (标签式UI)
    """
    with st.form("style_form", border=True):
        st.markdown("#### 🖋️ 写作风格配置")
        
        st.markdown('<div class="tag-label">叙事风格</div>', unsafe_allow_html=True)
        style = st.radio("叙事风格", 
            ["现实主义", "浪漫主义", "古典文学", "现代都市", "奇幻史诗", "科幻未来", "悬疑推理", "童话寓言", "轻小说", "武侠仙侠"], 
            horizontal=True, label_visibility="collapsed")
            
        st.markdown('<div class="tag-label" style="margin-top: 15px;">情感基调</div>', unsafe_allow_html=True)
        tone = st.radio("情感基调", 
            ["轻松", "幽默", "悲伤", "治愈", "悬疑", "恐怖", "浪漫", "冷峻", "史诗", "热血"], 
            horizontal=True, label_visibility="collapsed")
            
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="tag-label" style="margin-top: 15px;">叙事视角</div>', unsafe_allow_html=True)
            pov = st.selectbox("叙事视角", ["第三人称全知", "第一人称 (主角)", "第三人称限知", "第二人称 (你)"], label_visibility="collapsed")
        with col2:
            st.markdown('<div class="tag-label" style="margin-top: 15px;">目标字数</div>', unsafe_allow_html=True)
            target_word_count = st.number_input("目标字数", min_value=100, max_value=20000, value=2000, step=100, label_visibility="collapsed")
        
        with st.expander("🎭 文本风格参考 (可选)"):
            st.caption("输入或上传一段您喜欢的参考文本，AI 将学习并模仿其辞藻、句式与行文节奏。")
            uploaded_style_file = st.file_uploader("上传文本文档 (.txt)", type=["txt"], label_visibility="collapsed")
            default_ref_text = ""
            if uploaded_style_file is not None:
                try:
                    default_ref_text = uploaded_style_file.getvalue().decode("utf-8")
                except:
                    st.error("文件读取失败，当前仅支持 UTF-8 编码的 TXT 文件。")
            
            reference_text = st.text_area("参考文本", value=default_ref_text, height=120, placeholder="例如：输入或上传一段古龙风格的对话，或马尔克斯风格的描写...", key="reference_text_input")
            
        st.write("")
        st.caption("✨ 已集成前沿 AI 写作技术：场景化叙事(Show, Don't Tell)、人物主体性微表情拉扯及多维感官锚点。")
        generate_btn = st.form_submit_button("📝 使用专业写作工坊模式生成正文", type="primary", use_container_width=True)
    
    return style, tone, pov, target_word_count, reference_text, generate_btn

def get_interactive_graph_data(network: Dict[str, Any], layout_algo: str = 'ForceAtlas2', rankdir: str = 'LR', highlight_target: str = None) -> Tuple[List[Node], List[Edge], Config]:
    """准备 streamlit-agraph 所需的数据"""
    
    nodes = []
    edges = []
    
    if not network:
        return [], [], None

    # 计算回溯路径 (祖先节点及包含的边)
    ancestor_nodes = set()
    ancestor_edges = set() # (source, target)
    
    if highlight_target:
        queue = [highlight_target]
        ancestor_nodes.add(highlight_target)
        
        # 建立反向图，只考虑 causal 或 temporal 这种有方向的关系，但也为了鲁棒兼容所有边
        reverse_adj = {}
        for edge in network.get('edges', []):
            src = edge['source']
            tgt = edge['target']
            if tgt not in reverse_adj:
                reverse_adj[tgt] = []
            reverse_adj[tgt].append((src, edge))
            
        while queue:
            curr = queue.pop(0)
            for src, edge in reverse_adj.get(curr, []):
                ancestor_edges.add((edge['source'], edge['target']))
                if src not in ancestor_nodes:
                    ancestor_nodes.add(src)
                    queue.append(src)

    # 定义节点样式映射（添加颜色、图标形状，并增强视觉区分度，专业版配色）
    style_map = {
        'setup': {'color': '#e0f2fe', 'shape': 'box', 'borderWidth': 1, 'icon': '📂'},        # 铺垫：清冷蓝
        'conflict': {'color': '#fee2e2', 'shape': 'box', 'borderWidth': 2, 'icon': '⚔️'},    # 冲突：警示红
        'climax': {'color': '#fef08a', 'shape': 'box', 'borderWidth': 3, 'icon': '🔥'},      # 高潮：炽烈黄
        'resolution': {'color': '#dcfce7', 'shape': 'box', 'borderWidth': 1, 'icon': '✅'},    # 结局：确认绿
        'investigation': {'color': '#f3e8ff', 'shape': 'box', 'borderWidth': 1, 'icon': '🔎'}, # 调查：悬疑紫
        'discovery': {'color': '#ffedd5', 'shape': 'box', 'borderWidth': 2, 'icon': '💡'},    # 发现：提示橙
        'prediction': {'color': '#f1f5f9', 'shape': 'box', 'borderWidth': 2, 'icon': '🔮'},    # 预测：神秘灰白
        'event': {'color': '#f9fafb', 'shape': 'box', 'borderWidth': 1, 'icon': '▫️'}         # 常规：极简灰白
    }

    # 添加节点
    for node in network.get('nodes', []):
        if not isinstance(node, dict) or 'id' not in node:
            continue
            
        node_type = node.get('type', 'event')
        style = style_map.get(node_type, style_map['event'])
        
        # 根据 salience 调整大小，默认值为 5
        salience = node.get('salience', 5)
        base_size = 25
        if node_type == 'climax':
            base_size = 35
        elif node_type == 'prediction':
            base_size = 20
            
        size = base_size + (salience - 5) * 2
        
        # 判断高亮状态
        is_highlighted = not highlight_target or node['id'] in ancestor_nodes
        is_target_itself = highlight_target and node['id'] == highlight_target
        
        # 设置节点颜色、字体、边框
        node_color = style['color'] if is_highlighted else '#f8fafc'
        node_border = style.get('borderColor', '#333333')
        node_border_width = style['borderWidth']
        font_color = '#333333' if is_highlighted else '#cbd5e1'
        
        if is_highlighted and highlight_target:
            if is_target_itself:
                node_border = '#6366f1'  # 靛蓝高亮边框
                node_border_width = 4
            else:
                node_border = '#f59e0b'  # 回溯路径上的节点用橙色高亮边框
                node_border_width = 3
        elif not is_highlighted:
            node_border = '#e2e8f0'
            node_border_width = 1
        
        # 应用图标于标签前
        raw_label = node['label']
        if node_type == 'prediction' and raw_label.startswith('🔮 '):
            raw_label = raw_label[2:] # 移除可能已有的🔮
            
        label = f"{style['icon']} {raw_label}"
        if node_type == 'prediction' and 'likelihood' in node:
            label += f"\n({node['likelihood']})"
                
        # 悬浮提示文本 (Tooltip) - 优化为 HTML 格式
        desc = node.get('description', '无描述')
        title_html = f"""
        <div style="font-family: 'Inter', sans-serif; padding: 8px; max-width: 300px; line-height: 1.5;">
            <div style="font-size: 14px; font-weight: bold; color: {'#4f46e5' if is_target_itself else '#1e293b'}; margin-bottom: 4px;">{node['label']} {(' (回溯起点)' if is_target_itself else '')}</div>
            <div style="font-size: 12px; color: #475569;">{desc}</div>
        """
        
        if 'arguments' in node and node['arguments']:
            args = node['arguments']
            title_html += '<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e2e8f0; font-size: 12px;">'
            
            if isinstance(args, dict):
                for key, val in args.items():
                    title_html += f'<div style="margin-bottom: 2px;"><span style="color: #64748b; font-weight: 600;">{key}:</span> <span style="color: #334155;">{val}</span></div>'
            elif isinstance(args, list):
                for arg in args:
                    if isinstance(arg, dict):
                        role = arg.get('role', '元素')
                        text = arg.get('text', str(arg))
                        title_html += f'<div style="margin-bottom: 2px;"><span style="color: #64748b; font-weight: 600;">{role}:</span> <span style="color: #334155;">{text}</span></div>'
                    else:
                        title_html += f'<div style="margin-bottom: 2px; color: #334155;">{str(arg)}</div>'
                        
            title_html += '</div>'
            
        title_html += "</div>"

        nodes.append(Node(
            id=node['id'],
            label=label,
            size=size,
            shape=style['shape'],
            color=node_color,
            borderWidth=node_border_width,
            title=title_html,
            font={'color': font_color, 'size': 14}
        ))
        
    # 添加边
    for edge in network.get('edges', []):
        if not isinstance(edge, dict) or 'source' not in edge or 'target' not in edge:
            continue
            
        is_edge_highlighted = not highlight_target or (edge['source'], edge['target']) in ancestor_edges
        
        edge_color = '#aaaaaa' if is_edge_highlighted else '#f1f5f9'
        edge_width = 1
        
        if is_edge_highlighted:
            if edge.get('relation_type') == 'probabilistic':
                edge_color = '#a0c0a0' # 预测边使用淡绿色
            
            if highlight_target:
                edge_color = '#f59e0b' # 突出显示路径上的边（琥珀橙色）
                edge_width = 3
            
        edges.append(Edge(
            source=edge['source'],
            target=edge['target'],
            label=edge.get('label', ''),
            type="curvedCW",
            color={'color': edge_color, 'highlight': edge_color},
            width=edge_width,
            arrows={'to': {'enabled': True, 'scaleFactor': 1.0, 'type': 'arrow'}},
            dashes=True if edge.get('relation_type') == 'probabilistic' else False,
            font={'align': 'middle', 'color': edge_color if is_edge_highlighted else '#cbd5e1'}
        ))

    # 配置
    hierarchical = False
    physics_config = {"enabled": True}

    if layout_algo == 'Hierarchical (Dot/Dagre)':
        hierarchical = True
        physics_config = {"enabled": False}
    elif layout_algo == 'ForceAtlas2':
        hierarchical = False
        physics_config = {
            "enabled": True,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
                "gravitationalConstant": -150,
                "centralGravity": 0.015,
                "springLength": 150,
                "springConstant": 0.08,
                "damping": 0.4,
                "avoidOverlap": 1
            },
            "stabilization": {"enabled": True, "iterations": 150, "fit": True},
            "minVelocity": 0.75
        }
    elif layout_algo == 'Spring (BarnesHut)':
        hierarchical = False
        physics_config = {
            "enabled": True,
            "solver": "barnesHut",
            "barnesHut": {
                "gravitationalConstant": -3000,
                "centralGravity": 0.3,
                "springLength": 150,
                "springConstant": 0.04,
                "damping": 0.09,
                "avoidOverlap": 1
            },
            "stabilization": {"enabled": True, "iterations": 150, "fit": True}
        }

    # 动态调整层级布局参数
    level_separation = 200
    node_spacing = 150
    
    if hierarchical:
        if rankdir in ['LR', 'RL']:
            # 左右布局：层级间距需要足够大以容纳横向的中文标签
            level_separation = 400 
            node_spacing = 150
        else: # TB, BT
            # 上下布局：同层节点间距需要足够大以防止标签重叠
            level_separation = 220
            node_spacing = 400

    config = Config(
        width='100%',
        height=800,
        directed=True, 
        nodeHighlightBehavior=True, 
        highlightColor="#F7A7A6",
        collapsible=False,
        rankdir=rankdir, 
        hierarchical=hierarchical, 
        physics=physics_config,
        layout={"hierarchical": {
            "enabled": hierarchical,
            "direction": rankdir,
            "sortMethod": "directed",
            "levelSeparation": level_separation,
            "nodeSpacing": node_spacing
        }} 
    )
    
    return nodes, edges, config

def render_graph_tab(network_data: Optional[Dict[str, Any]]) -> bool:
    """渲染事件网络图标签页，返回是否点击了'预测未来'按钮"""
    predict_clicked = False
    if network_data:
        nodes_count = len(network_data.get('nodes', []))
        edges_count = len(network_data.get('edges', []))
        
        col_info, col_btn = st.columns([3, 1])
        with col_info:
            st.write(f"**节点数:** {nodes_count} | **连线数:** {edges_count}")
        with col_btn:
            predict_clicked = st.button("🔮 预测未来发展", help="基于当前网络推演后续可能发生的事件", use_container_width=True)
        
        with st.form("graph_layout_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                rankdir = st.selectbox("布局方向", ["LR (左到右)", "TB (上到下)", "RL (右到左)", "BT (下到上)"], index=0)
                rankdir_code = rankdir.split(" ")[0]
            with c2:
                layout_algo = st.selectbox("布局算法", ["力导向图 (ForceAtlas2)", "弹簧模型 (BarnesHut)", "层级树状图 (Hierarchical)"], index=0)
                
                # 映射回内部算法名称
                algo_map = {
                    "力导向图 (ForceAtlas2)": "ForceAtlas2",
                    "弹簧模型 (BarnesHut)": "Spring (BarnesHut)",
                    "层级树状图 (Hierarchical)": "Hierarchical (Dot/Dagre)"
                }
                internal_algo = algo_map[layout_algo]
            with c3:
                node_options = ["无"] + [f"[{n['id']}] {n['label']}" for n in network_data.get('nodes', [])]
                traceback_selection = st.selectbox("🔍 剧情回溯 (高亮前置路径)", node_options, index=0, help="选择一个节点，回溯并高亮直接或间接导致该事件发生的所有前置节点与关系。")
                
                highlight_target = None
                if traceback_selection != "无":
                    m = re.match(r"^\[(.*?)\]", traceback_selection)
                    if m:
                        highlight_target = m.group(1)
            
            st.form_submit_button("应用视图设置")

        st.caption("提示: 点击节点可在下方查看详细描述；支持拖动节点。")
        
        try:
            nodes, edges, config = get_interactive_graph_data(network_data, layout_algo=internal_algo, rankdir=rankdir_code, highlight_target=highlight_target)
            selected_node_id = agraph(nodes=nodes, edges=edges, config=config)
            
            if selected_node_id:
                selected_node = next((n for n in network_data['nodes'] if n['id'] == selected_node_id), None)
                if selected_node:
                    st.info(f"📌 **选中事件: {selected_node['label']}**\n\n{selected_node.get('description', '暂无描述')}")
                    if 'type' in selected_node:
                        st.caption(f"类型 (Type): {selected_node['type']}")
                    if 'salience' in selected_node:
                        st.caption(f"重要性 (Salience): {selected_node['salience']}")
                    if 'likelihood' in selected_node:
                        st.caption(f"发生概率 (Likelihood): {selected_node['likelihood']}")
                    
        except Exception as e:
            st.error(f"无法绘制图表: {e}")
            st.info("您可以查看 'JSON 数据' 标签页来确认提取结果。")
    else:
        st.info("尚未生成事件网络。请确保 Ollama 已启动并点击左侧按钮。")
        
    return predict_clicked

def render_edit_network_tab(network_data: Optional[Dict[str, Any]]) -> Tuple[bool, bool, bool]:
    """渲染编辑网络标签页"""
    if not network_data:
        st.info("尚未生成事件网络。")
        return False, False, False
        
    st.markdown("### ✏️ 编辑节点 (Nodes)")
    st.caption("您可以直接在表格中修改节点信息，或在底部添加/删除节点。")
    
    nodes = network_data.get('nodes', [])
    if nodes:
        nodes_df = pd.DataFrame(nodes)
    else:
        nodes_df = pd.DataFrame(columns=['id', 'label', 'description', 'type', 'salience', 'likelihood'])
        
    for col in ['id', 'label', 'description', 'type', 'salience']:
        if col not in nodes_df.columns:
            nodes_df[col] = None

    for col in ['id', 'label', 'description']:
        if col in nodes_df.columns:
            nodes_df[col] = nodes_df[col].apply(lambda x: str(x) if pd.notnull(x) else None)
            
    cols = ['id', 'label', 'type', 'salience', 'description']
    if 'likelihood' in nodes_df.columns:
        cols.append('likelihood')
    for col in nodes_df.columns:
        if col not in cols:
            cols.append(col)
    nodes_df = nodes_df[cols]
            
    edited_nodes = st.data_editor(
        nodes_df, 
        num_rows="dynamic", 
        use_container_width=True,
        key="nodes_editor",
        column_config={
            "id": st.column_config.TextColumn("节点 ID", required=True),
            "label": st.column_config.TextColumn("事件名称", required=True),
            "type": st.column_config.SelectboxColumn("类型", options=['setup', 'conflict', 'climax', 'resolution', 'investigation', 'discovery', 'prediction', 'event'], required=True),
            "salience": st.column_config.NumberColumn("重要性 (1-10)", min_value=1, max_value=10, step=1),
            "description": st.column_config.TextColumn("详细描述"),
        }
    )
    
    st.markdown("### 🔗 编辑连线 (Edges)")
    st.caption("定义事件之间的关系。Source 和 Target 必须对应节点的 ID。")
    
    edges = network_data.get('edges', [])
    if edges:
        edges_df = pd.DataFrame(edges)
    else:
        edges_df = pd.DataFrame(columns=['source', 'target', 'label', 'relation_type'])
        
    for col in ['source', 'target', 'label', 'relation_type']:
        if col not in edges_df.columns:
            edges_df[col] = None

    for col in ['source', 'target', 'label']:
        if col in edges_df.columns:
            edges_df[col] = edges_df[col].apply(lambda x: str(x) if pd.notnull(x) else None)
            
    edited_edges = st.data_editor(
        edges_df, 
        num_rows="dynamic", 
        use_container_width=True,
        key="edges_editor",
        column_config={
            "source": st.column_config.TextColumn("起点 ID", required=True),
            "target": st.column_config.TextColumn("终点 ID", required=True),
            "label": st.column_config.TextColumn("关系描述"),
            "relation_type": st.column_config.SelectboxColumn("关系类型", options=['causal', 'probabilistic', 'temporal']),
        }
    )
    
    st.markdown("### 🛠️ 操作区")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💾 保存修改并更新图谱", type="primary", use_container_width=True):
            new_nodes = edited_nodes.where(pd.notnull(edited_nodes), None).to_dict('records')
            new_edges = edited_edges.where(pd.notnull(edited_edges), None).to_dict('records')
            
            clean_nodes = [{k: v for k, v in node.items() if v is not None} for node in new_nodes]
            clean_edges = [{k: v for k, v in edge.items() if v is not None} for edge in new_edges]
            
            st.session_state['network'] = {
                "nodes": clean_nodes,
                "edges": clean_edges
            }
            st.session_state['network_saved_trigger'] = True
            st.rerun()
            
    with col2:
        audit_clicked = st.button("🔍 逻辑审查修复", use_container_width=True, help="检查连线逻辑漏洞并自动修复")
        
    with col3:
        analyze_args_clicked = st.button("🔎 补全缺失论元", use_container_width=True, help="发现缺失的主体/客体/时间/地点，并智能补齐")
        
    with col4:
        refine_edges_clicked = st.button("🔗 深度因果推理", use_container_width=True, help="分析 temporal 边，将其精确升级为 causal 关系")
        
    return audit_clicked, analyze_args_clicked, refine_edges_clicked

def render_story_tab(story_text: Optional[str], image_prompts_data: Optional[Dict[str, Any]] = None) -> bool:
    """渲染故事标签页，包含多模态绘画提示词生成"""
    gen_prompts_clicked = False
    
    if story_text:
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            font_family = st.selectbox("字体", ["Serif", "Sans-serif", "Monospace"], index=0)
        with col_t2:
            font_size = st.slider("字号", 12, 36, 18)
        with col_t3:
            text_align = st.selectbox("对齐方式", ["justify", "left", "center", "right"], index=0)
        
        st.markdown(f"""
        <style>
        .story-container {{
            font-family: {font_family}, 'Noto Serif SC', 'Source Han Serif SC', serif;
            font-size: {font_size}px;
            text-align: {text_align};
            line-height: 1.9;
            padding: 3rem;
            background-color: var(--bg-base);
            color: var(--text-primary);
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-md);
            max-width: 850px;
            margin: 2rem auto;
            transition: var(--transition-normal);
        }}
        .story-container p {{
            margin-bottom: 1.2em;
            text-indent: 2em;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<div class="story-container">{story_text.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
        
        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            st.download_button(
                label="💾 下载故事文本 (TXT)",
                data=story_text,
                file_name="story.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col_act2:
            if st.button("🗑️ 清空当前故事", use_container_width=True):
                st.session_state['story'] = None
                st.rerun()
        
        st.divider()
        st.subheader("🎨 多模态绘画提示词")
        st.caption("为关键情节生成 AI 绘画提示词，辅助视觉创作。")
        
        gen_prompts_clicked = st.button("✨ 生成关键帧绘画提示词", use_container_width=True)
        
        if image_prompts_data:
            prompts = image_prompts_data.get('prompts', [])
            if prompts:
                prompts_json = json.dumps(prompts, ensure_ascii=False, indent=2)
                st.download_button(
                    label="💾 下载提示词数据 (JSON)",
                    data=prompts_json,
                    file_name="image_prompts.json",
                    mime="application/json",
                    use_container_width=True
                )
                for p in prompts:
                    with st.expander(f"🖼️ {p.get('event_label', '未命名事件')}", expanded=True):
                        st.markdown(f"**中文描述:** {p.get('description_cn', '')}")
                        st.code(p.get('prompt_en', ''), language="text")
                        st.caption("可直接复制上方英文提示词到 Midjourney 或 Stable Diffusion 中使用。")
            else:
                st.info("生成结果为空，请重试。")

    else:
        st.info("尚未生成故事。您可以点击上方按钮进行生成。")

    # 总是显示故事历史，只要有历史记录
    history = st.session_state.get('story_history', [])
    if len(history) > 0:
        st.divider()
        st.subheader("📜 故事生成历史")
        st.caption("下方是您本次会话中生成的所有历史版本。")
        
        # 找到当前展示的内容对应的索引或内容
        current_story = story_text if story_text else ""
        
        for idx, item in enumerate(reversed(history)):
            is_current = item.get("content") == current_story
            title_suffix = " (当前版本)" if is_current else ""
            
            with st.expander(f"🕰️ {item.get('time', '')} - 风格: {item.get('style', '')} 语调: {item.get('tone', '')}{title_suffix}"):
                st.markdown(f'<div class="story-container" style="padding: 1rem; margin: 0; background-color: var(--bg-surface);">{item.get("content", "").replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                if not is_current:
                    if st.button("⏪ 恢复此版本", key=f"restore_story_{idx}"):
                        st.session_state['story'] = item.get("content")
                        st.session_state['restored_story_trigger'] = True
                        st.rerun()

    return gen_prompts_clicked

def render_json_tab(network_data: Optional[Dict[str, Any]]):
    """渲染 JSON 数据标签页"""
    if network_data:
        json_str = json.dumps(network_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="💾 下载事件网络数据 (JSON)",
            data=json_str,
            file_name="event_network.json",
            mime="application/json",
            use_container_width=False
        )
        st.json(network_data)

def render_knowledge_tab():
    st.markdown("### 📚 小说流派特征库 (Genre Library)")
    st.info("在这里创建并训练多个类型的小说特征库。生成新的小说时，AI将经过选定的底库，完美继承该类型的文风、套路与特征。")
    
    try:
        genres = genre_lib.get_all_genres()
    except Exception as e:
        st.error(f"加载流派库失败: {e}")
        genres = []
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("➕ 自动训练新流派 (AI Auto-Train)")
        training_sample = st.text_area("输入小说章节段落，让 AI 一键提取并提炼流派特征：", placeholder="将你想模仿的小说文本粘贴在这里，字数越多越准确...", height=150, key="training_sample")
        
        if st.button("🤖 AI 一键自动分析并训练流派", type="secondary", use_container_width=True):
            if not training_sample.strip():
                st.error("请先上方输入小说短片或文段作为训练样本。")
            else:
                with st.spinner("AI 正在深入分析文本风格、拆解套路与世界规律..."):
                    from event_net_gen import extract_genre_from_text
                    extracted = extract_genre_from_text(training_sample)
                    if extracted:
                        # Auto-save to library directly or auto-populate session state
                        new_id = extracted.get('id', 'new_genre')
                        # Check exist
                        if genre_lib.get_genre_by_id(new_id):
                            import time
                            new_id = f"{new_id}_{int(time.time())}"
                            
                        genre_lib.add_genre({
                            "id": new_id,
                            "name": extracted.get('name', '未命名流派'),
                            "system_prompt": extracted.get('system_prompt', ''),
                            "reference_text": training_sample[:500] + "..." if len(training_sample) > 500 else training_sample,
                            "network_prompt": extracted.get('network_prompt', '')
                        })
                        st.success(f"🎉 训练成功！已自动录入流派：{extracted.get('name')}！")
                        st.session_state['active_genre_id'] = new_id
                        st.session_state['active_genre_name'] = extracted.get('name', '未命名流派')
                        import time; time.sleep(1)
                        st.rerun()

        st.divider()
        st.subheader("➕ 手动创建流派 (Manual Train)")
        new_genre_id = st.text_input("流派 ID (如 wuxia, scifi)", key="new_genre_id")
        new_genre_name = st.text_input("流派名称 (如 传统武侠, 硬科幻)", key="new_genre_name")
        new_genre_prompt = st.text_area("系统指令 (文风和套路约束)", placeholder="你是一位传统武侠大师，文风古朴...", height=100, key="new_genre_prompt")
        new_genre_ref = st.text_area("代表性参考文本 (灵魂注入)", placeholder="落日余晖，长剑滴血...", height=100, key="new_genre_ref")
        
        if st.button("💾 训练并保存流派", type="primary"):
            if new_genre_id and new_genre_name:
                genre_lib.add_genre({
                    "id": new_genre_id,
                    "name": new_genre_name,
                    "system_prompt": new_genre_prompt,
                    "reference_text": new_genre_ref,
                    "network_prompt": ""
                })
                st.success(f"已成功训练并录入流派：{new_genre_name}！")
                st.rerun()
            else:
                st.error("请输入完整的 ID 和名称。")
                
    with col2:
        st.subheader("🗄️ 已训练的流派库")
        
        active_genre_id = st.session_state.get('active_genre_id', None)
        
        for g in genres:
            is_active = active_genre_id == g['id']
            border_color = "var(--primary-color)" if is_active else "var(--border-color)"
            bg_color = "var(--bg-surface)" if not is_active else "rgba(var(--primary-color-rgb), 0.1)"
            
            st.markdown(f'<div style="border: 1px solid {border_color}; border-radius: 8px; padding: 15px; margin-bottom: 15px; background-color: {bg_color};">', unsafe_allow_html=True)
            st.markdown(f"**{g['name']} ({g['id']})**")
            st.caption(f"设定: {g.get('system_prompt', '')[:30]}...")
            
            c1, c2 = st.columns([1, 1])
            with c1:
                if not is_active:
                    if st.button(f"✅ 启动该底库", key=f"activate_{g['id']}"):
                        st.session_state['active_genre_id'] = g['id']
                        st.session_state['active_genre_name'] = g['name']
                        st.toast(f"已启动 {g['name']} 底库！", icon="🚀")
                        st.rerun()
                else:
                    st.success("正在拦截并通过本库", icon="🔥")
            with c2:
                if st.button("🗑️ 删除", key=f"delete_{g['id']}"):
                    genre_lib.remove_genre(g['id'])
                    if active_genre_id == g['id']:
                        st.session_state['active_genre_id'] = None
                        st.session_state['active_genre_name'] = None
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
