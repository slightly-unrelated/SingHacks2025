1. Simple Navigation

  - Two main sections: "Transaction Monitoring" and "Document Analysis"
  - Basic top bar with title
  - No complex role-based access (just assume single user for demo)

  2. Part 1: Transaction Monitoring (Minimal)

  - Transaction List/Table: Show the 1,000 transactions with key columns
    - Transaction ID, Customer, Amount, Risk Score, Status
    - Sort by risk score (show highest risk first)
  - Click to see details: Modal/panel showing:
    - Transaction data
    - Risk score
    - Why it was flagged (rule violated)
    - Recommended action
  - Filter by risk level: Simple dropdown (All / High / Medium / Low)

  3. Part 2: Document Analysis (Minimal)

  - Upload button: Single file upload
  - Document viewer: Show the PDF/image
  - Analysis results panel:
    - Risk score (big number)
    - List of issues found (critical/warnings)
    - OCR extracted text
  - Approve/Reject buttons

  4. Dashboard Home (Simple Overview)

  - Summary cards:
    - Total high-risk transactions
    - Documents analyzed
    - Critical alerts
  - Recent activity list: Last 10 items

  5. Cross-Reference (The Key Feature)

  Since you don't have Part 1 and Part 2 APIs yet, build this as a placeholder but make it       
  clear in the UI:
  - Simple view: Show "Link Transaction to Document"
  - Customer ID input → Show related transactions + documents
  - Display any mismatches (amounts, dates) in a simple list

  6. PDF Report Generation

  - Single button: "Generate Report"
  - Creates a PDF with:
    - Summary of findings
    - Red flags highlighted
    - Risk scores
  - Download button

  What to SKIP (For Now)

  ❌ Mobile responsive - Desktop only for demo
  ❌ User management/roles - Single user
  ❌ Real-time WebSocket updates - Static data is fine
  ❌ Audit trail - Not essential for demo
  ❌ Settings page - Hardcode configuration
  ❌ Notification center - Too complex
  ❌ Geographic heat maps - Nice to have
  ❌ Charts/graphs - Unless you have time
  ❌ Batch upload - Single file is enough
  ❌ Search functionality - Filter is sufficient
  ❌ Investigation case management - Overkill
  ❌ Email notifications - Not needed
  ❌ Keyboard shortcuts - Not needed
  ❌ Scheduled reports - Not needed

  Absolute Minimum for Judging Criteria

  Based on the hackathon requirements, you MUST have:

  ✅ Visual Design (20%): Clean, professional UI with good UX
  ✅ Objective Achievement (20%): Both Part 1 and Part 2 working
  ✅ Creativity (20%): The cross-reference feature (your differentiator)
  ✅ Technical Depth (20%): Show the AI agents working
  ✅ Presentation (20%): Clear demo flow

  Recommended MVP Structure

  Dashboard
  ├── Home (Overview with 3-4 summary cards)
  ├── Transactions
  │   ├── Table with filters
  │   └── Detail view (modal)
  ├── Documents
  │   ├── Upload
  │   └── Analysis view
  ├── Cross-Reference
  │   └── Simple customer lookup showing both
  └── Generate Report (button that creates PDF)