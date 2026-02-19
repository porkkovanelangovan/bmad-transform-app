#!/bin/bash
# Seed UAT test data for ING Bank — all 7 steps
# Usage: bash seed_ing_bank.sh [BASE_URL]
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

echo "=== Seeding UAT data for ING Bank at $BASE ==="

# Reset existing data
echo -e "\n--- Resetting all data ---"
post "$API/step1/reset-data" '{}'
echo " done"

# ============================================================
# Organization
# ============================================================
echo -e "\n--- Organization ---"
post "$API/step1/organization" '{"name":"ING Group","industry":"Banking & Financial Services","sub_industry":"Universal Banking & Digital Banking","competitor_1_name":"ABN AMRO","competitor_2_name":"Rabobank"}'

# ============================================================
# Step 1: Business Performance Dashboard
# ============================================================
echo -e "\n--- Step 1: Business Units ---"
post "$API/step1/business-units" '{"name":"ING Group","description":"ING Group N.V. — Dutch multinational banking and financial services"}'
BU2=$(post "$API/step1/business-units" '{"name":"Retail Banking Netherlands","description":"Dutch retail banking: savings, mortgages, consumer lending, daily banking"}')
BU3=$(post "$API/step1/business-units" '{"name":"Retail Banking International","description":"Retail banking across Belgium, Germany, Poland, Spain, Italy, Australia, and other markets"}')
BU4=$(post "$API/step1/business-units" '{"name":"Wholesale Banking","description":"Corporate banking, lending, transaction services, financial markets, trade finance"}')
BU5=$(post "$API/step1/business-units" '{"name":"ING Direct Digital","description":"Digital-first banking platform across all markets — savings, payments, personal loans"}')

BU_LIST=$(curl -s "$API/step1/business-units")
ING_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next((b['id'] for b in data if b['name']=='ING Group'),data[0]['id']))")
RNL_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if 'Netherlands' in b['name']))")
RI_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if 'International' in b['name']))")
WB_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if 'Wholesale' in b['name']))")
DD_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if 'Digital' in b['name']))")

echo "BU IDs: ING=$ING_BU_ID RNL=$RNL_BU_ID RI=$RI_BU_ID WB=$WB_BU_ID DD=$DD_BU_ID"

echo -e "\n--- Step 1: Revenue Splits ---"
# Revenue by segment (in EUR M)
post "$API/step1/revenue-splits" "{\"business_unit_id\":$RNL_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Retail Netherlands\",\"revenue\":5420,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$RNL_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Retail Netherlands\",\"revenue\":5180,\"period\":\"2024\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$RNL_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Retail Netherlands\",\"revenue\":4890,\"period\":\"2023\"}"

post "$API/step1/revenue-splits" "{\"business_unit_id\":$RI_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Retail International\",\"revenue\":7850,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$RI_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Retail International\",\"revenue\":7420,\"period\":\"2024\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$RI_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Retail International\",\"revenue\":6980,\"period\":\"2023\"}"

post "$API/step1/revenue-splits" "{\"business_unit_id\":$WB_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Wholesale Banking\",\"revenue\":6230,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$WB_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Wholesale Banking\",\"revenue\":6010,\"period\":\"2024\"}"

# Regional splits
post "$API/step1/revenue-splits" "{\"business_unit_id\":$ING_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Netherlands\",\"revenue\":5420,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$ING_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Belgium\",\"revenue\":2850,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$ING_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Germany\",\"revenue\":3210,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$ING_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Poland & CEE\",\"revenue\":1890,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$ING_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Spain & Southern Europe\",\"revenue\":1420,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$ING_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Australia & Asia-Pacific\",\"revenue\":1180,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$ING_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Rest of World\",\"revenue\":3530,\"period\":\"2025\"}"

# Segment splits
post "$API/step1/revenue-splits" "{\"business_unit_id\":$ING_BU_ID,\"dimension\":\"segment\",\"dimension_value\":\"Net Interest Income\",\"revenue\":14280,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$ING_BU_ID,\"dimension\":\"segment\",\"dimension_value\":\"Fee & Commission Income\",\"revenue\":3520,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$ING_BU_ID,\"dimension\":\"segment\",\"dimension_value\":\"Investment & Trading Income\",\"revenue\":1700,\"period\":\"2025\"}"

echo " done"

echo -e "\n--- Step 1: Ops Efficiency ---"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$ING_BU_ID,\"metric_name\":\"Net Profit Margin\",\"metric_value\":0.298,\"target_value\":0.32,\"period\":\"2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$ING_BU_ID,\"metric_name\":\"Return on Equity (ROE)\",\"metric_value\":0.128,\"target_value\":0.14,\"period\":\"2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$ING_BU_ID,\"metric_name\":\"Return on Assets (ROA)\",\"metric_value\":0.0058,\"target_value\":0.006,\"period\":\"2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$ING_BU_ID,\"metric_name\":\"Cost-to-Income Ratio\",\"metric_value\":0.528,\"target_value\":0.50,\"period\":\"2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$ING_BU_ID,\"metric_name\":\"Net Interest Margin\",\"metric_value\":0.0158,\"target_value\":0.016,\"period\":\"2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$ING_BU_ID,\"metric_name\":\"CET1 Capital Ratio\",\"metric_value\":0.148,\"target_value\":0.14,\"period\":\"2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$ING_BU_ID,\"metric_name\":\"Total Capital Ratio\",\"metric_value\":0.198,\"target_value\":0.18,\"period\":\"2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$ING_BU_ID,\"metric_name\":\"Loan-to-Deposit Ratio\",\"metric_value\":0.88,\"target_value\":0.90,\"period\":\"2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$ING_BU_ID,\"metric_name\":\"Revenue Growth (YoY)\",\"metric_value\":0.058,\"target_value\":0.06,\"period\":\"2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$ING_BU_ID,\"metric_name\":\"EPS\",\"metric_value\":5.12,\"target_value\":5.50,\"period\":\"2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$ING_BU_ID,\"metric_name\":\"Dividend Yield\",\"metric_value\":0.062,\"target_value\":0.06,\"period\":\"2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$ING_BU_ID,\"metric_name\":\"Non-Performing Loans Ratio\",\"metric_value\":0.016,\"target_value\":0.012,\"period\":\"2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$ING_BU_ID,\"metric_name\":\"Digital Customer Adoption\",\"metric_value\":0.78,\"target_value\":0.85,\"period\":\"2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$ING_BU_ID,\"metric_name\":\"Mobile Primary Customers (M)\",\"metric_value\":14.2,\"target_value\":16.0,\"period\":\"2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$ING_BU_ID,\"metric_name\":\"Sustainable Finance Volume (EUR B)\",\"metric_value\":142,\"target_value\":175,\"period\":\"2025\"}"

# Digital-specific metrics
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$DD_BU_ID,\"metric_name\":\"Monthly Active App Users (M)\",\"metric_value\":11.5,\"target_value\":14.0,\"period\":\"2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$DD_BU_ID,\"metric_name\":\"Digital Sales Conversion Rate\",\"metric_value\":0.042,\"target_value\":0.06,\"period\":\"2025\"}"

echo " done"

echo -e "\n--- Step 1: Competitors ---"
post "$API/step1/competitors" '{"name":"ABN AMRO","ticker":"ABN.AS","market_share":0.18,"revenue":9250,"profit_margin":0.285,"operating_margin":0.34,"return_on_equity":0.11,"return_on_assets":0.005,"pe_ratio":8.2,"eps":3.15,"market_cap_value":28500,"strengths":"Strong Dutch market position, wealth management expertise, clear sustainability strategy, improving cost efficiency","weaknesses":"Limited international presence post-restructuring, legacy IT infrastructure, higher cost-to-income ratio, CRE exposure","data_source":"simulated"}'
post "$API/step1/competitors" '{"name":"Rabobank","market_share":0.15,"revenue":14200,"profit_margin":0.195,"operating_margin":0.25,"return_on_equity":0.085,"return_on_assets":0.004,"strengths":"Cooperative structure provides stable funding, dominant in agri-finance globally, strong Dutch retail brand, leading in sustainable agriculture finance","weaknesses":"Lower profitability than listed peers, complex cooperative governance, limited digital innovation pace, concentrated in agriculture","data_source":"simulated"}'
post "$API/step1/competitors" '{"name":"Deutsche Bank","ticker":"DBK.DE","market_share":0.12,"revenue":32400,"profit_margin":0.185,"operating_margin":0.22,"return_on_equity":0.08,"return_on_assets":0.003,"pe_ratio":6.5,"eps":2.80,"market_cap_value":32000,"strengths":"Global investment banking reach, corporate banking scale, rebuilding under new strategy, strong in German corporate market","weaknesses":"Ongoing restructuring, compliance and legal costs, weak retail digital offering, reputation risk from scandals","data_source":"simulated"}'
post "$API/step1/competitors" '{"name":"BNP Paribas","ticker":"BNP.PA","market_share":0.14,"revenue":48500,"profit_margin":0.21,"operating_margin":0.26,"return_on_equity":0.10,"return_on_assets":0.004,"pe_ratio":7.8,"eps":8.50,"market_cap_value":78000,"strengths":"Largest Eurozone bank by assets, diversified geographic and business mix, strong CIB franchise, scale advantages","weaknesses":"Complex organizational structure, higher cost base, limited digital disruption, French regulatory environment","data_source":"simulated"}'

