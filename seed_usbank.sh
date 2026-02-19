#!/bin/bash
# Seed UAT test data for US Bank (US Bancorp) — all 7 steps
# Usage: bash seed_usbank.sh [BASE_URL]
BASE="${1:-https://business-transformation-architect.onrender.com}"
API="$BASE/api"

post() {
  local url="$1"
  local data="$2"
  curl -s -X POST "$url" -H 'Content-Type: application/json' -d "$data"
}

put() {
  local url="$1"
  local data="$2"
  curl -s -X PUT "$url" -H 'Content-Type: application/json' -d "$data"
}

echo "=== Seeding UAT data for US Bank at $BASE ==="

# Reset existing data
echo -e "\n--- Resetting all data ---"
post "$API/step1/reset-data" '{}'
echo " done"

# ============================================================
# Organization
# ============================================================
echo -e "\n--- Organization ---"
post "$API/step1/organization" '{"name":"US Bancorp","industry":"Banking & Financial Services","sub_industry":"Diversified Banking","competitor_1_name":"JPMorgan Chase","competitor_2_name":"Wells Fargo"}'

# ============================================================
# Step 1: Business Performance Dashboard
# ============================================================
echo -e "\n--- Step 1: Business Units ---"
post "$API/step1/business-units" '{"name":"US Bancorp","description":"US Bancorp — parent holding company"}'
BU2=$(post "$API/step1/business-units" '{"name":"Consumer & Business Banking","description":"Retail banking, consumer loans, small business banking, branch network"}')
BU3=$(post "$API/step1/business-units" '{"name":"Wealth Management & Investment Services","description":"Private banking, asset management, trust services, brokerage"}')
BU4=$(post "$API/step1/business-units" '{"name":"Payment Services","description":"Merchant processing, corporate payments, prepaid cards, Elavon"}')
BU5=$(post "$API/step1/business-units" '{"name":"Treasury & Corporate Support","description":"Treasury management, capital markets, institutional services"}')

BU_LIST=$(curl -s "$API/step1/business-units")
USB_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next((b['id'] for b in data if b['name']=='US Bancorp'),data[0]['id']))")
CBB_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if 'Consumer' in b['name']))")
WM_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if 'Wealth' in b['name']))")
PS_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if 'Payment' in b['name']))")
TC_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if 'Treasury' in b['name']))")

echo "BU IDs: USB=$USB_BU_ID CBB=$CBB_BU_ID WM=$WM_BU_ID PS=$PS_BU_ID TC=$TC_BU_ID"

echo -e "\n--- Step 1: Revenue Splits ---"
# Revenue by business segment (in $M)
post "$API/step1/revenue-splits" "{\"business_unit_id\":$CBB_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Consumer & Business Banking\",\"revenue\":9842,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$CBB_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Consumer & Business Banking\",\"revenue\":9518,\"period\":\"2024\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$CBB_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Consumer & Business Banking\",\"revenue\":9201,\"period\":\"2023\"}"

post "$API/step1/revenue-splits" "{\"business_unit_id\":$WM_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Wealth Management\",\"revenue\":3845,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$WM_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Wealth Management\",\"revenue\":3621,\"period\":\"2024\"}"

post "$API/step1/revenue-splits" "{\"business_unit_id\":$PS_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Payment Services\",\"revenue\":7218,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$PS_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Payment Services\",\"revenue\":6890,\"period\":\"2024\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$PS_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Payment Services\",\"revenue\":6542,\"period\":\"2023\"}"

post "$API/step1/revenue-splits" "{\"business_unit_id\":$TC_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Treasury & Corporate\",\"revenue\":4295,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$TC_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Treasury & Corporate\",\"revenue\":4102,\"period\":\"2024\"}"

# Regional splits
post "$API/step1/revenue-splits" "{\"business_unit_id\":$USB_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Midwest\",\"revenue\":8450,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$USB_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"West Coast\",\"revenue\":6320,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$USB_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Northeast\",\"revenue\":5280,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$USB_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"South & Southeast\",\"revenue\":3150,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$USB_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"International (Elavon)\",\"revenue\":2000,\"period\":\"2025\"}"

# Segment splits
post "$API/step1/revenue-splits" "{\"business_unit_id\":$USB_BU_ID,\"dimension\":\"segment\",\"dimension_value\":\"Net Interest Income\",\"revenue\":14820,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$USB_BU_ID,\"dimension\":\"segment\",\"dimension_value\":\"Fee & Commission Income\",\"revenue\":7680,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$USB_BU_ID,\"dimension\":\"segment\",\"dimension_value\":\"Payment Processing Revenue\",\"revenue\":2700,\"period\":\"2025\"}"

echo " done"

echo -e "\n--- Step 1: Ops Efficiency ---"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$USB_BU_ID,\"metric_name\":\"Net Profit Margin\",\"metric_value\":0.2414,\"target_value\":0.27,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$USB_BU_ID,\"metric_name\":\"Operating Margin\",\"metric_value\":0.3019,\"target_value\":0.33,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$USB_BU_ID,\"metric_name\":\"Return on Equity (ROE)\",\"metric_value\":0.1161,\"target_value\":0.14,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$USB_BU_ID,\"metric_name\":\"Return on Assets (ROA)\",\"metric_value\":0.011,\"target_value\":0.013,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$USB_BU_ID,\"metric_name\":\"EPS\",\"metric_value\":4.86,\"target_value\":5.50,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$USB_BU_ID,\"metric_name\":\"Net Interest Margin\",\"metric_value\":0.0281,\"target_value\":0.032,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$USB_BU_ID,\"metric_name\":\"Efficiency Ratio\",\"metric_value\":0.612,\"target_value\":0.55,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$USB_BU_ID,\"metric_name\":\"CET1 Capital Ratio\",\"metric_value\":0.102,\"target_value\":0.11,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$USB_BU_ID,\"metric_name\":\"Dividend Yield\",\"metric_value\":0.0388,\"target_value\":0.04,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$USB_BU_ID,\"metric_name\":\"Beta\",\"metric_value\":1.045,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$USB_BU_ID,\"metric_name\":\"Revenue Growth (YoY)\",\"metric_value\":0.034,\"target_value\":0.05,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$USB_BU_ID,\"metric_name\":\"Non-Performing Assets Ratio\",\"metric_value\":0.0042,\"target_value\":0.003,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$USB_BU_ID,\"metric_name\":\"Loan-to-Deposit Ratio\",\"metric_value\":0.72,\"target_value\":0.75,\"period\":\"TTM\"}"

# Payment Services specific metrics
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$PS_BU_ID,\"metric_name\":\"Revenue Growth (YoY)\",\"metric_value\":0.048,\"target_value\":0.06,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$PS_BU_ID,\"metric_name\":\"Payment Volume Growth\",\"metric_value\":0.072,\"target_value\":0.08,\"period\":\"TTM\"}"

echo " done"

echo -e "\n--- Step 1: Competitors ---"
post "$API/step1/competitors" '{"name":"JPMorgan Chase","ticker":"JPM","market_share":0.15,"revenue":177600,"profit_margin":0.334,"operating_margin":0.41,"return_on_equity":0.17,"return_on_assets":0.013,"pe_ratio":12.8,"eps":19.75,"market_cap_value":690000,"strengths":"Largest US bank by assets, leading investment bank, massive technology spend ($15B+/yr), strongest brand in banking","weaknesses":"Regulatory scrutiny, complexity of global operations, litigation exposure","data_source":"simulated"}'
post "$API/step1/competitors" '{"name":"Wells Fargo","ticker":"WFC","market_share":0.10,"revenue":82600,"profit_margin":0.255,"operating_margin":0.31,"return_on_equity":0.12,"return_on_assets":0.011,"pe_ratio":13.1,"eps":5.14,"market_cap_value":218000,"strengths":"Largest US bank by branch count, strong consumer deposit base, improving efficiency","weaknesses":"Ongoing regulatory consent orders, asset cap still in place, reputational damage from scandals","data_source":"simulated"}'
post "$API/step1/competitors" '{"name":"PNC Financial","ticker":"PNC","market_share":0.06,"revenue":22400,"profit_margin":0.268,"operating_margin":0.34,"return_on_equity":0.12,"return_on_assets":0.011,"pe_ratio":14.2,"eps":13.20,"market_cap_value":85000,"strengths":"Strong mid-Atlantic presence, BBVA USA acquisition integration complete, growing treasury management","weaknesses":"Limited West Coast presence, smaller technology budget than top 4 banks, commercial real estate exposure","data_source":"simulated"}'

