import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import os
import time

# Import core logic from the bot
# Ensure vn30_quant_bot.py is in the same directory
from vn30_quant_bot import get_data, analyze_signal, AI_Forecaster, VN30_LIST, AI_LOOKBACK
from openai import OpenAI
import feedparser
from textblob import TextBlob

# === Streamlit Cloud Secrets Support ===
# Check if running on Streamlit Cloud (has st.secrets) or locally (use os.environ)
def get_secret(key, default=""):
    """Get secret from Streamlit Cloud or environment variable"""
    try:
        return st.secrets.get(key, default)
    except (FileNotFoundError, KeyError):
        return os.environ.get(key, default)

st.set_page_config(
    page_title="VN30 Quant Bot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed" # Collapsed for more space
)

# --- Helper Functions ---
@st.cache_data(ttl=3600) # Cache data for 1 hour to avoid spamming vnstock
def fetch_stock_data(symbol, days_back=None):
    return get_data(symbol, days=days_back)

def plot_candle_chart(df, symbol):
    # Create figure with secondary y-axis
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, subplot_titles=(f'Biểu đồ giá {symbol}', 'Chỉ báo RSI'),
                        row_heights=[0.7, 0.3])

    # Candlestick
    fig.add_trace(go.Candlestick(x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Giá'), row=1, col=1)

    # EMA 50
    if 'EMA_50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='orange', width=1), name='EMA 50 (Trung hạn)'), row=1, col=1)
    
    # EMA 200
    if 'EMA_200' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='blue', width=1), name='EMA 200 (Dài hạn)'), row=1, col=1)

    # Bollinger Bands
    bbu = [c for c in df.columns if c.startswith('BBU_')][0] if any(c.startswith('BBU_') for c in df.columns) else None
    bbl = [c for c in df.columns if c.startswith('BBL_')][0] if any(c.startswith('BBL_') for c in df.columns) else None
    
    if bbu and bbl:
        fig.add_trace(go.Scatter(x=df.index, y=df[bbu], line=dict(color='gray', width=0.5, dash='dot'), name='Dải trên BB'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df[bbl], line=dict(color='gray', width=0.5, dash='dot'), fill='tonexty', name='Dải dưới BB'), row=1, col=1)

    # RSI
    if 'RSI_14' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI_14'], line=dict(color='purple', width=2), name='RSI'), row=2, col=1)
        fig.add_shape(type="line", x0=df.index[0], y0=70, x1=df.index[-1], y1=70, line=dict(color="red", width=1, dash="dash"), row=2, col=1)
        fig.add_shape(type="line", x0=df.index[0], y0=30, x1=df.index[-1], y1=30, line=dict(color="green", width=1, dash="dash"), row=2, col=1)

    fig.update_layout(height=800, title_text=f"Phân tích kỹ thuật {symbol}", xaxis_rangeslider_visible=False)
    return fig

def plot_prediction_chart(df, symbol, predicted_price, lookback):
    last_90 = df.tail(90).copy()
    last_date = last_90.index[-1]
    next_date = last_date + datetime.timedelta(days=1)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=last_90.index, y=last_90['close'], mode='lines', name='Giá Thực Tế', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=[next_date], y=[predicted_price], mode='markers', name='AI Dự Báo', 
                             marker=dict(color='red', size=12, symbol='star')))
    fig.add_trace(go.Scatter(x=[last_date, next_date], y=[last_90['close'].iloc[-1], predicted_price], 
                             mode='lines', name='Đường Dự Báo', line=dict(color='red', dash='dot')))
    fig.update_layout(title=f"Dự báo AI cho {symbol}", xaxis_title="Ngày", yaxis_title="Giá")
    return fig

