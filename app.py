import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf

# 1. 介面標題
st.title("🛡️ 交易決策助手")

# 2. 抓取試算表支撐位
conn = st.connection("gsheets", type=GSheetsConnection)
try:
    df_sheets = conn.read(ttl="1m")
    # 讀取第 45 列 (Index 44), 第二欄 (Index 1)
    # 使用 .values[0] 確保只取單一數值
    support_price = float(df_sheets.iloc[44, 1])
except:
    support_price = 0.0

# 3. 輸入代號
target = st.text_input("輸入股票代號 (例: 2330.TW)", value="2330.TW")

if target:
    # 抓取 1 年數據 (確保有足夠的 60MA 計算天數)
    df = yf.download(target, period="1y")
    
    if not df.empty:
        # 抓取最新收盤價並強制轉為浮點數
        curr_price = float(df['Close'].iloc[-1])
        
        # 計算 60MA (季線)
        ma60_series = df['Close'].rolling(window=60).mean()
        ma60 = float(ma60_series.iloc[-1])
        
        # 安全計算乖離率
        if ma60 != 0:
            bias = ((curr_price - ma60) / ma60) * 100
        else:
            bias = 0.0

        # --- 顯示區 ---
        st.subheader("📊 關鍵數據")
        c1, c2, c3 = st.columns(3)
        c1.metric("當前股價", f"{curr_price:.2f}")
        c2.metric("雲端支撐", f"{support_price:.2f}")
        # 這裡單純顯示數字，避免格式化錯誤
        c3.metric("60日乖離", f"{bias:.1f}%")

        st.divider()

        # 判定邏輯
        st.subheader("💡 交易判斷")
        if curr_price <= support_price:
            st.error(f"🚨 觸發：目前股價 {curr_price:.2f} 已跌破支撐位 {support_price:.2f}")
        elif bias <= -10:
            st.warning(f"⚠️ 警告：負乖離達 {bias:.1f}%，進入超跌觀察區")
        else:
            st.success("✅ 目前安全：股價在支撐位上方")

        # 簡單圖表
        st.line_chart(df['Close'].tail(60))
    else:
        st.error("讀取失敗，請確認代號格式。")