echo " done"

echo -e "\n--- Step 1: Data URLs ---"
post "$API/step1/urls" '{"url":"https://www.usbank.com/about-us-bank/investor-relations.html","label":"US Bancorp Investor Relations","url_type":"external"}'
post "$API/step1/urls" '{"url":"https://ir.usbank.com/annual-reports","label":"USB Annual Report 2025","url_type":"external"}'
post "$API/step1/urls" '{"url":"https://www.fdic.gov/analysis/quarterly-banking-profile","label":"FDIC Quarterly Banking Profile","url_type":"external"}'

echo " done"

# ============================================================
# Step 2: Value Stream Analysis
# ============================================================
echo -e "\n--- Step 2: Value Streams ---"
VS1=$(post "$API/step2/value-streams" "{\"business_unit_id\":$CBB_BU_ID,\"name\":\"Digital Mortgage Origination\",\"description\":\"End-to-end mortgage application from online pre-qualification through underwriting to closing\"}")
VS1_ID=$(echo "$VS1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

VS2=$(post "$API/step2/value-streams" "{\"business_unit_id\":$PS_BU_ID,\"name\":\"Merchant Payment Processing\",\"description\":\"Transaction lifecycle from merchant swipe/tap through settlement via Elavon platform\"}")
VS2_ID=$(echo "$VS2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

VS3=$(post "$API/step2/value-streams" "{\"business_unit_id\":$CBB_BU_ID,\"name\":\"Digital Account Opening\",\"description\":\"New customer onboarding from application through KYC/AML verification to funded account\"}")
VS3_ID=$(echo "$VS3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

VS4=$(post "$API/step2/value-streams" "{\"business_unit_id\":$WM_BU_ID,\"name\":\"Wealth Advisory Onboarding\",\"description\":\"High-net-worth client intake from initial consultation through portfolio construction and compliance review\"}")
VS4_ID=$(echo "$VS4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "VS IDs: Mortgage=$VS1_ID, Payments=$VS2_ID, AccountOpen=$VS3_ID, Wealth=$VS4_ID"

echo -e "\n--- Step 2: Value Stream Steps (Digital Mortgage) ---"
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":1,"step_name":"Online Pre-Qualification","description":"Customer enters income, assets, credit info for instant pre-qual estimate","step_type":"trigger","process_time_hours":0.5,"wait_time_hours":0,"resources":"Digital Platform, Credit API"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":2,"step_name":"Full Application & Document Upload","description":"Customer completes full application, uploads pay stubs, tax returns, bank statements","step_type":"process","process_time_hours":2,"wait_time_hours":24,"resources":"Digital Platform, OCR System"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":3,"step_name":"Automated Underwriting","description":"DU/LP automated underwriting system analyzes application against guidelines","step_type":"process","process_time_hours":0.25,"wait_time_hours":2,"resources":"AUS System, Credit Bureau APIs"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":4,"step_name":"Manual Underwriter Review","description":"Underwriter reviews exceptions, conditions, and complex cases","step_type":"decision","process_time_hours":4,"wait_time_hours":48,"is_bottleneck":1,"notes":"Underwriter capacity is primary bottleneck — 45-day avg close time vs 30-day target","resources":"Underwriting Team"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":5,"step_name":"Appraisal & Title","description":"Order and receive property appraisal and title search","step_type":"process","process_time_hours":2,"wait_time_hours":168,"resources":"Appraisal Vendors, Title Company"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":6,"step_name":"Conditions & Clear to Close","description":"Resolve remaining conditions, verify final documents, issue CTC","step_type":"decision","process_time_hours":3,"wait_time_hours":24,"resources":"Loan Processor, Underwriter"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":7,"step_name":"Closing & Funding","description":"E-signing or in-person closing, fund disbursement, recording","step_type":"delivery","process_time_hours":1,"wait_time_hours":48,"resources":"Closing Team, Title Agent"}'

echo -e "\n--- Step 2: Value Stream Steps (Merchant Payments) ---"
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":1,"step_name":"Card Tap/Swipe/Insert","description":"Cardholder presents payment at merchant POS terminal","step_type":"trigger","process_time_hours":0.001,"wait_time_hours":0,"resources":"POS Terminal, Elavon Gateway"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":2,"step_name":"Authorization Request","description":"Transaction routed to card network (Visa/MC) for issuer authorization","step_type":"process","process_time_hours":0.0003,"wait_time_hours":0,"resources":"Payment Gateway, Card Networks"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":3,"step_name":"Fraud Screening","description":"Real-time fraud detection scoring and rules evaluation","step_type":"decision","process_time_hours":0.0001,"wait_time_hours":0,"resources":"Fraud Detection AI, Rules Engine"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":4,"step_name":"Batch Settlement","description":"End-of-day batch processing, netting, and settlement file creation","step_type":"process","process_time_hours":2,"wait_time_hours":12,"is_bottleneck":1,"notes":"T+1 settlement standard — moving toward real-time","resources":"Settlement Engine, ACH Network"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":5,"step_name":"Merchant Funding","description":"Net settlement amount deposited to merchant bank account","step_type":"delivery","process_time_hours":0.5,"wait_time_hours":24,"resources":"ACH, Merchant Account System"}'

echo -e "\n--- Step 2: Value Stream Steps (Account Opening) ---"
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":1,"step_name":"Online Application Start","description":"Customer selects account type, enters personal information","step_type":"trigger","process_time_hours":0.25,"wait_time_hours":0,"resources":"Digital Banking Platform"}'
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":2,"step_name":"Identity Verification","description":"KYC checks: ID scan, SSN verification, OFAC/CIP screening","step_type":"process","process_time_hours":0.05,"wait_time_hours":0.5,"resources":"KYC/AML Platform, LexisNexis"}'
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":3,"step_name":"Credit Check & Risk Assessment","description":"Soft credit pull, ChexSystems check for banking history","step_type":"decision","process_time_hours":0.02,"wait_time_hours":0.5,"resources":"Credit Bureau APIs, ChexSystems"}'
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":4,"step_name":"Account Provisioning","description":"Create account, assign account number, set up online/mobile access","step_type":"process","process_time_hours":0.05,"wait_time_hours":0.5,"resources":"Core Banking System"}'
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":5,"step_name":"Initial Funding","description":"Customer links external account or makes initial deposit","step_type":"delivery","process_time_hours":0.1,"wait_time_hours":24,"resources":"ACH, Debit Network"}'

# Recalculate metrics
post "$API/step2/value-streams/$VS1_ID/recalculate" '{}'
post "$API/step2/value-streams/$VS2_ID/recalculate" '{}'
post "$API/step2/value-streams/$VS3_ID/recalculate" '{}'

echo -e "\n--- Step 2: Value Stream Levers ---"
post "$API/step2/levers" "{\"value_stream_id\":$VS1_ID,\"lever_type\":\"efficiency\",\"opportunity\":\"AI-powered automated underwriting to handle 80% of conforming loans without manual review\",\"current_state\":\"60% of applications require manual underwriter review, avg 48hr wait\",\"target_state\":\"Only 20% need manual review via AI risk models and automated doc verification\",\"impact_estimate\":\"high\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS1_ID,\"lever_type\":\"experience\",\"opportunity\":\"Real-time application status with AI-powered document coaching\",\"current_state\":\"Customers call loan officers for status updates, unclear document requirements\",\"target_state\":\"Push notifications on status changes, AI suggests fixes for rejected documents\",\"impact_estimate\":\"medium\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS2_ID,\"lever_type\":\"efficiency\",\"opportunity\":\"Move from T+1 to real-time settlement using RTP/FedNow\",\"current_state\":\"T+1 batch settlement via ACH\",\"target_state\":\"Real-time settlement for eligible merchants via FedNow rails\",\"impact_estimate\":\"high\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS2_ID,\"lever_type\":\"effectiveness\",\"opportunity\":\"ML-based adaptive fraud scoring reducing false declines by 30%\",\"current_state\":\"Rule-based fraud with 2.1% false decline rate\",\"target_state\":\"ML ensemble model with 1.4% false decline rate, improving merchant experience\",\"impact_estimate\":\"high\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS3_ID,\"lever_type\":\"experience\",\"opportunity\":\"60-second account opening with instant virtual debit card\",\"current_state\":\"Average 8 minutes to open account, 5-7 days for debit card delivery\",\"target_state\":\"Sub-60s opening with instant virtual card in Apple/Google Wallet\",\"impact_estimate\":\"medium\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS3_ID,\"lever_type\":\"growth\",\"opportunity\":\"Cross-sell credit card and savings during onboarding flow\",\"current_state\":\"No cross-sell during account opening\",\"target_state\":\"AI-recommended products presented post-funding with one-click signup\",\"impact_estimate\":\"medium\"}"

echo " done"

# ============================================================
# Step 3: SWOT to TOWS Action Engine
# ============================================================
echo -e "\n--- Step 3: SWOT Entries ---"
# Strengths
S1=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"strength\",\"description\":\"#1 US corporate payments provider — Elavon processes \$500B+ annually with growing merchant base\",\"severity\":\"high\",\"confidence\":\"high\"}")
S1_ID=$(echo "$S1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

S2=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"strength\",\"description\":\"Top 5 US bank by assets (\$675B) with diversified revenue across 4 business lines\",\"severity\":\"high\",\"confidence\":\"high\"}")
S2_ID=$(echo "$S2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

S3=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"strength\",\"description\":\"Strong digital banking platform — 75% of consumer transactions now digital, award-winning mobile app\",\"severity\":\"high\",\"confidence\":\"high\"}")
S3_ID=$(echo "$S3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

S4=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"strength\",\"description\":\"Conservative credit culture with consistently below-peer charge-off rates (0.42% vs 0.58% peer avg)\",\"severity\":\"medium\",\"confidence\":\"high\"}")
S4_ID=$(echo "$S4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Weaknesses
W1=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"weakness\",\"description\":\"Efficiency ratio (61.2%) lags top peers JPM (55%) and PNC (58%) — higher cost base\",\"severity\":\"high\",\"confidence\":\"high\"}")
W1_ID=$(echo "$W1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

W2=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"weakness\",\"description\":\"Commercial real estate (CRE) exposure at 18% of loan book — office sector stress increasing\",\"severity\":\"high\",\"confidence\":\"medium\"}")
W2_ID=$(echo "$W2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

W3=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"weakness\",\"description\":\"Technology spend (\$3.5B) is 25% of JPM (\$15B) — limits AI/ML and cloud transformation velocity\",\"severity\":\"medium\",\"confidence\":\"high\"}")
W3_ID=$(echo "$W3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

W4=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"weakness\",\"description\":\"Limited international presence outside Elavon — geographic concentration in Midwest/West\",\"severity\":\"medium\",\"confidence\":\"high\"}")
W4_ID=$(echo "$W4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Opportunities
O1=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"opportunity\",\"description\":\"Embedded finance & BaaS: white-label banking services for fintechs and non-bank brands\",\"severity\":\"high\",\"confidence\":\"medium\"}")
O1_ID=$(echo "$O1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

O2=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"opportunity\",\"description\":\"Real-time payments (RTP/FedNow) adoption creating new revenue streams in instant settlement\",\"severity\":\"high\",\"confidence\":\"high\"}")
O2_ID=$(echo "$O2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

O3=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"opportunity\",\"description\":\"Gen AI for operational efficiency: automate loan processing, compliance, customer service (est. \$800M cost savings)\",\"severity\":\"high\",\"confidence\":\"medium\"}")
O3_ID=$(echo "$O3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

O4=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"opportunity\",\"description\":\"Open banking APIs to attract fintech partnerships and build ecosystem revenue\",\"severity\":\"medium\",\"confidence\":\"medium\"}")
O4_ID=$(echo "$O4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Threats
T1=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"threat\",\"description\":\"Fintech disruption: neobanks (Chime, SoFi) capturing younger demographics with lower fees\",\"severity\":\"high\",\"confidence\":\"high\"}")
T1_ID=$(echo "$T1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

T2=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"threat\",\"description\":\"Rising interest rate environment compressing net interest margin while increasing credit losses\",\"severity\":\"high\",\"confidence\":\"medium\"}")
T2_ID=$(echo "$T2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

T3=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"threat\",\"description\":\"Increased regulatory capital requirements (Basel III endgame) reducing lending capacity\",\"severity\":\"high\",\"confidence\":\"high\"}")
T3_ID=$(echo "$T3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

T4=$(post "$API/step3/swot" "{\"business_unit_id\":$USB_BU_ID,\"category\":\"threat\",\"description\":\"Cybersecurity risk: major bank breaches in industry increasing regulatory expectations and costs\",\"severity\":\"high\",\"confidence\":\"high\"}")
T4_ID=$(echo "$T4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "SWOT IDs: S=$S1_ID,$S2_ID,$S3_ID,$S4_ID W=$W1_ID,$W2_ID,$W3_ID,$W4_ID O=$O1_ID,$O2_ID,$O3_ID,$O4_ID T=$T1_ID,$T2_ID,$T3_ID,$T4_ID"

echo -e "\n--- Step 3: TOWS Actions ---"
TOWS1=$(post "$API/step3/tows" "{\"strategy_type\":\"SO\",\"swot_entry_1_id\":$S1_ID,\"swot_entry_2_id\":$O2_ID,\"action_description\":\"Leverage Elavon payment network to offer instant merchant settlement via FedNow — premium pricing for real-time access to funds\",\"priority\":\"critical\",\"impact_score\":9,\"rationale\":\"Payment leadership + RTP = first-mover advantage in real-time merchant settlement\"}")
TOWS1_ID=$(echo "$TOWS1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS2=$(post "$API/step3/tows" "{\"strategy_type\":\"SO\",\"swot_entry_1_id\":$S3_ID,\"swot_entry_2_id\":$O1_ID,\"action_description\":\"Build embedded finance platform using digital banking strengths to power BaaS for fintech partners\",\"priority\":\"high\",\"impact_score\":8,\"rationale\":\"Digital platform maturity enables white-label offering at lower marginal cost\"}")
TOWS2_ID=$(echo "$TOWS2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS3=$(post "$API/step3/tows" "{\"strategy_type\":\"WO\",\"swot_entry_1_id\":$W1_ID,\"swot_entry_2_id\":$O3_ID,\"action_description\":\"Deploy Gen AI across operations to reduce efficiency ratio from 61% to 55% — automate underwriting, compliance, customer service\",\"priority\":\"critical\",\"impact_score\":10,\"rationale\":\"AI addresses cost weakness while creating competitive advantage\"}")
TOWS3_ID=$(echo "$TOWS3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS4=$(post "$API/step3/tows" "{\"strategy_type\":\"ST\",\"swot_entry_1_id\":$S4_ID,\"swot_entry_2_id\":$T2_ID,\"action_description\":\"Use conservative credit culture as competitive advantage — tighten CRE exposure while competitors face losses, gain share in quality originations\",\"priority\":\"high\",\"impact_score\":7,\"rationale\":\"Credit discipline in a downturn becomes a growth lever\"}")
TOWS4_ID=$(echo "$TOWS4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS5=$(post "$API/step3/tows" "{\"strategy_type\":\"WT\",\"swot_entry_1_id\":$W3_ID,\"swot_entry_2_id\":$T1_ID,\"action_description\":\"Accelerate cloud migration and API-first architecture to compete with fintechs despite smaller tech budget — focus on highest-impact digital journeys\",\"priority\":\"high\",\"impact_score\":8,\"rationale\":\"Prioritize tech spend on customer-facing digital over legacy modernization\"}")
TOWS5_ID=$(echo "$TOWS5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS6=$(post "$API/step3/tows" "{\"strategy_type\":\"ST\",\"swot_entry_1_id\":$S2_ID,\"swot_entry_2_id\":$T3_ID,\"action_description\":\"Optimize balance sheet to exceed Basel III requirements with margin — diversified revenue mix reduces capital intensity vs lending-heavy peers\",\"priority\":\"medium\",\"impact_score\":6,\"rationale\":\"Diversification provides natural capital efficiency advantage\"}")
TOWS6_ID=$(echo "$TOWS6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "TOWS IDs: $TOWS1_ID,$TOWS2_ID,$TOWS3_ID,$TOWS4_ID,$TOWS5_ID,$TOWS6_ID"

# ============================================================
# Step 4: Four-Layer Strategy & Strategic OKRs
# ============================================================
echo -e "\n--- Step 4: Strategy Inputs ---"
post "$API/step4/inputs" '{"input_type":"business_strategy","title":"USB 2025 Strategic Plan — Investor Day Presentation","content":"Drive top-quartile returns through: (1) Payment Services growth via Elavon expansion and real-time payments, (2) Efficiency improvement targeting 55% ratio via technology and process optimization, (3) Deepening consumer digital engagement, (4) Disciplined credit management through the cycle."}'
post "$API/step4/inputs" '{"input_type":"digital_strategy","title":"USB Digital Transformation Roadmap 2025-2027","content":"Cloud-first architecture migration (target 70% workloads by 2027). API-first platform enabling embedded finance. AI/ML in fraud, credit decisions, and customer service. Mobile-first design for all consumer and small business journeys."}'
post "$API/step4/inputs" '{"input_type":"data_strategy","title":"USB Enterprise Data Strategy","content":"Unified customer data platform (CDP) across all business lines. Real-time data streaming for fraud and risk. Data mesh architecture for business unit autonomy. ML feature store for cross-team model sharing. Strict data governance and lineage."}'
post "$API/step4/inputs" '{"input_type":"gen_ai_strategy","title":"USB Gen AI Enterprise Strategy","content":"Deploy Gen AI for: (1) Automated loan document processing and underwriting assistance, (2) Customer service chatbot handling 60% of Tier 1 inquiries, (3) Compliance monitoring and SAR generation, (4) Code generation for developer productivity. Guardrails: no Gen AI in final credit decisions, human-in-the-loop for regulatory outputs."}'
post "$API/step4/inputs" '{"input_type":"competitor_strategy","title":"Competitive Intelligence Summary","content":"JPM investing $15B in tech with focus on AI-first banking. Wells Fargo accelerating digital under new CEO. Chime/SoFi growing deposits via fee-free banking targeting <35 demographics. Square/Block expanding business banking. Key differentiator needed: payments + digital integration."}'
post "$API/step4/inputs" '{"input_type":"document_reference","title":"OCC Examination Report Q3 2025","content":"Key findings: Satisfactory rating maintained. Recommendations to strengthen model risk management for AI/ML models in credit. CRE concentration monitoring required. Cybersecurity program meets expectations but needs continuous improvement for emerging threats.","file_name":"occ_exam_q3_2025.pdf"}'
post "$API/step4/inputs" '{"input_type":"document_reference","title":"McKinsey Banking Industry Report 2025","content":"US banking industry faces margin compression, fintech competition, and regulatory tightening. Winners will be banks that successfully deploy AI at scale, build ecosystem partnerships, and maintain credit discipline. Estimated $200B industry cost savings from Gen AI by 2030.","file_name":"mckinsey_banking_2025.pdf"}'

echo -e "\n--- Step 4: Strategies ---"
STR1=$(post "$API/step4/strategies" "{\"layer\":\"business\",\"name\":\"Real-Time Payment Leadership\",\"description\":\"Become the #1 bank for real-time payments — offer instant merchant settlement, consumer P2P, and corporate treasury via FedNow/RTP integration across all channels.\",\"tows_action_id\":$TOWS1_ID,\"risk_level\":\"medium\",\"risks\":\"Network adoption pace, pricing pressure, fraud risk in instant payments\"}")
STR1_ID=$(echo "$STR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR2=$(post "$API/step4/strategies" "{\"layer\":\"business\",\"name\":\"Embedded Finance & BaaS Platform\",\"description\":\"Launch USB embedded finance platform providing banking-as-a-service to fintechs, retailers, and enterprise clients via APIs.\",\"tows_action_id\":$TOWS2_ID,\"risk_level\":\"medium\",\"risks\":\"Partner credit risk, regulatory scrutiny of BaaS, technology integration complexity\"}")
STR2_ID=$(echo "$STR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR3=$(post "$API/step4/strategies" "{\"layer\":\"digital\",\"name\":\"AI-First Operations Transformation\",\"description\":\"Deploy Gen AI and ML across the enterprise to reduce efficiency ratio from 61% to 55% by 2027 through automation of underwriting, compliance, and customer service.\",\"tows_action_id\":$TOWS3_ID,\"risk_level\":\"high\",\"risks\":\"Model risk, regulatory acceptance of AI in banking, change management, bias in credit models\"}")
STR3_ID=$(echo "$STR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR4=$(post "$API/step4/strategies" "{\"layer\":\"data\",\"name\":\"Unified Customer Intelligence Platform\",\"description\":\"Build enterprise-wide customer data platform (CDP) unifying profiles across all 4 business lines to enable personalization, cross-sell, and risk management.\",\"risk_level\":\"medium\",\"risks\":\"Data privacy regulations, integration complexity, organizational silos, data quality\"}")
STR4_ID=$(echo "$STR4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR5=$(post "$API/step4/strategies" "{\"layer\":\"gen_ai\",\"name\":\"Gen AI Copilot for Banking Operations\",\"description\":\"Build internal Gen AI copilot for loan officers, compliance analysts, and relationship managers — automate document review, generate reports, surface insights.\",\"risk_level\":\"high\",\"risks\":\"Hallucination in financial contexts, regulatory compliance of AI outputs, employee adoption\"}")
STR5_ID=$(echo "$STR5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR6=$(post "$API/step4/strategies" "{\"layer\":\"digital\",\"name\":\"Next-Gen Digital Banking Experience\",\"description\":\"Rebuild consumer and small business digital banking with mobile-first UX, instant account opening, personalized financial coaching, and seamless payment integration.\",\"tows_action_id\":$TOWS5_ID,\"risk_level\":\"low\",\"risks\":\"Execution timeline, customer migration, feature parity with fintechs\"}")
STR6_ID=$(echo "$STR6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Strategy IDs: $STR1_ID,$STR2_ID,$STR3_ID,$STR4_ID,$STR5_ID,$STR6_ID"

echo -e "\n--- Step 4: Strategic OKRs ---"
OKR1=$(post "$API/step4/okrs" "{\"strategy_id\":$STR1_ID,\"objective\":\"Process 25% of Elavon merchant settlements in real-time by Q4 2026\",\"time_horizon\":\"2025-2026\",\"status\":\"active\"}")
OKR1_ID=$(echo "$OKR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR2=$(post "$API/step4/okrs" "{\"strategy_id\":$STR2_ID,\"objective\":\"Generate \$500M in embedded finance revenue with 20 active BaaS partners by 2027\",\"time_horizon\":\"2025-2027\",\"status\":\"active\"}")
OKR2_ID=$(echo "$OKR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR3=$(post "$API/step4/okrs" "{\"strategy_id\":$STR3_ID,\"objective\":\"Reduce efficiency ratio from 61.2% to 55% through AI-powered operational transformation\",\"time_horizon\":\"2025-2027\",\"status\":\"active\"}")
OKR3_ID=$(echo "$OKR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR4=$(post "$API/step4/okrs" "{\"strategy_id\":$STR5_ID,\"objective\":\"Deploy Gen AI copilot to 5,000 employees with measurable productivity gains\",\"time_horizon\":\"2025-2026\",\"status\":\"active\"}")
OKR4_ID=$(echo "$OKR4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR5=$(post "$API/step4/okrs" "{\"strategy_id\":$STR6_ID,\"objective\":\"Achieve #1 consumer banking app rating among top 10 US banks\",\"time_horizon\":\"2025-2026\",\"status\":\"active\"}")
OKR5_ID=$(echo "$OKR5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR6=$(post "$API/step4/okrs" "{\"strategy_id\":$STR4_ID,\"objective\":\"Unify customer profiles across all 4 business lines with 360-degree view\",\"time_horizon\":\"2025-2027\",\"status\":\"draft\"}")
OKR6_ID=$(echo "$OKR6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "OKR IDs: $OKR1_ID,$OKR2_ID,$OKR3_ID,$OKR4_ID,$OKR5_ID,$OKR6_ID"

echo -e "\n--- Step 4: Key Results ---"
post "$API/step4/okrs/$OKR1_ID/key-results" '{"key_result":"Integrate FedNow/RTP rails for 100% of Elavon merchant accounts","metric":"merchant_rtp_enabled_pct","current_value":5,"target_value":100,"unit":"%","rationale":"Currently 5% of merchants have real-time settlement option"}'
post "$API/step4/okrs/$OKR1_ID/key-results" '{"key_result":"Process $125B in real-time settled transactions annually","metric":"rtp_volume","current_value":8,"target_value":125,"unit":"$B","rationale":"$500B total Elavon volume, target 25% on real-time rails"}'
post "$API/step4/okrs/$OKR1_ID/key-results" '{"key_result":"Achieve 15bps premium pricing for real-time settlement","metric":"rtp_premium_bps","current_value":0,"target_value":15,"unit":"bps","rationale":"Merchants will pay premium for instant access to funds vs T+1"}'

post "$API/step4/okrs/$OKR2_ID/key-results" '{"key_result":"Onboard 20 BaaS partners (fintechs and brands)","metric":"baas_partners","current_value":2,"target_value":20,"unit":"partners","rationale":"Currently 2 pilot partners, need to scale go-to-market"}'
post "$API/step4/okrs/$OKR2_ID/key-results" '{"key_result":"Launch developer portal with 50+ banking APIs","metric":"api_count","current_value":12,"target_value":50,"unit":"APIs","rationale":"Current 12 internal APIs need productization and documentation"}'

post "$API/step4/okrs/$OKR3_ID/key-results" '{"key_result":"Automate 70% of mortgage underwriting decisions","metric":"auto_underwrite_pct","current_value":40,"target_value":70,"unit":"%","rationale":"Currently 40% auto-decided, target 70% via AI underwriting models"}'
post "$API/step4/okrs/$OKR3_ID/key-results" '{"key_result":"Reduce compliance review time by 50% via AI document analysis","metric":"compliance_time_reduction","current_value":0,"target_value":50,"unit":"%","rationale":"AI-powered SAR and BSA review to halve analyst workload"}'
post "$API/step4/okrs/$OKR3_ID/key-results" '{"key_result":"Achieve $400M annual cost savings from AI automation","metric":"ai_cost_savings","current_value":25,"target_value":400,"unit":"$M","rationale":"Initial $25M from pilot programs, scale across enterprise"}'

post "$API/step4/okrs/$OKR4_ID/key-results" '{"key_result":"5,000 employees using Gen AI copilot daily","metric":"daily_active_users","current_value":200,"target_value":5000,"unit":"users","rationale":"200 users in pilot, rolling out to loan officers, compliance, and RMs"}'
post "$API/step4/okrs/$OKR4_ID/key-results" '{"key_result":"30% reduction in loan processing time via AI-assisted document review","metric":"loan_processing_time_reduction","current_value":5,"target_value":30,"unit":"%","rationale":"Early pilots show 5% improvement, target 30% at full deployment"}'

post "$API/step4/okrs/$OKR5_ID/key-results" '{"key_result":"Achieve 4.8+ App Store rating (currently 4.5)","metric":"app_rating","current_value":4.5,"target_value":4.8,"unit":"stars","rationale":"Rebuild core journeys and add financial wellness features"}'
post "$API/step4/okrs/$OKR5_ID/key-results" '{"key_result":"Increase digital-only account openings to 70% of new accounts","metric":"digital_account_pct","current_value":48,"target_value":70,"unit":"%","rationale":"48% currently digital, targeting 70% with instant account opening"}'

post "$API/step4/okrs/$OKR6_ID/key-results" '{"key_result":"Unify 95% of customer records across business lines","metric":"unified_profiles_pct","current_value":35,"target_value":95,"unit":"%","rationale":"35% of customers currently have cross-business-line profiles"}'

echo " done"

# ============================================================
# Step 5: Digital Initiatives & RICE Prioritization
# ============================================================
echo -e "\n--- Step 5: Product Groups & Digital Products ---"
PG1=$(post "$API/step5/product-groups" '{"name":"Payment Platform","description":"Real-time payments, merchant services, and payment infrastructure"}')
PG1_ID=$(echo "$PG1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

PG2=$(post "$API/step5/product-groups" '{"name":"AI & Automation Platform","description":"Gen AI copilot, ML models, and automation tools for banking operations"}')
PG2_ID=$(echo "$PG2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

PG3=$(post "$API/step5/product-groups" '{"name":"Digital Banking","description":"Consumer and business digital banking experiences"}')
PG3_ID=$(echo "$PG3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

PG4=$(post "$API/step5/product-groups" '{"name":"Embedded Finance","description":"BaaS APIs and embedded finance platform for partners"}')
PG4_ID=$(echo "$PG4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP1=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG1_ID,\"name\":\"Real-Time Settlement Engine\",\"description\":\"FedNow/RTP integration for instant merchant and corporate payment settlement\"}")
DP1_ID=$(echo "$DP1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP2=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG2_ID,\"name\":\"Banking AI Copilot\",\"description\":\"Gen AI assistant for loan officers, compliance analysts, and relationship managers\"}")
DP2_ID=$(echo "$DP2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP3=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG2_ID,\"name\":\"AI Underwriting Engine\",\"description\":\"ML-powered automated underwriting for consumer and mortgage lending\"}")
DP3_ID=$(echo "$DP3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP4=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG3_ID,\"name\":\"USB Mobile Banking 3.0\",\"description\":\"Next-gen mobile banking with AI coaching, instant features, and personalized UX\"}")
DP4_ID=$(echo "$DP4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP5=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG4_ID,\"name\":\"USB BaaS API Platform\",\"description\":\"Developer portal with banking APIs for embedded finance partners\"}")
DP5_ID=$(echo "$DP5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP6=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG2_ID,\"name\":\"Fraud Detection ML Platform\",\"description\":\"Real-time ML fraud scoring for transactions, applications, and account activity\"}")
DP6_ID=$(echo "$DP6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Product Group IDs: $PG1_ID,$PG2_ID,$PG3_ID,$PG4_ID | Digital Product IDs: $DP1_ID,$DP2_ID,$DP3_ID,$DP4_ID,$DP5_ID,$DP6_ID"

echo -e "\n--- Step 5: Initiatives ---"
INIT1=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP1_ID,\"strategy_id\":$STR1_ID,\"name\":\"FedNow Merchant Settlement Integration\",\"description\":\"Integrate FedNow instant payment rails into Elavon merchant settlement platform for real-time fund access\",\"reach\":50000,\"impact\":3,\"confidence\":0.8,\"effort\":10,\"value_score\":5,\"size_score\":4,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT1_ID=$(echo "$INIT1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT2=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP2_ID,\"strategy_id\":$STR5_ID,\"name\":\"Loan Officer AI Assistant\",\"description\":\"Gen AI copilot for loan officers — auto-summarize applications, extract conditions, draft correspondence, flag risks\",\"reach\":3000,\"impact\":3,\"confidence\":0.8,\"effort\":8,\"value_score\":5,\"size_score\":4,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT2_ID=$(echo "$INIT2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT3=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP3_ID,\"strategy_id\":$STR3_ID,\"name\":\"AI Mortgage Auto-Decisioning\",\"description\":\"ML model for automated mortgage underwriting decisions — approve/deny/condition without human underwriter for conforming loans\",\"reach\":100000,\"impact\":3,\"confidence\":0.8,\"effort\":14,\"value_score\":5,\"size_score\":5,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT3_ID=$(echo "$INIT3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT4=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP4_ID,\"strategy_id\":$STR6_ID,\"name\":\"Instant Account Opening & Virtual Card\",\"description\":\"Sub-60-second checking account opening with instant virtual debit card provisioned to Apple/Google Wallet\",\"reach\":500000,\"impact\":2,\"confidence\":1.0,\"effort\":6,\"value_score\":4,\"size_score\":3,\"roadmap_phase\":\"Phase 1\",\"status\":\"approved\"}")
INIT4_ID=$(echo "$INIT4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT5=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP5_ID,\"strategy_id\":$STR2_ID,\"name\":\"BaaS Developer Portal & API Gateway\",\"description\":\"Self-service developer portal with sandbox, documentation, and API gateway for embedded banking partners\",\"reach\":200,\"impact\":3,\"confidence\":0.8,\"effort\":12,\"value_score\":5,\"size_score\":5,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT5_ID=$(echo "$INIT5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT6=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP6_ID,\"strategy_id\":$STR3_ID,\"name\":\"Real-Time Adaptive Fraud ML\",\"description\":\"Deploy ensemble ML fraud detection with real-time feature computation, reducing false declines 30% while maintaining fraud catch rate\",\"reach\":1000000,\"impact\":2,\"confidence\":0.8,\"effort\":10,\"value_score\":4,\"size_score\":4,\"roadmap_phase\":\"Phase 1\",\"status\":\"approved\"}")
INIT6_ID=$(echo "$INIT6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT7=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP4_ID,\"strategy_id\":$STR6_ID,\"name\":\"AI Financial Wellness Coach\",\"description\":\"Personalized AI-powered financial coaching in mobile app — spending insights, savings recommendations, debt payoff plans\",\"reach\":800000,\"impact\":2,\"confidence\":0.5,\"effort\":8,\"value_score\":3,\"size_score\":3,\"roadmap_phase\":\"Phase 2\",\"status\":\"proposed\"}")
INIT7_ID=$(echo "$INIT7" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT8=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP2_ID,\"strategy_id\":$STR5_ID,\"name\":\"Compliance AI — SAR Auto-Generation\",\"description\":\"Gen AI system to auto-draft Suspicious Activity Reports from transaction monitoring alerts, reducing analyst time by 60%\",\"reach\":500,\"impact\":3,\"confidence\":0.5,\"effort\":12,\"value_score\":4,\"size_score\":4,\"roadmap_phase\":\"Phase 2\",\"status\":\"proposed\"}")
INIT8_ID=$(echo "$INIT8" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Initiative IDs: $INIT1_ID,$INIT2_ID,$INIT3_ID,$INIT4_ID,$INIT5_ID,$INIT6_ID,$INIT7_ID,$INIT8_ID"

# ============================================================
# Step 6: Epics & Teams + Product OKRs
# ============================================================
echo -e "\n--- Step 6: Teams ---"
TEAM1=$(post "$API/step6/teams" '{"name":"Payments Engineering","capacity":30}')
TEAM1_ID=$(echo "$TEAM1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM2=$(post "$API/step6/teams" '{"name":"AI/ML Platform","capacity":25}')
TEAM2_ID=$(echo "$TEAM2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM3=$(post "$API/step6/teams" '{"name":"Consumer Digital","capacity":35}')
TEAM3_ID=$(echo "$TEAM3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM4=$(post "$API/step6/teams" '{"name":"Credit & Lending Tech","capacity":20}')
TEAM4_ID=$(echo "$TEAM4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM5=$(post "$API/step6/teams" '{"name":"API Platform & Integration","capacity":18}')
TEAM5_ID=$(echo "$TEAM5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM6=$(post "$API/step6/teams" '{"name":"Fraud & Risk Analytics","capacity":15}')
TEAM6_ID=$(echo "$TEAM6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Team IDs: $TEAM1_ID,$TEAM2_ID,$TEAM3_ID,$TEAM4_ID,$TEAM5_ID,$TEAM6_ID"

echo -e "\n--- Step 6: Product OKRs ---"
POKR1=$(post "$API/step6/product-okrs" "{\"strategic_okr_id\":$OKR1_ID,\"digital_product_id\":$DP1_ID,\"objective\":\"Launch real-time settlement for top 10,000 Elavon merchants by Q2 2026\",\"status\":\"active\"}")
POKR1_ID=$(echo "$POKR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

POKR2=$(post "$API/step6/product-okrs" "{\"strategic_okr_id\":$OKR3_ID,\"digital_product_id\":$DP3_ID,\"objective\":\"Achieve 70% auto-decision rate for conforming mortgage applications\",\"status\":\"active\"}")
POKR2_ID=$(echo "$POKR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

POKR3=$(post "$API/step6/product-okrs" "{\"strategic_okr_id\":$OKR4_ID,\"digital_product_id\":$DP2_ID,\"objective\":\"Roll out AI copilot to all loan officers and compliance analysts\",\"status\":\"active\"}")
POKR3_ID=$(echo "$POKR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

POKR4=$(post "$API/step6/product-okrs" "{\"strategic_okr_id\":$OKR5_ID,\"digital_product_id\":$DP4_ID,\"objective\":\"Launch Mobile Banking 3.0 with instant account opening and AI coaching\",\"status\":\"active\"}")
POKR4_ID=$(echo "$POKR4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Product OKR IDs: $POKR1_ID,$POKR2_ID,$POKR3_ID,$POKR4_ID"

echo -e "\n--- Step 6: Epics ---"
EPIC1=$(post "$API/step6/epics" "{\"initiative_id\":$INIT1_ID,\"team_id\":$TEAM1_ID,\"product_okr_id\":$POKR1_ID,\"name\":\"FedNow Gateway Integration\",\"description\":\"Build FedNow message adapter and integrate with Elavon settlement engine for real-time merchant payments\",\"status\":\"in_progress\",\"start_date\":\"2025-07-01\",\"target_date\":\"2026-01-15\",\"value_score\":5,\"size_score\":5,\"effort_score\":5,\"risk_level\":\"high\",\"risks\":\"FedNow API stability, settlement finality edge cases, bank partner readiness\",\"roadmap_phase\":\"Phase 1\"}")
EPIC1_ID=$(echo "$EPIC1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC2=$(post "$API/step6/epics" "{\"initiative_id\":$INIT1_ID,\"team_id\":$TEAM1_ID,\"product_okr_id\":$POKR1_ID,\"name\":\"Merchant RTP Dashboard\",\"description\":\"Self-service merchant portal for real-time settlement enrollment, monitoring, and reconciliation\",\"status\":\"backlog\",\"start_date\":\"2025-12-01\",\"target_date\":\"2026-03-01\",\"value_score\":3,\"size_score\":3,\"effort_score\":3,\"risk_level\":\"low\",\"roadmap_phase\":\"Phase 1\"}")
EPIC2_ID=$(echo "$EPIC2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC3=$(post "$API/step6/epics" "{\"initiative_id\":$INIT3_ID,\"team_id\":$TEAM4_ID,\"product_okr_id\":$POKR2_ID,\"name\":\"Mortgage ML Decisioning Model\",\"description\":\"Build and validate ML model for automated mortgage approval/deny/condition decisions on conforming loans\",\"status\":\"in_progress\",\"start_date\":\"2025-06-01\",\"target_date\":\"2026-03-01\",\"value_score\":5,\"size_score\":5,\"effort_score\":5,\"risk_level\":\"high\",\"risks\":\"Fair lending compliance, model explainability for regulators, data quality\",\"roadmap_phase\":\"Phase 1\"}")
EPIC3_ID=$(echo "$EPIC3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC4=$(post "$API/step6/epics" "{\"initiative_id\":$INIT3_ID,\"team_id\":$TEAM4_ID,\"product_okr_id\":$POKR2_ID,\"name\":\"Automated Document Verification\",\"description\":\"AI-powered extraction and verification of income, employment, and asset documents for mortgage applications\",\"status\":\"in_progress\",\"start_date\":\"2025-08-01\",\"target_date\":\"2026-02-01\",\"value_score\":4,\"size_score\":4,\"effort_score\":4,\"risk_level\":\"medium\",\"risks\":\"OCR accuracy on diverse document formats, fraud detection in doctored documents\",\"roadmap_phase\":\"Phase 1\"}")
EPIC4_ID=$(echo "$EPIC4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC5=$(post "$API/step6/epics" "{\"initiative_id\":$INIT2_ID,\"team_id\":$TEAM2_ID,\"product_okr_id\":$POKR3_ID,\"name\":\"Gen AI Loan Review Copilot\",\"description\":\"Build Gen AI assistant that summarizes loan applications, extracts conditions, drafts correspondence for loan officers\",\"status\":\"in_progress\",\"start_date\":\"2025-09-01\",\"target_date\":\"2026-03-01\",\"value_score\":5,\"size_score\":4,\"effort_score\":4,\"risk_level\":\"medium\",\"risks\":\"Hallucination in financial summaries, loan officer trust and adoption\",\"roadmap_phase\":\"Phase 1\"}")
EPIC5_ID=$(echo "$EPIC5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC6=$(post "$API/step6/epics" "{\"initiative_id\":$INIT4_ID,\"team_id\":$TEAM3_ID,\"product_okr_id\":$POKR4_ID,\"name\":\"Instant Account Opening\",\"description\":\"Rebuild account opening flow: sub-60s digital application, instant KYC, instant virtual debit card provisioning\",\"status\":\"in_progress\",\"start_date\":\"2025-10-01\",\"target_date\":\"2026-02-01\",\"value_score\":4,\"size_score\":4,\"effort_score\":3,\"risk_level\":\"medium\",\"risks\":\"KYC speed vs accuracy tradeoff, identity fraud risk\",\"roadmap_phase\":\"Phase 1\"}")
EPIC6_ID=$(echo "$EPIC6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC7=$(post "$API/step6/epics" "{\"initiative_id\":$INIT4_ID,\"team_id\":$TEAM3_ID,\"product_okr_id\":$POKR4_ID,\"name\":\"Mobile Banking UX Redesign\",\"description\":\"Complete UX redesign of mobile banking app with personalized dashboard, financial insights, and streamlined navigation\",\"status\":\"backlog\",\"start_date\":\"2026-01-01\",\"target_date\":\"2026-06-01\",\"value_score\":4,\"size_score\":4,\"effort_score\":4,\"risk_level\":\"low\",\"roadmap_phase\":\"Phase 1\"}")
EPIC7_ID=$(echo "$EPIC7" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC8=$(post "$API/step6/epics" "{\"initiative_id\":$INIT6_ID,\"team_id\":$TEAM6_ID,\"name\":\"Real-Time Fraud ML Pipeline\",\"description\":\"Build streaming ML pipeline for real-time transaction fraud scoring with sub-50ms latency\",\"status\":\"in_progress\",\"start_date\":\"2025-08-01\",\"target_date\":\"2026-02-01\",\"value_score\":5,\"size_score\":4,\"effort_score\":4,\"risk_level\":\"medium\",\"risks\":\"Latency requirements, feature computation at scale, model drift monitoring\",\"roadmap_phase\":\"Phase 1\"}")
EPIC8_ID=$(echo "$EPIC8" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Epic IDs: $EPIC1_ID,$EPIC2_ID,$EPIC3_ID,$EPIC4_ID,$EPIC5_ID,$EPIC6_ID,$EPIC7_ID,$EPIC8_ID"

echo -e "\n--- Step 6: Epic Dependencies ---"
post "$API/step6/dependencies" "{\"epic_id\":$EPIC2_ID,\"depends_on_epic_id\":$EPIC1_ID,\"dependency_type\":\"blocks\",\"notes\":\"Merchant dashboard needs FedNow integration to be operational\"}"
post "$API/step6/dependencies" "{\"epic_id\":$EPIC3_ID,\"depends_on_epic_id\":$EPIC4_ID,\"dependency_type\":\"relates_to\",\"notes\":\"Auto-decisioning depends on automated document verification for input data\"}"
post "$API/step6/dependencies" "{\"epic_id\":$EPIC7_ID,\"depends_on_epic_id\":$EPIC6_ID,\"dependency_type\":\"blocks\",\"notes\":\"UX redesign depends on instant account opening being live\"}"

echo " done"

# ============================================================
# Step 7: Features & Roadmap + Delivery OKRs
# ============================================================
echo -e "\n--- Step 7: Delivery OKRs ---"
DOKR1=$(post "$API/step7/delivery-okrs" "{\"product_okr_id\":$POKR1_ID,\"team_id\":$TEAM1_ID,\"objective\":\"Ship FedNow integration with 99.99% uptime and <500ms settlement confirmation\",\"status\":\"active\"}")
DOKR1_ID=$(echo "$DOKR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DOKR2=$(post "$API/step7/delivery-okrs" "{\"product_okr_id\":$POKR2_ID,\"team_id\":$TEAM4_ID,\"objective\":\"Deploy mortgage auto-decisioning model with <0.5% adverse action error rate\",\"status\":\"active\"}")
DOKR2_ID=$(echo "$DOKR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DOKR3=$(post "$API/step7/delivery-okrs" "{\"product_okr_id\":$POKR3_ID,\"team_id\":$TEAM2_ID,\"objective\":\"Launch Gen AI copilot beta to 500 loan officers by Q1 2026\",\"status\":\"active\"}")
DOKR3_ID=$(echo "$DOKR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DOKR4=$(post "$API/step7/delivery-okrs" "{\"product_okr_id\":$POKR4_ID,\"team_id\":$TEAM3_ID,\"objective\":\"Ship Mobile Banking 3.0 with instant account opening to 100% of markets\",\"status\":\"active\"}")
DOKR4_ID=$(echo "$DOKR4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Delivery OKR IDs: $DOKR1_ID,$DOKR2_ID,$DOKR3_ID,$DOKR4_ID"

echo -e "\n--- Step 7: Features ---"
# Features for Epic 1: FedNow Gateway
post "$API/step7/features" "{\"epic_id\":$EPIC1_ID,\"delivery_okr_id\":$DOKR1_ID,\"name\":\"FedNow Message Adapter\",\"description\":\"ISO 20022 message translation layer between Elavon settlement engine and FedNow Service\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":20,\"start_date\":\"2025-07-15\",\"target_date\":\"2025-11-01\",\"roadmap_phase\":\"Phase 1\",\"acceptance_criteria\":\"All 8 FedNow message types supported with 99.99% translation accuracy\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC1_ID,\"delivery_okr_id\":$DOKR1_ID,\"name\":\"Settlement Finality Engine\",\"description\":\"Handle settlement finality, reversals, and exception processing for real-time payments\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":15,\"start_date\":\"2025-09-01\",\"target_date\":\"2025-12-15\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC1_ID,\"delivery_okr_id\":$DOKR1_ID,\"name\":\"RTP Liquidity Management\",\"description\":\"Real-time liquidity monitoring and pre-funding management for instant settlement obligations\",\"priority\":\"high\",\"status\":\"backlog\",\"estimated_effort\":12,\"roadmap_phase\":\"Phase 1\"}"

# Features for Epic 3: Mortgage ML
post "$API/step7/features" "{\"epic_id\":$EPIC3_ID,\"delivery_okr_id\":$DOKR2_ID,\"name\":\"Fair Lending Model Validation\",\"description\":\"Comprehensive fair lending testing and adverse impact analysis for ML underwriting model across protected classes\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":18,\"start_date\":\"2025-06-15\",\"target_date\":\"2026-01-15\",\"roadmap_phase\":\"Phase 1\",\"acceptance_criteria\":\"No statistically significant disparate impact across race, gender, age. OCC model risk review passed.\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC3_ID,\"delivery_okr_id\":$DOKR2_ID,\"name\":\"Explainable AI Decision Report\",\"description\":\"Generate human-readable explanations for every automated underwriting decision — required for adverse action notices\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":14,\"start_date\":\"2025-08-01\",\"target_date\":\"2026-02-01\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC3_ID,\"delivery_okr_id\":$DOKR2_ID,\"name\":\"Automated Condition Generation\",\"description\":\"ML model generates specific underwriting conditions when application needs additional documentation or clarification\",\"priority\":\"high\",\"status\":\"backlog\",\"estimated_effort\":10,\"roadmap_phase\":\"Phase 1\"}"

# Features for Epic 5: Gen AI Copilot
post "$API/step7/features" "{\"epic_id\":$EPIC5_ID,\"delivery_okr_id\":$DOKR3_ID,\"name\":\"Loan Application Summarizer\",\"description\":\"Gen AI auto-summarizes mortgage application package: borrower profile, income analysis, risk flags, comparable properties\",\"priority\":\"high\",\"status\":\"in_progress\",\"estimated_effort\":10,\"start_date\":\"2025-09-15\",\"target_date\":\"2025-12-15\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC5_ID,\"delivery_okr_id\":$DOKR3_ID,\"name\":\"Condition Letter Drafter\",\"description\":\"Auto-draft condition letters and borrower correspondence from underwriting decisions\",\"priority\":\"medium\",\"status\":\"backlog\",\"estimated_effort\":8,\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC5_ID,\"delivery_okr_id\":$DOKR3_ID,\"name\":\"Copilot Guardrails & Audit Log\",\"description\":\"Safety guardrails preventing hallucinated financial figures, plus complete audit trail of all AI-generated content\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":12,\"start_date\":\"2025-10-01\",\"target_date\":\"2026-01-15\",\"roadmap_phase\":\"Phase 1\"}"

# Features for Epic 6: Instant Account Opening
post "$API/step7/features" "{\"epic_id\":$EPIC6_ID,\"delivery_okr_id\":$DOKR4_ID,\"name\":\"Instant KYC/CIP Verification\",\"description\":\"Real-time identity verification combining ID document scan, selfie liveness check, and bureau data — sub-10s verification\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":14,\"start_date\":\"2025-10-15\",\"target_date\":\"2026-01-01\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC6_ID,\"delivery_okr_id\":$DOKR4_ID,\"name\":\"Virtual Debit Card Provisioning\",\"description\":\"Instant virtual debit card generation and push provisioning to Apple Pay and Google Wallet\",\"priority\":\"high\",\"status\":\"backlog\",\"estimated_effort\":8,\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC6_ID,\"delivery_okr_id\":$DOKR4_ID,\"name\":\"Micro-Deposit Instant Funding\",\"description\":\"Instant account funding via debit card or real-time bank transfer instead of 2-day ACH micro-deposits\",\"priority\":\"medium\",\"status\":\"backlog\",\"estimated_effort\":6,\"roadmap_phase\":\"Phase 1\"}"

# Features for Epic 8: Fraud ML Pipeline
post "$API/step7/features" "{\"epic_id\":$EPIC8_ID,\"name\":\"Streaming Feature Store\",\"description\":\"Real-time feature computation engine for transaction-level fraud features (velocity, device, geolocation, behavioral)\",\"priority\":\"high\",\"status\":\"in_progress\",\"estimated_effort\":16,\"start_date\":\"2025-08-15\",\"target_date\":\"2025-12-15\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC8_ID,\"name\":\"Adaptive Fraud Model Ensemble\",\"description\":\"Multi-model ensemble combining gradient boosting, neural network, and rule-based scoring with dynamic weight adjustment\",\"priority\":\"high\",\"status\":\"backlog\",\"estimated_effort\":14,\"roadmap_phase\":\"Phase 1\"}"

echo " done"

# ============================================================
# Review Gates (HITL checkpoints)
# ============================================================
echo -e "\n--- Review Gates ---"
post "$API/gates/" '{"step_number":1,"gate_number":1,"gate_name":"Org Setup & Data Ingestion Review","status":"approved","reviewer":"CFO Office","review_notes":"Financial data validated against 10-K filing. Competitor data confirmed."}'
post "$API/gates/" '{"step_number":1,"gate_number":2,"gate_name":"KPI & Metrics Validation","status":"approved","reviewer":"Head of FP&A","review_notes":"Ops metrics align with internal reporting. NIM and efficiency ratio confirmed."}'
post "$API/gates/" '{"step_number":2,"gate_number":1,"gate_name":"Value Stream Mapping Review","status":"approved","reviewer":"COO","review_notes":"Mortgage origination VSM validated by ops team. Bottleneck confirmed at manual underwriting."}'
post "$API/gates/" '{"step_number":3,"gate_number":1,"gate_name":"SWOT/TOWS Strategy Review","status":"approved","reviewer":"Chief Strategy Officer","review_notes":"SWOT entries validated. TOWS actions aligned with strategic priorities."}'
post "$API/gates/" '{"step_number":4,"gate_number":1,"gate_name":"Strategy & OKR Alignment Gate","status":"approved","reviewer":"CEO","review_notes":"All 6 strategies approved. OKRs cascaded properly from board-level objectives."}'
post "$API/gates/" '{"step_number":5,"gate_number":1,"gate_name":"Initiative RICE Prioritization Review","status":"approved","reviewer":"CTO","review_notes":"RICE scores validated. FedNow and AI underwriting confirmed as top priorities."}'
post "$API/gates/" '{"step_number":6,"gate_number":1,"gate_name":"Epic Decomposition & Team Allocation","status":"pending","reviewer":"VP Engineering","review_notes":"Pending review of team capacity allocation and dependency analysis."}'
post "$API/gates/" '{"step_number":7,"gate_number":1,"gate_name":"Feature Backlog & Roadmap Approval","status":"pending","reviewer":"Product Council","review_notes":"Awaiting feature prioritization review and Q1 2026 roadmap sign-off."}'

echo -e "\n\n=== SEEDING COMPLETE FOR US BANK ==="
echo "Summary:"
echo "  Organization: US Bancorp (Banking & Financial Services)"
echo "  Step 1: 5 BUs, 18 revenue splits, 15 ops metrics, 3 competitors, 3 data URLs"
echo "  Step 2: 4 value streams, 17 steps, 6 levers"
echo "  Step 3: 4 strengths, 4 weaknesses, 4 opportunities, 4 threats, 6 TOWS actions"
echo "  Step 4: 7 strategy inputs (incl 2 documents), 6 strategies, 6 OKRs, 14 key results"
echo "  Step 5: 4 product groups, 6 digital products, 8 initiatives (RICE scored)"
echo "  Step 6: 6 teams, 4 product OKRs, 8 epics, 3 dependencies"
echo "  Step 7: 4 delivery OKRs, 15 features"
echo "  Review Gates: 8 gates (6 approved, 2 pending)"