# --- Feature: News Analysis ---
@st.cache_data(ttl=1800)
def fetch_news(symbol):
    # Using Google News RSS as a generic source (Replace with specific VN source if available)
    # Query: symbol + " stock vietnam"
    rss_url = f"https://news.google.com/rss/search?q={symbol}+stock+vietnam&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(rss_url)
    
    news_items = []
    for entry in feed.entries[:5]:
        try:
            sentiment = TextBlob(entry.title).sentiment.polarity
            sentiment_label = "Trung tính ⚪"
            if sentiment > 0.1: sentiment_label = "Tích cực 🟢"
            if sentiment < -0.1: sentiment_label = "Tiêu cực 🔴"
            
            news_items.append({
                "Title": entry.title,
                "Link": entry.link,
                "Published": entry.published,
                "Sentiment": sentiment_label
            })
        except Exception:
            continue
            
    return news_items

# --- Feature: OpenAI Analysis ---
def ask_openai(symbol, df, indicators):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    prompt = f"""
    Phân tích kỹ thuật cho cổ phiếu {symbol} dựa trên dữ liệu sau:
    - Giá hiện tại: {df['close'].iloc[-1]}
    - RSI: {indicators['rsi']}
    - MACD: {indicators['macd']}
    - Xu hướng: Giá nằm {'trên' if df['close'].iloc[-1] > df['EMA_200'].iloc[-1] else 'dưới'} EMA200.
    
    Hãy đưa ra nhận định ngắn gọn (dưới 100 từ) về xu hướng sắp tới và lời khuyên cho nhà đầu tư.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": '''Bạn là một chuyên gia Phân tích Kỹ thuật Định lượng (Quantitative Technical Analyst) theo trường phái "Trend Following" an toàn.
    Nhiệm vụ: Đánh giá dữ liệu cổ phiếu và đưa ra nhận định khách quan, ngắn gọn, súc tích.
    Quy tắc phân tích:
    1. Xu hướng dài hạn (EMA200) là quan trọng nhất. Không khuyến nghị MUA nếu giá dưới EMA200.
    2. MACD > Signal là động lượng tích cực.
    3. RSI > 70 là vùng quá mua (cẩn trọng), RSI < 30 là vùng quá bán (cơ hội).
    Định dạng câu trả lời (bắt buộc dưới 100 từ):
    - 🚦 TÍN HIỆU: [MUA / BÁN / QUAN SÁT]
    - 💡 Lý do chính: [1 câu tóm tắt]
    - ⚠️ Cảnh báo rủi ro: [Nếu có]'''},
                {"role": "user", "content": prompt}
            ],
			temperature=0.3, # Giảm sáng tạo để nhận định chính xác, logic hơn
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Lỗi OpenAI: {str(e)}"

# --- Feature: Backtest Logic ---
def run_backtest(df, initial_capital=100000000):
    """
    Simple Backtest for Trend Following Strategy
    Rule: Buy if Close > EMA200 + MACD Bullish. Sell if Close < EMA50.
    """
    capital = initial_capital
    position = 0 # 0: Cash, >0: Shares
    df = df.copy()
    
    # Ensure indicators exist
    if 'EMA_200' not in df.columns:
        df.ta.ema(length=200, append=True)
    if 'EMA_50' not in df.columns:
        df.ta.ema(length=50, append=True)
    if 'MACD_12_26_9' not in df.columns:
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        
    trades = []
    equity_curve = []
    
    for i in range(200, len(df)):
        date = df.index[i]
        close = df['close'].iloc[i]
        ema200 = df['EMA_200'].iloc[i]
        ema50 = df['EMA_50'].iloc[i]
        macd = df['MACD_12_26_9'].iloc[i]
        signal = df['MACDs_12_26_9'].iloc[i]
        
        # Buy Condition
        if position == 0:
            if close > ema200 and macd > signal:
                position = capital / close
                capital = 0
                trades.append({'Date': date, 'Type': 'BUY', 'Price': close})
        
        # Sell Condition
        elif position > 0:
            if close < ema50:
                capital = position * close
                position = 0
                trades.append({'Date': date, 'Type': 'SELL', 'Price': close})
                
        # Track Equity
        current_equity = capital + (position * close)
        equity_curve.append({'Date': date, 'Equity': current_equity})
        
    return pd.DataFrame(trades), pd.DataFrame(equity_curve).set_index('Date')

# --- CSS Styles ---
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
        margin-bottom: 10px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
</style>
""", unsafe_allow_html=True)

