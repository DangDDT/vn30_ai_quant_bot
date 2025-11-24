# 🤖 Hướng Dẫn Chạy Bot Scheduler Tự Động

## 📋 Tổng Quan

`scheduler_bot.py` là bot tự động gửi báo cáo phân tích VN30 qua Telegram vào:

- **🌅 8:45 sáng**: Trước khi mở cửa phiên giao dịch (9:00)
- **🌆 15:15 chiều**: Sau khi đóng cửa phiên giao dịch (15:00)

Báo cáo bao gồm:

- ✅ Tín hiệu kỹ thuật (MUA/BÁN/CHỜ) cho tất cả 30 cổ phiếu VN30
- 📊 Giá vào lệnh, Stop Loss, Take Profit
- 🤖 **Phân tích chuyên sâu từ OpenAI GPT-4** (nếu có API key)
- 📈 Tổng kết thị trường

---

## ⚙️ Bước 1: Cài Đặt Dependencies

Đảm bảo bạn đã cài đủ thư viện:

```bash
pip install -r requirements.txt
```

---

## 🔑 Bước 2: Cấu Hình API Keys

### 2.1. Telegram Bot (Bắt buộc)

1. Tạo bot qua [@BotFather](https://t.me/BotFather) trên Telegram
2. Lấy `Bot Token` (dạng: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
3. Lấy `Chat ID` của bạn bằng cách:
   - Nhắn tin cho bot [@userinfobot](https://t.me/userinfobot)
   - Copy số `Id` (dạng: `123456789`)

### 2.2. OpenAI API (Tùy chọn - để có phân tích AI chuyên sâu)

1. Đăng ký tài khoản tại [platform.openai.com](https://platform.openai.com)
2. Tạo API Key tại [API Keys](https://platform.openai.com/api-keys)
3. Copy key (dạng: `sk-proj-...`)

---

## 🚀 Bước 3: Chạy Bot

### Cách 1: Set Environment Variables (Khuyến nghị)

**MacOS/Linux:**

```bash
export TELEGRAM_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
export CHAT_ID="123456789"
export OPENAI_API_KEY="sk-proj-xxxxx"  # (Tùy chọn)

python3 scheduler_bot.py
```

**Windows (PowerShell):**

```powershell
$env:TELEGRAM_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
$env:CHAT_ID="123456789"
$env:OPENAI_API_KEY="sk-proj-xxxxx"  # (Tùy chọn)

python scheduler_bot.py
```

### Cách 2: Sửa trực tiếp file `vn30_quant_bot.py`

Mở file `vn30_quant_bot.py` và thay đổi:

```python
TELEGRAM_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"  # Thay token của bạn
CHAT_ID = "123456789"  # Thay chat ID của bạn
```

Sau đó chạy:

```bash
python3 scheduler_bot.py
```

---

## 🔄 Bước 4: Chạy Bot Liên Tục (Background)

### MacOS/Linux - Dùng `nohup`:

```bash
nohup python3 scheduler_bot.py > scheduler.log 2>&1 &
```

Để dừng bot:

```bash
# Tìm process ID
ps aux | grep scheduler_bot

# Kill process (thay PID bằng số thực tế)
kill -9 <PID>
```

### MacOS - Dùng `launchd` (Khởi động cùng máy):

1. Tạo file `~/Library/LaunchAgents/com.vn30bot.scheduler.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vn30bot.scheduler</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/YOUR_USERNAME/Desktop/eykh/vn30_ai_quant_bot/scheduler_bot.py</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>TELEGRAM_TOKEN</key>
        <string>YOUR_TOKEN_HERE</string>
        <key>CHAT_ID</key>
        <string>YOUR_CHAT_ID_HERE</string>
        <key>OPENAI_API_KEY</key>
        <string>YOUR_OPENAI_KEY_HERE</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/Desktop/eykh/vn30_ai_quant_bot/scheduler.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/Desktop/eykh/vn30_ai_quant_bot/scheduler_error.log</string>
</dict>
</plist>
```

2. Load service:

```bash
launchctl load ~/Library/LaunchAgents/com.vn30bot.scheduler.plist
```

3. Kiểm tra trạng thái:

```bash
launchctl list | grep vn30bot
```

4. Dừng service:

```bash
launchctl unload ~/Library/LaunchAgents/com.vn30bot.scheduler.plist
```

### Windows - Dùng Task Scheduler:

1. Mở `Task Scheduler`
2. Tạo `Basic Task`:
   - Name: `VN30 Quant Bot`
   - Trigger: `When the computer starts`
   - Action: `Start a program`
   - Program: `C:\Python39\python.exe`
   - Arguments: `C:\path\to\scheduler_bot.py`
   - Environment Variables: Thêm vào Properties → Actions → Edit → Add arguments

---

## 📊 Bước 5: Kiểm Tra Logs

Bot tạo 2 file log:

- `scheduler_activity.log`: Log hoạt động của scheduler
- `bot_activity.log`: Log của các hàm phân tích từ `vn30_quant_bot.py`

Xem log real-time:

```bash
tail -f scheduler_activity.log
```

---

## 🧪 Test Ngay Lập Tức (Không Đợi Lịch)

Nếu bạn muốn test ngay mà không chờ đến 8:45 hoặc 15:15, mở Python và chạy:

```python
from scheduler_bot import morning_report, afternoon_report

# Test báo cáo sáng
morning_report()

# Hoặc test báo cáo chiều
afternoon_report()
```

---

## 💡 Tips & Lưu Ý

1. **OpenAI API Key không bắt buộc**: Bot vẫn chạy được mà không có OpenAI, nhưng sẽ không có phần phân tích chuyên sâu từ AI.

2. **Chi phí OpenAI**: Mỗi lần quét 30 cổ phiếu với GPT-4o (~$0.01-0.03/request), tổng ~$0.30-0.90/lần báo cáo. Nếu muốn tiết kiệm, đổi model về `gpt-3.5-turbo` trong file `scheduler_bot.py`.

3. **Telegram Rate Limit**: Telegram giới hạn ~30 message/giây. Bot đã tối ưu để gửi 1 message duy nhất chứa toàn bộ báo cáo.

4. **Dữ liệu vnstock**: Đôi khi vnstock bị chậm hoặc lỗi. Bot có retry logic và sẽ bỏ qua cổ phiếu lỗi.

5. **Múi giờ**: Bot sử dụng giờ hệ thống. Đảm bảo máy của bạn đang ở múi giờ Việt Nam (UTC+7).

---

## 🛑 Dừng Bot

**Cách 1: Ctrl+C** (nếu chạy foreground)

**Cách 2: Kill process** (nếu chạy background)

```bash
ps aux | grep scheduler_bot
kill -9 <PID>
```

**Cách 3: Unload launchd** (nếu dùng launchd trên Mac)

```bash
launchctl unload ~/Library/LaunchAgents/com.vn30bot.scheduler.plist
```

---

## 🆘 Troubleshooting

### Lỗi "Telegram Token invalid"

- Kiểm tra lại token từ BotFather
- Đảm bảo không có khoảng trắng thừa

### Lỗi "OpenAI API Key"

- Kiểm tra key còn hoạt động
- Kiểm tra credit còn đủ tại [platform.openai.com/usage](https://platform.openai.com/usage)

### Bot không gửi tin nhắn

- Kiểm tra `CHAT_ID` có đúng không
- Đảm bảo đã `/start` bot trên Telegram
- Xem log: `tail -f scheduler_activity.log`

### Lỗi "vnstock data fetch failed"

- Thử chạy lại sau vài phút
- Kiểm tra kết nối internet
- vnstock đôi khi bảo trì

---

## 📞 Liên Hệ

Nếu gặp vấn đề, kiểm tra:

1. Log files: `scheduler_activity.log`
2. Python version: `python3 --version` (nên >= 3.9)
3. Dependencies: `pip list | grep schedule`

---

**Chúc bạn giao dịch thành công! 🚀📈**
