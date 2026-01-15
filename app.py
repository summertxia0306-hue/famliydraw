import streamlit as st
import google.generativeai as genai
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import time
import uuid
import qrcode
import io

# --- 1. 配置与初始化 ---

# ⚠️⚠️⚠️ 请务必在 Streamlit Cloud 的 Secrets 里配置 GOOGLE_API_KEY
# 或者在本地测试时临时解开下面这行的注释填入 Key
# GOOGLE_API_KEY = "你的_API_KEY_粘贴在这里"

# 尝试获取 API Key
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    # 本地容错
    api_key = locals().get("GOOGLE_API_KEY", "")

if api_key:
    genai.configure(api_key=api_key)

# --- 2. CSS 美化 (核心：让界面像你的截图一样) ---
def inject_custom_css():
    st.markdown("""
    <style>
        /* 全局背景色：浅米色/淡黄 */
        .stApp {
            background-color: #FDFBF7;
        }
        /* 隐藏 Streamlit 默认的顶部菜单和Footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* 卡片样式 (模仿截图的白底圆角) */
        .css-card {
            background-color: #FFFFFF;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
            margin-bottom: 20px;
            text-align: center;
        }
        
        /* 标题样式 */
        h1, h2, h3 {
            font-family: 'Helvetica Neue', sans-serif;
            color: #333;
            font-weight: 700;
        }
        
        /* 按钮美化 */
        .stButton>button {
            border-radius: 12px;
            height: 3em;
            font-weight: bold;
            border: none;
            transition: all 0.3s;
        }
        /* 主按钮颜色 (蓝色渐变) */
        .stButton>button:hover {
            transform: scale(1.02);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        /* 角色选择卡片 */
        .role-card {
            border: 2px solid #eee;
            border-radius: 15px;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: 0.3s;
        }
        .role-card:hover {
            border-color: #4A90E2;
            background-color: #F0F7FF;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 全局状态管理 (模拟后端) ---
@st.cache_resource
class GameServer:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.room_id = str(uuid.uuid4())[:4].upper()
        self.status = "LOBBY" # LOBBY, PLAYING, JUDGING, RESULTS
        self.topic = ""
        # 玩家字典: {session_id: {'name': '爸爸', 'role': 'dad', 'avatar': '🧔', 'image': data, 'score': 0}}
        self.players = {} 
        self.updated_at = time.time()

    def join_player(self, sid, name, role, avatar):
        if sid not in self.players:
            self.players[sid] = {
                'name': name, 'role': role, 'avatar': avatar, 
                'image': None, 'score': 0, 'comment': ''
            }
            self.updated_at = time.time()
    
    def submit_work(self, sid, img_data):
        if sid in self.players:
            self.players[sid]['image'] = img_data
            self.updated_at = time.time()

server = GameServer()

# --- 4. 辅助函数 ---
def make_qr(url):
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def ai_generate_topic():
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = "生成一个非常具体、画面感强且搞笑的绘画题目，适合家庭娱乐。例如：'正在敷面膜的哥斯拉'。只返回题目文字。"
        return model.generate_content(prompt).text.strip()
    except:
        return "正在吃火锅的奥特曼" # 降级方案

def ai_judge_works(topic):
    # 这里简化为批量评价，实际可用循环调用
    # 这一步通常比较慢，需要 Loading 动画
    pass

# --- 5. 页面逻辑 ---

def main():
    st.set_page_config(page_title="灵魂画手家庭版", layout="wide", page_icon="🎨")
    inject_custom_css()

    # 获取当前 URL (用于生成二维码)
    # Streamlit Cloud 上部署后，这里会自动获取公网 URL
    try:
        # 获取当前 URL 的基础部分
        base_url = st.query_params.get("base_url", window_location_href=True)
    except:
        base_url = "请部署后查看"

    # 路由控制
    params = st.query_params
    role = params.get("role", "landing") # 默认为 landing 页

    if role == "landing":
        render_landing()
    elif role == "host":
        render_host_view()
    elif role == "player":
        render_player_view()

# --- 界面 A: 落地页 (类似图1/图3选择入口) ---
def render_landing():
    st.markdown("<div style='text-align: center; margin-top: 50px;'>", unsafe_allow_html=True)
    st.title("🎨 灵魂画手大乱斗")
    st.markdown("### —— 全家人的联机涂鸦战场 ——")
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.write("")

    # 模仿图3的卡片选择布局
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown("### 📺 我是主机 (电视/电脑)")
            st.write("负责出题、展示和投屏")
            if st.button("我是主机，开始建房", use_container_width=True, type="primary"):
                st.query_params.role = "host"
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("### 🖌️ 我是选手 (手机)")
            st.write("负责画画和提交作品")
            if st.button("我是选手，加入游戏", use_container_width=True):
                st.query_params.role = "player"
                st.rerun()

# --- 界面 B: 主机大厅 (复刻图2) ---
def render_host_view():
    # 顶部Logo区
    st.markdown("<h2 style='color:#4A90E2'>Soul Painter <span style='font-size:0.6em;color:#999'>主机端</span></h2>", unsafe_allow_html=True)
    
    # 使用两列布局：左侧控制板，右侧扫码区
    c1, c2 = st.columns([3, 2], gap="large")

    with c1:
        # 大白卡片
        st.markdown(f"""
        <div class="css-card">
            <h3>🎮 控制面板</h3>
            <p style="color:#888; margin-bottom: 30px;">等待玩家加入后点击开始...</p>
            <div style="padding: 20px; background: #f9f9f9; border-radius: 10px; margin-bottom:20px;">
                <h4>已加入玩家 ({len(server.players)})</h4>
                <div style="display: flex; justify-content: center; gap: 10px; flex-wrap: wrap;">
                    {''.join([f'<span style="font-size:2em" title="{p["name"]}">{p["avatar"]}</span>' for p in server.players.values()]) if server.players else '<span style="color:#ccc">...虚位以待...</span>'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 开始按钮逻辑
        start_disabled = len(server.players) == 0
        if st.button("🚀 开启挑战", type="primary", use_container_width=True, disabled=start_disabled):
            with st.spinner("AI 正在想题目..."):
                topic = ai_generate_topic()
                server.topic = topic
                server.status = "PLAYING"
                st.rerun()

    with c2:
        # 右侧扫码卡片
        st.markdown('<div class="css-card" style="border: 2px solid #4CAF50;">', unsafe_allow_html=True)
        st.markdown("### 📱 扫码加入房间")
        
        # 动态生成指向 Player 的二维码
        # 注意：这里需要你部署后的真实链接，本地测试时如果是 localhost 手机扫不了
        # 我们可以用 st.context 获取，或者假设部署在 Streamlit Cloud
        # 这里的链接逻辑是：当前URL + /?role=player
        try:
             # 这是一个 hack，获取当前页面 URL
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            # 实际上 Streamlit Cloud 部署后，直接让用户复制浏览器地址栏即可
            # 为了演示，我们先生成一个通用提示
            join_url = "请把浏览器地址栏的链接发给手机\n并在后面加上 /?role=player"
        except:
            pass
            
        st.image("https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=Play", caption="请扫码或复制链接")
        st.info("手机端请访问本网页链接并选择【我是选手】")
        st.markdown('</div>', unsafe_allow_html=True)

    # 自动刷新机制 (轮询玩家加入状态)
    if server.status == "LOBBY":
        time.sleep(2)
        st.rerun()

    # 如果状态变了，跳转到游戏界面 (这里简化，实际需要写游戏进行中界面)
    if server.status == "PLAYING":
        st.markdown(f"## 当前题目：{server.topic}")
        st.write("等待大家作画...")
        # ... 后续的主机游戏逻辑 ...

# --- 界面 C: 选手角色选择 (复刻图3 & 图6bdb8c) ---
def render_player_view():
    
    # 检查 Session
    if 'uid' not in st.session_state:
        st.session_state.uid = str(uuid.uuid4())
    
    # 阶段 1: 选择身份
    if 'player_info' not in st.session_state:
        st.markdown("<div style='text-align: center;'><h2>请选择你的身份加入房间</h2></div>", unsafe_allow_html=True)
        
        # 2x2 网格布局
        col1, col2 = st.columns(2)
        
        # 定义角色数据
        roles = [
            ("爸爸", "dad", "🧔‍♂️", "#E3F2FD"),
            ("妈妈", "mom", "👩", "#FCE4EC"),
            ("鹅 (女儿)", "goose", "👧", "#F3E5F5"),
            ("猴 (儿子)", "monkey", "👦", "#FFF9C4")
        ]
        
        # 渲染按钮
        for i, (name, role_id, avatar, color) in enumerate(roles):
            # 奇偶列分配
            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                # 使用 Streamlit 原生按钮，配合 CSS 容器
                st.markdown(f"""
                <div style="background-color: {color}; padding: 15px; border-radius: 15px; margin-bottom: 15px; text-align: center;">
                    <div style="font-size: 3em;">{avatar}</div>
                    <div style="font-weight: bold; color: #555;">{name}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"我是 {name}", key=role_id, use_container_width=True):
                    st.session_state.player_info = {'name': name, 'role': role_id, 'avatar': avatar}
                    # 向服务器注册
                    server.join_player(st.session_state.uid, name, role_id, avatar)
                    st.rerun()
                    
    # 阶段 2: 等待/作画
    else:
        p_info = st.session_state.player_info
        
        # 顶部用户信息条
        st.markdown(f"""
        <div style="background: white; padding: 10px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; align-items: center; margin-bottom: 20px;">
            <span style="font-size: 2em; margin-right: 10px;">{p_info['avatar']}</span>
            <div>
                <div style="font-weight: bold;">{p_info['name']}</div>
                <div style="font-size: 0.8em; color: #888;">PLAYER IDENTITY</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if server.status == "LOBBY":
            # 对应图6be38b (已经成功占位)
            st.markdown(f"""
            <div class="css-card">
                <div style="font-size: 4em;">🖌️</div>
                <h3>已经成功占位！</h3>
                <p style="color:#666">请盯着主机大屏幕...</p>
                <p style="color:#aaa">等待挑战题目刷新在你的手机上</p>
                <div style="font-size: 2em; color: #4A90E2;">● ● ●</div>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(2)
            st.rerun()
            
        elif server.status == "PLAYING":
            st.markdown(f"### 题目：**{server.topic}**")
            # 画板
            canvas = st_canvas(
                fill_color="rgba(255, 165, 0, 0.3)",
                stroke_width=3,
                stroke_color="#000",
                background_color="#fff",
                height=300,
                width=300,
                drawing_mode="freedraw",
                key="main_canvas",
            )
            
            if st.button("📤 提交作品", type="primary", use_container_width=True):
                if canvas.image_data is not None:
                    server.submit_work(st.session_state.uid, canvas.image_data)
                    st.success("提交成功！请看大屏幕")
                    
if __name__ == "__main__":
    main()