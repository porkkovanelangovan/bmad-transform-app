#!/bin/bash
# Seed test data for Apple — all 7 steps
# Usage: bash seed_test_data.sh [BASE_URL]
BASE="${1:-https://business-transformation-architect.onrender.com}"
API="$BASE/api"

post() {
  local url="$1"
  local data="$2"
  curl -s -X POST "$url" -H 'Content-Type: application/json' -d "$data"
}

echo "=== Seeding test data for Apple at $BASE ==="

# ============================================================
# Organization
# ============================================================
echo -e "\n--- Organization ---"
post "$API/step1/organization" '{"name":"Apple","industry":"Technology","competitor_1_name":"Microsoft","competitor_2_name":"Samsung"}'

# ============================================================
# Step 1: Business Performance Dashboard
# ============================================================
echo -e "\n--- Step 1: Business Units ---"
# Explicitly create Apple BU first (org setup doesn't auto-create one)
post "$API/step1/business-units" '{"name":"Apple","description":"Apple Inc. — primary business unit"}'
BU2=$(post "$API/step1/business-units" '{"name":"iPhone Division","description":"Hardware: iPhone product line"}')
BU3=$(post "$API/step1/business-units" '{"name":"Services","description":"Apple Services: App Store, iCloud, Apple Music, TV+, Pay"}')
BU4=$(post "$API/step1/business-units" '{"name":"Mac & iPad","description":"Mac and iPad hardware lines"}')
BU5=$(post "$API/step1/business-units" '{"name":"Wearables & Accessories","description":"Apple Watch, AirPods, Vision Pro"}')

echo "$BU2"
echo "$BU3"
echo "$BU4"
echo "$BU5"

# Get BU IDs
BU_LIST=$(curl -s "$API/step1/business-units")
APPLE_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next((b['id'] for b in data if b['name']=='Apple'),data[0]['id']))")
IPHONE_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if b['name']=='iPhone Division'))")
SERVICES_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if b['name']=='Services'))")
MAC_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if b['name']=='Mac & iPad'))")
WEARABLE_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if b['name']=='Wearables & Accessories'))")

echo "BU IDs: Apple=$APPLE_BU_ID iPhone=$IPHONE_BU_ID Services=$SERVICES_BU_ID Mac=$MAC_BU_ID Wearable=$WEARABLE_BU_ID"

echo -e "\n--- Step 1: Revenue Splits ---"
# iPhone revenue by year
post "$API/step1/revenue-splits" "{\"business_unit_id\":$IPHONE_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"iPhone\",\"revenue\":200583,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$IPHONE_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"iPhone\",\"revenue\":205489,\"period\":\"2024\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$IPHONE_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"iPhone\",\"revenue\":200583,\"period\":\"2023\"}"

# Services revenue
post "$API/step1/revenue-splits" "{\"business_unit_id\":$SERVICES_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Services\",\"revenue\":96169,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$SERVICES_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Services\",\"revenue\":85200,\"period\":\"2024\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$SERVICES_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Services\",\"revenue\":78132,\"period\":\"2023\"}"

# Mac revenue
post "$API/step1/revenue-splits" "{\"business_unit_id\":$MAC_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Mac & iPad\",\"revenue\":54840,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$MAC_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Mac & iPad\",\"revenue\":49170,\"period\":\"2024\"}"

# Wearables revenue
post "$API/step1/revenue-splits" "{\"business_unit_id\":$WEARABLE_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Wearables & Accessories\",\"revenue\":41000,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$WEARABLE_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Wearables & Accessories\",\"revenue\":39845,\"period\":\"2024\"}"

# Regional splits
post "$API/step1/revenue-splits" "{\"business_unit_id\":$APPLE_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Americas\",\"revenue\":169658,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$APPLE_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Europe\",\"revenue\":101325,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$APPLE_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Greater China\",\"revenue\":72559,\"period\":\"2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$APPLE_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Asia Pacific\",\"revenue\":49050,\"period\":\"2025\"}"

echo " done"

echo -e "\n--- Step 1: Ops Efficiency ---"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$APPLE_BU_ID,\"metric_name\":\"Net Profit Margin\",\"metric_value\":0.2637,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$APPLE_BU_ID,\"metric_name\":\"Operating Margin\",\"metric_value\":0.3099,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$APPLE_BU_ID,\"metric_name\":\"Return on Equity (ROE)\",\"metric_value\":1.6095,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$APPLE_BU_ID,\"metric_name\":\"Return on Assets (ROA)\",\"metric_value\":0.2734,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$APPLE_BU_ID,\"metric_name\":\"EPS\",\"metric_value\":6.42,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$APPLE_BU_ID,\"metric_name\":\"Beta\",\"metric_value\":1.24,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$APPLE_BU_ID,\"metric_name\":\"Dividend Yield\",\"metric_value\":0.0044,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$APPLE_BU_ID,\"metric_name\":\"Revenue Growth (YoY)\",\"metric_value\":0.049,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$APPLE_BU_ID,\"metric_name\":\"Gross Margin\",\"metric_value\":0.462,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$APPLE_BU_ID,\"metric_name\":\"R&D as % of Revenue\",\"metric_value\":0.079,\"period\":\"TTM\"}"

# Services-specific metrics
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$SERVICES_BU_ID,\"metric_name\":\"Gross Margin\",\"metric_value\":0.74,\"period\":\"TTM\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$SERVICES_BU_ID,\"metric_name\":\"Revenue Growth (YoY)\",\"metric_value\":0.129,\"period\":\"TTM\"}"

echo " done"

