import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import pandas as pd

# 1. 抓取試算表支撐位
conn = st.connection("gsheets", type=GSheetsConnection)
try:
    df_sheets = conn.read(ttl="1m")
    sheet_support = float(df_sheets.iloc[44, 1])
except:
    sheet_support = 0.0

st.title("🎯 左側交易買點決策")

target = st.text_input("輸入股票代號", value="2330.TW")

if target:
    df = yf.download(target, period="1y")
    if not df.empty:
        # 處理 yfinance 標籤
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        close = df['Close']
        curr_price = float(close.iloc[-1])
        
        # --- 手動計算指標 (不依賴外部 package，保證不報錯) ---
        # 1. 季線 (60MA)
        ma60 = close.rolling(window=60).mean().iloc[-1]
        bias_10_price = ma60 * 0.9 
        
        # 2. 布林下軌 (20MA - 2倍標準差)
        ma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        lower_bb = float((ma20 - 2 * std20).iloc[-1])
        
        # 3. 建議買點 (綜合參考值)
        suggested_buy = (sheet_support + bias_10_price + lower_bb) / 3

        # --- 顯示區 ---
        st.subheader("📍 買點精算清單")
        st.write(f"1. **你的腳本支撐價：** `{sheet_support:.2f}`")
        st.write(f"2. **季線負10%價位：** `{bias_10_price:.2f}`")
        st.write(f"3. **布林下軌價位：** `{lower_bb:.2f}`")
        
        st.divider()
        st.success(f"### 💡 建議第一批進場位：{suggested_buy:.2f} 以下")
        
        if curr_price > suggested_buy:
            diff = ((curr_price - suggested_buy) / suggested_buy) * 100
            st.info(f"🚩 目前股價 {curr_price:.2f}，距離買點還差 **{diff:.1f}%**")
        else:
            st.error(f"🔥 目前股價 {curr_price:.2f} 已低於建議買點！")

        # 圖表
        df['My_Support'] = sheet_support
        df['Target_Buy'] = suggested_buy
        st.line_chart(df[['Close', 'My_Support', 'Target_Buy']].tail(60))
