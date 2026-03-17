import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf

# 1. 基礎設定
st.set_page_config(page_title="左側交易助手")

# 2. 連接 Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
try:
    df_sheets = conn.read(ttl="1m")
    # 讀取第 45 列 (Index 44), 第二欄 (Index 1)
    support_price = float(df_sheets.iloc[44, 1])
except:
    support_price = 0.0

st.title("🛡️ 左側交易監測")

# 3. 輸入代號
target = st.text_input("輸入代號 (例: 2330.TW)", value="2330.TW")

if target:
    # 抓取近半年數據計算乖離率
    df = yf.download(target, period="6mo")
    
    if not df.empty:
        curr_price = float(df['Close'].iloc[-1])
        # 計算 60MA
        ma60 = df['Close'].rolling(window=60).mean().iloc[-1]
        bias = ((curr_price - ma60) / ma60) * 100

        # 4. 顯示數據 (修正了導致 TypeError 的地方)
        col1, col2 = st.columns(2)
        col1.metric("當前股價", f"{curr_price:.2f}")
        col2.metric("腳本支撐位", f"{support_price:.2f}")
        
        # 乖離率單獨顯示，delta 設為 None 避免報錯
        st.metric(label="60日乖離率", value=f"{bias:.2f}%")

        # 5. 判定邏輯
        if curr_price <= support_price:
            st.error(f"🚨 觸發：股價已低於支撐位 ({support_price})")
        elif bias <= -10:
            st.warning("⚠️ 警告：負乖離過大，進入觀察區")
        else:
            st.success("✅ 目前股價尚在支撐上方")

        # 簡單圖表
        st.line_chart(df['Close'].tail(100))
    else:
        st.write("讀取不到股價資料，請檢查代號是否正確。")
