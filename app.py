import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import pandas as pd

# 1. 抓取試算表支撐位
conn = st.connection("gsheets", type=GSheetsConnection)
try:
    df_sheets = conn.read(ttl="1m")
    # 讀取第 45 列 (Index 44), 第二欄 (Index 1)
    sheet_support = float(df_sheets.iloc[44, 1])
except:
    sheet_support = 0.0

st.title("🎯 左側交易買點決策")

target = st.text_input("輸入股票代號 (例: 2330.TW)", value="2330.TW")

if target:
    # 抓取數據 (使用 1y 確保 60MA 計算準確)
    df = yf.download(target, period="1y")
    
    if not df.empty:
        # 處理 yfinance 標籤格式
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        close = df['Close']
        curr_price = float(close.iloc[-1])
        
        # --- 手動計算指標 (不依賴第三方外掛) ---
        # 1. 季線 (60MA)
        ma60_val = close.rolling(window=60).mean().iloc[-1]
        bias_10_price = ma60_val * 0.9  # 季線負10%價位
        
        # 2. 布林下軌 (20MA - 2倍標準差)
        ma20_series = close.rolling(window=20).mean()
        std20_series = close.rolling(window=20).std()
        lower_bb = float((ma20_series - 2 * std20_series).iloc[-1])
        
        # 3. 建議買點 (綜合參考值：腳本支撐、負乖離、布林下軌三者平均)
        suggested_buy = (sheet_support + bias_10_price + lower_bb) / 3

        # --- 顯示區 ---
        st.subheader("📍 買點精算清單")
        col1, col2 = st.columns(2)
        col1.write(f"你的腳本支撐：**{sheet_support:.2f}**")
        col1.write(f"季線負10%價：**{bias_10_price:.2f}**")
        col2.write(f"布林下軌價：**{lower_bb:.2f}**")
        col2.write(f"目前 60MA：**{ma60_val:.2f}**")
        
        st.divider()
        
        # 核心判定
        st.success(f"### 💡 建議第一批進場位：{suggested_buy:.2f} 以下")
        
        if curr_price > suggested_buy:
            diff = ((curr_price - suggested_buy) / suggested_buy) * 100
            st.info(f"🚩 目前股價 {curr_price:.2f}，距離買點還差 **{diff:.1f}%**")
        else:
            st.error(f"🔥 目前股價 {curr_price:.2f} 已低於建議買點！")

        # 圖表視覺化
        df['腳本支撐'] = sheet_support
        df['建議買點'] = suggested_buy
        st.line_chart(df[['Close', '腳本支撐', '建議買點']].tail(60))

    else:
        st.error("查無資料，請確認代號格式。")
