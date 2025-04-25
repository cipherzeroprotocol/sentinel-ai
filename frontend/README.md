<div align="center">
  <img src="https://img.shields.io/badge/Sentinel-AI-14F195?style=for-the-badge&logo=solana&logoColor=white" alt="Sentinel AI" />
  
  # 🛡️ Sentinel AI Frontend
  ### Next.js Frontend for Solana Security Analysis Platform
  
  <p>
    <img src="https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js&logoColor=white" alt="Next.js 14" />
    <img src="https://img.shields.io/badge/React-18-blue?style=flat-square&logo=react&logoColor=white" alt="React 18" />
    <img src="https://img.shields.io/badge/TypeScript-5-blue?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript 5" />
    <img src="https://img.shields.io/badge/Tailwind-CSS-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
  </p>
</div>

## 📋 Overview

This is the modern Next.js frontend for the Sentinel AI platform, an AI-powered security analysis tool for the Solana blockchain. The frontend provides an intuitive user interface for blockchain security analysis with interactive visualizations and comprehensive reporting.

## ✨ Features

- **🔍 Multiple Analysis Types**: Analyze ICOs, detect rugpulls, identify money laundering patterns
- **📊 Interactive Reports**: View comprehensive security reports with detailed analysis
- **🤖 AI-Powered Insights**: Leverage advanced AI models for deeper security analysis
- **🔎 Search Functionality**: Find and investigate addresses and tokens
- **📱 Responsive Design**: Works on desktop, tablet, and mobile devices
- **🌙 Dark Mode**: Fully supported dark and light themes

## 🚀 Getting Started

### Prerequisites

| Requirement | Description |
|------------|-------------|
| **Node.js** | Version 18+ required |
| **Backend** | Python Flask API running |
| **API Keys** | Required for backend services |

### Configuration

1. Create a `.env.local` file in the frontend directory:

```env
# API URL for connecting to the Sentinel AI backend
NEXT_PUBLIC_API_URL=http://localhost:5000

# Optional: Configure timeouts (in milliseconds)
NEXT_PUBLIC_API_TIMEOUT=120000

# Optional: Configure retry settings (number of retries)
NEXT_PUBLIC_API_MAX_RETRIES=3

# Authentication Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret

# JWT Configuration
JWT_SECRET=your-jwt-secret
```

### Backend Setup

1. Navigate to the main `sentinel` directory:
   ```bash
   cd sentinel
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   # Linux/macOS
   export OPENAI_API_KEY=your_api_key_here
   export HELIUS_API_KEY=your_helius_key_here
   
   # Windows
   set OPENAI_API_KEY=your_api_key_here
   set HELIUS_API_KEY=your_helius_key_here
   ```

4. Run the Flask API server:
   ```bash
   cd sentinel/web
   python app.py
   ```
   The API should now be running on `http://localhost:5000`

### Frontend Setup

1. Navigate to the `frontend` directory:
   ```bash
   cd sentinel/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) with your browser to access the Sentinel AI dashboard.

## 🔌 API Connection Details

The frontend communicates with the Flask backend through these primary endpoints:

| Endpoint | Description | Method |
|----------|-------------|--------|
| `/api/analyze` | Submit analysis requests | POST |
| `/api/reports` | Get list of generated reports | GET |
| `/generated_reports/<filename>` | View report content | GET |
| `/api/search` | Search addresses and tokens | POST |
| `/api/health` | API health check | GET |

## 📱 UI Components

The Sentinel AI frontend includes these key components:

- **Dashboard**: Overview of recent analyses and high-risk entities
- **Analysis Form**: Request new security analyses
- **Report Viewer**: View detailed analysis reports with visualizations
- **Search Interface**: Find and investigate blockchain entities
- **Settings**: Configure user preferences and API tokens

## 🔧 Troubleshooting API Connection Issues

If you encounter API connection issues:

1. **Check Backend Status**:
   - Ensure the backend is running at `http://localhost:5000`
   - Verify Flask server logs for errors

2. **Check CORS Issues**:
   - Examine browser console for CORS errors
   - Verify backend CORS settings allow your frontend origin

3. **Check API Configuration**:
   - Verify your `.env.local` has the correct API URL
   - Ensure all required API keys are set in the backend

4. **Network Issues**:
   - Check for firewalls blocking connections
   - Verify proxy settings if applicable

## 🧩 Project Structure

```
frontend/
├── src/
│   ├── app/           # Next.js App Router pages
│   ├── components/    # React components
│   ├── hooks/         # Custom React hooks
│   ├── lib/           # Utility functions
│   ├── styles/        # Global styles
│   └── types/         # TypeScript types
├── public/            # Static assets
└── ...configuration files
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Learn More

- [Next.js Documentation](https://nextjs.org/docs) - Next.js features and API
- [Sentinel AI Backend](../README.md) - Backend documentation
