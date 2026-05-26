import re
import random
import requests
import streamlit as st
from bs4 import BeautifulSoup
from opencc import OpenCC
from pyvis.network import Network
import streamlit.components.v1 as components

# =====================================================================
# 1. 初始化設定 (必須是第一個 Streamlit 指令)
# =====================================================================
st.set_page_config(page_title="星域神話與守護神圖鑑", page_icon="🌌", layout="wide")

# 初始化簡轉繁轉換器
cc = OpenCC('s2twp')

# 注入自訂 CSS，打造極具質感的「古典神殿」浪漫暗黑 UI
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0B0E14;
        color: #E2E8F0;
    }
    /* 星座核心卡片 */
    .zodiac-card {
        background: linear-gradient(135deg, #1A1F2C, #11151F);
        border: 2px solid #D97706; /* 奢華古銅金 */
        border-radius: 16px;
        padding: 25px;
        box-shadow: 0 8px 32px rgba(217, 119, 6, 0.15);
        margin-bottom: 25px;
    }
    /* 故事內文卡片 */
    .story-card {
        background: rgba(22, 27, 38, 0.8);
        border-left: 4px solid #38BDF8;
        border-radius: 4px;
        padding: 20px;
        line-height: 1.8;
        font-size: 1.1em;
        white-space: pre-wrap;
    }
    .game-title {
        font-family: 'Georgia', serif;
        color: #F59E0B;
        text-shadow: 0 0 15px rgba(245, 158, 11, 0.6);
        text-align: center;
        margin-bottom: 5px;
    }
    .god-title {
        color: #F43F5E;
        font-weight: bold;
        font-size: 1.3em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# 2. 浪漫神話核心資料庫 (守護星、守護神、古典圖片網址)
# =====================================================================
ZODIAC_ROMANCE_DB = {
    "雙子座": {
        "guardian_god": "赫密斯 (Hermes)",
        "guardian_star": "水星 (Mercury)",
        "god_desc": "雄辯與旅人的守護神，精明且充滿智慧，賦予雙子座靈動的思考與無拘無束的靈魂。",
        "image_url": "https://images.unsplash.com/photo-1605721911519-3dfeb3be25e7?q=80&w=400&auto=format&fit=crop", # 藝術感雕像風格
        "core_nodes": ["宙斯", "波魯克斯", "卡斯托爾", "赫密斯"]
    },
    "金牛座": {
        "guardian_god": "阿芙蘿黛蒂 (Aphrodite)",
        "guardian_star": "金星 (Venus)",
        "god_desc": "愛與美的女神，賦予金牛座對世間美好事物的敏銳感知、優雅的品味與執著的愛。",
        "image_url": "https://images.unsplash.com/photo-1580136579312-94651dfd596d?q=80&w=400&auto=format&fit=crop", # 維納斯女神雕像風格
        "core_nodes": ["宙斯", "歐羅巴", "白牛", "阿芙蘿黛蒂"]
    },
    "獅子座": {
        "guardian_god": "阿波羅 (Apollo)",
        "guardian_star": "太陽 (Sun)",
        "god_desc": "光明與藝術之神，賦予獅子座如烈陽般耀眼的自信、王者風範與源源不絕的創造力。",
        "image_url": "https://images.unsplash.com/photo-1578301978693-85fa9c0320b9?q=80&w=400&auto=format&fit=crop", # 太陽神風格畫作
        "core_nodes": ["海克力士", "涅梅亞猛獅", "阿波羅", "宙斯"]
    },
    "白羊座": {
        "guardian_god": "阿瑞斯 (Ares)",
        "guardian_star": "火星 (Mars)",
        "god_desc": "戰神，賦予白羊座無所畏懼的勇氣、衝勁與開拓者的戰鬥精神。",
        "image_url": "https://images.unsplash.com/photo-1599733589046-10c005739ef9?q=80&w=400&auto=format&fit=crop",
        "core_nodes": ["阿瑞斯", "金羊", "菲里克索斯", "宙斯"]
    }
}

ALL_ZODIAC_SIGNS = ["白羊座", "金牛座", "雙子座", "獅子座"] # 可自行擴充其他星座

# =====================================================================
# 3. 智慧爬蟲與關係圖引擎
# =====================================================================
def crawl_zodiac_myth(zodiac_name_zh):
    url = f"https://zh.wikipedia.org/wiki/{zodiac_name_zh}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            paragraphs = soup.find_all("p")
            myth_text = ""
            keywords = ["神話", "宙斯", "傳說", "由來", "起源", "化身", "英雄", "希臘", "星座"]

            for p in paragraphs:
                text = p.get_text().strip()
                if any(keyword in text for keyword in keywords):
                    myth_text += text + "\n\n"

            if myth_text:
                return cc.convert(myth_text)
            else:
                return "在維基百科找到了頁面，但未篩選到包含希臘神話起源的相關章節。"
        else:
            return f"無法讀取維基百科頁面 (錯誤碼: {response.status_code})"
    except Exception as e:
        return f"連線發生錯誤: {str(e)}"

def generate_relation_graph(text, center_node, db_gods):
    """結合爬蟲文本與核心守護神資料庫，繪製漂浮網"""
    # 合併爬蟲發現的神明與資料庫設定的核心角色
    all_potential_nodes = list(set(db_gods + ["宙斯", "赫拉", "波塞頓", "哈迪斯", "阿波羅", "雅典娜"]))
    found_nodes = [node for node in all_potential_nodes if node in text or node == center_node]

    net = Network(height="400px", width="100%", bgcolor="#11151F", font_color="#E2E8F0")

    # 建立核心星座節點 (金色大星星)
    net.add_node(center_node, label=center_node, color="#F59E0B", size=35, shape="star")

    for node in found_nodes:
        if node != center_node:
            # 如果是守護神，特別放大並改成粉色/紅色球體
            if "⚡" in node or "守護" in node:
                net.add_node(node, label=node, color="#EC4899", size=28, shape="dot")
            else:
                net.add_node(node, label=node, color="#38BDF8", size=20, shape="dot")
            net.add_edge(center_node, node, color="#475569", width=2)

    # 段落共現連線 (建立人物之間的交織關係)
    for i in range(len(found_nodes)):
        for j in range(i + 1, len(found_nodes)):
            node_a, node_b = found_nodes[i], found_nodes[j]
            if any(node_a in p and node_b in p for p in text.split('\n\n')):
                net.add_edge(node_a, node_b, color="#F43F5E", width=1, dashes=True)

    net.toggle_physics(True)
    return net.generate_html()

# =====================================================================
# 4. 主網頁介面
# =====================================================================
def main():
    st.markdown("<h1 class='game-title'>🌌 星域神話：守護神圖鑑 v3.0</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>融合維基百科史詩與古典浪漫美學的諸神關係網</p>", unsafe_allow_html=True)
    st.write("---")

    # 頂部控制列
    ctrl_col1, ctrl_col2 = st.columns([3, 1])
    with ctrl_col1:
        user_input = st.selectbox("🔮 請選擇你想探索的星域：", ALL_ZODIAC_SIGNS)

    with ctrl_col2:
        st.write("🎲 讓命運做決定？")
        if st.button("✨ 啟動命運之輪", use_container_width=True):
            user_input = random.choice(ALL_ZODIAC_SIGNS)
            st.toast(f"🌌 命運指引你前往：{user_input}！")

    if user_input:
        target_zodiac = user_input

        # 讀取守護神浪漫資料庫
        zodiac_info = ZODIAC_ROMANCE_DB.get(target_zodiac, {
            "guardian_god": "未知", "guardian_star": "未知", "god_desc": "文獻整理中...",
            "image_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23", "core_nodes": []
        })

        # 執行爬蟲抓故事
        with st.spinner(f"正在詠唱星空咒語，召喚 【{target_zodiac}】 的歷史文獻..."):
            result_text = crawl_zodiac_myth(target_zodiac)

        # =====================================================================
        # 🌟 重點：浪漫視覺排版（大卡片與圖片呈現）
        # =====================================================================
        # 第一層：守護神美感圖鑑卡片
        st.markdown(f"""
        <div class="zodiac-card">
            <div style="display: flex; flex-wrap: wrap; align-items: center;">
                <div style="flex: 1; min-width: 250px; padding-right: 20px;">
                    <h2 style="color: #F59E0B; margin-top: 0;">✨ {target_zodiac} 🌌 星域主宰</h2>
                    <p style="font-size: 1.1em;"><b>🏛️ 守護神祇：</b> <span class="god-title">{zodiac_info['guardian_god']}</span></p>
                    <p style="font-size: 1.1em;"><b>🪐 💡 守護星體：</b> <span style="color: #10B981; font-weight: bold;">{zodiac_info['guardian_star']}</span></p>
                    <p style="color: #94A3B8; font-style: italic; line-height: 1.6; margin-top: 15px;">「 {zodiac_info['god_desc']} 」</p>
                </div>
                <div style="flex: 0 0 200px; text-align: center;">
                    <img src="{zodiac_info['image_url']}" style="border-radius: 12px; max-width: 100%; height: 220px; object-fit: cover; border: 2px solid #D97706; box-shadow: 0 0 15px rgba(217,119,6,0.3);"/>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 第二層：二分版面（左故事，右關係圖）
        display_col1, display_col2 = st.columns([4, 3])

        with display_col1:
            st.markdown(f"### 📜 維基百科·編年史紀錄")
            st.markdown(f'<div class="story-card">{result_text}</div>', unsafe_allow_html=True)

        with display_col2:
            st.markdown("### 🔗 諸神交織關係網")
            st.caption("💡 提示：點擊星星為核心星座，拖拽藍球探索神明之間的愛恨糾葛連線。")

            # 將守護神也加入圖表節點
            display_nodes = zodiac_info["core_nodes"] + [zodiac_info["guardian_god"].split(" ")[0]]
            # 產生結合文本分析與手動設定的 Pyvis 漂浮圖
            graph_html = generate_relation_graph(result_text, target_zodiac, display_nodes)
            components.html(graph_html, height=420)

if __name__ == "__main__":
    main()
