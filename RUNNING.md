# Running the Sentinel AI Application

This guide explains how to run the complete Sentinel AI application, including both the Python Flask backend and the Next.js frontend.

## Prerequisites

- Python 3.8+ with pip installed
- Node.js 18+ with npm installed
- API keys:
  - OpenAI API key
  - Helius API key (for Solana blockchain data)
  - Other Solana data providers as needed (Range, Vybe, RugCheck)

## 1. Setup and Run the Python Backend

### 1.1. Environment Setup

First, navigate to the project root directory after cloning the repository:

```bash
cd sentinel-ai
```

Create and activate a Python virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

### 1.2. Configure Environment Variables

Set the necessary API keys. The OpenAI API key is **required** for the AI analysis functionality:

```bash
# Windows
set OPENAI_API_KEY=your_openai_api_key_here
set HELIUS_API_KEY=your_helius_api_key_here
set RANGE_API_KEY=your_range_api_key_here
set VYBE_API_KEY=your_vybe_api_key_here
set RUGCHECK_API_KEY=your_rugcheck_api_key_here

# macOS/Linux
export OPENAI_API_KEY=your_openai_api_key_here
export HELIUS_API_KEY=your_helius_api_key_here
export RANGE_API_KEY=your_range_api_key_here
export VYBE_API_KEY=your_vybe_api_key_here
export RUGCHECK_API_KEY=your_rugcheck_api_key_here
```

> **Important:** If you don't set the `OPENAI_API_KEY`, you'll see warnings and AI-powered analysis features will not function correctly. You can get an API key from the [OpenAI Platform](https://platform.openai.com/).

### 1.3. Start the Flask Backend

Run the Flask API server:

```bash
cd sentinel/web
python app.py
```

This will start the API server at http://localhost:5000 by default.

Alternative using the main script:

```bash
cd sentinel
python main.py web
```

> **Note:** If you want to make the API accessible from other computers on your network, use:
> ```bash
> python app.py --host 0.0.0.0 --port 5000
> ```
> Or with main.py: `python main.py web --host 0.0.0.0 --port 5000`

Verify the API is running by accessing http://localhost:5000/api/health in your browser. You should see a JSON response with status "ok".

## 2. Setup and Run the Next.js Frontend

### 2.1. Environment Setup

Open a new terminal window (keep the backend running). Navigate to the frontend directory:

```bash
cd sentinel-ai/sentinel/frontend
```

Install Node.js dependencies:

```bash
npm install
# or
yarn install
# or
pnpm install
```

### 2.2. Configure Environment Variables

Create a file named `.env.local` in the frontend directory with the following content:

```
# API URL for connecting to the Sentinel AI backend
NEXT_PUBLIC_API_URL=http://localhost:5000

# Optional: Configure timeouts (in milliseconds)
NEXT_PUBLIC_API_TIMEOUT=120000

# Authentication Configuration (if using Next Auth)
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret-key-here
```

### 2.3. Start the Next.js Frontend

Run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

This will start the frontend at http://localhost:3000.

## 3. Access the Complete Application

1. Ensure both servers are running:
   - Backend: http://localhost:5000
   - Frontend: http://localhost:3000

2. Open http://localhost:3000 in your browser to access the Sentinel AI dashboard.

3. Use the connection indicator at the bottom right to verify that the frontend is successfully connected to the backend.

## 4. Troubleshooting

### 4.1. Backend Connection Issues

- Verify the API is running by accessing http://localhost:5000/api/health
- Check the API logs for any initialization errors
- Ensure all required API keys are set
- Verify the database directory exists and is writable

### 4.2. Frontend Connection Issues

- Check that NEXT_PUBLIC_API_URL is correctly set in .env.local
- Examine the browser console for network errors or CORS issues
- Verify that the backend has CORS configured to allow requests from the frontend origin

### 4.3. Data Analysis Issues

- **OpenAI API Key**: Ensure your OpenAI API key is valid and has sufficient quota
  - Run `echo %OPENAI_API_KEY%` (Windows) or `echo $OPENAI_API_KEY` (macOS/Linux) to verify the key is set
  - If you see the warning `OPENAI_API_KEY not found in config`, this means the environment variable is not set correctly
- Check that Helius API key and other blockchain data provider keys are valid
- Verify the backend logs for specific error messages related to data fetching or analysis

## 5. Production Deployment

For production deployment, additional steps are recommended:

1. Build the optimized frontend:
   ```bash
   cd frontend
   npm run build
   npm run start
   ```

2. Use a production WSGI server for the Flask backend:
   ```bash
   pip install waitress
   waitress-serve --host=0.0.0.0 --port=5000 sentinel.web.app:app
   ```

3. Set up proper environment variables for production, including:
   - SECRET_KEY (for Flask)
   - NEXTAUTH_SECRET (for NextAuth)
   - Database paths
   - API URLs
   - Disable DEBUG mode

## 6. Command Line Interface

The Sentinel AI application also provides a command-line interface for running analyses without using the web interface:

```bash
# ICO Analysis
python main.py ico --token <token_address> [--days <days>]

# Rugpull Detection
python main.py rugpull --token <token_address>

# Money Laundering Detection
python main.py money-laundering --address <wallet_address> [--days <days>]

# Mixer Detection
python main.py mixer --address <wallet_address> [--days <days>]

# Address Poisoning Analysis
python main.py dusting --address <wallet_address> [--days <days>]

# Wallet Profiling
python main.py wallet --address <wallet_address> [--days <days>]

# Transaction Analysis
python main.py transaction --address <wallet_address> [--days <days>]
```

## 7. Additional Resources

- [Sentinel AI Documentation](./README.md)
- [API Documentation](./API.md) (if available)
- [Frontend Documentation](./frontend/README.md)