echo -e "\n--- Step 1: Competitors ---"
post "$API/step1/competitors" '{"name":"Microsoft","ticker":"MSFT","market_share":0.32,"revenue":245122,"profit_margin":0.359,"operating_margin":0.449,"return_on_equity":0.381,"return_on_assets":0.191,"pe_ratio":35.2,"eps":12.41,"market_cap_value":3150000,"strengths":"Cloud dominance (Azure), Enterprise ecosystem, AI leadership (Copilot, OpenAI partnership)","weaknesses":"Mobile presence weak, Hardware market share small","data_source":"simulated"}'
post "$API/step1/competitors" '{"name":"Samsung","ticker":"005930.KS","market_share":0.20,"revenue":211870,"profit_margin":0.112,"operating_margin":0.147,"return_on_equity":0.087,"return_on_assets":0.056,"pe_ratio":18.5,"eps":4.12,"market_cap_value":385000,"strengths":"Largest smartphone vendor globally, Semiconductor manufacturing, Display technology leader","weaknesses":"Software ecosystem fragmented, Lower brand premium, AI services lag","data_source":"simulated"}'
post "$API/step1/competitors" '{"name":"Google (Alphabet)","ticker":"GOOGL","market_share":0.15,"revenue":350018,"profit_margin":0.274,"operating_margin":0.322,"return_on_equity":0.318,"return_on_assets":0.198,"pe_ratio":24.1,"eps":7.54,"market_cap_value":2080000,"strengths":"Search & advertising dominance, Android ecosystem, AI/ML leadership, Cloud growth","weaknesses":"Hardware market share small, Privacy concerns, Ad revenue concentration","data_source":"simulated"}'

echo " done"

