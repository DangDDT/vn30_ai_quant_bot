# 🚀 Hướng Dẫn Deploy VN30 Quant Bot Lên Streamlit Cloud

## 📋 Tổng Quan

Dashboard của bạn sẽ được host **MIỄN PHÍ** trên Streamlit Cloud với URL riêng như: `https://vn30-quant-bot-yourusername.streamlit.app`

---

## 🎯 Bước 1: Chuẩn Bị Repository GitHub

### 1.1. Tạo Repository Mới

1. Đi đến [github.com](https://github.com) và đăng nhập
2. Click **"New repository"** hoặc [tạo mới tại đây](https://github.com/new)
3. Điền thông tin:
   - **Repository name**: `vn30-ai-quant-bot` (hoặc tên bạn thích)
   - **Visibility**: `Private` (khuyến nghị) hoặc `Public`
   - **Initialize**: ✅ Tick "Add a README file"
4. Click **"Create repository"**

### 1.2. Push Code Lên GitHub

Mở Terminal tại thư mục project và chạy:

```bash
# Initialize git (nếu chưa có)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: VN30 Quant Bot"

# Connect to GitHub (thay YOUR_USERNAME và YOUR_REPO)
git remote add origin https://github.com/YOUR_USERNAME/vn30-ai-quant-bot.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Lưu ý**: Nếu bị lỗi authentication, sử dụng **Personal Access Token** thay vì password:

- Tạo token tại: [github.com/settings/tokens](https://github.com/settings/tokens)
- Chọn: `repo` (full control)
- Copy token và dùng làm password khi push

---

## 🌐 Bước 2: Deploy Lên Streamlit Cloud

### 2.1. Tạo Tài Khoản Streamlit Cloud

1. Đi đến [share.streamlit.io](https://share.streamlit.io)
2. Click **"Sign up"** và đăng nhập bằng GitHub
3. Cho phép Streamlit truy cập GitHub repositories của bạn

### 2.2. Deploy App

1. Click **"New app"**
2. Điền thông tin:

   - **Repository**: Chọn `YOUR_USERNAME/vn30-ai-quant-bot`
   - **Branch**: `main`
   - **Main file path**: `dashboard.py` ⚠️ **Quan trọng!**
   - **App URL**: Chọn URL tùy thích (VD: `vn30-quant-dashboard`)

3. Click **"Advanced settings"** và cấu hình:
   - **Python version**: `3.11` (khuyến nghị)
   - **Secrets**: Nhập các API keys (xem bước 2.3)

### 2.3. Cấu Hình Secrets (API Keys)

Trong phần **"Advanced settings" → "Secrets"**, paste nội dung này và thay bằng keys thật của bạn:

```toml
# Telegram Configuration
TELEGRAM_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
CHAT_ID = "123456789"

# OpenAI Configuration (Optional)
OPENAI_API_KEY = "sk-proj-xxxxxxxxxxxxx"
```

**Lấy API Keys ở đâu?**

- **Telegram**:
  - Token: Tạo bot qua [@BotFather](https://t.me/BotFather)
  - Chat ID: Nhắn [@userinfobot](https://t.me/userinfobot) để lấy
- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### 2.4. Deploy!

Click **"Deploy!"** và chờ 2-3 phút. Streamlit sẽ:

- ✅ Clone repo từ GitHub
- ✅ Cài đặt dependencies từ `requirements.txt`
- ✅ Khởi động app

---

## 🔧 Bước 3: Cập Nhật Code để Đọc Secrets

Streamlit Cloud lưu secrets trong `st.secrets`, không phải `os.environ`. Cần điều chỉnh một chút:

### 3.1. Cập Nhật `dashboard.py`

<function_calls>
<invoke name="read_file">
<parameter name="target_file">dashboard.py
