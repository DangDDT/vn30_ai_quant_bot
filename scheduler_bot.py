#!/usr/bin/env python3
"""
VN30 Quant Bot - Scheduled Auto Reporter
Tự động gửi báo cáo phân tích qua Telegram vào:
- 8:45 sáng (trước phiên giao dịch)
- 15:15 chiều (sau phiên giao dịch)
"""

import os
import time
import logging
import schedule
import datetime
from vn30_quant_bot import (
    get_data, analyze_signal, AI_Forecaster, VN30_LIST, 
    TELEGRAM_TOKEN, CHAT_ID, AI_LOOKBACK
)
import requests
from openai import OpenAI

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [SCHEDULER] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler_activity.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === OpenAI Integration ===
def get_ai_expert_opinion(symbol, df):
    """
    Gọi OpenAI để phân tích chuyên sâu
    """
    if not os.environ.get("OPENAI_API_KEY"):
        return "⚠️ Chưa cấu hình OpenAI API Key"
    
    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        last_row = df.iloc[-1]
        current_price = last_row['close']
        rsi = last_row.get('RSI_14', 0)
        macd = last_row.get('MACD_12_26_9', 0)
        ema200 = last_row.get('EMA_200', 0)
        
        prompt = f"""
        Phân tích kỹ thuật cho cổ phiếu {symbol} dựa trên dữ liệu sau:
        - Giá hiện tại: {current_price:,.0f} VND
        - RSI: {rsi:.2f}
        - MACD: {macd:.2f}
        - Xu hướng: Giá nằm {'trên' if current_price > ema200 else 'dưới'} EMA200 ({ema200:,.0f}).
        
        Hãy đưa ra nhận định ngắn gọn (dưới 100 từ) về xu hướng sắp tới và lời khuyên cho nhà đầu tư.
        """
        
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
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI Error for {symbol}: {e}")
        return f"❌ Lỗi OpenAI: {str(e)}"


