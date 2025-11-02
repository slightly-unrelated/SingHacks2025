# Plutus: AI-Powered Anti-Money Laundering Detection System

**Plutus** is an advanced Anti-Money Laundering (AML) detection system that leverages Graph Neural Networks (GNNs) to identify suspicious financial transactions and high-risk accounts. The system combines transaction network analysis with document verification to provide comprehensive compliance monitoring.

## Key Features

- **Graph Neural Network Analysis**: Uses an inductive GNN model with SAGEConv layers to detect suspicious transaction patterns
- **Multi-Modal Detection**: Analyzes both transaction networks and document content
- **Behavioral Feature Engineering**: Extracts 26+ behavioral features including:
  - Cross-border transaction patterns
  - Night-time transaction detection
  - Payment channel analysis
  - Transaction frequency and velocity
  - Account age and history
- **Real-Time Dashboard**: Modern React-based UI for compliance officers
- **Document Processing**: OCR-based document verification with Tesseract
- **Scalable Architecture**: Inductive learning approach handles new accounts not seen during training
- **Pre-trained Models**: Production-ready champion model included

## Tech Stack

### Backend
- **FastAPI** - High-performance API framework
- **PyTorch + PyTorch Geometric** - Graph Neural Network implementation
- **scikit-learn** - Feature preprocessing and scaling
- **Pandas/NumPy** - Data processing
- **OpenCV** - Image processing
- **Tesseract OCR** - Document text extraction
- **PyMuPDF** - PDF processing

### Frontend
- **React 19** - UI framework
- **Vite** - Build tool and dev server
- **TailwindCSS** - Styling framework
- **React Router** - Navigation
- **jsPDF** - PDF report generation

### Machine Learning
- **Graph Neural Networks** - SAGEConv architecture with 3 layers
- **Inductive Learning** - Handles unseen nodes at inference time
- **Feature Engineering** - Custom transaction behavioral features

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  Dashboard | Transactions | Documents | Risk Alerts      │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP/REST
┌─────────────────▼───────────────────────────────────────┐
│                 FastAPI Backend                          │
│  ┌───────────────────────┐  ┌─────────────────────────┐ │
│  │   Document Processing │  │   GNN Inference Engine  │ │
│  │   - PDF to Image      │  │   - Graph Builder       │ │
│  │   - OCR Extraction    │  │   - Feature Engineering │ │
│  │   - Text Analysis     │  │   - Risk Scoring        │ │
│  └───────────────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│              Pre-trained Assets                          │
│  - GNN Model Weights (PyTorch)                          │
│  - Feature Scaler (scikit-learn)                        │
│  - Account Mapping (Training baseline)                  │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

### System Requirements
- **Python 3.8+**
- **Node.js 16+** and npm
- **Tesseract OCR** (for document processing)

### Installing Tesseract

**Windows:**
```bash
# Download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH during installation
```

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install tesseract-ocr
sudo apt install libtesseract-dev
```

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/SingHacks2025.git
cd SingHacks2025
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd aml-dashboard
npm install
cd ..
```

### 4. Verify Tesseract Installation

```bash
tesseract --version
```

If Tesseract is not found, ensure it's added to your system PATH.

## Running the Application

### Start the Backend API

```bash
# From project root
python api/api.py
```

The API will be available at `http://localhost:4000`

### Start the Frontend Dashboard

```bash
# In a new terminal
cd aml-dashboard
npm run dev
```

The dashboard will be available at `http://localhost:5173`

## Usage

### 1. Transaction Analysis (Batch Inference)

Upload a CSV file containing transactions to detect high-risk accounts:

**Endpoint:** `POST /api/v1/infer_batch`

**CSV Format (Auto-detected):**
- Supports two column naming conventions:
  - `Sender_account`, `Receiver_account`, `Amount`, `Payment_type`, `Sender_bank_location`, `Receiver_bank_location`, `Date`, `Time`
  - `originator_account`, `beneficiary_account`, `amount`, `channel`, `originator_country`, `beneficiary_country`, `booking_datetime`

**Example:**
```bash
curl -X POST http://localhost:4000/api/v1/infer_batch \
  -F "file=@transactions_mock_1000_for_participants.csv"
```

