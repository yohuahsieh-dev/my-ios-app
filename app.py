import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.set_page_config(page_title="左側買點決策", layout="centered")

# 1. 抓取試算表支撐位
conn = st.connection("gsheets", type=GSheetsConnection)
try:
    df_sheets = conn.read(ttl="1m")
    # 讀取你的 B45 格子
    sheet_support = float(df_sheets.iloc[44, 1])
except:
    sheet_support = 0.0

st.title("🎯 左側交易買點決策")

target = st.text_input("輸入股票代號", value="2330.TW")

if target:
    df = yf.download(target, period="1y")
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        curr_price = float(df['Close'].iloc[-1])
        
        # --- 計算關鍵買點參考價 ---
        # 1. 季線 (60MA) 負 10% 價格 (歷史常見的超跌買點)
        ma60 = df['Close'].rolling(window=60).mean().iloc[-1]
        bias_10_price = ma60 * 0.9 
        
        # 2. 布林下軌價格 (極端波動邊界)
        bbands = ta.bbands(df['Close'], length=20, std=2)
        lower_bb = bbands.iloc[-1, 0] # BBL_20_2.0
        
        # 3. 綜合參考買點 (取這三個價格的平均或最保守值)
        # 我們取你試算表價格與市場超跌價的平均，作為「第一批進場參考」
        suggested_buy = (sheet_support + bias_10_price + lower_bb) / 3

        # --- 決策顯示區 ---
        st.subheader("📍 買點精算清單")
        
        # 用清單方式直接告訴你價位
        st.write(f"1. **你的腳本支撐價：** `{sheet_support:.2f}`")
        st.write(f"2. **季線負10%價位：** `{bias_10_price:.2f}` (目前季線：{ma60:.2f})")
        st.write(f"3. **布林下軌價位：** `{lower_bb:.2f}`")
        
        st.divider()
        
        # 核心結論
        st.success(f"### 💡 建議第一批進場位：{suggested_buy:.2f} 以下")
        
        diff = ((curr_price - suggested_buy) / suggested_buy) * 100
        if curr_price > suggested_buy:
            st.info(f"🚩 目前股價 {curr_price:.2f} 距離建議買點還有約 **{diff:.1f}%** 的回落空間。")
        else:
            st.error(f"🔥 目前股價 {curr_price:.2f} 已進入買進區間！")

        # --- 視覺化參考 ---
        st.subheader("📉 價格與買點對照圖")
        df['My_Support'] = sheet_support
        df['Target_Buy'] = suggested_buy
        plot_data = df[['Close', 'My_Support', 'Target_Buy']].tail(60)
        st.line_chart(plot_data)

    else:
        st.error("查無資料")
