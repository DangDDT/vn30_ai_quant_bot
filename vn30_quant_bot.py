import os
import time
import logging
import datetime
import requests
import numpy as np
import pandas as pd
import pandas_ta as ta
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Streamlit
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler

# Try importing torch, but don't fail if not available
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("⚠️ PyTorch not available. AI features will be disabled.")

from vnstock import Vnstock

# --- Configuration & Constants ---
VN30_LIST = [
    'ACB', 'BCM', 'BID', 'BVH', 'CTG', 'FPT', 'GAS', 'GVR', 'HDB', 'HPG',
    'MBB', 'MSN', 'MWG', 'PLX', 'POW', 'SAB', 'SHB', 'SSB', 'SSI', 'STB',
    'TCB', 'TPB', 'VCB', 'VHM', 'VIB', 'VIC', 'VJC', 'VNM', 'VPB', 'VRE'
]

# Placeholder credentials - User should replace these via env vars or direct edit
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")

# AI Settings
AI_LOOKBACK = 60
AI_TRAIN_YEARS = 5

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_activity.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- 1. Data Acquisition ---
def get_data(symbol, days=None, retry=3, delay=1.5):
    """
    Fetch OHLCV data for a symbol from vnstock with retry & rate limiting.
    Args:
        symbol: Stock symbol
        days: Number of days back to fetch. If None, uses default AI_TRAIN_YEARS * 365
        retry: Number of retry attempts
        delay: Initial delay between retries (exponential backoff)
    Returns a clean DataFrame or None if failed.
    """
    for attempt in range(retry):
        try:
            # Add delay to avoid rate limiting
            if attempt > 0:
                wait_time = delay * (2 ** (attempt - 1))  # 1.5s, 3s, 6s
                logger.info(f"⏳ Retry {attempt + 1}/{retry} for {symbol} after {wait_time:.1f}s...")
                time.sleep(wait_time)
            
            end_date = datetime.datetime.now().strftime('%Y-%m-%d')
            
            if days:
                 start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
            else:
                 start_date = (datetime.datetime.now() - datetime.timedelta(days=AI_TRAIN_YEARS * 365)).strftime('%Y-%m-%d')
            
            # Fetch data using Vnstock class (v3.x)
            stock = Vnstock().stock(symbol=symbol, source='VCI')
            df = stock.quote.history(start=start_date, end=end_date, interval='1D')
            
            if df is None or df.empty:
                logger.warning(f"⚠️ No data for {symbol} (attempt {attempt + 1}/{retry})")
                if attempt < retry - 1:
                    continue
                return None

            # Standardize columns
            df.columns = [c.lower() for c in df.columns]
            
            # Ensure 'time' is index
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'])
                df.set_index('time', inplace=True)
            elif 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)

            # Sort by date
            df.sort_index(inplace=True)

            # Ensure numeric types for OHLCV
            cols = ['open', 'high', 'low', 'close', 'volume']
            for col in cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                else:
                    logger.error(f"❌ Missing column {col} for {symbol}")
                    return None
                    
            df.dropna(inplace=True)
            logger.info(f"✅ Fetched {len(df)} rows for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error for {symbol} (attempt {attempt + 1}/{retry}): {e}")
            if attempt == retry - 1:
                logger.error(f"⚠️ Failed {symbol} after {retry} attempts")
                return None
    
    return None

