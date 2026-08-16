# 🚀 CryptoArbAI

> **An AI-powered cryptocurrency arbitrage detection platform that combines real-time market analysis, portfolio management, sentiment analysis, and intelligent trading insights using Google Gemini AI.**

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-success?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

</p>

<p align="center">

### 🌐 Live Demo

### **https://cryptoarbai-v1-1.onrender.com**

Experience the application live without any installation.

</p>

---

# 📌 Overview

CryptoArbAI is a comprehensive cryptocurrency analytics platform designed to help traders identify profitable arbitrage opportunities across multiple cryptocurrency exchanges.

The application continuously monitors live market prices, compares exchange spreads, evaluates trading opportunities after fees, performs market sentiment analysis, and generates AI-powered market insights using **Google Gemini AI**.

Whether you're an active trader or a crypto enthusiast, CryptoArbAI provides an intuitive dashboard for monitoring market trends and making data-driven trading decisions.

---

# ✨ Features

## 💹 Real-Time Arbitrage Detection

- Live cryptocurrency price monitoring
- Cross-exchange price comparison
- Arbitrage opportunity detection
- Profit estimation after trading fees
- Multi-exchange support

---

## 📊 Portfolio Management

- Portfolio tracking
- Trade history
- Watchlist management
- Investment performance analytics
- Portfolio overview dashboard

---

## 🤖 AI Market Advisor

Powered by **Google Gemini AI**

- Market trend explanations
- AI-generated trading insights
- Market summaries
- Intelligent recommendations
- Cryptocurrency analysis

---

## 📰 Sentiment Analysis

- Cryptocurrency news aggregation
- News sentiment analysis
- Market confidence indicators
- AI-assisted market interpretation

---

## 📈 Interactive Analytics

- Live market charts
- Historical price visualization
- Interactive dashboards
- Performance graphs
- Price movement analysis

---

## 🔒 Authentication

- Secure user registration
- Login system
- Password hashing using Werkzeug
- Session management

---

# 🏗 Project Structure

```
CryptoArbAI
│
├── api/                 # Exchange API integrations
├── arbitrage/           # Arbitrage engine
├── database/            # SQLAlchemy models
├── graphs/              # Visualization utilities
├── llm/                 # Gemini AI integration
├── ml/                  # Machine learning modules
├── sentiment/           # Sentiment analysis
├── static/              # Static assets
├── templates/           # HTML templates
├── tests/               # Unit tests
├── utils/               # Utility functions
│
├── app.py               # Main Streamlit application
├── config.py            # Application configuration
├── requirements.txt
└── README.md
```

---

# 🛠 Tech Stack

### Frontend

- Streamlit

### Backend

- Python
- SQLAlchemy
- SQLite / PostgreSQL

### AI

- Google Gemini AI

### Data Processing

- Pandas
- NumPy

### APIs

- CoinGecko
- Binance
- Kraken
- CoinCap

### Visualization

- Plotly
- Streamlit Charts

---

# ⚡ Installation

## Clone the Repository

```bash
git clone https://github.com/rongalidhanush/CryptoArbAI-Streamlit.git

cd CryptoArbAI-Streamlit
```

---

## Create Virtual Environment

```bash
python -m venv .venv
```

---

## Activate Virtual Environment

### Windows

```bash
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create a **.env** file in the project root.

```env
DATABASE_URL=sqlite:///database/database.db

GEMINI_API_KEY=YOUR_GEMINI_API_KEY

API_TIMEOUT_SECONDS=8

MARKET_CACHE_TTL_SECONDS=30

MARKET_REFRESH_INTERVAL_SECONDS=30
```

---

# ▶ Run Locally

```bash
streamlit run app.py
```

Application runs at

```
http://localhost:8501
```

---

# ☁ Deployment

## Render

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
streamlit run app.py --server.address=0.0.0.0 --server.port=$PORT
```

---

# 📸 Screenshots

Add screenshots inside a **screenshots/** folder.

Example:

```
screenshots/
    dashboard.png
    arbitrage.png
    portfolio.png
    sentiment.png
```

Then include them here.

```markdown
![Dashboard](screenshots/dashboard.png)

![Arbitrage](screenshots/arbitrage.png)

![Portfolio](screenshots/portfolio.png)
```

---

# Supported Exchanges

- ✅ Binance
- ✅ Kraken
- ✅ CoinGecko
- ✅ CoinCap

---

# Future Enhancements

- WebSocket live market updates
- Automated arbitrage execution
- Telegram alerts
- Email notifications
- Mobile responsive interface
- Docker support
- Kubernetes deployment
- Advanced ML price forecasting
- More exchange integrations
- Dark/Light themes

---

# Why CryptoArbAI?

✔ Real-time cryptocurrency monitoring

✔ AI-powered market insights

✔ Portfolio tracking

✔ Arbitrage opportunity detection

✔ Sentiment analysis

✔ Interactive dashboards

✔ Clean Streamlit interface

✔ Modular architecture

---

# Contributing

Contributions are always welcome.

1. Fork the repository

2. Create a new feature branch

```bash
git checkout -b feature-name
```

3. Commit your changes

```bash
git commit -m "Added new feature"
```

4. Push to GitHub

```bash
git push origin feature-name
```

5. Open a Pull Request

---

# Author

**Dhanush Rongali**

GitHub

https://github.com/rongalidhanush

LinkedIn

(Add your LinkedIn profile here)
https://www.linkedin.com/in/dhanushrongali

---
