# Part 2: Document & Image Corroboration  What You Need to Build

This PDF is a **Client Corroboration Statement** from Helvetia Private Bank AG - the type of document compliance teams need to verify for AML/KYC purposes.

## What's in This Document:

Looking at page 1, I can see:
- **Client information**: John A. Müller, Zürich address, Swiss/German nationality
- **Transaction details**: Source of Wealth Corroboration related to a company sale (CHF 1,250,000)
- **Reference documents**:
  - Share Purchase Agreement (SPA) - Annex A
  - Bank statements - Annex B
  - Dividend vouchers - Annex C
  - Board resolution - Annex D
- **Witnesses**: Mr. I. Frei & Ms. S. Schmid
- **Bank contact details**
- **Document reference table** with dates and reference numbers
- **Stamp and signature section**

## What Part 2 Wants You to Build:

### 1. Document Processing Engine

Your AI system needs to:
- **Extract text via OCR** (this is a scanned document, notice the grainy/noisy quality)
- **Parse structured data**:
  - Client name: "John A. Müller"
  - Transaction amount: "CHF 1,250,000"
  - Date: "30.10.2023"
  - Reference numbers: "Ref: CH-2025/10/0307"
  - Account number: "ACCOUNT No. 00000"
  - Referenced annexes: A, B, C, D, E
- **Handle multiple formats**: PDF, images, text documents

### 2. Format Validation System

Detect errors and inconsistencies like:

**In this specific document, your system should catch:**
- **Spelling errors**: "Gliessenstrasse" (should be verified against Swiss addresses)
- **Formatting issues**:
  - Inconsistent spacing (notice the gaps in the text)
  - Poor scan quality (grainy background)
  - Alignment issues
- **Missing information**:
  - Account number shown as "00000" (likely placeholder/redacted)
  - Some fields appear incomplete
- **Date consistency**:
  - Multiple dates referenced (30.10.2023, 31.10.2023, Q3 2023, 2024-05-18)
  - Check if dates are logical (e.g., tax assessment dated 2024-05-18 but transaction in Oct 2023?)
- **Reference integrity**:
  - Check if all referenced annexes (A, B, C, D, E) are actually attached
  - Verify document table matches actual attachments
- **Signature/stamp validation**:
  - Stamp says "HELVETIA PRIVATE BANK - RECEIVED 31.10.2025" (future date! Red flag!)
  - Check if signature is present (compliance requirement)

### 3. Image Analysis Engine

**This is where the advanced AI comes in:**

a) **Authenticity Verification**:
- **Reverse image search**: Check if bank logo/stamp images are stolen from internet
- **Template matching**: Does this match standard Helvetia Private Bank letterhead?

b) **AI-Generated Detection**:
- Analyze if any images/signatures are AI-generated synthetics
- Look for telltale signs of synthetic documents

c) **Tampering Detection**:
- **Metadata analysis**:
  - Check PDF creation date vs. document date
  - Examine EXIF data for modification history
  - Look for multiple authors/editing tools
- **Pixel-level forensics**:
  - Detect if numbers have been altered (e.g., amount changed from CHF 125,000 to CHF 1,250,000)
  - Check for copy-paste artifacts
  - Analyze compression artifacts that suggest editing
  - Look for inconsistent fonts (suggesting text replacement)
- **Stamp/signature analysis**:
  - Is the stamp digitally placed or original?
  - Signature consistency across pages

### 4. Risk Scoring & Reporting

Generate a report like:

```
DOCUMENT RISK ASSESSMENT REPORT
Document: Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.pdf
Analysis Date: 2025-11-01
Overall Risk Score: 73/100 (HIGH RISK)

CRITICAL ISSUES FOUND:
L Date Anomaly: Stamp dated "31.10.2025" (future date - impossible)
L Account Number: Shows "00000" (invalid/placeholder)
L Missing Annexes: Referenced Annexes A-E not found in document

WARNING FLAGS:
  Scan Quality: Poor quality suggests re-scanning or photocopying
  Date Inconsistency: Tax assessment (2024-05-18) dated after transaction (2023-10-30)
  Incomplete Fields: Several fields appear partially filled

VALIDATION RESULTS:
 OCR Confidence: 89% (acceptable)
 Client Name Format: Valid
 Amount Format: Valid (CHF 1,250,000)
 Reference Check: 5 missing annexes

RECOMMENDED ACTIONS:
1. Request original (non-scanned) documents
2. Verify stamp date with bank (future date impossible)
3. Request all referenced annexes (A, B, C, D, E)
4. Validate account number (currently shows placeholder)
5. Enhanced Due Diligence required before approval

AUDIT TRAIL:
- OCR performed: 2025-11-01 10:23:45
- Image forensics: 2025-11-01 10:24:12
- Risk scoring: 2025-11-01 10:24:30
- Analyst: AI Agent (Document-Corroboration-v1)
```

### 5. Real-Time Feedback System

As a compliance officer uploads the document:
- **Live validation**: Show errors as they're detected
- **Interactive highlighting**: Click to see specific issues
- **Severity indicators**: Color-coded (red/yellow/green)
- **Suggested fixes**: "Date appears to be in future - please verify"

## Specific Issues to Detect in This Sample PDF:

Your AI should flag these issues in the provided document:

1. **CRITICAL: Future date stamp** (31.10.2025) - impossible/fraudulent
2. **Missing annexes** - Document references Annexes A, B, C, D, E but they're not attached
3. **Invalid account number** - "00000" is clearly a placeholder
4. **Date timeline issues** - Tax assessment from 2024 for 2023 transaction
5. **Poor scan quality** - Suggests document has been copied/re-scanned (manipulation?)
6. **Inconsistent formatting** - Spacing and alignment issues throughout
7. **Incomplete contact info** - Email shown as "john.mueller@example.com" (example.com is fake)

## The "Agentic AI" Part for Part 2:

Use AI agents to:
- **Understand context**: Know what a "Source of Wealth" document should contain
- **Cross-reference**: Check if amounts match across different sections
- **Reason about anomalies**: "This date is in the future - likely error or fraud"
- **Learn document templates**: Understand what legitimate bank documents look like
- **Provide explanations**: Tell compliance officers WHY something is flagged

## Technical Implementation Ideas:

1. **OCR**: Use Tesseract, Google Vision API, or Claude's vision capabilities
2. **Image forensics**:
   - Reverse search: Google Images API, TinEye
   - AI detection: Check for GAN artifacts, unnatural patterns
   - Tampering: ELA (Error Level Analysis), metadata extraction (ExifTool)
3. **Format validation**: NLP to check grammar, regex for formats, template matching
4. **Risk scoring**: Weighted algorithm based on issue severity

## Expected Deliverable:

A system where you:
1. Upload the PDF
2. Get instant analysis showing all the red flags above
3. See visual highlights on the document showing problematic areas
4. Receive an actionable risk score with remediation steps
5. Get an audit trail proving you did proper due diligence

**The Goal**: Turn a 30-minute manual document review into a 30-second automated scan that catches MORE issues than a human would.