# === Telegram Reporter ===
def send_telegram_report(message, parse_mode="Markdown"):
    """
    Gửi message qua Telegram
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": parse_mode
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Đã gửi báo cáo qua Telegram")
        else:
            logger.error(f"❌ Telegram Error: {response.text}")
    except Exception as e:
        logger.error(f"❌ Không thể gửi Telegram: {e}")


def generate_market_report(report_type="morning"):
    """
    Tạo báo cáo tổng hợp cho toàn bộ VN30
    report_type: "morning" hoặc "afternoon"
    """
    now = datetime.datetime.now()
    
    if report_type == "morning":
        header = f"🌅 *BÁO CÁO SÁNG - VN30 QUANT BOT*\n📅 {now.strftime('%d/%m/%Y %H:%M')}\n"
        header += "=" * 35 + "\n"
        header += "📊 *TÍN HIỆU GIAO DỊCH TRƯỚC PHIÊN*\n\n"
    else:
        header = f"🌆 *BÁO CÁO CHIỀU - VN30 QUANT BOT*\n📅 {now.strftime('%d/%m/%Y %H:%M')}\n"
        header += "=" * 35 + "\n"
        header += "📊 *TỔNG KẾT PHIÊN GIAO DỊCH*\n\n"
    
    buy_signals = []
    sell_signals = []
    wait_signals = []
    
    logger.info(f"🔄 Bắt đầu quét {len(VN30_LIST)} cổ phiếu VN30...")
    
    for i, symbol in enumerate(VN30_LIST):
        try:
            logger.info(f"  → [{i+1}/{len(VN30_LIST)}] Đang phân tích {symbol}...")
            
            # Add small delay between stocks to avoid rate limit
            if i > 0:
                time.sleep(0.5)  # 500ms delay between stocks
            
            df = get_data(symbol, days=365)
            
            if df is None or len(df) < 200:
                logger.warning(f"  ⚠️ {symbol}: Không đủ dữ liệu")
                continue
            
            rec = analyze_signal(df)
            last_price = df['close'].iloc[-1]
            
            # Lấy ý kiến AI (nếu có)
            ai_opinion = ""
            if os.environ.get("OPENAI_API_KEY"):
                logger.info(f"  🤖 Đang hỏi OpenAI về {symbol}...")
                ai_opinion = get_ai_expert_opinion(symbol, df)
            
            stock_info = {
                "symbol": symbol,
                "price": last_price,
                "entry": rec.get("entry_price", last_price),
                "sl": rec.get("stop_loss", 0),
                "tp": rec.get("take_profit", 0),
                "reasons": rec.get("reasons", []),
                "ai_opinion": ai_opinion
            }
            
            if rec["action"] == "BUY":
                buy_signals.append(stock_info)
            elif rec["action"] == "SELL":
                sell_signals.append(stock_info)
            else:
                wait_signals.append(stock_info)
                
        except Exception as e:
            logger.error(f"  ❌ Lỗi khi xử lý {symbol}: {e}")
            continue
    
    # === Xây dựng nội dung báo cáo ===
    report = header
    
    # BUY Signals
    if buy_signals:
        report += f"🟢 *TÍN HIỆU MUA ({len(buy_signals)} mã)*\n"
        for stock in buy_signals[:5]:  # Top 5 để tránh quá dài
            report += f"\n📌 *{stock['symbol']}*: {stock['price']:,.0f} VND\n"
            report += f"  • Entry: {stock['entry']:,.0f} | SL: {stock['sl']:,.0f} | TP: {stock['tp']:,.0f}\n"
            
            # Lý do phân tích
            if stock['reasons']:
                report += f"  • Lý do: {stock['reasons'][0][:60]}...\n"
            
            # Ý kiến AI
            if stock['ai_opinion']:
                # Rút gọn AI opinion để không quá dài
                ai_short = stock['ai_opinion'][:150].replace('\n', ' ')
                report += f"  🤖 AI: {ai_short}...\n"
            
            report += "\n"
    
    # SELL Signals
    if sell_signals:
        report += f"\n🔴 *TÍN HIỆU BÁN ({len(sell_signals)} mã)*\n"
        for stock in sell_signals[:3]:
            report += f"📌 *{stock['symbol']}*: {stock['price']:,.0f} VND\n"
            if stock['reasons']:
                report += f"  • {stock['reasons'][0][:80]}\n"
            
            if stock['ai_opinion']:
                ai_short = stock['ai_opinion'][:120].replace('\n', ' ')
                report += f"  🤖 {ai_short}\n"
            report += "\n"
    
    # Summary
    report += "\n" + "=" * 35 + "\n"
    report += f"📊 *TỔNG KẾT*\n"
    report += f"✅ Mua: {len(buy_signals)} | ❌ Bán: {len(sell_signals)} | ⏸️ Chờ: {len(wait_signals)}\n"
    
    if report_type == "morning":
        report += "\n💡 _Chúc bạn một phiên giao dịch thành công!_"
    else:
        report += "\n💡 _Hẹn gặp lại vào phiên giao dịch tiếp theo!_"
    
    return report


# === Scheduled Jobs ===
def morning_report():
    """
    Báo cáo sáng - 8:45 AM
    """
    logger.info("=" * 50)
    logger.info("🌅 BẮT ĐẦU BÁO CÁO SÁNG")
    logger.info("=" * 50)
    
    try:
        report = generate_market_report(report_type="morning")
        send_telegram_report(report)
        logger.info("✅ Hoàn tất báo cáo sáng")
    except Exception as e:
        logger.error(f"❌ Lỗi báo cáo sáng: {e}")
        send_telegram_report(f"⚠️ Lỗi tạo báo cáo sáng:\n{str(e)}")


def afternoon_report():
    """
    Báo cáo chiều - 15:15 PM
    """
    logger.info("=" * 50)
    logger.info("🌆 BẮT ĐẦU BÁO CÁO CHIỀU")
    logger.info("=" * 50)
    
    try:
        report = generate_market_report(report_type="afternoon")
        send_telegram_report(report)
        logger.info("✅ Hoàn tất báo cáo chiều")
    except Exception as e:
        logger.error(f"❌ Lỗi báo cáo chiều: {e}")
        send_telegram_report(f"⚠️ Lỗi tạo báo cáo chiều:\n{str(e)}")


# === Main Scheduler ===
def main():
    """
    Khởi động bot scheduler
    """
    logger.info("=" * 60)
    logger.info("🤖 VN30 QUANT BOT SCHEDULER STARTED")
    logger.info("=" * 60)
    logger.info(f"📅 Lịch gửi báo cáo:")
    logger.info(f"  🌅 Sáng: 08:45 (Trước phiên giao dịch)")
    logger.info(f"  🌆 Chiều: 15:15 (Sau phiên giao dịch)")
    logger.info("=" * 60)
    
    # Kiểm tra config
    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or CHAT_ID == "YOUR_TELEGRAM_CHAT_ID":
        logger.error("❌ Chưa cấu hình Telegram Token/Chat ID!")
        logger.error("Vui lòng set environment variables: TELEGRAM_TOKEN và CHAT_ID")
        return
    
    # Schedule jobs
    schedule.every().day.at("08:45").do(morning_report)
    schedule.every().day.at("15:15").do(afternoon_report)
    
    # Gửi thông báo khởi động
    startup_msg = f"""
🤖 *VN30 QUANT BOT ACTIVATED*
📅 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}

✅ Bot đã được khởi động thành công!

⏰ *Lịch gửi báo cáo tự động:*
🌅 Sáng: 08:45
🌆 Chiều: 15:15

💡 _Bot đang chạy liên tục, bạn có thể tắt terminal này._
"""
    send_telegram_report(startup_msg)
    
    logger.info("✅ Scheduler đã được cấu hình. Bot đang chờ...")
    logger.info("⏳ Nhấn Ctrl+C để dừng bot.\n")
    
    # Run scheduler loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\n⚠️ Nhận tín hiệu dừng từ người dùng...")
        send_telegram_report("⚠️ *Bot đã được tắt bởi người dùng.*")
        logger.info("👋 Bot đã dừng. Goodbye!")


if __name__ == "__main__":
    main()

