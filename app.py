import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import pandas as pd

# 1. 頁面設定
st.set_page_config(page_title="左側交易實戰版", layout="centered")
st.title("🛡️ 左側交易實戰監控")

# 2. 抓取試算表支撐位
conn = st.connection("gsheets", type=GSheetsConnection)
try:
    df_sheets = conn.read(ttl="1m")
    # 讀取 B45 格子
    support_price = float(df_sheets.iloc[44, 1])
except:
    support_price = 0.0

# 3. 輸入代號
target = st.text_input("輸入股票代號 (例: 2330.TW)", value="2330.TW")

if target:
    # 抓取 2 年數據
    df = yf.download(target, period="2y")
    
    if not df.empty:
        # --- 重要：處理 yfinance 新版的標籤問題 ---
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # 確保價格是數字格式
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        curr_price = float(df['Close'].iloc[-1])
        
        # 計算均線
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        ma20 = float(df['MA20'].iloc[-1])
        ma60 = float(df['MA60'].iloc[-1])
        
        # 計算乖離率
        bias_20 = ((curr_price - ma20) / ma20) * 100
        bias_60 = ((curr_price - ma60) / ma60) * 100

        # --- 數據儀表板 ---
        st.subheader("📊 關鍵指標")
        c1, c2, c3 = st.columns(3)
        c1.metric("當前股價", f"{curr_price:.2f}")
        c2.metric("20MA (月線)", f"{ma20:.2f}", f"{bias_20:.1f}%", delta_color="inverse")
        c3.metric("60MA (季線)", f"{ma60:.2f}", f"{bias_60:.1f}%", delta_color="inverse")

        st.info(f"🎯 **雲端支撐價：{support_price:.2f}**")
        
        # --- 交易判斷 ---
        st.subheader("💡 交易判斷")
        if curr_price <= support_price and bias_60 <= -7:
            st.error(f"🔥 強烈訊號：股價已破支撐 ({support_price}) 且季線負乖離達 {bias_60:.1f}%，符合進場標準！")
        elif curr_price <= support_price:
            st.warning(f"⚠️ 警報：股價破支撐，但負乖離尚不足，建議分批觀察。")
        else:
            st.success("✅ 狀態：股價尚在支撐上方。")

        # --- 歷史走勢與乖離率圖表 ---
        st.subheader("📈 價格與均線 (近120日)")
        # 準備繪圖數據，只取最後 120 筆
        plot_df = df[['Close', 'MA20', 'MA60']].tail(120)
        st.line_chart(plot_df)
        
        st.subheader("📉 60日乖離率分佈 (尋找超跌低點)")
        all_bias_60 = ((df['Close'] - df['MA60']) / df['MA60']) * 100
        # 畫出乖離率走勢，幫助判斷目前是否處於歷史低位
        st.area_chart(all_bias_60.tail(250))
        st.caption("※ 當曲線降至低谷時，通常是極佳的左側布局時機。")

    else:
        st.error("查無資料，請確認代號格式是否正確。")
