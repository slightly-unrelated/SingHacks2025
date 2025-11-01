

  Part 1: Real-Time AML Monitoring ΓÇö What You Need to Build

  Looking at the CSV data, here's what the hackathon expects:

  The Transaction Data Contains:

  Each of the 1,000 transactions has rich fields including:
  - Basic info: transaction_id, amounts, currencies, dates
  - Jurisdictions: booking_jurisdiction (HK, SG, CH), regulator (HKMA/SFC, MAS, FINMA)
  - Parties: originator/beneficiary names, accounts, countries
  - SWIFT details: MT103/MT202COV message types, BIC codes, purpose fields
  - Customer info: customer_id, risk_rating (Low/Medium/High), customer_is_pep (Politically Exposed
   Person)
  - Compliance flags:
    - edd_required / edd_performed (Enhanced Due Diligence)
    - travel_rule_complete (FATF Travel Rule compliance)
    - sanctions_screening (none/potential)
    - suspicion_determined_datetime and str_filed_datetime (Suspicious Transaction Reports)
  - FX details: currency conversions, spreads, counterparties
  - Cash tracking: daily_cash_total_customer, daily_cash_txn_count

  What You Need to Build:

  1. Rules Engine

  Create an AI agent that can:
  - Ingest regulatory rules from FINMA, MAS, HKMA websites (or simulate this with predefined rules)
  - Examples of AML rules to check:
    - Large cash deposits: Multiple cash deposits >$10k in 24 hours (structuring)
    - High-risk jurisdictions: Transactions from/to sanctioned countries (IR, RU mentioned in data)
    - PEP transactions: Extra scrutiny for customer_is_pep=TRUE
    - Missing compliance: edd_required=TRUE but edd_performed=FALSE
    - Sanctions hits: sanctions_screening=potential needs investigation
    - FX spread anomalies: Excessive fx_spread_bps (basis points) suggesting markup abuse
    - Travel Rule violations: travel_rule_complete=FALSE
    - Round amount patterns: Exact amounts like 20,000 CHF (appears 3 times) - possible structuring

  2. Real-Time Transaction Analyzer

  Process the 1,000 transactions and:
  - Score each transaction for AML risk (0-100)
  - Flag suspicious patterns (e.g., row 12 and 38 have str_filed_datetime - already flagged as
  suspicious!)
  - Detect behavioral patterns (multiple small transactions same day)
  - Cross-reference against current rules

  3. Alert Generation System

  Create role-specific alerts:
  - Front Office (Relationship Managers): "Client CUST-790068 made 5 cash deposits totaling $30,585
   today - review needed"
  - Compliance: "Transaction ad66338d flagged: potential sanctions hit + missing EDD"
  - Legal: "STR filed for transaction 9db0c15a - high-risk individual from RU"

  Each alert should include:
  - Risk score
  - Specific rule violated
  - Transaction context
  - Recommended action

  4. Remediation Workflow

  Suggest actions like:
  - Block transaction (high risk)
  - Request Enhanced Due Diligence (missing documentation)
  - Escalate to Compliance (sanctions screening hit)
  - File STR (suspicious activity)
  - Request additional documentation (unclear purpose)

  5. Audit Trail

  Log everything:
  - Which rules were checked
  - When alerts were generated
  - Who received alerts
  - What actions were taken
  - Rule version used (for regulatory defensibility)

  Specific Red Flags in Your Data to Detect:

  Looking at the sample rows:
  - Row 12: Already has STR filed (suspicion_determined_datetime populated) - your system should
  catch this pattern
  - Row 38: Another STR filed case
  - Row 9: Customer made 5 cash deposits totaling $30,585 in one day
  - Row 21: High-risk customer + EDD required but not performed
  - Row 20: EDD required but not performed for domiciliary company
  - Row 30: Transaction from Russia (RU) with PEP customer
  - Multiple exact 20,000 CHF transactions (structuring?)

  Example Output:

  Your system should produce alerts like:

  ALERT #1 - HIGH PRIORITY
  Transaction: db78512e-524f-41df-ae9c-d254556670f9
  Customer: CUST-956783 (Medium Risk, Domiciliary Company)
  Rule Violated: Cash Structuring (FINMA Circular 2016/7)
  Details: 5 cash deposits totaling JPY 30,496.46 within 24 hours
  Risk Score: 87/100
  Action Required: File STR, Review account activity
  Assigned To: Compliance Team
  STR Status: FILED (2024-11-01)

  The "Agentic AI" Part:

  Use AI agents to:
  - Parse unstructured regulatory circulars and extract rules
  - Reason about complex patterns (not just threshold checks)
  - Adapt to new rules without reprogramming
  - Explain why transactions are flagged (for audit defense)
  - Prioritize alerts based on risk severity





