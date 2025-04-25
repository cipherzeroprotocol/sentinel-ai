<div align="center">
  <img src="https://img.shields.io/badge/Solana-Security-14F195?style=for-the-badge&logo=solana&logoColor=white" alt="Solana Security Platform" />

  # 🛡️ Sentinel AI
  ### Advanced Solana Blockchain Security Analysis Platform

  <p>
    <img src="https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.8+" />
    <img src="https://img.shields.io/badge/AI-Powered-green?style=flat-square&logo=openai&logoColor=white" alt="AI Powered" />
    <img src="https://img.shields.io/badge/NextJS-Frontend-black?style=flat-square&logo=next.js&logoColor=white" alt="Next.js Frontend" />
    <img src="https://img.shields.io/badge/Flask-API-lightgrey?style=flat-square&logo=flask&logoColor=white" alt="Flask API" />
  </p>
</div>

---

## 📋 Overview

Sentinel AI is an advanced security analysis platform that leverages machine learning and data analysis to detect and investigate security threats on the Solana blockchain. Our platform combines blockchain data with AI-powered insights to identify patterns associated with various security risks, including money laundering, mixing services, rugpulls, and address poisoning attacks.

---

## ✨ Key Features

| Feature                     | Description                                                      |
| :-------------------------- | :--------------------------------------------------------------- |
| **📊 ICO Analysis**         | Analyze token launches to identify suspicious patterns & funds   |
| **🚩 Rugpull Detection**    | Identify potential rugpulls before they happen                   |
| **💰 Money Laundering**     | Detect sophisticated laundering techniques (layering, etc.)      |
| **🔄 Mixer Detection**      | Identify cryptocurrency mixing services & usage patterns         |
| **🎯 Address Poisoning**    | Detect dusting campaigns & lookalike address attacks             |
| **👤 Wallet Profiling**    | Generate comprehensive profiles of wallet behavior & classify    |
| **📝 Transaction Analysis** | Analyze transaction patterns & detect suspicious activities      |

---

## 🏗️ Architecture

Sentinel is built with a modular architecture:

#### 1️⃣ Data Collection Layer
   - Integrates with Solana APIs (Helius, Range, Vybe, RugCheck).
   - Fetches transaction data, token info, and security insights.
   - Handles data normalization and storage.

#### 2️⃣ Analysis Modules
   - **ICO Analysis:** Analyzes token launches and fund flows.
   - **Rugpull Detector:** Identifies potential rugpull scams.
   - **Money Laundering Detector:** Detects sophisticated laundering techniques.
   - **Mixer Detector:** Identifies mixing services and patterns.
   - **Dusting Analyzer:** Detects address poisoning and dusting attacks.

#### 3️⃣ Shared Components
   - **Transaction Analyzer:** Provides in-depth transaction analysis.
   - **Wallet Profiler:** Classifies wallets based on behavior patterns.

#### 4️⃣ AI Engine
   - Utilizes OpenAI for pattern recognition, entity classification, risk scoring, and anomaly detection.
   - Employs custom prompt engineering for specialized analysis tasks.

#### 5️⃣ Backend API (Flask)
   - Exposes analysis endpoints for the frontend.
   - Manages analysis requests and orchestrates module execution.
   - Serves generated reports.

#### 6️⃣ Frontend Interface (Next.js - *Separate Repository/Directory*)
   - Provides a user-friendly dashboard for interaction.
   - Visualizes analysis results and reports.
   - Includes search capabilities.

---

## 🔧 Installation

### Prerequisites

- Python 3.8+
- Node.js & npm/yarn (for the separate frontend)
- SQLite (for local development database)
- API Keys:
  - Helius
  - Range Protocol
  - Vybe Network
  - RugCheck.xyz
  - OpenAI

### Backend Setup (This Repository)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/sentinel-ai.git
    cd sentinel-ai/sentinel/sentinel # Navigate to the inner sentinel directory
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # Linux/macOS
    source venv/bin/activate
    # Windows
    .\venv\Scripts\activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the `sentinel-ai/sentinel/sentinel` directory with your API keys:
    ```dotenv
    # .env
    HELIUS_API_KEY=your_helius_api_key
    RANGE_API_KEY=your_range_api_key
    VYBE_API_KEY=your_vybe_api_key
    RUGCHECK_API_KEY=your_rugcheck_api_key
    OPENAI_API_KEY=your_openai_api_key

    # Optional: API Host/Port Configuration
    # API_HOST=0.0.0.0
    # API_PORT=5000
    # API_DEBUG=True
    # CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
    ```

---

## 🚀 Usage

### Command-Line Interface (CLI)

Run analyses directly from the command line within the `sentinel-ai/sentinel/sentinel` directory (ensure your virtual environment is active).