# --- 2. Technical Analysis (The Filter) ---
def analyze_signal(df):
    """
    Apply Technical Analysis rules.
    Returns: 'BUY', 'SELL', or 'WAIT'
    Adds indicators to the dataframe in place.
    """
    # Calculate Indicators using pandas_ta
    # Trend
    df.ta.ema(length=50, append=True)
    df.ta.ema(length=200, append=True)
    
    # Momentum
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    
    # Volatility
    df.ta.bbands(length=20, std=2, append=True)
    
    # Strength
    df.ta.rsi(length=14, append=True)
    
    # ATR for Stop Loss/Take Profit Calculation
    df.ta.atr(length=14, append=True)
    
    # Volume
    # SMA of volume. 'volume' column is expected.
    # Custom calculation or pandas_ta
    df['VOL_SMA_20'] = df['volume'].rolling(window=20).mean()
    
    # Get the latest row (current day)
    current = df.iloc[-1]
    
    # Extract values for readability
    close = current['close']
    ema50 = current['EMA_50']
    ema200 = current['EMA_200']
    macd = current['MACD_12_26_9']
    macd_signal = current['MACDs_12_26_9']
    rsi = current['RSI_14']
    # pandas_ta 0.4.x beta might produce double suffix for std
    upper_band = current.get('BBU_20_2.0', current.get('BBU_20_2.0_2.0'))
    vol = current['volume']
    vol_sma = current['VOL_SMA_20']
    atr = current['ATRr_14']

    # --- Logic ---
    
    recommendation = {
        "action": "WAIT",
        "entry_price": 0,
        "stop_loss": 0,
        "take_profit": 0,
        "reasons": []
    }
    
    reasons = []
    
    # BUY Logic Breakdown
    cond_trend = close > ema200
    cond_macd = macd > macd_signal
    cond_vol = vol > vol_sma
    cond_rsi_buy = rsi < 70
    cond_bb = close < upper_band
    
    is_buy = cond_trend and cond_macd and cond_vol and cond_rsi_buy and cond_bb
    
    if is_buy:
        reasons = [
            "✅ Xu hướng dài hạn Tăng (Giá > EMA200)",
            "✅ Lực mua mạnh (MACD cắt lên Signal)",
            "✅ Dòng tiền vào (Volume > TB 20 phiên)",
            "✅ An toàn (RSI < 70 & Giá dưới dải trên BB)"
        ]
        recommendation.update({
            "action": "BUY",
            "entry_price": close,
            "stop_loss": close - (atr * 2), # SL at 2 ATR
            "take_profit": close + (atr * 3), # TP at 3 ATR (Risk:Reward 1:1.5)
            "reasons": reasons
        })
        return recommendation
        
    # SELL Logic Breakdown
    cond_trend_broken = close < ema50
    cond_overheated = rsi > 75
    
    is_sell = cond_trend_broken or cond_overheated
    
    if is_sell:
        if cond_trend_broken:
            reasons.append("❌ Gãy xu hướng ngắn hạn (Giá < EMA50)")
        if cond_overheated:
            reasons.append("🔥 Quá mua - Rủi ro đảo chiều (RSI > 75)")
            
        recommendation.update({
            "action": "SELL",
            "entry_price": close,
            "reasons": reasons
        })
        return recommendation
        
    # WAIT Logic Breakdown
    reasons.append("⏸️ Chưa đủ điều kiện Mua:")
    if not cond_trend: reasons.append("- Giá dưới EMA200 (Downtrend)")
    if not cond_macd: reasons.append("- MACD chưa cắt lên (Momentum yếu)")
    if not cond_vol: reasons.append("- Volume thấp (Dưới TB 20 phiên)")
    if not cond_rsi_buy: reasons.append("- RSI quá cao (>70)")
    if not cond_bb: reasons.append("- Giá chạm dải trên BB (Kháng cự)")
    
    recommendation["reasons"] = reasons
    return recommendation

# --- 3. AI Module (Deep Dive) ---
if TORCH_AVAILABLE:
    class LSTMModel(nn.Module):
        def __init__(self, input_size, hidden_size, num_layers, output_size, dropout=0.2):
            super(LSTMModel, self).__init__()
            self.hidden_size = hidden_size
            self.num_layers = num_layers
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
            self.fc = nn.Linear(hidden_size, output_size)
        
        def forward(self, x):
            # Initialize hidden and cell states
            h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
            c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
            
            # Forward propagate LSTM
            out, _ = self.lstm(x, (h0, c0))
            
            # Decode the hidden state of the last time step
            out = self.fc(out[:, -1, :])
            return out

if TORCH_AVAILABLE:
    class AI_Forecaster:
        def __init__(self, symbol, df, lookback=60):
            self.symbol = symbol
            self.df = df
            self.lookback = lookback
            self.scaler = MinMaxScaler(feature_range=(0, 1))
            self.model = None
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
        def prepare_data(self):
            data = self.df.filter(['close']).values
            scaled_data = self.scaler.fit_transform(data)
            
            x_train = []
            y_train = []
            
            if len(scaled_data) <= self.lookback:
                raise ValueError("Not enough data for AI training")
                
            for i in range(self.lookback, len(scaled_data)):
                x_train.append(scaled_data[i-self.lookback:i, 0])
                y_train.append(scaled_data[i, 0])
                
            x_train, y_train = np.array(x_train), np.array(y_train)
            x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
            
            return x_train, y_train
            
        def build_and_train(self, x_train, y_train):
            x_train_tensor = torch.from_numpy(x_train).float().to(self.device)
            y_train_tensor = torch.from_numpy(y_train).float().to(self.device)
            
            input_size = 1
            hidden_size = 50
            num_layers = 2
            output_size = 1
            num_epochs = 20
            learning_rate = 0.001
            
            self.model = LSTMModel(input_size, hidden_size, num_layers, output_size).to(self.device)
            
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
            
            self.model.train()
            for epoch in range(num_epochs):
                outputs = self.model(x_train_tensor)
                optimizer.zero_grad()
                loss = criterion(outputs, y_train_tensor.view(-1, 1))
                loss.backward()
                optimizer.step()
                
        def predict_next_day(self):
            data = self.df.filter(['close']).values
            last_lookback = data[-self.lookback:]
            scaled_last_lookback = self.scaler.transform(last_lookback)
            
            X_test = scaled_last_lookback.reshape(1, self.lookback, 1)
            X_test_tensor = torch.from_numpy(X_test).float().to(self.device)
            
            self.model.eval()
            with torch.no_grad():
                pred_scaled = self.model(X_test_tensor)
                
            pred_price = self.scaler.inverse_transform(pred_scaled.cpu().numpy())
            
            return float(pred_price[0][0])
            
        def generate_chart(self, predicted_price):
            """Generate comparison chart"""
            plt.style.use('seaborn-v0_8-darkgrid')
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            ax1.plot(self.df.index, self.df['close'], label='Close Price', color='blue')
            ax1.set_title(f"{self.symbol} - 5 Year History")
            ax1.legend()
            
            last_90 = self.df.tail(90).copy()
            last_date = last_90.index[-1]
            next_date = last_date + datetime.timedelta(days=1)
            
            ax2.plot(last_90.index, last_90['close'], label='Actual', color='blue')
            ax2.plot([last_date, next_date], [last_90['close'].iloc[-1], predicted_price], 
                     linestyle='--', marker='o', color='red', label='AI Prediction')
            
            ax2.set_title(f"{self.symbol} - Last 90 Days & AI Forecast")
            ax2.legend()
            
            chart_path = f"temp_chart_{self.symbol}.png"
            plt.tight_layout()
            plt.savefig(chart_path)
            plt.close()
            return chart_path
