import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import ta

# 1. iOS 介面優化設定
st.set_page_config(page_title="左側交易助手", layout="centered")

# 2. 連接 Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
try:
    # 讀取試算表數據
    df_sheets = conn.read(ttl="5m")
    # 抓取第 45 列，第 2 欄的數據 (Index 為 44, 1)
    support_price = float(df_sheets.iloc[44, 1])
except:
    support_price = 0.0

# 3. App 標題與輸入
st.title("🛡️ 左側交易 iOS 版")

target = st.text_input("輸入股票代號 (例: 2330.TW 或 TSLA)", value="2330.TW")

if target:
    # 下載股價數據
    df = yf.download(target, period="1y")
    curr_price = float(df['Close'].iloc[-1])
    
    # 計算 60MA 與 乖離率
    ma60 = df['Close'].rolling(window=60).mean().iloc[-1]
    bias = ((curr_price - ma60) / ma60) * 100

    # 顯示數據卡片 (iOS 適合閱讀的大尺寸)
    c1, c2 = st.columns(2)
    c1.metric("當前股價", f"{curr_price:.2f}")
    c2.metric("腳本支撐位", f"{support_price:.2f}")
    
    # 顯示乖離率，紅色代表負乖離（超跌）
    st.metric("60日乖離率", f"{bias:.2f}%", delta=f"{bias:.2f}%", delta_color="inverse")

    st.markdown("---")
    
    # 4. 判定邏輯
    if curr_price <= support_price:
        st.error(f"🚨 觸發：股價已低於或觸及腳本支撐位 ({support_price})")
    elif bias <= -10:
        st.warning(f"⚠️ 警告：負乖離率過大，進入左側觀察區")
    else:
        st.success("✅ 目前走勢尚穩，未達左側交易標準")

    # 5. 繪製 K 線走勢圖
    st.line_chart(df['Close'].tail(100))
