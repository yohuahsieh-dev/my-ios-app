import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf

# 1. 介面標題
st.title("🛡️ 交易決策助手")

# 2. 抓取試算表支撐位
conn = st.connection("gsheets", type=GSheetsConnection)
try:
    df_sheets = conn.read(ttl="1m")
    # 確保抓取的是 B45 格子
    support_price = float(df_sheets.iloc[44, 1])
except:
    support_price = 0.0

# 3. 輸入代號與數據抓取
target = st.text_input("輸入股票代號 (例: 2330.TW)", value="2330.TW")

if target:
    df = yf.download(target, period="1y")
    if not df.empty:
        curr_price = float(df['Close'].iloc[-1])
        # 計算 60MA (季線)
        ma60 = df['Close'].rolling(window=60).mean().iloc[-1]
        # 計算乖離率
        bias = ((curr_price - ma60) / ma60) * 100

        # --- 以下是確保會顯示出來的內容 ---
        
        # 顯示主要數據
        st.subheader("📊 關鍵數據")
        col1, col2, col3 = st.columns(3)
        col1.metric("當前股價", f"{curr_price:.2f}")
        col2.metric("雲端支撐", f"{support_price:.2f}")
        col3.metric("60日乖離", f"{bias:.2f}%")

        st.divider() # 畫一條分隔線

        # 顯示判定燈號
        st.subheader("💡 交易判斷")
        if curr_price <= support_price:
            st.error(f"🚨 警報：目前股價 {curr_price:.2f} 已跌破或觸及支撐位！")
        elif bias <= -10:
            st.warning(f"⚠️ 警告：負乖離率達 {bias:.2f}%，已進入超跌觀察區。")
        else:
            st.success("✅ 狀態：目前股價尚在安全區間。")

        # 顯示簡單走勢圖
        st.line_chart(df['Close'].tail(100))
    else:
        st.error("找不到該代號的股價資料，請確認輸入格式。")