# ============================================================
# Step 2: Value Stream Analysis
# ============================================================
echo -e "\n--- Step 2: Value Streams ---"
VS1=$(post "$API/step2/value-streams" "{\"business_unit_id\":$IPHONE_BU_ID,\"name\":\"iPhone Product Development\",\"description\":\"End-to-end product development lifecycle from concept to launch for iPhone\"}")
VS1_ID=$(echo "$VS1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

VS2=$(post "$API/step2/value-streams" "{\"business_unit_id\":$SERVICES_BU_ID,\"name\":\"App Store Review & Publishing\",\"description\":\"Developer app submission through review to publishing on App Store\"}")
VS2_ID=$(echo "$VS2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

VS3=$(post "$API/step2/value-streams" "{\"business_unit_id\":$APPLE_BU_ID,\"name\":\"Customer Support Resolution\",\"description\":\"Customer issue from initial contact through Apple Support to resolution\"}")
VS3_ID=$(echo "$VS3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "VS IDs: iPhone=$VS1_ID, AppStore=$VS2_ID, Support=$VS3_ID"

echo -e "\n--- Step 2: Value Stream Steps (iPhone Dev) ---"
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":1,"step_name":"Market Research & Concept","description":"Identify market needs, competitive analysis, concept definition","step_type":"trigger","process_time_hours":480,"wait_time_hours":120,"resources":"Product Marketing, Design"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":2,"step_name":"Industrial Design","description":"Physical design, materials, form factor prototyping","step_type":"process","process_time_hours":960,"wait_time_hours":240,"resources":"Industrial Design Team"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":3,"step_name":"Hardware Engineering","description":"SoC design, camera, display, battery engineering","step_type":"process","process_time_hours":2400,"wait_time_hours":480,"resources":"Hardware Engineering","is_bottleneck":1,"notes":"Custom silicon (A-series/M-series) is longest lead-time item"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":4,"step_name":"Software Integration","description":"iOS integration, firmware, drivers, feature development","step_type":"process","process_time_hours":1920,"wait_time_hours":320,"resources":"Software Engineering"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":5,"step_name":"Testing & QA","description":"Hardware/software validation, compliance, carrier testing","step_type":"decision","process_time_hours":720,"wait_time_hours":240,"resources":"QA, Compliance"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":6,"step_name":"Mass Production","description":"Ramp up manufacturing with supply chain partners","step_type":"process","process_time_hours":1440,"wait_time_hours":480,"resources":"Operations, Supply Chain"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":7,"step_name":"Launch & Distribution","description":"Keynote, marketing campaign, global distribution","step_type":"delivery","process_time_hours":240,"wait_time_hours":48,"resources":"Marketing, Retail, Logistics"}'

echo -e "\n--- Step 2: Value Stream Steps (App Store Review) ---"
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":1,"step_name":"Developer Submission","description":"Developer uploads app binary and metadata","step_type":"trigger","process_time_hours":2,"wait_time_hours":0,"resources":"Developers (external)"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":2,"step_name":"Automated Screening","description":"Static analysis, malware scan, API compliance checks","step_type":"process","process_time_hours":0.5,"wait_time_hours":1,"resources":"Automated Systems"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":3,"step_name":"Human Review","description":"Manual review of app content, guidelines compliance, functionality","step_type":"decision","process_time_hours":4,"wait_time_hours":24,"is_bottleneck":1,"notes":"Human reviewer capacity is primary bottleneck","resources":"App Review Team"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":4,"step_name":"Publishing","description":"Approved app goes live on App Store globally","step_type":"delivery","process_time_hours":1,"wait_time_hours":2,"resources":"CDN, App Store Infrastructure"}'

# Recalculate metrics
echo -e "\n--- Step 2: Recalculate Metrics ---"
post "$API/step2/value-streams/$VS1_ID/recalculate" '{}'
post "$API/step2/value-streams/$VS2_ID/recalculate" '{}'

echo -e "\n--- Step 2: Value Stream Levers ---"
post "$API/step2/levers" "{\"value_stream_id\":$VS1_ID,\"lever_type\":\"efficiency\",\"opportunity\":\"Reduce silicon design iteration cycles with AI-assisted chip layout\",\"current_state\":\"3 major design iterations per chip generation\",\"target_state\":\"2 iterations with AI optimization\",\"impact_estimate\":\"high\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS1_ID,\"lever_type\":\"growth\",\"opportunity\":\"Expand iPhone AI features to increase ASP and upgrade rate\",\"current_state\":\"Limited on-device AI features\",\"target_state\":\"Full Apple Intelligence suite driving premium pricing\",\"impact_estimate\":\"high\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS2_ID,\"lever_type\":\"efficiency\",\"opportunity\":\"Increase automated review coverage to reduce human review queue\",\"current_state\":\"60% apps require human review\",\"target_state\":\"35% require human review via improved ML screening\",\"impact_estimate\":\"medium\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS2_ID,\"lever_type\":\"experience\",\"opportunity\":\"Provide real-time review status and AI-assisted rejection explanations\",\"current_state\":\"Generic rejection reasons, no real-time status\",\"target_state\":\"Specific actionable feedback, live status tracking\",\"impact_estimate\":\"medium\"}"

echo " done"

# ============================================================
# Step 3: SWOT to TOWS Action Engine
# ============================================================
echo -e "\n--- Step 3: SWOT Entries ---"
# Strengths
S1=$(post "$API/step3/swot" "{\"business_unit_id\":$APPLE_BU_ID,\"category\":\"strength\",\"description\":\"Strongest consumer brand globally — 98% brand awareness, premium pricing power\",\"severity\":\"high\",\"confidence\":\"high\"}")
S1_ID=$(echo "$S1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

S2=$(post "$API/step3/swot" "{\"business_unit_id\":$APPLE_BU_ID,\"category\":\"strength\",\"description\":\"Services segment growing 13% YoY with 74% gross margin, now \$96B annual revenue\",\"severity\":\"high\",\"confidence\":\"high\"}")
S2_ID=$(echo "$S2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

S3=$(post "$API/step3/swot" "{\"business_unit_id\":$APPLE_BU_ID,\"category\":\"strength\",\"description\":\"Vertical integration: custom silicon (M-series, A-series) provides performance and efficiency lead\",\"severity\":\"high\",\"confidence\":\"high\"}")
S3_ID=$(echo "$S3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

S4=$(post "$API/step3/swot" "{\"business_unit_id\":$APPLE_BU_ID,\"category\":\"strength\",\"description\":\"2B+ active devices creating unmatched ecosystem lock-in and recurring revenue\",\"severity\":\"high\",\"confidence\":\"high\"}")
S4_ID=$(echo "$S4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Weaknesses
W1=$(post "$API/step3/swot" "{\"business_unit_id\":$APPLE_BU_ID,\"category\":\"weakness\",\"description\":\"iPhone revenue concentration (51% of total) creates cyclical risk\",\"severity\":\"high\",\"confidence\":\"high\"}")
W1_ID=$(echo "$W1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

W2=$(post "$API/step3/swot" "{\"business_unit_id\":$APPLE_BU_ID,\"category\":\"weakness\",\"description\":\"AI/LLM capabilities lag behind Google and Microsoft — Apple Intelligence behind competitors\",\"severity\":\"high\",\"confidence\":\"medium\"}")
W2_ID=$(echo "$W2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

W3=$(post "$API/step3/swot" "{\"business_unit_id\":$APPLE_BU_ID,\"category\":\"weakness\",\"description\":\"China market share declining under local competition (Huawei resurgence)\",\"severity\":\"medium\",\"confidence\":\"high\"}")
W3_ID=$(echo "$W3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Opportunities
O1=$(post "$API/step3/swot" "{\"business_unit_id\":$APPLE_BU_ID,\"category\":\"opportunity\",\"description\":\"Health tech expansion: FDA-approved monitoring, clinical trials data platform\",\"severity\":\"high\",\"confidence\":\"medium\"}")
O1_ID=$(echo "$O1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

O2=$(post "$API/step3/swot" "{\"business_unit_id\":$APPLE_BU_ID,\"category\":\"opportunity\",\"description\":\"India market growth: fastest-growing smartphone market, rising middle class\",\"severity\":\"high\",\"confidence\":\"high\"}")
O2_ID=$(echo "$O2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

O3=$(post "$API/step3/swot" "{\"business_unit_id\":$APPLE_BU_ID,\"category\":\"opportunity\",\"description\":\"Spatial computing (Vision Pro) and AR — new platform opportunity\",\"severity\":\"medium\",\"confidence\":\"medium\"}")
O3_ID=$(echo "$O3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Threats
T1=$(post "$API/step3/swot" "{\"business_unit_id\":$APPLE_BU_ID,\"category\":\"threat\",\"description\":\"EU Digital Markets Act forcing App Store changes, threatening services margin\",\"severity\":\"high\",\"confidence\":\"high\"}")
T1_ID=$(echo "$T1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

T2=$(post "$API/step3/swot" "{\"business_unit_id\":$APPLE_BU_ID,\"category\":\"threat\",\"description\":\"AI disruption risk: Google/Microsoft AI assistants may reduce iOS differentiation\",\"severity\":\"high\",\"confidence\":\"medium\"}")
T2_ID=$(echo "$T2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

T3=$(post "$API/step3/swot" "{\"business_unit_id\":$APPLE_BU_ID,\"category\":\"threat\",\"description\":\"Geopolitical risk: China supply chain concentration, Taiwan semiconductor dependency\",\"severity\":\"high\",\"confidence\":\"high\"}")
T3_ID=$(echo "$T3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "SWOT IDs: S=$S1_ID,$S2_ID,$S3_ID,$S4_ID W=$W1_ID,$W2_ID,$W3_ID O=$O1_ID,$O2_ID,$O3_ID T=$T1_ID,$T2_ID,$T3_ID"

echo -e "\n--- Step 3: TOWS Actions ---"
# SO: Strength + Opportunity
TOWS1=$(post "$API/step3/tows" "{\"strategy_type\":\"SO\",\"swot_entry_1_id\":$S4_ID,\"swot_entry_2_id\":$O1_ID,\"action_description\":\"Leverage 2B device ecosystem to build health data platform — partner with hospitals/insurers\",\"priority\":\"high\",\"impact_score\":9,\"rationale\":\"Ecosystem + health = recurring high-margin revenue\"}")
TOWS1_ID=$(echo "$TOWS1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS2=$(post "$API/step3/tows" "{\"strategy_type\":\"SO\",\"swot_entry_1_id\":$S1_ID,\"swot_entry_2_id\":$O2_ID,\"action_description\":\"Expand India retail presence and create India-specific pricing tiers to capture market growth\",\"priority\":\"high\",\"impact_score\":8,\"rationale\":\"Brand strength can drive premium positioning in growing market\"}")
TOWS2_ID=$(echo "$TOWS2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# WO: Weakness + Opportunity
TOWS3=$(post "$API/step3/tows" "{\"strategy_type\":\"WO\",\"swot_entry_1_id\":$W2_ID,\"swot_entry_2_id\":$O3_ID,\"action_description\":\"Invest heavily in on-device AI for spatial computing — differentiate via privacy-first AI on Vision Pro\",\"priority\":\"critical\",\"impact_score\":10,\"rationale\":\"Turn AI weakness into strength by combining with new platform\"}")
TOWS3_ID=$(echo "$TOWS3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# ST: Strength + Threat
TOWS4=$(post "$API/step3/tows" "{\"strategy_type\":\"ST\",\"swot_entry_1_id\":$S3_ID,\"swot_entry_2_id\":$T3_ID,\"action_description\":\"Diversify manufacturing to India and Vietnam, leverage custom silicon to reduce TSMC single-source risk\",\"priority\":\"high\",\"impact_score\":8,\"rationale\":\"Vertical integration enables faster supply chain diversification\"}")
TOWS4_ID=$(echo "$TOWS4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# WT: Weakness + Threat
TOWS5=$(post "$API/step3/tows" "{\"strategy_type\":\"WT\",\"swot_entry_1_id\":$W1_ID,\"swot_entry_2_id\":$T1_ID,\"action_description\":\"Accelerate Services revenue diversification to offset potential App Store margin compression from DMA\",\"priority\":\"critical\",\"impact_score\":9,\"rationale\":\"Reduce iPhone dependency while defending against regulatory margin pressure\"}")
TOWS5_ID=$(echo "$TOWS5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "TOWS IDs: $TOWS1_ID,$TOWS2_ID,$TOWS3_ID,$TOWS4_ID,$TOWS5_ID"

# ============================================================
# Step 4: Four-Layer Strategy & Strategic OKRs
# ============================================================
echo -e "\n--- Step 4: Strategy Inputs ---"
post "$API/step4/inputs" '{"input_type":"business_strategy","title":"Apple 10-K FY2025 Strategy Section","content":"Focus on innovation through custom silicon, services growth, and emerging markets expansion. Maintain premium brand positioning while growing installed base."}'
post "$API/step4/inputs" '{"input_type":"digital_strategy","title":"Apple Intelligence & Platform Strategy","content":"Deploy Apple Intelligence across all platforms. Expand developer tools. Invest in spatial computing. Privacy-first approach to AI."}'
post "$API/step4/inputs" '{"input_type":"data_strategy","title":"Apple Data & Privacy Strategy","content":"On-device processing first. Differential privacy for aggregate insights. Health data platform with HL7 FHIR. Federated learning for personalization."}'
post "$API/step4/inputs" '{"input_type":"gen_ai_strategy","title":"Apple AI/ML Roadmap","content":"Foundation models for Siri, on-device LLMs, generative image/video tools, code completion in Xcode, AI-powered developer tools."}'

echo -e "\n--- Step 4: Strategies ---"
STR1=$(post "$API/step4/strategies" "{\"layer\":\"business\",\"name\":\"Health & Wellness Platform\",\"description\":\"Build FDA-approved health monitoring ecosystem across Watch, iPhone, and new health devices. Partner with healthcare providers.\",\"tows_action_id\":$TOWS1_ID,\"risk_level\":\"high\",\"risks\":\"FDA regulatory timeline, healthcare data liability, insurance partnership complexity\"}")
STR1_ID=$(echo "$STR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR2=$(post "$API/step4/strategies" "{\"layer\":\"business\",\"name\":\"India Market Expansion\",\"description\":\"Triple India retail presence, launch manufacturing, create market-specific products and pricing.\",\"tows_action_id\":$TOWS2_ID,\"risk_level\":\"medium\",\"risks\":\"Price sensitivity, local competition, regulatory environment\"}")
STR2_ID=$(echo "$STR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR3=$(post "$API/step4/strategies" "{\"layer\":\"digital\",\"name\":\"Apple Intelligence Platform\",\"description\":\"Deploy on-device AI across all products. Build privacy-first AI that differentiates from cloud-dependent competitors.\",\"tows_action_id\":$TOWS3_ID,\"risk_level\":\"high\",\"risks\":\"On-device model size constraints, compute cost, falling behind cloud AI capabilities\"}")
STR3_ID=$(echo "$STR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR4=$(post "$API/step4/strategies" "{\"layer\":\"data\",\"name\":\"Federated Health Data Platform\",\"description\":\"Create privacy-preserving health data platform using federated learning. Enable clinical research without centralizing patient data.\",\"risk_level\":\"high\",\"risks\":\"HIPAA compliance, data quality, cross-border health data regulations\"}")
STR4_ID=$(echo "$STR4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR5=$(post "$API/step4/strategies" "{\"layer\":\"gen_ai\",\"name\":\"On-Device Foundation Models\",\"description\":\"Develop and deploy small but capable foundation models that run entirely on Apple silicon. Enable offline AI, private Siri, code generation.\",\"risk_level\":\"medium\",\"risks\":\"Model performance vs cloud alternatives, silicon power constraints, development cost\"}")
STR5_ID=$(echo "$STR5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR6=$(post "$API/step4/strategies" "{\"layer\":\"business\",\"name\":\"Supply Chain Diversification\",\"description\":\"Reduce China manufacturing concentration to below 50%. Scale India and Vietnam facilities.\",\"tows_action_id\":$TOWS4_ID,\"risk_level\":\"medium\",\"risks\":\"Quality control during transition, higher initial costs, workforce training\"}")
STR6_ID=$(echo "$STR6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Strategy IDs: $STR1_ID,$STR2_ID,$STR3_ID,$STR4_ID,$STR5_ID,$STR6_ID"

echo -e "\n--- Step 4: Strategic OKRs ---"
OKR1=$(post "$API/step4/okrs" "{\"strategy_id\":$STR1_ID,\"objective\":\"Establish Apple as the #1 consumer health platform by 2027\",\"time_horizon\":\"2025-2027\",\"status\":\"active\"}")
OKR1_ID=$(echo "$OKR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR2=$(post "$API/step4/okrs" "{\"strategy_id\":$STR2_ID,\"objective\":\"Grow India revenue from \$8B to \$25B by 2027\",\"time_horizon\":\"2025-2027\",\"status\":\"active\"}")
OKR2_ID=$(echo "$OKR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR3=$(post "$API/step4/okrs" "{\"strategy_id\":$STR3_ID,\"objective\":\"Achieve feature parity with cloud AI assistants using on-device models\",\"time_horizon\":\"2025-2026\",\"status\":\"active\"}")
OKR3_ID=$(echo "$OKR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR4=$(post "$API/step4/okrs" "{\"strategy_id\":$STR5_ID,\"objective\":\"Ship on-device foundation model powering 50+ features across all platforms\",\"time_horizon\":\"2025-2026\",\"status\":\"active\"}")
OKR4_ID=$(echo "$OKR4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR5=$(post "$API/step4/okrs" "{\"strategy_id\":$STR6_ID,\"objective\":\"Reduce China manufacturing share from 75% to 50% by 2027\",\"time_horizon\":\"2025-2027\",\"status\":\"active\"}")
OKR5_ID=$(echo "$OKR5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "OKR IDs: $OKR1_ID,$OKR2_ID,$OKR3_ID,$OKR4_ID,$OKR5_ID"

echo -e "\n--- Step 4: Key Results ---"
post "$API/step4/okrs/$OKR1_ID/key-results" '{"key_result":"Achieve 150M Health app active users","metric":"monthly_active_users","current_value":85,"target_value":150,"unit":"million","rationale":"Baseline 85M MAU on Health app, drive adoption through Watch and new features"}'
post "$API/step4/okrs/$OKR1_ID/key-results" '{"key_result":"Secure 3 FDA clearances for new health monitoring features","metric":"fda_clearances","current_value":1,"target_value":3,"unit":"clearances","rationale":"Currently 1 approved (ECG). Target: blood pressure, glucose estimation"}'
post "$API/step4/okrs/$OKR1_ID/key-results" '{"key_result":"Launch health data API with 50 hospital system partners","metric":"hospital_partners","current_value":5,"target_value":50,"unit":"partners","rationale":"HealthKit has 5 pilot partners, need to scale to clinical grade"}'

post "$API/step4/okrs/$OKR2_ID/key-results" '{"key_result":"Open 25 Apple retail stores in India","metric":"retail_stores","current_value":4,"target_value":25,"unit":"stores","rationale":"Currently 4 stores (Mumbai, Delhi). Expand to tier 1 and tier 2 cities"}'
post "$API/step4/okrs/$OKR2_ID/key-results" '{"key_result":"Grow iPhone India market share to 8%","metric":"market_share_pct","current_value":4,"target_value":8,"unit":"%","rationale":"Currently ~4% unit share. Double via retail expansion and local pricing"}'

post "$API/step4/okrs/$OKR3_ID/key-results" '{"key_result":"Siri on-device response accuracy reaches 95% for top-100 queries","metric":"accuracy_pct","current_value":78,"target_value":95,"unit":"%"}'
post "$API/step4/okrs/$OKR3_ID/key-results" '{"key_result":"Apple Intelligence available on 1B+ devices","metric":"devices","current_value":200,"target_value":1000,"unit":"million"}'

post "$API/step4/okrs/$OKR4_ID/key-results" '{"key_result":"On-device model latency under 200ms for text generation","metric":"latency_ms","current_value":800,"target_value":200,"unit":"ms"}'
post "$API/step4/okrs/$OKR4_ID/key-results" '{"key_result":"Foundation model powers summarization, writing, image gen across iOS, macOS, visionOS","metric":"platform_coverage","current_value":1,"target_value":3,"unit":"platforms"}'

post "$API/step4/okrs/$OKR5_ID/key-results" '{"key_result":"India iPhone manufacturing reaches 25% of global volume","metric":"india_mfg_pct","current_value":7,"target_value":25,"unit":"%"}'
post "$API/step4/okrs/$OKR5_ID/key-results" '{"key_result":"Vietnam AirPods/Watch production reaches 40% of volume","metric":"vietnam_mfg_pct","current_value":15,"target_value":40,"unit":"%"}'

echo " done"

# ============================================================
# Step 5: Digital Initiatives & RICE Prioritization
# ============================================================
echo -e "\n--- Step 5: Product Groups & Digital Products ---"
PG1=$(post "$API/step5/product-groups" '{"name":"Apple Intelligence","description":"AI/ML platform across all Apple devices"}')
PG1_ID=$(echo "$PG1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

PG2=$(post "$API/step5/product-groups" '{"name":"Health Platform","description":"Health monitoring and wellness ecosystem"}')
PG2_ID=$(echo "$PG2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

PG3=$(post "$API/step5/product-groups" '{"name":"Developer Platform","description":"Tools and services for Apple developers"}')
PG3_ID=$(echo "$PG3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP1=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG1_ID,\"name\":\"Siri Intelligence\",\"description\":\"Next-gen Siri powered by on-device LLM\"}")
DP1_ID=$(echo "$DP1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP2=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG1_ID,\"name\":\"Writing & Summarization Tools\",\"description\":\"AI writing assistance, email summarization, notification summaries\"}")
DP2_ID=$(echo "$DP2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP3=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG2_ID,\"name\":\"Health Monitoring Suite\",\"description\":\"Blood pressure, glucose, sleep, mental health monitoring\"}")
DP3_ID=$(echo "$DP3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP4=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG3_ID,\"name\":\"Xcode AI Assistant\",\"description\":\"AI-powered code completion, debugging, and testing for Xcode\"}")
DP4_ID=$(echo "$DP4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Product Group IDs: $PG1_ID,$PG2_ID,$PG3_ID | Digital Product IDs: $DP1_ID,$DP2_ID,$DP3_ID,$DP4_ID"

echo -e "\n--- Step 5: Initiatives ---"
INIT1=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP1_ID,\"strategy_id\":$STR3_ID,\"name\":\"On-Device Conversational LLM for Siri\",\"description\":\"Deploy 3B parameter LLM on-device for natural conversations, context awareness, multi-turn dialogue\",\"reach\":500,\"impact\":3,\"confidence\":0.8,\"effort\":12,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT1_ID=$(echo "$INIT1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT2=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP2_ID,\"strategy_id\":$STR3_ID,\"name\":\"Smart Summarization Engine\",\"description\":\"Summarize emails, messages, documents, and notifications using on-device models\",\"reach\":800,\"impact\":2,\"confidence\":1.0,\"effort\":6,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT2_ID=$(echo "$INIT2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT3=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP3_ID,\"strategy_id\":$STR1_ID,\"name\":\"Non-Invasive Blood Glucose Estimation\",\"description\":\"Use optical sensors on Apple Watch to estimate blood glucose levels without finger pricks\",\"reach\":200,\"impact\":3,\"confidence\":0.5,\"effort\":18,\"roadmap_phase\":\"Phase 2\",\"status\":\"proposed\"}")
INIT3_ID=$(echo "$INIT3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT4=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP3_ID,\"strategy_id\":$STR1_ID,\"name\":\"Blood Pressure Monitoring\",\"description\":\"Continuous blood pressure monitoring via Apple Watch sensors with FDA clearance\",\"reach\":300,\"impact\":3,\"confidence\":0.8,\"effort\":12,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT4_ID=$(echo "$INIT4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT5=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP4_ID,\"strategy_id\":$STR5_ID,\"name\":\"Xcode Predictive Code Completion\",\"description\":\"AI-powered code completion and generation in Xcode using on-device Swift-tuned model\",\"reach\":1000,\"impact\":2,\"confidence\":0.8,\"effort\":8,\"roadmap_phase\":\"Phase 1\",\"status\":\"approved\"}")
INIT5_ID=$(echo "$INIT5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT6=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP1_ID,\"strategy_id\":$STR3_ID,\"name\":\"App Intents AI Orchestration\",\"description\":\"Enable Siri to chain app actions intelligently — book ride, then message ETA, then set timer\",\"reach\":600,\"impact\":2,\"confidence\":0.8,\"effort\":10,\"roadmap_phase\":\"Phase 2\",\"status\":\"proposed\"}")
INIT6_ID=$(echo "$INIT6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Initiative IDs: $INIT1_ID,$INIT2_ID,$INIT3_ID,$INIT4_ID,$INIT5_ID,$INIT6_ID"

# ============================================================
# Step 6: Epics & Teams + Product OKRs
# ============================================================
echo -e "\n--- Step 6: Teams ---"
TEAM1=$(post "$API/step6/teams" '{"name":"Siri AI Team","capacity":25}')
TEAM1_ID=$(echo "$TEAM1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM2=$(post "$API/step6/teams" '{"name":"Health Sensors Team","capacity":30}')
TEAM2_ID=$(echo "$TEAM2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM3=$(post "$API/step6/teams" '{"name":"Developer Tools Team","capacity":20}')
TEAM3_ID=$(echo "$TEAM3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM4=$(post "$API/step6/teams" '{"name":"ML Platform Team","capacity":35}')
TEAM4_ID=$(echo "$TEAM4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Team IDs: $TEAM1_ID,$TEAM2_ID,$TEAM3_ID,$TEAM4_ID"

echo -e "\n--- Step 6: Product OKRs ---"
POKR1=$(post "$API/step6/product-okrs" "{\"strategic_okr_id\":$OKR3_ID,\"digital_product_id\":$DP1_ID,\"objective\":\"Siri handles 90% of queries without cloud fallback\",\"status\":\"active\"}")
POKR1_ID=$(echo "$POKR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

POKR2=$(post "$API/step6/product-okrs" "{\"strategic_okr_id\":$OKR1_ID,\"digital_product_id\":$DP3_ID,\"objective\":\"Launch blood pressure monitoring with FDA approval in 2026\",\"status\":\"active\"}")
POKR2_ID=$(echo "$POKR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

POKR3=$(post "$API/step6/product-okrs" "{\"strategic_okr_id\":$OKR4_ID,\"digital_product_id\":$DP4_ID,\"objective\":\"50% of Xcode users adopt AI code completion within 6 months of launch\",\"status\":\"active\"}")
POKR3_ID=$(echo "$POKR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Product OKR IDs: $POKR1_ID,$POKR2_ID,$POKR3_ID"

echo -e "\n--- Step 6: Epics ---"
EPIC1=$(post "$API/step6/epics" "{\"initiative_id\":$INIT1_ID,\"team_id\":$TEAM1_ID,\"product_okr_id\":$POKR1_ID,\"name\":\"On-Device LLM Runtime\",\"description\":\"Build optimized inference runtime for 3B param model on A17/M-series chips\",\"status\":\"in_progress\",\"start_date\":\"2025-09-01\",\"target_date\":\"2026-03-01\",\"value_score\":5,\"size_score\":5,\"effort_score\":5,\"risk_level\":\"high\",\"risks\":\"Memory constraints on older devices, thermal management\",\"roadmap_phase\":\"Phase 1\"}")
EPIC1_ID=$(echo "$EPIC1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC2=$(post "$API/step6/epics" "{\"initiative_id\":$INIT1_ID,\"team_id\":$TEAM4_ID,\"product_okr_id\":$POKR1_ID,\"name\":\"Conversational Context Engine\",\"description\":\"Multi-turn conversation management with personal context awareness\",\"status\":\"in_progress\",\"start_date\":\"2025-10-01\",\"target_date\":\"2026-04-01\",\"value_score\":4,\"size_score\":4,\"effort_score\":4,\"risk_level\":\"medium\",\"roadmap_phase\":\"Phase 1\"}")
EPIC2_ID=$(echo "$EPIC2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC3=$(post "$API/step6/epics" "{\"initiative_id\":$INIT4_ID,\"team_id\":$TEAM2_ID,\"product_okr_id\":$POKR2_ID,\"name\":\"Blood Pressure Sensor Calibration\",\"description\":\"Hardware sensor calibration algorithms and clinical validation for BP monitoring\",\"status\":\"in_progress\",\"start_date\":\"2025-06-01\",\"target_date\":\"2026-06-01\",\"value_score\":5,\"size_score\":5,\"effort_score\":5,\"risk_level\":\"high\",\"risks\":\"FDA validation timeline, sensor accuracy across skin tones\",\"roadmap_phase\":\"Phase 1\"}")
EPIC3_ID=$(echo "$EPIC3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC4=$(post "$API/step6/epics" "{\"initiative_id\":$INIT4_ID,\"team_id\":$TEAM2_ID,\"product_okr_id\":$POKR2_ID,\"name\":\"Health Dashboard BP Integration\",\"description\":\"Integrate BP readings into Health app with trend analysis, alerts, doctor sharing\",\"status\":\"backlog\",\"start_date\":\"2026-01-01\",\"target_date\":\"2026-06-01\",\"value_score\":4,\"size_score\":3,\"effort_score\":3,\"risk_level\":\"low\",\"roadmap_phase\":\"Phase 1\"}")
EPIC4_ID=$(echo "$EPIC4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC5=$(post "$API/step6/epics" "{\"initiative_id\":$INIT5_ID,\"team_id\":$TEAM3_ID,\"product_okr_id\":$POKR3_ID,\"name\":\"Swift Code Completion Model\",\"description\":\"Train and deploy Swift/ObjC-specialized code completion model for Xcode\",\"status\":\"in_progress\",\"start_date\":\"2025-08-01\",\"target_date\":\"2026-06-01\",\"value_score\":4,\"size_score\":4,\"effort_score\":4,\"risk_level\":\"medium\",\"roadmap_phase\":\"Phase 1\"}")
EPIC5_ID=$(echo "$EPIC5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC6=$(post "$API/step6/epics" "{\"initiative_id\":$INIT5_ID,\"team_id\":$TEAM3_ID,\"product_okr_id\":$POKR3_ID,\"name\":\"AI Test Generation\",\"description\":\"Auto-generate unit tests and UI tests from code context in Xcode\",\"status\":\"backlog\",\"start_date\":\"2026-03-01\",\"target_date\":\"2026-09-01\",\"value_score\":3,\"size_score\":3,\"effort_score\":4,\"risk_level\":\"medium\",\"roadmap_phase\":\"Phase 2\"}")
EPIC6_ID=$(echo "$EPIC6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Epic IDs: $EPIC1_ID,$EPIC2_ID,$EPIC3_ID,$EPIC4_ID,$EPIC5_ID,$EPIC6_ID"

echo -e "\n--- Step 6: Epic Dependencies ---"
post "$API/step6/dependencies" "{\"epic_id\":$EPIC2_ID,\"depends_on_epic_id\":$EPIC1_ID,\"dependency_type\":\"blocks\",\"notes\":\"Context engine needs LLM runtime to be functional\"}"
post "$API/step6/dependencies" "{\"epic_id\":$EPIC4_ID,\"depends_on_epic_id\":$EPIC3_ID,\"dependency_type\":\"blocks\",\"notes\":\"Dashboard needs validated sensor data\"}"
post "$API/step6/dependencies" "{\"epic_id\":$EPIC6_ID,\"depends_on_epic_id\":$EPIC5_ID,\"dependency_type\":\"blocks\",\"notes\":\"Test gen needs base code completion model\"}"

echo " done"

# ============================================================
# Step 7: Features & Roadmap + Delivery OKRs
# ============================================================
echo -e "\n--- Step 7: Delivery OKRs ---"
DOKR1=$(post "$API/step7/delivery-okrs" "{\"product_okr_id\":$POKR1_ID,\"team_id\":$TEAM1_ID,\"objective\":\"Ship LLM runtime with <200ms first-token latency on iPhone 16+\",\"status\":\"active\"}")
DOKR1_ID=$(echo "$DOKR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DOKR2=$(post "$API/step7/delivery-okrs" "{\"product_okr_id\":$POKR2_ID,\"team_id\":$TEAM2_ID,\"objective\":\"Complete FDA 510(k) submission for BP monitoring by Q2 2026\",\"status\":\"active\"}")
DOKR2_ID=$(echo "$DOKR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DOKR3=$(post "$API/step7/delivery-okrs" "{\"product_okr_id\":$POKR3_ID,\"team_id\":$TEAM3_ID,\"objective\":\"Launch Xcode AI beta at WWDC 2026 with 85% suggestion acceptance rate\",\"status\":\"active\"}")
DOKR3_ID=$(echo "$DOKR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Delivery OKR IDs: $DOKR1_ID,$DOKR2_ID,$DOKR3_ID"

echo -e "\n--- Step 7: Features ---"
# Features for Epic 1: On-Device LLM Runtime
post "$API/step7/features" "{\"epic_id\":$EPIC1_ID,\"delivery_okr_id\":$DOKR1_ID,\"name\":\"Neural Engine Quantization Pipeline\",\"description\":\"4-bit quantization pipeline optimized for Apple Neural Engine, maintaining quality with 75% memory reduction\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":15,\"start_date\":\"2025-09-15\",\"target_date\":\"2025-12-15\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC1_ID,\"delivery_okr_id\":$DOKR1_ID,\"name\":\"Speculative Decoding Engine\",\"description\":\"Implement speculative decoding with draft model for 2x faster token generation\",\"priority\":\"high\",\"status\":\"in_progress\",\"estimated_effort\":12,\"start_date\":\"2025-10-01\",\"target_date\":\"2026-01-15\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC1_ID,\"delivery_okr_id\":$DOKR1_ID,\"name\":\"Adaptive Compute Scaling\",\"description\":\"Dynamic model scaling based on device thermal state and battery level\",\"priority\":\"medium\",\"status\":\"backlog\",\"estimated_effort\":8,\"roadmap_phase\":\"Phase 1\"}"

# Features for Epic 2: Conversational Context
post "$API/step7/features" "{\"epic_id\":$EPIC2_ID,\"name\":\"Personal Context Graph\",\"description\":\"Build on-device knowledge graph from contacts, calendar, messages, location patterns\",\"priority\":\"high\",\"status\":\"backlog\",\"estimated_effort\":20,\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC2_ID,\"name\":\"Multi-Turn Memory Manager\",\"description\":\"Efficient KV-cache management for long conversations within device memory constraints\",\"priority\":\"high\",\"status\":\"backlog\",\"estimated_effort\":10,\"roadmap_phase\":\"Phase 1\"}"

# Features for Epic 3: BP Sensor
post "$API/step7/features" "{\"epic_id\":$EPIC3_ID,\"delivery_okr_id\":$DOKR2_ID,\"name\":\"Optical BP Sensor Algorithm v2\",\"description\":\"Improved pulse transit time algorithm using photoplethysmography for continuous BP estimation\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":25,\"start_date\":\"2025-06-01\",\"target_date\":\"2026-02-01\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC3_ID,\"delivery_okr_id\":$DOKR2_ID,\"name\":\"Clinical Validation Study Manager\",\"description\":\"Tool for managing multi-site clinical validation studies, data collection, and FDA submission prep\",\"priority\":\"high\",\"status\":\"in_progress\",\"estimated_effort\":12,\"start_date\":\"2025-09-01\",\"target_date\":\"2026-03-01\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC3_ID,\"delivery_okr_id\":$DOKR2_ID,\"name\":\"Skin Tone Calibration ML Model\",\"description\":\"ML model to adjust BP readings across different skin tones for accuracy equity\",\"priority\":\"high\",\"status\":\"backlog\",\"estimated_effort\":15,\"roadmap_phase\":\"Phase 1\"}"

# Features for Epic 5: Swift Code Completion
post "$API/step7/features" "{\"epic_id\":$EPIC5_ID,\"delivery_okr_id\":$DOKR3_ID,\"name\":\"Swift AST-Aware Tokenizer\",\"description\":\"Custom tokenizer that understands Swift syntax tree for more accurate completions\",\"priority\":\"high\",\"status\":\"in_progress\",\"estimated_effort\":10,\"start_date\":\"2025-08-15\",\"target_date\":\"2025-12-01\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC5_ID,\"delivery_okr_id\":$DOKR3_ID,\"name\":\"Project Context Retrieval\",\"description\":\"RAG system indexing full Xcode project for context-aware code suggestions\",\"priority\":\"high\",\"status\":\"backlog\",\"estimated_effort\":14,\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC5_ID,\"delivery_okr_id\":$DOKR3_ID,\"name\":\"Inline Ghost Text UX\",\"description\":\"Ghost text completion UI in Xcode editor with Tab-to-accept, multi-line preview\",\"priority\":\"medium\",\"status\":\"backlog\",\"estimated_effort\":6,\"roadmap_phase\":\"Phase 1\"}"

# Features for Epic 6: AI Test Generation
post "$API/step7/features" "{\"epic_id\":$EPIC6_ID,\"name\":\"Unit Test Skeleton Generator\",\"description\":\"Generate XCTest stubs with assertions from function signatures and docstrings\",\"priority\":\"medium\",\"status\":\"backlog\",\"estimated_effort\":8,\"roadmap_phase\":\"Phase 2\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC6_ID,\"name\":\"UI Test Recorder with AI\",\"description\":\"AI-enhanced UI test recording that generates maintainable, readable test code\",\"priority\":\"low\",\"status\":\"backlog\",\"estimated_effort\":12,\"roadmap_phase\":\"Phase 2\"}"

echo -e "\n\n=== SEEDING COMPLETE ==="
echo "Summary:"
echo "  Organization: Apple (Technology)"
echo "  Step 1: 5 BUs, 14 revenue splits, 12 ops metrics, 3 competitors"
echo "  Step 2: 3 value streams, 11 steps, 4 levers"
echo "  Step 3: 4 strengths, 3 weaknesses, 3 opportunities, 3 threats, 5 TOWS actions"
echo "  Step 4: 4 strategy inputs, 6 strategies, 5 OKRs, 12 key results"
echo "  Step 5: 3 product groups, 4 digital products, 6 initiatives (RICE scored)"
echo "  Step 6: 4 teams, 3 product OKRs, 6 epics, 3 dependencies"
echo "  Step 7: 3 delivery OKRs, 14 features"
