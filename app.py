import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import pandas as pd

# 1. 介面標題
st.title("🛡️ 左側交易實戰監控")

# 2. 抓取試算表支撐位
conn = st.connection("gsheets", type=GSheetsConnection)
try:
    df_sheets = conn.read(ttl="1m")
    # 讀取 B45 格子 (Index 44, 1)
    support_price = float(df_sheets.iloc[44, 1])
except:
    support_price = 0.0

# 3. 輸入代號
target = st.text_input("輸入股票代號", value="2330.TW")

if target:
    # 抓取 2 年數據 (為了計算長期乖離分佈)
    df = yf.download(target, period="2y")
    
    if not df.empty:
        curr_price = float(df['Close'].iloc[-1])
        
        # 計算 20MA 與 60MA
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

        st.write(f"🎯 **雲端支撐價：{support_price:.2f}**")
        
        # --- 實戰判定 ---
        st.subheader("💡 交易判斷")
        # 判斷邏輯：股價低於支撐 且 負乖離夠大
        if curr_price <= support_price and bias_60 <= -7:
            st.error(f"🔥 強烈訊號：股價已破支撐 ({support_price}) 且季線負乖離達 {bias_60:.1f}%，符合左側進場條件！")
        elif curr_price <= support_price:
            st.warning(f"⚠️ 警報：股價破支撐，但負乖離尚不足，建議分批觀察。")
        else:
            st.success("✅ 狀態：股價尚在支撐上方，耐心等待回檔。")

        # --- 歷史走勢圖 (含均線) ---
        st.subheader("📈 走勢與均線對照")
        plot_df = df[['Close', 'MA20', 'MA60']].tail(120)
        st.line_chart(plot_df)
        
        # --- 乖離率歷史分佈 (判斷現在夠不夠低) ---
        st.subheader("📉 歷史乖離分佈 (近兩年)")
        all_bias_60 = ((df['Close'] - df['MA60']) / df['MA60']) * 100
        st.area_chart(all_bias_60.tail(250))
        st.caption("當曲線處於低點時，代表進入歷史超跌區。")

    else:
        st.error("讀取失敗，請確認代號。")