else:
    # Dummy AI_Forecaster when torch is not available
    class AI_Forecaster:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch is not available. AI features are disabled.")
        
        def prepare_data(self):
            raise ImportError("PyTorch is not available")
        
        def build_and_train(self, *args):
            raise ImportError("PyTorch is not available")
        
        def predict_next_day(self):
            raise ImportError("PyTorch is not available")
        
        def generate_chart(self, *args):
            raise ImportError("PyTorch is not available")

# --- 4. Telegram Reporter ---
def send_alert(symbol, signal, price, ai_price, indicators, image_path, reasons):
    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or CHAT_ID == "YOUR_TELEGRAM_CHAT_ID":
        logger.warning("Telegram credentials not set. Skipping alert.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    
    # Emoji based on signal
    sig_emoji = "🟢" if signal == "BUY" else "🔴"
    
    reasons_text = "\n".join(reasons)
    
    caption = f"""
{sig_emoji} **SIGNAL: {signal} for {symbol}**

💰 Current Price: {price:,.0f}
🔮 AI Prediction (Next Day): {ai_price:,.0f}

📋 **Reason:**
{reasons_text}

📊 Indicators:
- RSI: {indicators['rsi']:.2f}
- MACD: {indicators['macd_status']}

⚠️ Recommendation: Check chart below.
    """
    
    try:
        with open(image_path, 'rb') as img:
            files = {'photo': img}
            data = {'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
            response = requests.post(url, files=files, data=data)
            
        if response.status_code == 200:
            logger.info(f"Alert sent for {symbol}")
        else:
            logger.error(f"Failed to send Telegram alert: {response.text}")
            
    except Exception as e:
        logger.error(f"Error sending telegram: {e}")

# --- 5. Main Execution Loop ---
def main():
    logger.info("Starting VN30 AI Quant Bot...")
    logger.info(f"Scanning {len(VN30_LIST)} stocks.")
    
    for symbol in VN30_LIST:
        try:
            logger.info(f"--- Processing {symbol} ---")
            
            # Step 1: Fast Filter
            df = get_data(symbol)
            if df is None:
                continue
                
            signal, reasons = analyze_signal(df)
            logger.info(f"Signal for {symbol}: {signal}")
            
            if signal == "WAIT":
                logger.info(f"Skipping {symbol} (No Signal)")
                continue
                
            # Step 2: Deep Dive (AI)
            logger.info(f"Signal detected! Initiating AI Analysis for {symbol}...")
            
            forecaster = AI_Forecaster(symbol, df, lookback=AI_LOOKBACK)
            
            try:
                x_train, y_train = forecaster.prepare_data()
                logger.info("Training LSTM model...")
                forecaster.build_and_train(x_train, y_train)
                
                predicted_price = forecaster.predict_next_day()
                logger.info(f"AI Prediction: {predicted_price:.2f}")
                
                chart_path = forecaster.generate_chart(predicted_price)
                
                # Gather indicators for report
                # analyze_signal added columns to df
                last_row = df.iloc[-1]
                macd_val = last_row['MACD_12_26_9']
                sig_val = last_row['MACDs_12_26_9']
                macd_status = "Bullish" if macd_val > sig_val else "Bearish"
                
                indicators = {
                    'rsi': last_row['RSI_14'],
                    'macd_status': macd_status
                }
                
                # Step 3: Alerting
                current_price = last_row['close']
                send_alert(symbol, signal, current_price, predicted_price, indicators, chart_path, reasons)
                
                # Cleanup chart
                if os.path.exists(chart_path):
                    os.remove(chart_path)
                    
            except Exception as e:
                logger.error(f"AI/Alerting failed for {symbol}: {e}")

            # Rate Limiting
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Critical error processing {symbol}: {e}")
            continue

    logger.info("Scan complete.")

if __name__ == "__main__":
    main()

