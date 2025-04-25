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

## 📋 Overview

Sentinel AI is an advanced security analysis platform that leverages machine learning and data analysis to detect and investigate security threats on the Solana blockchain. Our platform combines blockchain data with AI-powered insights to identify patterns associated with various security risks, including money laundering, mixing services, rugpulls, and address poisoning attacks.

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **📊 ICO Analysis** | Analyze token launches to identify suspicious patterns and fund flows |
| **🚩 Rugpull Detection** | Identify potential rugpulls before they happen |
| **💰 Money Laundering Detection** | Detect sophisticated laundering techniques |
| **🔄 Mixer Detection** | Identify cryptocurrency mixing services |
| **🎯 Address Poisoning Analysis** | Detect dusting campaigns targeting specific addresses |
| **👤 Wallet Profiling** | Generate comprehensive profiles of wallet behavior |
| **📝 Transaction Analysis** | Analyze transaction patterns and detect suspicious activities |

## 🏗️ Architecture

Sentinel is built with a modular architecture consisting of the following components:

### 🧩 Core Components

#### 1️⃣ Data Collection Layer
- Integrates with multiple Solana APIs (Helius, Range, Vybe, RugCheck)
- Fetches transaction data, token information, and security insights
- Handles data normalization and storage

#### 2️⃣ Analysis Modules
- ICO Analysis: Analyzes token launches and fund flows
- Rugpull Detector: Identifies potential rugpull scams
- Money Laundering Detector: Detects sophisticated money laundering techniques
- Mixer Detector: Identifies mixing services and their patterns
- Dusting Analyzer: Detects address poisoning and dusting attacks

#### 3️⃣ Shared Components
- Transaction Analyzer: Provides in-depth transaction analysis
- Wallet Profiler: Classifies wallets based on behavior patterns

#### 4️⃣ AI Engine
- Pattern recognition for suspicious transaction flows
- Entity classification and relationship mapping
- Risk scoring and anomaly detection

#### 5️⃣ Web Interface
- Dashboard for visualization and interaction
- Report generation and viewing
- Search capabilities for entities

## 🔧 Installation

### Prerequisites

- Python 3.8+
- SQLite (for local development)
- API keys for Helius, Range, Vybe, and RugCheck

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sentinel-ai.git
   cd sentinel-ai
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables for API keys:
   ```bash
   export HELIUS_API_KEY=your_helius_api_key
   export RANGE_API_KEY=your_range_api_key
   export VYBE_API_KEY=your_vybe_api_key
   export RUGCHECK_API_KEY=your_rugcheck_api_key
   export OPENAI_API_KEY=your_openai_api_key
   ```
   On Windows, use `set` instead of `export`.

## 🚀 Usage

### Command-Line Interface

Sentinel provides a comprehensive command-line interface for running analyses:

<details>
<summary><b>📈 ICO Analysis</b></summary>

```bash
python main.py ico --token <token_address> [--days <days>]
```
</details>

<details>
<summary><b>⚠️ Rugpull Detection</b></summary>

```bash
python main.py rugpull --token <token_address>
```
</details>

<details>
<summary><b>🔍 Money Laundering Detection</b></summary>

```bash
python main.py money-laundering --address <wallet_address> [--days <days>]
```
</details>

<details>
<summary><b>🌀 Mixer Detection</b></summary>

```bash
python main.py mixer --address <wallet_address> [--days <days>]
```
</details>

<details>
<summary><b>💨 Address Poisoning Analysis</b></summary>

```bash
python main.py dusting --address <wallet_address> [--days <days>]
```
</details>

<details>
<summary><b>👛 Wallet Profiling</b></summary>

```bash
python main.py wallet --address <wallet_address> [--days <days>]
```
</details>

<details>
<summary><b>📊 Transaction Analysis</b></summary>

```bash
python main.py transaction --address <wallet_address> [--days <days>]
```
</details>

<details>
<summary><b>🔢 Batch Analysis</b></summary>

```bash
python main.py batch --type <analysis_type> [--limit <limit>]
```
</details>

### Web Interface

To start the web interface:

```bash
python main.py web [--host <host>] [--port <port>]
```

This will start a Flask web server that provides a user-friendly interface for running analyses and viewing reports.

## 📊 Module Details

### ICO Analysis 📈

The ICO Analysis module identifies suspicious patterns in token launches by:
- Tracking fund flows from ICO wallets
- Analyzing team wallet behavior
- Monitoring liquidity pool changes
- Detecting suspicious fund outflows

### Rugpull Detector 🚩

The Rugpull Detector identifies potential scams by:
- Analyzing token creator behavior patterns
- Monitoring liquidity pool changes
- Tracking token authority abuse
- Detecting suspicious developer activity

### Money Laundering Detector 💰

The Money Laundering Detector identifies sophisticated techniques by:
- Detecting complex transaction layering
- Identifying cross-chain fund routes
- Analyzing address clustering to link related entities
- Tracking fund flows from identified illicit sources

### Mixer Detector 🔄

The Mixer Detector identifies cryptocurrency mixing services by:
- Detecting known mixer addresses
- Identifying mixer-like transaction patterns
- Analyzing transaction graphs for mixing behavior
- Generating comprehensive reports on mixer activity

### Dusting Analyzer 🎯

The Dusting Analyzer detects address poisoning attacks by:
- Identifying small "dust" transactions across multiple addresses
- Detecting lookalike addresses (address poisoning)
- Analyzing transaction patterns consistent with dusting
- Generating reports on detected dusting campaigns

## 📝 Examples

<details>
<summary><b>Example 1: Analyzing a Token for Rugpull Risk</b></summary>

```bash
python main.py rugpull --token EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
```

This will analyze the token and generate a comprehensive report about its rugpull risk.
</details>

<details>
<summary><b>Example 2: Detecting Money Laundering Activity</b></summary>

```bash
python main.py money-laundering --address VinesRG7K3ubzKLbxXz197c1RHV3cACkvGr9Zca7BSw --days 60
```

This will analyze the wallet's transactions over the past 60 days to detect money laundering patterns.
</details>

<details>
<summary><b>Example 3: Batch Analysis of Recent Tokens</b></summary>

```bash
python main.py batch --type ico --limit 20
```

This will analyze the 20 most recent token launches for suspicious activity.
</details>

<details>
<summary><b>Example 4: Running the Web Interface</b></summary>

```bash
python main.py web --host 0.0.0.0 --port 8000
```

This will start the web interface on all network interfaces (accessible from other computers) on port 8000.
</details>

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- Solana Foundation for blockchain infrastructure
- Helius, Range, Vybe, and RugCheck for providing API access to blockchain data
- All contributors and supporters of the project#   s e n t i n e l - a i  
 