# --- Main Layout ---
st.title("📈 Trung Tâm Giao Dịch Thông Minh VN30")

# --- Top Bar Settings ---
with st.expander("⚙️ Cấu Hình & Cài Đặt", expanded=False):
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    
    with col_s1:
        st.subheader("📅 Khung Thời Gian Dữ Liệu")
        timeframe_option = st.selectbox(
            "Chọn Khoảng Thời Gian Phân Tích",
            options=["1 Năm", "3 Năm", "5 Năm (Mặc định)", "Tùy Chỉnh"],
            index=2
        )
        
        days_back = 5 * 365 # Default
        
        if timeframe_option == "1 Năm":
            days_back = 365
        elif timeframe_option == "3 Năm":
            days_back = 3 * 365
        elif timeframe_option == "5 Năm (Mặc định)":
            days_back = 5 * 365
        elif timeframe_option == "Tùy Chỉnh":
            days_back = st.number_input("Nhập số ngày lùi lại:", min_value=90, max_value=5000, value=365)

    with col_s2:
        st.subheader("🧠 Cài Đặt AI")
        ai_lookback = st.slider("Độ Dài Chuỗi AI (Ngày)", 30, 120, AI_LOOKBACK, help="Số lượng ngày quá khứ mà AI sử dụng để dự đoán ngày tiếp theo.")

    with col_s3:
        st.subheader("💬 Cấu Hình Telegram")
        telegram_token = st.text_input("Telegram Bot Token", type="password", help="Token từ BotFather")
        chat_id = st.text_input("Telegram Chat ID", help="ID chat của bạn")
        
        # Pre-fill from secrets if available
        if not telegram_token:
            telegram_token = get_secret("TELEGRAM_TOKEN")
        if not chat_id:
            chat_id = get_secret("CHAT_ID")
            
        if telegram_token and chat_id:
            os.environ["TELEGRAM_TOKEN"] = telegram_token
            os.environ["CHAT_ID"] = chat_id
            if telegram_token != "YOUR_TELEGRAM_BOT_TOKEN":
                st.success("✅ Đã lưu Telegram!")
    
    with col_s4:
        st.subheader("🤖 OpenAI API")
        openai_key = st.text_input("OpenAI API Key", type="password", help="Key từ platform.openai.com", 
                                    value=get_secret("OPENAI_API_KEY") if get_secret("OPENAI_API_KEY") else "")
        
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
            if openai_key.startswith("sk-"):
                st.success("✅ Đã lưu OpenAI!")

st.markdown("---")

# --- Market Overview (Full Width Table) ---
st.subheader("📋 Nhịp Đập Thị Trường VN30")
st.caption("Bảng tổng hợp tín hiệu kỹ thuật thời gian thực của 30 cổ phiếu lớn nhất Việt Nam.")

if st.button("🔄 Quét Toàn Bộ VN30", type="primary", help="Bấm để quét tín hiệu mới nhất cho tất cả cổ phiếu"):
    with st.spinner(f"Đang quét thị trường ({timeframe_option})..."):
        scan_results = []
        progress_bar = st.progress(0)
        
        for i, symbol in enumerate(VN30_LIST):
            df = fetch_stock_data(symbol, days_back=days_back)
            if df is not None:
                rec = analyze_signal(df)
                last_row = df.iloc[-1]
                
                # Get specific columns
                macd_val = last_row.get('MACD_12_26_9', 0)
                sig_val = last_row.get('MACDs_12_26_9', 0)
                rsi_val = last_row.get('RSI_14', 0)
                
                reasons_summary = ", ".join(rec["reasons"]) if isinstance(rec["reasons"], list) else str(rec["reasons"])

                scan_results.append({
                    "Mã CP": symbol,
                    "Tín Hiệu": rec["action"],
                    "Giá": f"{last_row['close']:,.0f}",
                    "RSI": f"{rsi_val:.1f}",
                    "Xu Hướng MACD": "Tăng" if macd_val > sig_val else "Giảm",
                    "Lý Do": reasons_summary
                })
            progress_bar.progress((i + 1) / len(VN30_LIST))
        
        st.session_state.scan_results = pd.DataFrame(scan_results)