<details>
<summary><b>📈 ICO Analysis</b></summary>

```bash
python main.py ico --token <token_mint_address> [--days <days>]
```
*Analyzes a token launch for suspicious activity.*
</details>

<details>
<summary><b>⚠️ Rugpull Detection</b></summary>

```bash
python main.py rugpull --token <token_mint_address>
```
*Assesses the risk of a rugpull for a given token.*
</details>

<details>
<summary><b>🔍 Money Laundering Detection</b></summary>

```bash
python main.py money-laundering --address <wallet_address> [--days <days>]
```
*Analyzes an address for patterns indicative of money laundering.*
</details>

<details>
<summary><b>🌀 Mixer Detection</b></summary>

```bash
python main.py mixer --address <wallet_address> [--days <days>]
```
*Identifies if an address belongs to or interacts heavily with known mixing services.*
</details>

<details>
<summary><b>💨 Address Poisoning / Dusting Analysis</b></summary>

```bash
python main.py dusting --address <wallet_address> [--days <days>]
```
*Detects dusting attacks and address poisoning attempts targeting an address.*
</details>

<details>
<summary><b>👛 Wallet Profiling</b></summary>

```bash
python main.py wallet --address <wallet_address> [--days <days>]
```
*Generates a behavioral profile and classification for a wallet.*
</details>

<details>
<summary><b>📊 Transaction Analysis</b></summary>

```bash
python main.py transaction --address <wallet_address> [--days <days>]
```
*Performs a general analysis of an address's transaction patterns for suspicious activity.*
</details>

<details>
<summary><b>🔢 Batch Analysis</b></summary>

```bash
python main.py batch --type <analysis_type> [--limit <limit>]
```
*Runs a specific analysis type (e.g., `ico`, `rugpull`) on multiple entities (implementation may vary).*
</details>

### Web API Server

To start the backend API server (which the frontend connects to):

```bash
python main.py web [--host <host>] [--port <port>]
# Example: python main.py web --host 0.0.0.0 --port 5000
```
This starts the Flask server, typically listening on `http://127.0.0.1:5000` by default.

---

## 📊 Module Details

### ICO Analysis 📈
- Tracks fund flows from ICO wallets.
- Analyzes team wallet behavior and token distribution.
- Monitors liquidity pool creation and changes.
- Detects suspicious fund outflows and concentration risks.

### Rugpull Detector 🚩
- Analyzes token creator history and behavior patterns.
- Monitors liquidity pool locking status and LP token distribution.
- Tracks token authority changes (mint/freeze).
- Leverages RugCheck.xyz data for known risks.

### Money Laundering Detector 💰
- Detects complex transaction layering and structuring (smurfing).
- Identifies cross-chain fund movements via bridges.
- Analyzes address clustering to link related entities.
- Tracks fund flows involving high-risk counterparties (mixers, sanctioned addresses).

### Mixer Detector 🔄
- Identifies interactions with known mixer addresses and programs.
- Analyzes transaction graphs for mixer-like patterns (e.g., fixed denominations, timed deposits/withdrawals).
- Assesses the likelihood of an address being part of a mixing service.

### Dusting & Address Poisoning Analyzer 🎯
- Identifies small "dust" transactions sent to many addresses.
- Detects lookalike addresses used in address poisoning scams.
- Analyzes transaction patterns consistent with deanonymization attempts.

---

## 📝 Examples

<details>
<summary><b>Example 1: Analyzing USDC for Rugpull Risk (Illustrative)</b></summary>

```bash
python main.py rugpull --token EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
```
*(Expect low risk for established tokens like USDC)*
</details>

<details>
<summary><b>Example 2: Detecting Money Laundering Activity for a Specific Address</b></summary>

```bash
# Replace with an address you want to investigate
python main.py money-laundering --address VinesRG7K3ubzKLbxXz197c1RHV3cACkvGr9Zca7BSw --days 60
```
*Analyzes the wallet's transactions over the past 60 days.*
</details>

<details>
<summary><b>Example 3: Running the Web API Server for Frontend</b></summary>

```bash
python main.py web --host 0.0.0.0 --port 5000
```
*Starts the API server, making it accessible on your local network.*
</details>

---

## 👥 Contributing

Contributions are welcome! Please fork the repository and submit a Pull Request with your proposed changes. Ensure your code follows existing style conventions and includes tests where applicable.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

---

## 🙏 Acknowledgements

- **Solana Foundation:** For the underlying blockchain technology.
- **API Providers:** Helius, Range Protocol, Vybe Network, RugCheck.xyz for invaluable blockchain data access.
- **OpenAI:** For the powerful AI models enabling advanced analysis.
- **Open Source Community:** For the libraries and tools used in this project.
- All contributors and supporters.