**Response:**
```json
{
  "status": "success",
  "alerts_found": 5,
  "alerts": [
    {
      "Account_ID": "ACC_12345",
      "Risk_Score": 0.94,
      "total_sent": 125000.0,
      "num_sent_tx": 23,
      "num_cross_border_tx_sent": 18,
      "num_night_tx_sent": 12,
      ...
    }
  ]
}
```

### 2. Document Processing

Upload PDF or image documents for OCR analysis:

**PDF Processing:**
```bash
curl -X POST http://localhost:4000/process/pdf \
  -F "file=@document.pdf"
```

**Image Processing:**
```bash
curl -X POST http://localhost:4000/process/image \
  -F "file=@document.png"
```

### 3. Using the Dashboard

1. Navigate to `http://localhost:5173`
2. View real-time AML alerts on the Dashboard
3. Explore detailed transaction analysis in the Transactions tab
4. Upload and analyze documents in the Documents tab
5. Export reports as PDF

## Project Structure

```
SingHacks2025/
├── api/                          # FastAPI backend
│   ├── api.py                   # Main API server with endpoints
│   └── __init__.py
├── aml-dashboard/               # React frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── utils/              # Utilities (PDF export, etc.)
│   │   └── data/               # Mock data
│   ├── package.json
│   └── vite.config.js
├── doc_processing/              # Document OCR pipeline
│   ├── pdf_pro.py              # PDF to PNG conversion
│   ├── img_pro.py              # Image OCR with Tesseract
│   ├── text_pro.py             # Text analysis and entity extraction
│   └── output_images/          # Processed document outputs
├── src/                         # ML training scripts
│   ├── build_graph_v3.py       # Graph construction from transactions
│   ├── train_inductive_model.py # GNN model training
│   └── inference.py            # Batch inference script
├── Pre-trained Model Files
│   ├── inductive_model_champion_V3.pth  # GNN model weights
│   ├── scaler_V3.pkl                    # Feature scaler
│   └── account_map_V3.pkl               # Training account mapping
├── requirements.txt             # Python dependencies
└── README.md
```

## Model Information

### GNN Architecture

The system uses an **Inductive Graph Neural Network** with the following architecture:

- **3 SAGEConv layers** (GraphSAGE convolution)
- **Hidden dimension:** 128
- **K-hop subgraph sampling:** 2-hop neighborhoods
- **Output:** Binary classification (illicit vs. legitimate)
- **Risk threshold:** 0.85 (accounts above this trigger alerts)

### Feature Engineering (26 Features)

**Transaction Volume:**
- `total_sent`, `total_received`
- `num_sent_tx`, `num_received_tx`
- `avg_sent`, `avg_received`

**Temporal Features:**
- `account_age_days`
- `tx_frequency_per_day`
- `num_night_tx_sent`, `num_night_tx_received`

**Geographic:**
- `num_cross_border_tx_sent`, `num_cross_border_tx_received`

**Payment Channels (Universal Features):**
- `sent_feat_CASH`, `received_feat_CASH`
- `sent_feat_INTL_WIRE`, `received_feat_INTL_WIRE`
- `sent_feat_DOMESTIC_FAST`, `received_feat_DOMESTIC_FAST`
- `sent_feat_LEGACY`, `received_feat_LEGACY`

**Behavioral:**
- `num_small_tx_sent`, `num_small_tx_received`


## Development

### Running Tests

```bash
# Backend tests
pytest

# Frontend tests
cd aml-dashboard
npm test
```

### Code Style

- **Python:** Follow PEP 8 guidelines
- **JavaScript:** ESLint configuration included
- **Formatting:** Use Prettier for frontend code

### Training a New Model

If you want to retrain the GNN model with your own data:

```bash
# 1. Build graph from transaction CSV
python src/build_graph_v3.py --input your_data.csv --output graph_v4.pt

# 2. Train the model
python src/train_inductive_model.py --graph graph_v4.pt --output model_v4.pth

# 3. Update model paths in api/api.py
```




## Acknowledgments

- Built for SingHacks 2025
- Graph Neural Network implementation based on PyTorch Geometric
- OCR powered by Tesseract
- UI components styled with TailwindCSS



