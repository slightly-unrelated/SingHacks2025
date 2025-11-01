 Part 1: Transaction Monitoring (GNN-Based AML 
  Detection)

  How It Works:

  1. Data Processing (build_graph_v3.py)

  Your solution builds a Graph Neural Network
  where:
  - Nodes = Bank accounts (from
  originator_account/beneficiary_account)
  - Edges = Transactions (money flows between
  accounts)
  - Node Features = 22 engineered features per
  account:
    - Transaction volume: total_sent,
  total_received, avg_sent, avg_received
    - Transaction counts: num_sent_tx,
  num_received_tx
    - Behavioral patterns:
        - Cross-border transactions (different
  countries)
      - Night transactions (12am-5am suspicious
  activity)
      - Small transactions (< $500, potential
  structuring)
    - Payment types (Universal features):
        - feat_CASH (cash deposits/withdrawals)
      - feat_INTL_WIRE (SWIFT, SEPA, RTGS)
      - feat_DOMESTIC_FAST (FPS, FAST, ACH)
      - feat_LEGACY (Cheques, cards)
    - Temporal features: account_age_days,
  tx_frequency_per_day

  2. Model Architecture (gnn_aml_detector.py)

  - Type: 2-layer Graph Convolutional Network
  (GCN)
  - Architecture:
  Input (22 features) → GCNConv(128) → ReLU →
  Dropout(0.5) → GCNConv(2) → Softmax
  - Training: Uses weighted Cross-Entropy Loss
  (pos_weight=0.25 to handle class imbalance)
  - Best Model:
  best_model_GCN_Champ_V3_PW25_Base.pth
    - Hidden dim: 128
    - Learning rate: 0.005
    - Dropout: 0.5
    - Val F1: ~0.85-0.90 (based on tuning logs)

  3. Inference Pipeline (run_inference.py)

  What happens when you analyze 1000 
  transactions:
  1. Build graph from CSV → Extract 22 features
  per account
  2. Standardize features using trained scaler
  (scaler_V3.pkl)
  3. Extract 2-hop subgraphs around each account
  (local neighborhood)
  4. Run GNN prediction → Output: 0 (benign) or 1
   (illicit)
  5. Generate account-level alerts → Save to
  predictions.csv

  Performance:
  - Processes 1000 transactions in ~30-60 seconds
  - Generates risk scores for every unique
  account
  - Much faster than GraphRAG because it's a
  trained model (not LLM inference)

  ---
  Part 2: Document Verification (OCR + Rule-Based
   Validation)

  Pipeline:

  1. PDF to Image (pdf_pro.py)

  PDF → PyMuPDF → PNG images (one per page)

  2. Image Preprocessing (img_pro.py)

  - Auto-orient: Detects rotation (90°, 180°,
  270°) and fixes it
  - Deskew: Uses Hough Line Transform to detect
  text lines and straighten document
  - OCR: Tesseract extracts text with bounding
  boxes, confidence scores

  Output: JSON with word-level data:
  [
    {"text": "Julius", "conf": 94.5, "left": 120,
   "top": 45, "width": 50, "height": 12},
    ...
  ]

  3. Document Analysis (text_pro.py)

  Performs 6 types of validation:

  a) Format Validation:
  - Double spacing: Detects abnormal gaps between
   words (>1.8× median)
  - Irregular fonts: Checks for inconsistent font
   heights (CV > 0.30)
  - Indentation: Ensures consistent left margins
  (within 24px of dominant)

  b) Content Validation:
  - Spelling: Flags low-confidence (<70%) words
  - Missing sections: Checks for required
  headers: ["ref", "date", "client", "name",
  "address", "nationality", "subject"]
  - Incorrect headers: Uses edit distance to find
   typos (e.g., "clent:" → "client:")

  c) Structure Analysis:
  - Header ordering: Validates that sections
  appear in expected order
  - Completeness score: % of required headers
  found
  - Template matching: How well document matches
  expected structure

  d) Risk Scoring:
  risk_score = (
    1×double_spacing_issues +
    5×irregular_font_lines +
    1×indent_issues +
    10×spelling_errors +
    15×missing_sections +
    8×order_violations
  ) × damping_factor

  Damping factor = Lower risk if document has
  good template match and completeness

  Example Output:
  {
    "risk": {
      "score": 73,  // 0-100 (higher = more
  suspicious)
      "factors": {
        "double": 12,
        "fonts": 3,
        "spelling": 5,
        "missing": 2
      }
    },
    "issues": [
      {"type": "double-spacing", "line": 15,
  "gaps": [[3, 18]]},
      {"type": "missing-section", "header":
  "nationality"},
      {"type": "incorrect-header", "got":
  "clent:", "want": "client"}
    ]
  }

  ---
  Integration: How Parts 1 & 2 Work Together

  Cross-Reference Strategy:

  1. Transaction CSV has customer_id field (e.g.,
   "CUST-956783")
  2. Document should have same customer ID
  extracted via OCR
  3. Your UI can link them and check for:
    - Amount mismatches: Transaction shows CHF
  1,250,000 but document shows CHF 125,000
    - Date discrepancies: Transaction dated
  2024-10-30 but document dated 2023-10-15
    - Missing documentation: High-risk GNN
  prediction but no supporting documents
    - Conflicting data: Transaction from RU but
  document claims UK source

  ---
  Technical Stack Summary

  Backend (Python):

  - Part 1: PyTorch, PyTorch Geometric, pandas,
  sklearn
  - Part 2: OpenCV, Tesseract OCR, PyMuPDF,
  pytesseract

  Frontend (React):

  - Dashboard: Already built (in aml-dashboard/)
  - Integration needed: Connect Python backend to
   React frontend

  ---
  Current State Assessment

  ✅ What You Have:

  1. Trained GNN model for transaction risk
  scoring
  2. Complete document validation pipeline (OCR →
   analysis → risk scoring)
  3. React dashboard UI with navigation and mock
  data
  4. All required features from hackathon
  requirements

  ⚠️ What's Missing:

  1. Backend API to expose Python functions to
  React
  2. Real-time processing: Currently runs as
  batch scripts
  3. Database: No persistence layer (everything
  is file-based)
  4. Integration: Frontend shows mock data, not
  real GNN/OCR results

  ---
  Your GNN vs. My Earlier Suggestions

  Why Your GNN Approach is Actually GOOD:

  | Aspect         | Your GNN
              | My Rule-Based Suggestion       |
  |----------------|-----------------------------
  ------------|--------------------------------|
  | Speed          | ✅ Fast (trained model, ~1s
  per batch)   | ✅ Faster (~10ms per txn)
  |
  | Accuracy       | ✅ High (F1 ~0.85-0.90)
               | ⚠️ Moderate (depends on rules) |
  | Explainability | ⚠️ Moderate (can show node
  features)    | ✅ Perfect (explicit rules)
  |
  | Novelty        | ✅✅ Very impressive for
  judges           | ⚠️ Basic (expected approach)
     |
  | "Agentic AI"   | ✅ Can claim "AI-powered
  graph analysis" | ❌ Not really "AI"
     |

  Verdict: Keep your GNN! It's more impressive
  than rules. Just need to:
  1. Add explainability: Show which features
  drove the prediction
  2. Make it real-time: Create FastAPI endpoint
  that processes uploads instantly
  3. Visualize the graph: Show network diagram
  with suspicious nodes highlighted

  ---
