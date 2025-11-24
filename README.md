# 🤖 VN30 AI Quant Bot & Dashboard

Chào mừng bạn đến với **VN30 AI Quant Bot** - bộ công cụ "lai" (Hybrid) kết hợp giữa Phân tích kỹ thuật (Technical Analysis) chặt chẽ và Trí tuệ nhân tạo (Deep Learning/LSTM) để săn tìm cơ hội trên thị trường chứng khoán Việt Nam (nhóm VN30).

Dự án này bao gồm:
1.  **Trading Bot Core**: Tự động quét, phân tích và gửi cảnh báo qua Telegram.
2.  **Interactive Dashboard**: Giao diện web trực quan để soi chart và chạy AI dự báo theo yêu cầu.

---

## 🚀 Tính năng nổi bật

-   **Smart Funnel**: Không train AI bừa bãi! Bot chỉ kích hoạt AI khi thỏa mãn các tiêu chí kỹ thuật (EMA, MACD, RSI, Bollinger Bands) -> Tiết kiệm tài nguyên.
-   **Deep Learning (PyTorch)**: Sử dụng mạng LSTM (Long Short-Term Memory) để học dữ liệu giá 5 năm và dự báo giá đóng cửa ngày tiếp theo.
-   **Data Real-time**: Lấy dữ liệu chứng khoán Việt Nam mới nhất qua thư viện `vnstock`.
-   **Telegram Alert**: Gửi tín hiệu Mua/Bán kèm chart và dự báo AI trực tiếp về điện thoại.
-   **Web Dashboard**: Xem toàn cảnh thị trường và "vọc" AI ngay trên trình duyệt.

---

## 🛠 Cài đặt

Yêu cầu: Python 3.9+ (Khuyên dùng Python 3.10 - 3.13)

1.  **Clone dự án về máy:**
    ```bash
    git clone https://github.com/your-repo/vn30-quant-bot.git
    cd vn30-quant-bot
    ```

2.  **Cài đặt thư viện:**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🎮 Hướng dẫn sử dụng

### 1. Chạy Dashboard (Giao diện Web) - **Khuyên dùng**
Đây là cách trực quan nhất để tương tác với bot.

```bash
streamlit run dashboard.py
```
Sau đó mở trình duyệt tại địa chỉ: `http://localhost:8501`

-   **Tab "🚀 Market Scanner"**: Bấm nút **"Scan All Stocks"** để quét nhanh 30 mã. Mã nào có tín hiệu Mua (Xanh) / Bán (Đỏ) sẽ hiện rõ.
-   **Tab "🧠 Stock Deep Dive"**:
    -   Chọn mã cổ phiếu (ví dụ: `HPG`, `FPT`).
    -   Xem biểu đồ nến, chỉ báo RSI, Bollinger Bands.
    -   Bấm **"🔮 Run AI Prediction"**: Bot sẽ train model ngay lập tức và vẽ đường dự báo giá ngày mai cho bạn.

### 2. Chạy Bot Tự Động (Gửi về Telegram)
Dành cho việc treo máy chạy ngầm hàng ngày.

**Bước 1: Cấu hình Telegram**
Mở file `vn30_quant_bot.py` hoặc set biến môi trường:
```bash
export TELEGRAM_TOKEN="YOUR_BOT_TOKEN"
export CHAT_ID="YOUR_CHAT_ID"
```

**Bước 2: Chạy bot**
```bash
python vn30_quant_bot.py
```
Bot sẽ quét lần lượt 30 mã. Nếu gặp tín hiệu Mua/Bán, nó sẽ train AI và gửi tin nhắn về Telegram cho bạn.

---

## 🧠 Chiến thuật hoạt động (Logic)

### Bước 1: Bộ lọc kỹ thuật (Fast Filter)
Bot sẽ **BỎ QUA** nếu không thỏa mãn các điều kiện an toàn:
-   **MUA khi**: Giá > EMA200 (Trend tăng) + MACD cắt lên + Volume đột biến + RSI chưa quá mua (<70).
-   **BÁN khi**: Gãy trend (Giá < EMA50) hoặc Quá mua (RSI > 75).

### Bước 2: AI "Phán" (Deep Dive)
Chỉ khi Bước 1 thông qua, AI (LSTM) mới vào cuộc:
-   Học dữ liệu 5 năm quá khứ.
-   Dự đoán giá chính xác của phiên ngày mai.
-   Giúp bạn có thêm cơ sở để confirm tín hiệu.

---

## ⚠️ Lưu ý
-   Dự án này sử dụng **PyTorch** thay vì TensorFlow để tối ưu hóa và ổn định hơn trên các máy Mac (M1/M2/M3) và Python mới.
-   Đây là công cụ hỗ trợ ra quyết định, **không phải lời khuyên đầu tư tài chính**. Tiền là của bạn, hãy cân nhắc kỹ! 💸

---
*Code dạo với ❤️ và ☕️.*