echo " done"

echo -e "\n--- Step 1: Data URLs ---"
post "$API/step1/urls" '{"url":"https://www.ing.com/Investor-relations/Financial-performance.htm","label":"ING Group Investor Relations","url_type":"external"}'
post "$API/step1/urls" '{"url":"https://www.ing.com/About-us/Annual-Report.htm","label":"ING Annual Report 2025","url_type":"external"}'
post "$API/step1/urls" '{"url":"https://www.ecb.europa.eu/stats/supervisory/html/index.en.html","label":"ECB Banking Supervision Statistics","url_type":"external"}'
post "$API/step1/urls" '{"url":"https://www.ing.com/Sustainability.htm","label":"ING Sustainability & ESG Reports","url_type":"external"}'

echo " done"

# ============================================================
# Step 2: Value Stream Analysis
# ============================================================
echo -e "\n--- Step 2: Value Streams ---"
VS1=$(post "$API/step2/value-streams" "{\"business_unit_id\":$DD_BU_ID,\"name\":\"Digital Customer Onboarding\",\"description\":\"End-to-end digital onboarding from app download through KYC verification, account creation, to first transaction\"}")
VS1_ID=$(echo "$VS1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

VS2=$(post "$API/step2/value-streams" "{\"business_unit_id\":$WB_BU_ID,\"name\":\"Cross-Border Trade Finance\",\"description\":\"Trade finance lifecycle from letter of credit application through document verification, compliance, to settlement\"}")
VS2_ID=$(echo "$VS2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

VS3=$(post "$API/step2/value-streams" "{\"business_unit_id\":$RNL_BU_ID,\"name\":\"Dutch Mortgage Origination\",\"description\":\"Mortgage application lifecycle specific to Dutch market (NHG, tax deductibility rules, notary process)\"}")
VS3_ID=$(echo "$VS3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

VS4=$(post "$API/step2/value-streams" "{\"business_unit_id\":$WB_BU_ID,\"name\":\"Sustainable Finance Assessment\",\"description\":\"ESG assessment and sustainable finance classification for wholesale lending and bond issuance\"}")
VS4_ID=$(echo "$VS4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "VS IDs: Onboarding=$VS1_ID, Trade=$VS2_ID, Mortgage=$VS3_ID, ESG=$VS4_ID"

echo -e "\n--- Step 2: Value Stream Steps (Digital Onboarding) ---"
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":1,"step_name":"App Download & Registration","description":"Customer downloads ING app, enters email/phone, creates account credentials","step_type":"trigger","process_time_hours":0.05,"wait_time_hours":0,"resources":"Mobile App, Auth Service"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":2,"step_name":"Identity Verification (eKYC)","description":"ID document scan, liveness check, PEP/sanctions screening, address verification","step_type":"process","process_time_hours":0.08,"wait_time_hours":0.5,"resources":"eKYC Platform, Onfido/Jumio, Sanctions DB"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":3,"step_name":"Product Selection & Eligibility","description":"Customer selects products (current account, savings, card), system checks eligibility","step_type":"decision","process_time_hours":0.03,"wait_time_hours":0,"resources":"Product Engine, Risk Scoring"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":4,"step_name":"Account Provisioning","description":"Create IBAN, provision debit card, set up payment limits, enable mobile payments","step_type":"process","process_time_hours":0.02,"wait_time_hours":0.5,"resources":"Core Banking, Card Management"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":5,"step_name":"First Transaction Activation","description":"Customer makes first payment or transfer, activating full account features","step_type":"delivery","process_time_hours":0.05,"wait_time_hours":24,"is_bottleneck":1,"notes":"72-hour dropout rate of 15% between provisioning and first transaction — engagement gap","resources":"Payment Engine, Push Notifications"}'

echo -e "\n--- Step 2: Value Stream Steps (Cross-Border Trade Finance) ---"
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":1,"step_name":"LC Application & Document Submission","description":"Corporate client submits letter of credit application with trade documents","step_type":"trigger","process_time_hours":2,"wait_time_hours":4,"resources":"Trade Finance Portal, Relationship Manager"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":2,"step_name":"Document Examination","description":"Trade operations team examines documents for UCP 600 compliance","step_type":"process","process_time_hours":4,"wait_time_hours":24,"is_bottleneck":1,"notes":"Manual document examination is primary bottleneck — 85% of trade docs have discrepancies requiring resolution","resources":"Trade Ops Specialists"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":3,"step_name":"Sanctions & Compliance Screening","description":"Screen counterparties, vessels, ports, goods against sanctions lists and dual-use controls","step_type":"decision","process_time_hours":1,"wait_time_hours":8,"resources":"Compliance Team, Sanctions Screening Engine"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":4,"step_name":"Credit Assessment & Approval","description":"Assess counterparty credit risk, country risk, set aside capital reserves","step_type":"decision","process_time_hours":2,"wait_time_hours":24,"resources":"Credit Risk Team, Risk Models"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":5,"step_name":"LC Issuance & SWIFT Messaging","description":"Issue letter of credit, send SWIFT MT700/MT760 messages to advising/confirming bank","step_type":"process","process_time_hours":1,"wait_time_hours":2,"resources":"SWIFT Network, Trade Ops"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":6,"step_name":"Settlement & Reconciliation","description":"Payment settlement upon document acceptance, reconciliation across correspondent banks","step_type":"delivery","process_time_hours":1,"wait_time_hours":48,"resources":"Treasury, Correspondent Banking"}'

echo -e "\n--- Step 2: Value Stream Steps (Dutch Mortgage) ---"
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":1,"step_name":"Online Mortgage Calculator","description":"Customer uses ING mortgage calculator with Dutch tax deductibility rules and NHG simulation","step_type":"trigger","process_time_hours":0.25,"wait_time_hours":0,"resources":"Digital Platform"}'
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":2,"step_name":"Advice Session (Mandatory)","description":"Dutch regulatory requirement — mortgage advice session (online or in-person) assessing suitability","step_type":"process","process_time_hours":1.5,"wait_time_hours":48,"resources":"Mortgage Advisors (AFM licensed)"}'
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":3,"step_name":"Application & Income Verification","description":"Full application with BKR credit check, employer income verification, self-employed assessment","step_type":"process","process_time_hours":1,"wait_time_hours":24,"resources":"Digital Platform, BKR, Employer APIs"}'
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":4,"step_name":"Property Valuation","description":"Mandatory property valuation by NWWI-registered appraiser","step_type":"process","process_time_hours":2,"wait_time_hours":120,"is_bottleneck":1,"notes":"NWWI appraiser shortage in Randstad creates 5-10 day wait","resources":"NWWI Appraisers"}'
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":5,"step_name":"Mortgage Offer","description":"Generate binding mortgage offer with Dutch regulatory disclosures (European Standardised Information Sheet)","step_type":"decision","process_time_hours":2,"wait_time_hours":24,"resources":"Underwriting, Legal"}'
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":6,"step_name":"Notary & Transfer","description":"Notary deed execution (required by Dutch law), property transfer, mortgage registration at Kadaster","step_type":"delivery","process_time_hours":2,"wait_time_hours":168,"resources":"Notary, Kadaster"}'

# Recalculate metrics
post "$API/step2/value-streams/$VS1_ID/recalculate" '{}'
post "$API/step2/value-streams/$VS2_ID/recalculate" '{}'
post "$API/step2/value-streams/$VS3_ID/recalculate" '{}'

echo -e "\n--- Step 2: Value Stream Levers ---"
post "$API/step2/levers" "{\"value_stream_id\":$VS1_ID,\"lever_type\":\"experience\",\"opportunity\":\"Reduce first-transaction dropout from 15% to 5% via guided onboarding journey and instant rewards\",\"current_state\":\"15% of new accounts inactive after 72 hours, generic welcome experience\",\"target_state\":\"Personalized nudge sequences, instant cashback on first purchase, gamified activation\",\"impact_estimate\":\"high\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS1_ID,\"lever_type\":\"growth\",\"opportunity\":\"Cross-sell savings and investment products during onboarding with personalized AI recommendations\",\"current_state\":\"No cross-sell during onboarding — only current account offered\",\"target_state\":\"AI recommends savings/investment based on income profile, one-click activation\",\"impact_estimate\":\"medium\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS2_ID,\"lever_type\":\"efficiency\",\"opportunity\":\"AI-powered trade document examination replacing 70% of manual checking\",\"current_state\":\"Manual examination: 4hrs average, 85% discrepancy rate, specialists scarce\",\"target_state\":\"AI examines documents in minutes, flags only genuine discrepancies for human review\",\"impact_estimate\":\"high\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS2_ID,\"lever_type\":\"effectiveness\",\"opportunity\":\"Blockchain-based trade finance for end-to-end digital document flow\",\"current_state\":\"Paper-based trade documents, multiple intermediaries, 5-10 day settlement\",\"target_state\":\"Digital trade documents on shared ledger, same-day settlement for compliant trades\",\"impact_estimate\":\"high\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS3_ID,\"lever_type\":\"efficiency\",\"opportunity\":\"Digital-first mortgage with AI valuation and instant offer\",\"current_state\":\"5-10 day wait for NWWI appraisal, 2-3 week total process\",\"target_state\":\"AI desktop valuation for 60% of properties, same-day conditional offer\",\"impact_estimate\":\"high\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS4_ID,\"lever_type\":\"effectiveness\",\"opportunity\":\"Automated ESG scoring using AI analysis of company sustainability reports and satellite data\",\"current_state\":\"Manual ESG assessment taking 2-3 weeks per client, inconsistent methodology\",\"target_state\":\"AI-powered ESG scoring in 2 days with consistent EU Taxonomy alignment\",\"impact_estimate\":\"high\"}"

echo " done"

# ============================================================
# Step 3: SWOT to TOWS Action Engine
# ============================================================
echo -e "\n--- Step 3: SWOT Entries ---"
# Strengths
S1=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"strength\",\"description\":\"Pioneer in digital banking — ING Direct model proved digital-first at scale, 14.2M mobile primary customers across 40+ countries\",\"severity\":\"high\",\"confidence\":\"high\"}")
S1_ID=$(echo "$S1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

S2=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"strength\",\"description\":\"Strong pan-European presence with scale in NL, BE, DE, PL, ES — diversified geographic risk\",\"severity\":\"high\",\"confidence\":\"high\"}")
S2_ID=$(echo "$S2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

S3=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"strength\",\"description\":\"Leading sustainability position — EUR 142B sustainable finance, Terra approach for climate alignment, top ESG ratings\",\"severity\":\"high\",\"confidence\":\"high\"}")
S3_ID=$(echo "$S3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

S4=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"strength\",\"description\":\"Wholesale Banking franchise with strong Lending, Transaction Services, and Financial Markets capabilities\",\"severity\":\"medium\",\"confidence\":\"high\"}")
S4_ID=$(echo "$S4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

S5=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"strength\",\"description\":\"CET1 ratio at 14.8% — well-capitalized with buffer above ECB requirements, enabling growth and dividends\",\"severity\":\"medium\",\"confidence\":\"high\"}")
S5_ID=$(echo "$S5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Weaknesses
W1=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"weakness\",\"description\":\"Cost-to-income ratio (52.8%) above strategic target of 50% — IT modernization costs and regulatory compliance burden\",\"severity\":\"high\",\"confidence\":\"high\"}")
W1_ID=$(echo "$W1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

W2=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"weakness\",\"description\":\"Legacy IT landscape across multiple geographies — core banking fragmented across markets, hindering platform banking vision\",\"severity\":\"high\",\"confidence\":\"high\"}")
W2_ID=$(echo "$W2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

W3=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"weakness\",\"description\":\"NIM pressure at 1.58% — lower than US peers, squeezed by ECB rate environment and deposit competition\",\"severity\":\"high\",\"confidence\":\"medium\"}")
W3_ID=$(echo "$W3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

W4=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"weakness\",\"description\":\"Exited multiple markets (US, France, Czech Republic, Austria) — reduced geographic footprint limits growth options\",\"severity\":\"medium\",\"confidence\":\"high\"}")
W4_ID=$(echo "$W4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Opportunities
O1=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"opportunity\",\"description\":\"Platform banking model — build open banking marketplace connecting ING customers to third-party financial services via APIs\",\"severity\":\"high\",\"confidence\":\"medium\"}")
O1_ID=$(echo "$O1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

O2=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"opportunity\",\"description\":\"EU Green Deal and CSRD creating massive demand for sustainable finance products, ESG advisory, and transition financing\",\"severity\":\"high\",\"confidence\":\"high\"}")
O2_ID=$(echo "$O2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

O3=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"opportunity\",\"description\":\"Gen AI for banking operations — potential EUR 500M+ cost savings across compliance, operations, and customer service\",\"severity\":\"high\",\"confidence\":\"medium\"}")
O3_ID=$(echo "$O3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

O4=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"opportunity\",\"description\":\"Digital euro (ECB CBDC) — early mover advantage in distribution and wallet infrastructure for European central bank digital currency\",\"severity\":\"medium\",\"confidence\":\"low\"}")
O4_ID=$(echo "$O4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Threats
T1=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"threat\",\"description\":\"European neobank competition: Revolut (40M+ users), N26, Bunq growing rapidly in ING core markets with lower cost structures\",\"severity\":\"high\",\"confidence\":\"high\"}")
T1_ID=$(echo "$T1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

T2=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"threat\",\"description\":\"ECB regulatory tightening — higher capital requirements, DORA operational resilience mandate, AI Act compliance\",\"severity\":\"high\",\"confidence\":\"high\"}")
T2_ID=$(echo "$T2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

T3=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"threat\",\"description\":\"Geopolitical risk: Russia-Ukraine conflict impact on European economy, energy transition disruption to wholesale lending clients\",\"severity\":\"high\",\"confidence\":\"medium\"}")
T3_ID=$(echo "$T3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

T4=$(post "$API/step3/swot" "{\"business_unit_id\":$ING_BU_ID,\"category\":\"threat\",\"description\":\"Big Tech entry: Apple Pay, Google Pay reducing bank payment relevance; potential for Apple/Google savings accounts in Europe\",\"severity\":\"medium\",\"confidence\":\"medium\"}")
T4_ID=$(echo "$T4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "SWOT IDs: S=$S1_ID,$S2_ID,$S3_ID,$S4_ID,$S5_ID W=$W1_ID,$W2_ID,$W3_ID,$W4_ID O=$O1_ID,$O2_ID,$O3_ID,$O4_ID T=$T1_ID,$T2_ID,$T3_ID,$T4_ID"

echo -e "\n--- Step 3: TOWS Actions ---"
TOWS1=$(post "$API/step3/tows" "{\"strategy_type\":\"SO\",\"swot_entry_1_id\":$S1_ID,\"swot_entry_2_id\":$O1_ID,\"action_description\":\"Build ING platform banking marketplace — leverage digital-first DNA to create open banking ecosystem connecting customers to embedded finance services\",\"priority\":\"critical\",\"impact_score\":9,\"rationale\":\"Digital leadership + open banking = platform revenue model beyond NII\"}")
TOWS1_ID=$(echo "$TOWS1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS2=$(post "$API/step3/tows" "{\"strategy_type\":\"SO\",\"swot_entry_1_id\":$S3_ID,\"swot_entry_2_id\":$O2_ID,\"action_description\":\"Become the #1 European bank for sustainable finance — scale Terra approach, build ESG advisory platform, lead transition financing for corporate clients\",\"priority\":\"critical\",\"impact_score\":10,\"rationale\":\"ESG leadership + Green Deal mandate = massive addressable market\"}")
TOWS2_ID=$(echo "$TOWS2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS3=$(post "$API/step3/tows" "{\"strategy_type\":\"WO\",\"swot_entry_1_id\":$W1_ID,\"swot_entry_2_id\":$O3_ID,\"action_description\":\"Deploy Gen AI across operations to achieve sub-50% cost-to-income ratio — automate trade operations, compliance, customer service, and internal processes\",\"priority\":\"critical\",\"impact_score\":9,\"rationale\":\"AI directly addresses cost weakness while leapfrogging legacy IT constraints\"}")
TOWS3_ID=$(echo "$TOWS3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS4=$(post "$API/step3/tows" "{\"strategy_type\":\"WO\",\"swot_entry_1_id\":$W2_ID,\"swot_entry_2_id\":$O1_ID,\"action_description\":\"Migrate to unified cloud-native core banking platform across all markets — enable platform banking and reduce per-market IT cost\",\"priority\":\"high\",\"impact_score\":8,\"rationale\":\"Platform vision requires unified technology foundation across geographies\"}")
TOWS4_ID=$(echo "$TOWS4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS5=$(post "$API/step3/tows" "{\"strategy_type\":\"ST\",\"swot_entry_1_id\":$S1_ID,\"swot_entry_2_id\":$T1_ID,\"action_description\":\"Accelerate mobile-first innovation — match neobank UX while leveraging full banking license, deposit guarantee, and wholesale banking cross-sell\",\"priority\":\"high\",\"impact_score\":8,\"rationale\":\"ING has scale and trust that neobanks lack; need UX parity\"}")
TOWS5_ID=$(echo "$TOWS5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS6=$(post "$API/step3/tows" "{\"strategy_type\":\"WT\",\"swot_entry_1_id\":$W3_ID,\"swot_entry_2_id\":$T2_ID,\"action_description\":\"Diversify revenue beyond NII — grow fee income via platform services, sustainable finance advisory, and wealth management to reduce rate sensitivity\",\"priority\":\"high\",\"impact_score\":7,\"rationale\":\"NIM pressure + regulatory capital costs require fee-based revenue growth\"}")
TOWS6_ID=$(echo "$TOWS6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "TOWS IDs: $TOWS1_ID,$TOWS2_ID,$TOWS3_ID,$TOWS4_ID,$TOWS5_ID,$TOWS6_ID"

# ============================================================
# Step 4: Four-Layer Strategy & Strategic OKRs
# ============================================================
echo -e "\n--- Step 4: Strategy Inputs ---"
post "$API/step4/inputs" '{"input_type":"business_strategy","title":"ING Group Strategic Plan 2025-2028 — Growing the Difference","content":"Three strategic pillars: (1) Superior customer experience through mobile-first digital banking, (2) Sustainable finance leadership targeting EUR 175B by 2027, (3) Operational excellence via AI and platform banking model. Financial targets: ROE >14%, CIR <50%, CET1 ~14%. Grow primary customers to 16M mobile-first."}'
post "$API/step4/inputs" '{"input_type":"digital_strategy","title":"ING Technology & Platform Strategy","content":"Unified core banking platform across markets (Project Phoenix). API-first architecture enabling platform banking. Cloud migration to AWS/Azure (target 80% by 2027). AI/ML at scale for risk, compliance, personalization. Digital identity and open banking leadership. DORA compliance embedded in architecture."}'
post "$API/step4/inputs" '{"input_type":"data_strategy","title":"ING Enterprise Data Strategy","content":"Customer 360 data platform across all markets. Real-time data streaming for fraud and personalization. EU data sovereignty compliance. Privacy-by-design with GDPR excellence. Sustainability data platform for ESG scoring and EU Taxonomy alignment. Data mesh for business unit autonomy with central governance."}'
post "$API/step4/inputs" '{"input_type":"gen_ai_strategy","title":"ING AI & Gen AI Roadmap","content":"Four pillars: (1) Customer AI — personalized financial coaching, conversational banking via Gen AI, (2) Operations AI — trade document processing, compliance automation, KYC, (3) Risk AI — credit decisioning, fraud detection, AML, (4) Sustainability AI — ESG scoring, climate risk modelling, EU Taxonomy classification. Governance: EU AI Act compliance, ECB expectations, model risk management, responsible AI framework."}'
post "$API/step4/inputs" '{"input_type":"competitor_strategy","title":"European Banking Competitive Landscape 2025","content":"Revolut reached 40M users and profitability — threatening retail deposits. N26 expanding business banking. Bunq growing in NL/DE/FR with sustainability positioning. Traditional peers (ABN, Rabo, BNP) investing heavily in digital. Big Tech payments reducing bank transaction relevance. Key ING differentiator: scale digital bank with wholesale cross-sell and sustainability leadership."}'
post "$API/step4/inputs" '{"input_type":"document_reference","title":"ECB DORA Implementation Guidelines 2025","content":"Digital Operational Resilience Act requirements: ICT risk management framework, incident reporting, digital operational resilience testing, third-party risk management. Compliance deadline January 2025. Key actions: classify critical ICT providers, establish incident response, conduct threat-led penetration testing.","file_name":"ecb_dora_guidelines_2025.pdf"}'
post "$API/step4/inputs" '{"input_type":"document_reference","title":"EU AI Act — Financial Services Impact Assessment","content":"High-risk AI classification for credit scoring, insurance pricing, and fraud detection. Requirements: transparency, human oversight, bias testing, model documentation. Compliance timeline: August 2025 for prohibited AI, August 2026 for high-risk. ING exposure: credit models, AML screening, customer profiling.","file_name":"eu_ai_act_fs_impact.pdf"}'
post "$API/step4/inputs" '{"input_type":"document_reference","title":"ING Terra Approach — Climate Alignment Methodology","content":"Sector-specific decarbonization pathways for lending portfolio. Covers 9 sectors: power generation, oil & gas, automotive, steel, cement, residential real estate, commercial real estate, aviation, shipping. 2025 targets: 50% of portfolio climate-aligned vs Paris Agreement pathways.","file_name":"ing_terra_methodology_2025.pdf"}'

echo -e "\n--- Step 4: Strategies ---"
STR1=$(post "$API/step4/strategies" "{\"layer\":\"business\",\"name\":\"Platform Banking Ecosystem\",\"description\":\"Transform ING from traditional bank to platform banking model — open banking marketplace connecting customers to embedded financial services from ING and third parties.\",\"tows_action_id\":$TOWS1_ID,\"risk_level\":\"high\",\"risks\":\"Platform adoption, partner ecosystem quality, regulatory complexity across markets, cannibalization risk\"}")
STR1_ID=$(echo "$STR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR2=$(post "$API/step4/strategies" "{\"layer\":\"business\",\"name\":\"Sustainable Finance Leadership\",\"description\":\"Become Europe's #1 bank for sustainable finance — scale Terra approach, build ESG advisory, lead transition financing. Target EUR 175B sustainable finance volume by 2027.\",\"tows_action_id\":$TOWS2_ID,\"risk_level\":\"medium\",\"risks\":\"Greenwashing accusations, EU Taxonomy interpretation, transition risk in high-carbon sectors, ESG data quality\"}")
STR2_ID=$(echo "$STR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR3=$(post "$API/step4/strategies" "{\"layer\":\"digital\",\"name\":\"AI-Powered Operations Excellence\",\"description\":\"Deploy Gen AI and ML across banking operations to achieve sub-50% cost-to-income ratio. Automate trade finance, compliance, customer service, and risk assessment.\",\"tows_action_id\":$TOWS3_ID,\"risk_level\":\"high\",\"risks\":\"EU AI Act compliance, model risk, employee displacement, ECB scrutiny of AI in critical processes\"}")
STR3_ID=$(echo "$STR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR4=$(post "$API/step4/strategies" "{\"layer\":\"digital\",\"name\":\"Unified Cloud-Native Core Banking\",\"description\":\"Migrate all markets to unified cloud-native core banking platform (Project Phoenix) — single platform for retail across NL, BE, DE, PL, ES, AU.\",\"tows_action_id\":$TOWS4_ID,\"risk_level\":\"high\",\"risks\":\"Migration risk, market-specific regulatory requirements, cost overruns, business disruption during transition\"}")
STR4_ID=$(echo "$STR4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR5=$(post "$API/step4/strategies" "{\"layer\":\"data\",\"name\":\"Customer 360 & Personalisation Engine\",\"description\":\"Build pan-European customer data platform enabling real-time personalisation, financial coaching, and cross-sell across all ING products and markets.\",\"risk_level\":\"medium\",\"risks\":\"GDPR cross-border data flows, data quality across legacy systems, organizational silos, privacy concerns\"}")
STR5_ID=$(echo "$STR5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR6=$(post "$API/step4/strategies" "{\"layer\":\"gen_ai\",\"name\":\"Conversational Banking AI\",\"description\":\"Build multi-lingual Gen AI banking assistant across all ING markets — handle 60% of customer interactions via AI, provide personalised financial coaching, enable conversational transactions.\",\"risk_level\":\"medium\",\"risks\":\"Multi-language quality, financial advice regulations, customer trust, EU AI Act transparency requirements\"}")
STR6_ID=$(echo "$STR6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Strategy IDs: $STR1_ID,$STR2_ID,$STR3_ID,$STR4_ID,$STR5_ID,$STR6_ID"

echo -e "\n--- Step 4: Strategic OKRs ---"
OKR1=$(post "$API/step4/okrs" "{\"strategy_id\":$STR1_ID,\"objective\":\"Launch platform banking marketplace in 3 core markets with 2M active users by 2027\",\"time_horizon\":\"2025-2027\",\"status\":\"active\"}")
OKR1_ID=$(echo "$OKR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR2=$(post "$API/step4/okrs" "{\"strategy_id\":$STR2_ID,\"objective\":\"Grow sustainable finance volume from EUR 142B to EUR 175B and achieve #1 ESG rating among European banks\",\"time_horizon\":\"2025-2027\",\"status\":\"active\"}")
OKR2_ID=$(echo "$OKR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR3=$(post "$API/step4/okrs" "{\"strategy_id\":$STR3_ID,\"objective\":\"Reduce cost-to-income ratio from 52.8% to below 50% via AI-powered automation\",\"time_horizon\":\"2025-2027\",\"status\":\"active\"}")
OKR3_ID=$(echo "$OKR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR4=$(post "$API/step4/okrs" "{\"strategy_id\":$STR6_ID,\"objective\":\"Launch multi-lingual AI banking assistant handling 60% of customer inquiries across 6 markets\",\"time_horizon\":\"2025-2027\",\"status\":\"active\"}")
OKR4_ID=$(echo "$OKR4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR5=$(post "$API/step4/okrs" "{\"strategy_id\":$STR4_ID,\"objective\":\"Migrate 3 markets to unified cloud core banking platform by 2027\",\"time_horizon\":\"2025-2027\",\"status\":\"active\"}")
OKR5_ID=$(echo "$OKR5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR6=$(post "$API/step4/okrs" "{\"strategy_id\":$STR5_ID,\"objective\":\"Achieve unified Customer 360 view across all retail markets with real-time personalisation\",\"time_horizon\":\"2025-2027\",\"status\":\"draft\"}")
OKR6_ID=$(echo "$OKR6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "OKR IDs: $OKR1_ID,$OKR2_ID,$OKR3_ID,$OKR4_ID,$OKR5_ID,$OKR6_ID"

echo -e "\n--- Step 4: Key Results ---"
post "$API/step4/okrs/$OKR1_ID/key-results" '{"key_result":"Launch platform marketplace in NL, BE, DE","metric":"markets_launched","current_value":0,"target_value":3,"unit":"markets"}'
post "$API/step4/okrs/$OKR1_ID/key-results" '{"key_result":"Onboard 50 third-party financial service partners","metric":"platform_partners","current_value":5,"target_value":50,"unit":"partners"}'
post "$API/step4/okrs/$OKR1_ID/key-results" '{"key_result":"Achieve 2M active platform users","metric":"platform_mau","current_value":0,"target_value":2000000,"unit":"users"}'

post "$API/step4/okrs/$OKR2_ID/key-results" '{"key_result":"Sustainable finance volume reaches EUR 175B","metric":"sustainable_finance_eur_b","current_value":142,"target_value":175,"unit":"EUR B"}'
post "$API/step4/okrs/$OKR2_ID/key-results" '{"key_result":"100% of wholesale lending portfolio assessed against Terra pathways","metric":"terra_coverage_pct","current_value":72,"target_value":100,"unit":"%"}'
post "$API/step4/okrs/$OKR2_ID/key-results" '{"key_result":"Top 3 ESG rating from all major agencies (MSCI, Sustainalytics, CDP)","metric":"esg_top3_agencies","current_value":2,"target_value":3,"unit":"agencies"}'

post "$API/step4/okrs/$OKR3_ID/key-results" '{"key_result":"Cost-to-income ratio below 50%","metric":"cir_pct","current_value":52.8,"target_value":49.5,"unit":"%"}'
post "$API/step4/okrs/$OKR3_ID/key-results" '{"key_result":"AI automates 70% of trade document examination","metric":"trade_doc_ai_pct","current_value":15,"target_value":70,"unit":"%"}'
post "$API/step4/okrs/$OKR3_ID/key-results" '{"key_result":"Reduce compliance screening time by 50% via AI","metric":"compliance_time_reduction","current_value":10,"target_value":50,"unit":"%"}'

post "$API/step4/okrs/$OKR4_ID/key-results" '{"key_result":"AI assistant handles 60% of customer inquiries without human handoff","metric":"ai_resolution_pct","current_value":18,"target_value":60,"unit":"%"}'
post "$API/step4/okrs/$OKR4_ID/key-results" '{"key_result":"Available in 8 languages across 6 markets","metric":"languages_supported","current_value":2,"target_value":8,"unit":"languages"}'

post "$API/step4/okrs/$OKR5_ID/key-results" '{"key_result":"Migrate NL, PL, and one additional market to unified platform","metric":"markets_migrated","current_value":0,"target_value":3,"unit":"markets"}'
post "$API/step4/okrs/$OKR5_ID/key-results" '{"key_result":"80% of workloads on cloud infrastructure","metric":"cloud_workload_pct","current_value":45,"target_value":80,"unit":"%"}'

post "$API/step4/okrs/$OKR6_ID/key-results" '{"key_result":"Unified customer profiles across 6 retail markets","metric":"unified_markets","current_value":1,"target_value":6,"unit":"markets"}'

echo " done"

# ============================================================
# Step 5: Digital Initiatives & RICE Prioritization
# ============================================================
echo -e "\n--- Step 5: Product Groups & Digital Products ---"
PG1=$(post "$API/step5/product-groups" '{"name":"Platform Banking","description":"Open banking marketplace, APIs, and embedded finance platform"}')
PG1_ID=$(echo "$PG1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

PG2=$(post "$API/step5/product-groups" '{"name":"Sustainable Finance","description":"ESG scoring, Terra alignment, and green finance products"}')
PG2_ID=$(echo "$PG2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

PG3=$(post "$API/step5/product-groups" '{"name":"AI & Automation","description":"Gen AI banking assistant, operations automation, and ML risk models"}')
PG3_ID=$(echo "$PG3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

PG4=$(post "$API/step5/product-groups" '{"name":"Core Banking Platform","description":"Unified cloud-native core banking and customer data platform"}')
PG4_ID=$(echo "$PG4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP1=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG1_ID,\"name\":\"ING Marketplace\",\"description\":\"Open banking marketplace connecting ING customers to third-party financial services\"}")
DP1_ID=$(echo "$DP1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP2=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG2_ID,\"name\":\"ESG Scoring Platform\",\"description\":\"Automated ESG assessment and EU Taxonomy classification for wholesale lending\"}")
DP2_ID=$(echo "$DP2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP3=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG3_ID,\"name\":\"ING AI Banking Assistant\",\"description\":\"Multi-lingual conversational AI for customer service, financial coaching, and transactions\"}")
DP3_ID=$(echo "$DP3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP4=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG3_ID,\"name\":\"Trade Document AI\",\"description\":\"AI-powered trade finance document examination and compliance automation\"}")
DP4_ID=$(echo "$DP4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP5=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG4_ID,\"name\":\"Project Phoenix Core Banking\",\"description\":\"Unified cloud-native core banking platform for all ING retail markets\"}")
DP5_ID=$(echo "$DP5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP6=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG4_ID,\"name\":\"Customer 360 Platform\",\"description\":\"Pan-European customer data platform with real-time personalisation engine\"}")
DP6_ID=$(echo "$DP6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Product Group IDs: $PG1_ID,$PG2_ID,$PG3_ID,$PG4_ID | Digital Product IDs: $DP1_ID,$DP2_ID,$DP3_ID,$DP4_ID,$DP5_ID,$DP6_ID"

echo -e "\n--- Step 5: Initiatives ---"
INIT1=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP1_ID,\"strategy_id\":$STR1_ID,\"name\":\"Open Banking Marketplace MVP\",\"description\":\"Launch marketplace in Netherlands with insurance, investment, and pension partners accessible via ING app\",\"reach\":2000000,\"impact\":3,\"confidence\":0.8,\"effort\":14,\"value_score\":5,\"size_score\":5,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT1_ID=$(echo "$INIT1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT2=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP2_ID,\"strategy_id\":$STR2_ID,\"name\":\"Automated ESG Scoring & EU Taxonomy Classification\",\"description\":\"AI-powered ESG assessment engine that auto-classifies wholesale lending against EU Taxonomy criteria and Terra sector pathways\",\"reach\":5000,\"impact\":3,\"confidence\":0.8,\"effort\":10,\"value_score\":5,\"size_score\":4,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT2_ID=$(echo "$INIT2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT3=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP3_ID,\"strategy_id\":$STR6_ID,\"name\":\"Multi-Lingual Gen AI Banking Assistant\",\"description\":\"Deploy conversational AI assistant in Dutch, English, German, Polish, Spanish, French across ING retail markets\",\"reach\":14000000,\"impact\":2,\"confidence\":0.8,\"effort\":16,\"value_score\":5,\"size_score\":5,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT3_ID=$(echo "$INIT3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT4=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP4_ID,\"strategy_id\":$STR3_ID,\"name\":\"AI Trade Document Examiner\",\"description\":\"Computer vision + NLP system to automatically examine trade finance documents for UCP 600 compliance, replacing 70% of manual examination\",\"reach\":2000,\"impact\":3,\"confidence\":0.8,\"effort\":12,\"value_score\":5,\"size_score\":4,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT4_ID=$(echo "$INIT4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT5=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP5_ID,\"strategy_id\":$STR4_ID,\"name\":\"Project Phoenix — NL Core Migration\",\"description\":\"Migrate Dutch retail banking to unified cloud-native core platform — first market on Project Phoenix\",\"reach\":8000000,\"impact\":3,\"confidence\":0.5,\"effort\":24,\"value_score\":5,\"size_score\":5,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT5_ID=$(echo "$INIT5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT6=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP6_ID,\"strategy_id\":$STR5_ID,\"name\":\"Customer 360 Data Platform\",\"description\":\"Build unified customer data platform with real-time event streaming, ML feature store, and personalisation engine\",\"reach\":14000000,\"impact\":2,\"confidence\":0.8,\"effort\":14,\"value_score\":4,\"size_score\":5,\"roadmap_phase\":\"Phase 1\",\"status\":\"approved\"}")
INIT6_ID=$(echo "$INIT6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT7=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP2_ID,\"strategy_id\":$STR2_ID,\"name\":\"Retail Green Mortgage Calculator\",\"description\":\"Energy efficiency scoring tool integrated into mortgage flow — recommend green improvements and offer preferential rates for sustainable properties\",\"reach\":500000,\"impact\":2,\"confidence\":1.0,\"effort\":6,\"value_score\":4,\"size_score\":3,\"roadmap_phase\":\"Phase 1\",\"status\":\"approved\"}")
INIT7_ID=$(echo "$INIT7" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT8=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP3_ID,\"strategy_id\":$STR3_ID,\"name\":\"AML & Sanctions Screening AI\",\"description\":\"ML-powered AML and sanctions screening with 50% reduction in false positives and automated SAR narrative generation\",\"reach\":1000,\"impact\":3,\"confidence\":0.5,\"effort\":14,\"value_score\":4,\"size_score\":4,\"roadmap_phase\":\"Phase 2\",\"status\":\"proposed\"}")
INIT8_ID=$(echo "$INIT8" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Initiative IDs: $INIT1_ID,$INIT2_ID,$INIT3_ID,$INIT4_ID,$INIT5_ID,$INIT6_ID,$INIT7_ID,$INIT8_ID"

# ============================================================
# Step 6: Epics & Teams + Product OKRs
# ============================================================
echo -e "\n--- Step 6: Teams ---"
TEAM1=$(post "$API/step6/teams" '{"name":"Platform Engineering","capacity":28}')
TEAM1_ID=$(echo "$TEAM1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM2=$(post "$API/step6/teams" '{"name":"Sustainable Finance Tech","capacity":15}')
TEAM2_ID=$(echo "$TEAM2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM3=$(post "$API/step6/teams" '{"name":"AI & Data Science","capacity":25}')
TEAM3_ID=$(echo "$TEAM3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM4=$(post "$API/step6/teams" '{"name":"Core Banking (Phoenix)","capacity":40}')
TEAM4_ID=$(echo "$TEAM4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM5=$(post "$API/step6/teams" '{"name":"Trade Finance Technology","capacity":18}')
TEAM5_ID=$(echo "$TEAM5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM6=$(post "$API/step6/teams" '{"name":"Customer Data & Analytics","capacity":20}')
TEAM6_ID=$(echo "$TEAM6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Team IDs: $TEAM1_ID,$TEAM2_ID,$TEAM3_ID,$TEAM4_ID,$TEAM5_ID,$TEAM6_ID"

echo -e "\n--- Step 6: Product OKRs ---"
POKR1=$(post "$API/step6/product-okrs" "{\"strategic_okr_id\":$OKR1_ID,\"digital_product_id\":$DP1_ID,\"objective\":\"Launch marketplace MVP in Netherlands with 500K users in first year\",\"status\":\"active\"}")
POKR1_ID=$(echo "$POKR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

POKR2=$(post "$API/step6/product-okrs" "{\"strategic_okr_id\":$OKR2_ID,\"digital_product_id\":$DP2_ID,\"objective\":\"Auto-classify 100% of new wholesale lending against EU Taxonomy by H2 2026\",\"status\":\"active\"}")
POKR2_ID=$(echo "$POKR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

POKR3=$(post "$API/step6/product-okrs" "{\"strategic_okr_id\":$OKR4_ID,\"digital_product_id\":$DP3_ID,\"objective\":\"Launch AI assistant in NL and DE with 40% inquiry resolution rate\",\"status\":\"active\"}")
POKR3_ID=$(echo "$POKR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

POKR4=$(post "$API/step6/product-okrs" "{\"strategic_okr_id\":$OKR5_ID,\"digital_product_id\":$DP5_ID,\"objective\":\"Complete Project Phoenix NL migration with zero customer impact\",\"status\":\"active\"}")
POKR4_ID=$(echo "$POKR4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Product OKR IDs: $POKR1_ID,$POKR2_ID,$POKR3_ID,$POKR4_ID"

echo -e "\n--- Step 6: Epics ---"
EPIC1=$(post "$API/step6/epics" "{\"initiative_id\":$INIT1_ID,\"team_id\":$TEAM1_ID,\"product_okr_id\":$POKR1_ID,\"name\":\"Open Banking API Gateway\",\"description\":\"Build PSD2-compliant API gateway with partner onboarding, consent management, and billing\",\"status\":\"in_progress\",\"start_date\":\"2025-07-01\",\"target_date\":\"2026-02-01\",\"value_score\":5,\"size_score\":5,\"effort_score\":5,\"risk_level\":\"high\",\"risks\":\"PSD2/PSD3 regulatory changes, partner API quality, data privacy compliance\",\"roadmap_phase\":\"Phase 1\"}")
EPIC1_ID=$(echo "$EPIC1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC2=$(post "$API/step6/epics" "{\"initiative_id\":$INIT1_ID,\"team_id\":$TEAM1_ID,\"product_okr_id\":$POKR1_ID,\"name\":\"Marketplace Frontend & Partner UX\",\"description\":\"In-app marketplace UI with partner product discovery, comparison, and one-click activation\",\"status\":\"backlog\",\"start_date\":\"2025-12-01\",\"target_date\":\"2026-04-01\",\"value_score\":4,\"size_score\":4,\"effort_score\":3,\"risk_level\":\"medium\",\"roadmap_phase\":\"Phase 1\"}")
EPIC2_ID=$(echo "$EPIC2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC3=$(post "$API/step6/epics" "{\"initiative_id\":$INIT2_ID,\"team_id\":$TEAM2_ID,\"product_okr_id\":$POKR2_ID,\"name\":\"EU Taxonomy Classification Engine\",\"description\":\"Build automated classification engine mapping wholesale lending activities to EU Taxonomy technical screening criteria\",\"status\":\"in_progress\",\"start_date\":\"2025-06-01\",\"target_date\":\"2026-01-01\",\"value_score\":5,\"size_score\":4,\"effort_score\":4,\"risk_level\":\"medium\",\"risks\":\"EU Taxonomy interpretation ambiguity, data availability from clients, audit requirements\",\"roadmap_phase\":\"Phase 1\"}")
EPIC3_ID=$(echo "$EPIC3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC4=$(post "$API/step6/epics" "{\"initiative_id\":$INIT3_ID,\"team_id\":$TEAM3_ID,\"product_okr_id\":$POKR3_ID,\"name\":\"Conversational Banking Engine\",\"description\":\"Multi-lingual Gen AI conversational engine with financial domain fine-tuning, safety guardrails, and transaction capabilities\",\"status\":\"in_progress\",\"start_date\":\"2025-08-01\",\"target_date\":\"2026-04-01\",\"value_score\":5,\"size_score\":5,\"effort_score\":5,\"risk_level\":\"high\",\"risks\":\"Multi-language quality, financial advice regulations per market, EU AI Act compliance\",\"roadmap_phase\":\"Phase 1\"}")
EPIC4_ID=$(echo "$EPIC4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC5=$(post "$API/step6/epics" "{\"initiative_id\":$INIT4_ID,\"team_id\":$TEAM5_ID,\"name\":\"Trade Document Vision AI\",\"description\":\"Computer vision and NLP model for automated trade document examination — bills of lading, invoices, certificates of origin\",\"status\":\"in_progress\",\"start_date\":\"2025-07-01\",\"target_date\":\"2026-03-01\",\"value_score\":5,\"size_score\":4,\"effort_score\":4,\"risk_level\":\"medium\",\"risks\":\"Document format variability, multi-language documents, handwritten content\",\"roadmap_phase\":\"Phase 1\"}")
EPIC5_ID=$(echo "$EPIC5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC6=$(post "$API/step6/epics" "{\"initiative_id\":$INIT5_ID,\"team_id\":$TEAM4_ID,\"product_okr_id\":$POKR4_ID,\"name\":\"Phoenix NL Data Migration\",\"description\":\"Migrate 8M Dutch retail customer accounts, transactions, and products from legacy to Phoenix cloud platform\",\"status\":\"in_progress\",\"start_date\":\"2025-06-01\",\"target_date\":\"2026-09-01\",\"value_score\":5,\"size_score\":5,\"effort_score\":5,\"risk_level\":\"high\",\"risks\":\"Data integrity during migration, regulatory compliance, customer impact, rollback complexity\",\"roadmap_phase\":\"Phase 1\"}")
EPIC6_ID=$(echo "$EPIC6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC7=$(post "$API/step6/epics" "{\"initiative_id\":$INIT5_ID,\"team_id\":$TEAM4_ID,\"product_okr_id\":$POKR4_ID,\"name\":\"Phoenix SEPA & iDEAL Integration\",\"description\":\"Implement SEPA payments, iDEAL, and Dutch direct debit (incasso) on Phoenix platform with full Betaalvereniging compliance\",\"status\":\"backlog\",\"start_date\":\"2026-01-01\",\"target_date\":\"2026-06-01\",\"value_score\":5,\"size_score\":4,\"effort_score\":4,\"risk_level\":\"high\",\"risks\":\"SEPA scheme compliance, iDEAL 2.0 migration timing, payment processing continuity\",\"roadmap_phase\":\"Phase 1\"}")
EPIC7_ID=$(echo "$EPIC7" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC8=$(post "$API/step6/epics" "{\"initiative_id\":$INIT7_ID,\"team_id\":$TEAM2_ID,\"product_okr_id\":$POKR2_ID,\"name\":\"Green Mortgage Energy Scoring\",\"description\":\"Build energy efficiency scoring engine integrated with Dutch energy label data (EP-online) for mortgage pricing incentives\",\"status\":\"backlog\",\"start_date\":\"2026-02-01\",\"target_date\":\"2026-07-01\",\"value_score\":3,\"size_score\":3,\"effort_score\":2,\"risk_level\":\"low\",\"roadmap_phase\":\"Phase 2\"}")
EPIC8_ID=$(echo "$EPIC8" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Epic IDs: $EPIC1_ID,$EPIC2_ID,$EPIC3_ID,$EPIC4_ID,$EPIC5_ID,$EPIC6_ID,$EPIC7_ID,$EPIC8_ID"

echo -e "\n--- Step 6: Epic Dependencies ---"
post "$API/step6/dependencies" "{\"epic_id\":$EPIC2_ID,\"depends_on_epic_id\":$EPIC1_ID,\"dependency_type\":\"blocks\",\"notes\":\"Marketplace frontend needs API gateway operational for partner integration\"}"
post "$API/step6/dependencies" "{\"epic_id\":$EPIC7_ID,\"depends_on_epic_id\":$EPIC6_ID,\"dependency_type\":\"blocks\",\"notes\":\"Payment integration needs data migration to be substantially complete\"}"
post "$API/step6/dependencies" "{\"epic_id\":$EPIC4_ID,\"depends_on_epic_id\":$EPIC6_ID,\"dependency_type\":\"relates_to\",\"notes\":\"AI assistant benefits from Phoenix platform for customer data access\"}"

echo " done"

# ============================================================
# Step 7: Features & Roadmap + Delivery OKRs
# ============================================================
echo -e "\n--- Step 7: Delivery OKRs ---"
DOKR1=$(post "$API/step7/delivery-okrs" "{\"product_okr_id\":$POKR1_ID,\"team_id\":$TEAM1_ID,\"objective\":\"Ship marketplace API gateway with 10 partners integrated and 99.9% uptime\",\"status\":\"active\"}")
DOKR1_ID=$(echo "$DOKR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DOKR2=$(post "$API/step7/delivery-okrs" "{\"product_okr_id\":$POKR2_ID,\"team_id\":$TEAM2_ID,\"objective\":\"Deploy EU Taxonomy classification engine with 90% auto-classification accuracy\",\"status\":\"active\"}")
DOKR2_ID=$(echo "$DOKR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DOKR3=$(post "$API/step7/delivery-okrs" "{\"product_okr_id\":$POKR3_ID,\"team_id\":$TEAM3_ID,\"objective\":\"Launch AI assistant in NL and DE with 4.0+ CSAT score\",\"status\":\"active\"}")
DOKR3_ID=$(echo "$DOKR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DOKR4=$(post "$API/step7/delivery-okrs" "{\"product_okr_id\":$POKR4_ID,\"team_id\":$TEAM4_ID,\"objective\":\"Complete Phoenix NL migration with <30min total downtime across all cutover windows\",\"status\":\"active\"}")
DOKR4_ID=$(echo "$DOKR4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Delivery OKR IDs: $DOKR1_ID,$DOKR2_ID,$DOKR3_ID,$DOKR4_ID"

echo -e "\n--- Step 7: Features ---"
# Features for Epic 1: Open Banking API Gateway
post "$API/step7/features" "{\"epic_id\":$EPIC1_ID,\"delivery_okr_id\":$DOKR1_ID,\"name\":\"PSD2/PSD3 Consent Management\",\"description\":\"Dynamic consent management supporting PSD2 strong customer authentication and upcoming PSD3 requirements\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":16,\"start_date\":\"2025-07-15\",\"target_date\":\"2025-12-01\",\"roadmap_phase\":\"Phase 1\",\"acceptance_criteria\":\"PSD2 SCA compliance verified, consent lifecycle management, 90-day renewal flows\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC1_ID,\"delivery_okr_id\":$DOKR1_ID,\"name\":\"Partner Onboarding & Sandbox\",\"description\":\"Self-service partner onboarding portal with sandbox environment, API documentation, and compliance checks\",\"priority\":\"high\",\"status\":\"in_progress\",\"estimated_effort\":12,\"start_date\":\"2025-08-01\",\"target_date\":\"2025-12-15\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC1_ID,\"delivery_okr_id\":$DOKR1_ID,\"name\":\"Revenue Sharing & Billing Engine\",\"description\":\"Automated revenue sharing calculations and billing for marketplace partners based on referrals and transactions\",\"priority\":\"medium\",\"status\":\"backlog\",\"estimated_effort\":8,\"roadmap_phase\":\"Phase 1\"}"

# Features for Epic 3: EU Taxonomy Classification
post "$API/step7/features" "{\"epic_id\":$EPIC3_ID,\"delivery_okr_id\":$DOKR2_ID,\"name\":\"Technical Screening Criteria Rules Engine\",\"description\":\"Rules engine implementing EU Taxonomy technical screening criteria for all 6 environmental objectives across eligible sectors\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":18,\"start_date\":\"2025-06-15\",\"target_date\":\"2025-12-15\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC3_ID,\"delivery_okr_id\":$DOKR2_ID,\"name\":\"Client ESG Data Ingestion\",\"description\":\"Automated ingestion of client sustainability reports, CDP filings, and emissions data for ESG scoring input\",\"priority\":\"high\",\"status\":\"in_progress\",\"estimated_effort\":10,\"start_date\":\"2025-07-01\",\"target_date\":\"2025-11-01\",\"roadmap_phase\":\"Phase 1\"}"

# Features for Epic 4: Conversational AI
post "$API/step7/features" "{\"epic_id\":$EPIC4_ID,\"delivery_okr_id\":$DOKR3_ID,\"name\":\"Dutch Financial NLP Model\",\"description\":\"Fine-tuned LLM for Dutch financial conversations — banking terminology, regulatory disclosures, and cultural context\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":20,\"start_date\":\"2025-08-15\",\"target_date\":\"2026-01-15\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC4_ID,\"delivery_okr_id\":$DOKR3_ID,\"name\":\"Transactional AI Capabilities\",\"description\":\"Enable AI assistant to execute transactions (transfers, payments, card controls) with multi-factor authentication\",\"priority\":\"high\",\"status\":\"backlog\",\"estimated_effort\":14,\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC4_ID,\"delivery_okr_id\":$DOKR3_ID,\"name\":\"Financial Coaching Module\",\"description\":\"AI-powered personalised financial insights — spending analysis, savings recommendations, investment suggestions\",\"priority\":\"medium\",\"status\":\"backlog\",\"estimated_effort\":10,\"roadmap_phase\":\"Phase 2\"}"

# Features for Epic 5: Trade Document AI
post "$API/step7/features" "{\"epic_id\":$EPIC5_ID,\"name\":\"Bill of Lading OCR & Validation\",\"description\":\"Computer vision model for bill of lading extraction with UCP 600 field validation and discrepancy detection\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":16,\"start_date\":\"2025-07-15\",\"target_date\":\"2025-12-15\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC5_ID,\"name\":\"Multi-Document Cross-Reference\",\"description\":\"Cross-reference data across LC, invoice, packing list, and transport documents to identify inconsistencies\",\"priority\":\"high\",\"status\":\"backlog\",\"estimated_effort\":12,\"roadmap_phase\":\"Phase 1\"}"

# Features for Epic 6: Phoenix NL Migration
post "$API/step7/features" "{\"epic_id\":$EPIC6_ID,\"delivery_okr_id\":$DOKR4_ID,\"name\":\"Customer Data Migration Pipeline\",\"description\":\"ETL pipeline for migrating 8M customer profiles, accounts, and transaction history with full data validation\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":22,\"start_date\":\"2025-06-15\",\"target_date\":\"2026-03-01\",\"roadmap_phase\":\"Phase 1\",\"acceptance_criteria\":\"100% data integrity validation, <0.001% error rate, full audit trail\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC6_ID,\"delivery_okr_id\":$DOKR4_ID,\"name\":\"Dual-Run Reconciliation Engine\",\"description\":\"Real-time reconciliation between legacy and Phoenix systems during parallel-run period\",\"priority\":\"critical\",\"status\":\"backlog\",\"estimated_effort\":18,\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC6_ID,\"delivery_okr_id\":$DOKR4_ID,\"name\":\"Automated Rollback Framework\",\"description\":\"Automated rollback capability with <15min recovery time in case of critical issues during migration cutover\",\"priority\":\"high\",\"status\":\"backlog\",\"estimated_effort\":14,\"roadmap_phase\":\"Phase 1\"}"

echo " done"

# ============================================================
# Review Gates (HITL checkpoints)
# ============================================================
echo -e "\n--- Review Gates ---"
post "$API/gates/" '{"step_number":1,"gate_number":1,"gate_name":"Financial & Market Data Validation","status":"approved","reviewer":"Group CFO Office","review_notes":"Financial data validated against ING Group annual report. Competitor data cross-referenced with ECB statistics."}'
post "$API/gates/" '{"step_number":2,"gate_number":1,"gate_name":"Value Stream Analysis Review","status":"approved","reviewer":"COO","review_notes":"Digital onboarding and trade finance VSMs validated. Bottlenecks confirmed by operations teams."}'
post "$API/gates/" '{"step_number":3,"gate_number":1,"gate_name":"SWOT & Competitive Review","status":"approved","reviewer":"Chief Strategy Officer","review_notes":"Neobank threat validated. Sustainability leadership strategy endorsed. Platform banking approach approved."}'
post "$API/gates/" '{"step_number":4,"gate_number":1,"gate_name":"Strategy & OKR Alignment","status":"approved","reviewer":"Management Board","review_notes":"Strategies aligned with Growing the Difference vision. EU regulatory compliance confirmed as cross-cutting priority."}'
post "$API/gates/" '{"step_number":4,"gate_number":2,"gate_name":"EU Regulatory Compliance Gate","status":"approved","reviewer":"Chief Risk Officer","review_notes":"EU AI Act impact assessed. DORA compliance roadmap confirmed. PSD3 preparation embedded in platform strategy."}'
post "$API/gates/" '{"step_number":5,"gate_number":1,"gate_name":"Initiative RICE Prioritization","status":"approved","reviewer":"CTO","review_notes":"RICE scores validated. Project Phoenix and AI assistant confirmed as top-priority investments."}'
post "$API/gates/" '{"step_number":6,"gate_number":1,"gate_name":"Epic & Team Allocation","status":"pending","reviewer":"VP Engineering","review_notes":"Pending review of Phoenix team capacity — may need additional 10 engineers for migration timeline."}'
post "$API/gates/" '{"step_number":7,"gate_number":1,"gate_name":"Feature Roadmap & Release Planning","status":"pending","reviewer":"Product Council","review_notes":"Awaiting EU AI Act final guidance on high-risk AI classification for financial services features."}'

echo -e "\n\n=== SEEDING COMPLETE FOR ING BANK ==="
echo "Summary:"
echo "  Organization: ING Group (Banking & Financial Services)"
echo "  Step 1: 5 BUs, 19 revenue splits, 17 ops metrics, 4 competitors, 4 data URLs"
echo "  Step 2: 4 value streams, 17 steps, 6 levers"
echo "  Step 3: 5 strengths, 4 weaknesses, 4 opportunities, 4 threats, 6 TOWS actions"
echo "  Step 4: 8 strategy inputs (incl 3 documents), 6 strategies, 6 OKRs, 15 key results"
echo "  Step 5: 4 product groups, 6 digital products, 8 initiatives (RICE scored)"
echo "  Step 6: 6 teams, 4 product OKRs, 8 epics, 3 dependencies"
echo "  Step 7: 4 delivery OKRs, 16 features"
echo "  Review Gates: 8 gates (6 approved, 2 pending)"
