# 🚀 Hướng Dẫn Deploy VN30 Quant Bot Lên Streamlit Cloud

## 📋 Tổng Quan

Dashboard của bạn sẽ được host **MIỄN PHÍ** trên Streamlit Cloud với URL riêng như: `https://vn30-quant-bot-yourusername.streamlit.app`

**Ưu điểm:**

- ✅ Miễn phí 100%
- ✅ Tự động update khi push code mới lên GitHub
- ✅ SSL/HTTPS tự động
- ✅ Chạy 24/7
- ✅ Không cần server riêng

---

## 🎯 Bước 1: Chuẩn Bị Repository GitHub

### 1.1. Tạo Repository Mới

1. Đi đến [github.com](https://github.com) và đăng nhập
2. Click **"New repository"** hoặc [tạo mới tại đây](https://github.com/new)
3. Điền thông tin:
   - **Repository name**: `vn30-ai-quant-bot` (hoặc tên bạn thích)
   - **Visibility**: `Private` (khuyến nghị) hoặc `Public`
   - ❌ **Không tick** "Add a README file" (vì project đã có rồi)
4. Click **"Create repository"**

### 1.2. Push Code Lên GitHub

Mở Terminal tại thư mục project (`/Users/doduongtamdang/Desktop/eykh/vn30_ai_quant_bot`) và chạy:

```bash
# Khởi tạo git repository (nếu chưa có)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: VN30 Quant Bot with AI & Streamlit Dashboard"

# Connect to GitHub (thay YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/vn30-ai-quant-bot.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**⚠️ Lưu ý về Authentication:**

Nếu gặp lỗi authentication, GitHub không chấp nhận password nữa. Phải dùng **Personal Access Token**:

1. Tạo token tại: [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **"Generate new token"** → **"Classic"**
3. Chọn quyền: ✅ `repo` (full control)
4. Click **"Generate token"** và **COPY ngay** (chỉ hiện 1 lần!)
5. Khi `git push` hỏi password, paste token vào (không hiện gì khi gõ là bình thường)

**Hoặc dùng GitHub CLI (dễ hơn):**

```bash
# Cài GitHub CLI (nếu chưa có)
brew install gh

# Login
gh auth login

# Push code
git push -u origin main
```

---

## 🌐 Bước 2: Deploy Lên Streamlit Cloud

### 2.1. Tạo Tài Khoản Streamlit Cloud

1. Đi đến [share.streamlit.io](https://share.streamlit.io)
2. Click **"Sign up"** (hoặc "Continue with GitHub")
3. Đăng nhập bằng tài khoản GitHub của bạn
4. Cho phép Streamlit truy cập GitHub repositories

### 2.2. Deploy App

1. Trên Streamlit Cloud Dashboard, click **"New app"**

2. Điền thông tin deploy:

   | Field              | Value                                 |
   | ------------------ | ------------------------------------- |
   | **Repository**     | `YOUR_USERNAME/vn30-ai-quant-bot`     |
   | **Branch**         | `main`                                |
   | **Main file path** | `dashboard.py` ⚠️ **Quan trọng!**     |
   | **App URL**        | Tùy chọn (VD: `vn30-quant-dashboard`) |

3. **Không click Deploy ngay!** → Click **"Advanced settings"** trước

### 2.3. Cấu Hình Advanced Settings

#### 2.3.1. Python Version

- Chọn: **Python 3.11** (khuyến nghị)

#### 2.3.2. Secrets (API Keys)

Click vào tab **"Secrets"** và paste nội dung này:

```toml
# Telegram Configuration (Optional - để gửi thông báo)
TELEGRAM_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
CHAT_ID = "123456789"

# OpenAI Configuration (Optional - để có phân tích AI chuyên sâu)
OPENAI_API_KEY = "sk-proj-xxxxxxxxxxxxx"
```

**⚠️ Thay bằng keys thật của bạn!**

**Lấy API Keys ở đâu?**

**Telegram Bot Token + Chat ID:**

1. Token:

   - Mở Telegram → Tìm [@BotFather](https://t.me/BotFather)
   - Gửi lệnh: `/newbot`
   - Đặt tên bot và username
   - Copy token (dạng: `123456789:ABCdefGHI...`)

2. Chat ID:
   - Mở Telegram → Tìm [@userinfobot](https://t.me/userinfobot)
   - Gửi `/start`
   - Copy số `Id` (dạng: `123456789`)

**OpenAI API Key:**

1. Đăng ký tại: [platform.openai.com](https://platform.openai.com)
2. Vào [API Keys](https://platform.openai.com/api-keys)
3. Click **"Create new secret key"**
4. Copy key (dạng: `sk-proj-...`)
5. Nạp ít nhất $5 credit để sử dụng

**💡 Lưu ý:** Nếu không cần Telegram hoặc OpenAI, bỏ qua phần đó hoặc để nguyên giá trị mẫu. Bot vẫn chạy được!

### 2.4. Deploy!

1. Click **"Deploy!"**
2. Chờ 3-5 phút (lần đầu lâu hơn vì phải cài dependencies)
3. Xem logs deploy real-time ở màn hình
4. Khi thấy **"Your app is live!"** → Xong! 🎉

URL của bạn sẽ là: `https://YOUR_APP_NAME-YOUR_USERNAME.streamlit.app`

---

## 🔄 Bước 3: Update App (Khi Sửa Code)

Mỗi khi bạn sửa code và muốn update lên cloud:

```bash
# Add changes
git add .

# Commit with message
git commit -m "Update: thêm tính năng XYZ"

# Push to GitHub
git push
```

**Streamlit sẽ tự động detect và deploy lại!** (mất ~1-2 phút)

---

## 🐛 Troubleshooting (Xử Lý Lỗi)

### Lỗi 1: "ModuleNotFoundError: No module named 'xxx'"

**Nguyên nhân:** Thiếu thư viện trong `requirements.txt`

**Giải pháp:**

1. Thêm thư viện vào `requirements.txt`
2. Push lên GitHub
3. Streamlit sẽ tự động cài lại

### Lỗi 2: "Error: vnstock API failed"

**Nguyên nhân:** vnstock đôi khi bị rate limit hoặc server lỗi

**Giải pháp:**

- Reload lại trang sau vài phút
- vnstock là API miễn phí nên đôi khi không ổn định

### Lỗi 3: "Streamlit app exceeded resource limits"

**Nguyên nhân:**

- Free tier có giới hạn: 1GB RAM, 1 CPU core
- Mô hình AI (LSTM) có thể tốn nhiều RAM

**Giải pháp:**

- Giảm `AI_LOOKBACK` xuống 30-40 thay vì 60
- Giảm số lượng cổ phiếu quét cùng lúc
- Hoặc nâng cấp lên Streamlit Pro ($20/tháng)

### Lỗi 4: "Secrets not found"

**Nguyên nhân:** Chưa cấu hình secrets đúng

**Giải pháp:**

1. Vào Streamlit Cloud Dashboard
2. Click vào app → **Settings** → **Secrets**
3. Thêm lại secrets theo format TOML
4. Click **"Save"**
5. App sẽ tự động restart

### Lỗi 5: App chạy chậm

**Nguyên nhân:**

- Đang fetch data cho 30 cổ phiếu
- Đang train LSTM model
- API vnstock chậm

**Giải pháp:**

- Sử dụng `@st.cache_data` (đã có trong code)
- Giảm thời gian data fetch (chọn 1 năm thay vì 5 năm)
- Chấp nhận chờ vài giây (là bình thường)

---

## 📊 Giám Sát App

### Xem Logs

1. Vào Streamlit Cloud Dashboard
2. Click vào app của bạn
3. Click **"Manage app"** → **"Logs"**
4. Xem real-time logs để debug

### Xem Metrics

Streamlit Cloud cung cấp:

- 📈 Number of viewers
- ⏱️ Average session duration
- 🔄 App restart history

### Restart App

Nếu app bị treo:

1. Vào **"Manage app"**
2. Click **"Reboot app"**
3. Chờ 30 giây

---

## 💰 Chi Phí

### Miễn Phí (Community Tier)

- ✅ 1 private app
- ✅ Unlimited public apps
- ✅ 1GB RAM
- ✅ 1 CPU core
- ✅ Unlimited viewers

### Nếu cần nhiều hơn

**Streamlit Pro**: $20/tháng

- 3 private apps
- 4GB RAM
- Priority support

---

## 🔒 Bảo Mật

### Quan trọng: Không commit secrets vào Git!

File `.gitignore` đã được cấu hình để loại trừ:

- `.streamlit/secrets.toml`
- `.env`
- `*.log`

**Kiểm tra trước khi push:**

```bash
# Xem files sẽ được commit
git status

# Nếu thấy secrets.toml → KHÔNG được push!
# Thêm vào .gitignore:
echo ".streamlit/secrets.toml" >> .gitignore
git add .gitignore
git commit -m "Update gitignore"
```

### Secrets trên Streamlit Cloud

Streamlit Cloud lưu secrets **RIÊNG BIỆT** khỏi Git:

- ✅ Được mã hóa
- ✅ Không xuất hiện trong logs
- ✅ Chỉ admin app mới thấy được

---

## 🚀 Next Steps

Sau khi deploy xong:

1. **Share URL** với team hoặc khách hàng
2. **Set up Scheduler Bot** để nhận báo cáo Telegram tự động (xem `RUN_SCHEDULER.md`)
3. **Monitor performance** và tối ưu nếu cần
4. **Customize theme** trong `.streamlit/config.toml`

---

## 🆘 Cần Trợ Giúp?

- 📖 Docs: [docs.streamlit.io](https://docs.streamlit.io)
- 💬 Forum: [discuss.streamlit.io](https://discuss.streamlit.io)
- 🐛 Issues: [GitHub Issues](https://github.com/streamlit/streamlit/issues)

---

## 🎯 Quick Reference

```bash
# Deploy mới
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main

# Update app
git add .
git commit -m "Update XYZ"
git push

# Check status
git status
git log --oneline
```

---

**Chúc bạn deploy thành công! 🚀📈**

Nếu có vấn đề gì, check logs trên Streamlit Cloud Dashboard hoặc xem phần Troubleshooting ở trên!