Part 1: AML Detection Agent (Left Side)

  Pipeline:

  1. Transactions Data (CSV Upload)
  ↓
  2. Two Parallel Paths:

  2. Path A: GNN-Based Detection (Your current implementation):
    - build input graph and subgraph
        - Converts CSV → Graph structure (nodes=accounts, edges=transactions)
      - Creates 22 features per node
      - Extracts 2-hop subgraphs for each account
    - Run it on the weights
        - Loads trained GCN model (best_model_GCN_Champ_V3_PW25_Base.pth)
      - Runs inference on subgraphs
    - Inference → Generates predictions (0 or 1)
    - Output → Account-level risk predictions

  Path B: Rule-Based Agent (Working on it now):
    - Mentioned in diagram as "Rule Based Agent (Working on it now)"
    - This is what I suggested earlier! Looks like your team is already building it
    - Likely implements explicit AML rules for explainability
  3. Output → Merges both GNN and Rule-based results

  ---
  Part 2: Document Assessor Agent (Right Side)

  Three Processing Streams:

  The diagram shows 3 parallel entry points (based on file type):

  Stream 1: PDF → Image Pipeline

  PDF Processor (pdf_pro.py)
      ↓
  Clean and Skew adjustment (img_pro.py: auto_orient + deskew)
      ↓
  Image Processor
      ↓
  OCR and positioning (img_pro.py: ocr_to_json)
      ↓
  Text Processor (text_pro.py)
      ↓
  Output (Risk Score + Issues JSON)

  Stream 2: Direct Image Upload

  Image Processor
      ↓
  OCR and positioning
      ↓
  Text Processor
      ↓
  Output

  Stream 3: Direct Text/JSON Upload

  Text Processor (text_pro.py)
      ↓
  Output

  ---
  Integration Layer: FastAPI Backend

  The diagram shows a FastAPI component that:
  - Receives outputs from both agents
  - Exposes REST API endpoints
  - Serves results to Frontend Dashboard

  Expected API Endpoints:

  # Part 1: Transaction Monitoring
  POST /api/transactions/analyze
    - Input: CSV file
    - Output: { predictions: [...], risk_scores: [...] }

  # Part 2: Document Analysis
  POST /api/documents/analyze
    - Input: PDF/Image file
    - Output: { risk_score: 73, issues: [...] }

  # Cross-Reference
  POST /api/cross-reference
    - Input: { customer_id: "CUST-956783" }
    - Output: { transactions: [...], documents: [...], mismatches: [...] }

  # Reports
  GET /api/reports/generate/{customer_id}
    - Output: PDF report with red flags

  ---
  Frontend Dashboard (Your React App)

  Based on the diagram, the UI should:
  1. Accept Inputs (file uploads)
  2. Call FastAPI endpoints
  3. Display Outputs from both agents
  4. Show Cross-Reference results
  5. Generate PDF Reports

  ---
  Key Insights from the Diagram

  1. Dual-Path Detection (Smart Design!)

  The diagram shows TWO detection methods for Part 1:
  - GNN-based (already built) → High accuracy, data-driven
  - Rule-based (in progress) → Explainable, regulatory compliance

  This is brilliant because:
  - GNN catches complex patterns
  - Rules provide audit trail
  - Combining both gives best of both worlds

  2. Multi-Format Document Support

  The Document Assessor has 3 entry points:
  - PDF files → Full pipeline (convert → clean → OCR → analyze)
  - Images → Skip PDF step (clean → OCR → analyze)
  - Text/JSON → Direct analysis (skip OCR entirely)

  This makes the system flexible and efficient!

  3. FastAPI as Integration Hub

  The diagram shows FastAPI centralizing all outputs, which means:
  - Single API layer for frontend
  - Easy to add more agents later
  - Clean separation of concerns

  ---

 
  