# Display Table if data exists
if 'scan_results' in st.session_state and not st.session_state.scan_results.empty:
    df_scan = st.session_state.scan_results
    
    def highlight_signal(val):
        color = ''
        if val == 'BUY': color = '#09F409FF' # Dark Green
        if val == 'SELL': color = '#EA1E1EFF' # Dark Red
        return f'background-color: {color}'

    st.dataframe(
        df_scan.style.map(highlight_signal, subset=['Tín Hiệu']),
        use_container_width=True,
        height=400,
        column_config={
            "Lý Do": st.column_config.TextColumn("Tóm Tắt Phân Tích", width="large"),
            "Mã CP": st.column_config.TextColumn("Cổ Phiếu"),
        }
    )

st.markdown("---")

col_left, col_right = st.columns([1, 2], gap="medium")

# Initialize session state for selected symbol
if 'selected_symbol' not in st.session_state:
    st.session_state.selected_symbol = VN30_LIST[0]

# --- Left Column: Stock Selection & Stats ---
with col_left:
    st.subheader("🔍 Chọn Cổ Phiếu")
    
    # Selection Dropdown (Primary Navigation)
    selected = st.selectbox("Chọn mã để phân tích chi tiết:", VN30_LIST, key="symbol_select")
    st.session_state.selected_symbol = selected
    symbol = selected
    
    # Show Quick Stats for Selected Stock
    df = fetch_stock_data(symbol, days_back=days_back)
    
    if df is not None:
        rec = analyze_signal(df)
        
        # Signal Card
        sig_color = "gray"
        vn_action = "CHỜ"
        if rec["action"] == "BUY": 
            sig_color = "green"
            vn_action = "MUA"
        if rec["action"] == "SELL": 
            sig_color = "red"
            vn_action = "BÁN"
        
        st.markdown(f"""
        <div style="background-color: {sig_color}; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 10px;">
            <h2 style="margin:0; color: white;">{vn_action}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📋 Kế Hoạch Giao Dịch")
        if rec["action"] == "BUY":
            c1, c2 = st.columns(2)
            c1.metric("Giá Vào Lệnh", f"{rec['entry_price']:,.0f}")
            c2.metric("Cắt Lỗ (Stop Loss)", f"{rec['stop_loss']:,.0f}", help="Mức giá nên bán để bảo toàn vốn (2 ATR)")
            st.metric("Chốt Lời (Take Profit)", f"{rec['take_profit']:,.0f}", help="Mức giá mục tiêu để chốt lời (3 ATR)")
            st.caption(f"Tỷ lệ Rủi ro/Lợi nhuận: 1:1.5")
        
        elif rec["action"] == "SELL":
            st.metric("Giá Khuyến Nghị Bán", f"{rec['entry_price']:,.0f}")
            st.warning("⚠️ Khuyến nghị: Nên đóng các vị thế nắm giữ.")
            
        else:
            st.info("Chưa có tín hiệu rõ ràng. Hãy kiên nhẫn chờ đợi.")
            
        st.markdown("### 📝 Phân Tích Chi Tiết")
        for r in rec["reasons"]:
            st.write(f"• {r}")

# --- Right Column: Deep Dive & AI ---
with col_right:
    st.subheader(f"📊 Phân Tích Toàn Diện: {symbol}")
    
    if df is not None:
        # --- Section 1: Technical Chart ---
        st.markdown("### 📈 Biểu Đồ Kỹ Thuật")
        st.plotly_chart(plot_candle_chart(df, symbol), use_container_width=True)
        st.markdown("---")
            
        # --- Section 2: AI Forecast (Auto Run) ---
        st.markdown("### 🔮 Dự Báo AI (Deep Learning)")
        
        # Check cache or session state to avoid re-running AI unnecessarily if symbol hasn't changed
        # But user requested "Auto fetch all info", so we run it.
        # We can use a simple check:
        ai_key = f"ai_pred_{symbol}_{days_back}"
        
        if ai_key not in st.session_state:
             with st.spinner("🤖 AI đang học và dự báo..."):
                try:
                    forecaster = AI_Forecaster(symbol, df, lookback=ai_lookback)
                    x_train, y_train = forecaster.prepare_data()
                    forecaster.build_and_train(x_train, y_train)
                    pred_price = forecaster.predict_next_day()
                    st.session_state[ai_key] = pred_price
                except Exception as e:
                    st.error(f"Lỗi AI: {e}")
                    st.session_state[ai_key] = None

        pred_price = st.session_state.get(ai_key)
        
        if pred_price:
            current_price = df['close'].iloc[-1]
            change = ((pred_price - current_price) / current_price) * 100
            
            st.metric("Giá AI Dự Báo (Ngày Mai)", f"{pred_price:,.0f}", f"{change:.2f}%", help="Giá đóng cửa dự kiến của phiên giao dịch tiếp theo.")
            st.plotly_chart(plot_prediction_chart(df, symbol, pred_price, ai_lookback), use_container_width=True)
            
        st.markdown("---")
            
        # --- Section 3: Backtest (Auto Run) ---
        st.markdown("### 🔙 Kiểm Thử Chiến Thuật (Trend Following)")
        # Auto run backtest
        trades, equity = run_backtest(df)
        
        if not trades.empty:
            initial_cap = 100000000
            final_cap = equity['Equity'].iloc[-1]
            profit = final_cap - initial_cap
            roi = (profit / initial_cap) * 100
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Lợi Nhuận Ròng", f"{profit:,.0f} VND")
            m2.metric("ROI (Tỷ suất sinh lời)", f"{roi:.2f}%")
            m3.metric("Tổng Số Lệnh", len(trades))
            
            st.line_chart(equity['Equity'])
            
            with st.expander("📋 Danh Sách Chi Tiết Các Lệnh"):
                st.dataframe(trades, use_container_width=True)
        else:
            st.info("Không có lệnh nào được thực hiện trong khoảng thời gian này.")
        
        st.markdown("---")
                    
        # --- Section 4: News & OpenAI (Auto Fetch News) ---
        st.markdown("### 📰 Tin Tức & Góc Nhìn Chuyên Gia")
        col_news, col_ai_chat = st.columns(2, gap="large")
        
        with col_news:
            st.markdown("#### 🗞️ Tin Tức Liên Quan")
            news = fetch_news(symbol)
            if news:
                for item in news:
                    st.markdown(f"**[{item['Title']}]({item['Link']})**")
                    st.caption(f"{item['Published']} | {item['Sentiment']}")
                    st.markdown("---")
            else:
                st.info("Không tìm thấy tin tức mới.")
            
        with col_ai_chat:
            st.markdown("#### 🤖 Góc Nhìn Chuyên Gia OpenAI")
            # OpenAI key is now in top expander or env var
            if os.environ.get("OPENAI_API_KEY"):
                # Auto-run AI analysis
                openai_cache_key = f"openai_{symbol}_{days_back}"
                
                if openai_cache_key not in st.session_state:
                    last_row = df.iloc[-1]
                    indicators = {
                        'rsi': f"{last_row.get('RSI_14', 0):.2f}",
                        'macd': f"{last_row.get('MACD_12_26_9', 0):.2f}"
                    }
                    with st.spinner("🤖 Chuyên gia AI đang phân tích..."):
                        analysis = ask_openai(symbol, df, indicators)
                        st.session_state[openai_cache_key] = analysis
                
                st.info(st.session_state.get(openai_cache_key, "Đang tải..."))
            else:
                st.warning("⚠️ Nhập OpenAI API Key ở phần **Cấu Hình** để kích hoạt.")



