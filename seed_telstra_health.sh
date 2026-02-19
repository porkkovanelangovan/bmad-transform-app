#!/bin/bash
# Seed UAT test data for Telstra Health — all 7 steps
# Usage: bash seed_telstra_health.sh [BASE_URL]
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

echo "=== Seeding UAT data for Telstra Health at $BASE ==="

# Reset existing data
echo -e "\n--- Resetting all data ---"
post "$API/step1/reset-data" '{}'
echo " done"

# ============================================================
# Organization
# ============================================================
echo -e "\n--- Organization ---"
post "$API/step1/organization" '{"name":"Telstra Health","industry":"Healthcare Information Technology","sub_industry":"Digital Health & Clinical Systems","competitor_1_name":"Oracle Health (Cerner)","competitor_2_name":"Epic Systems"}'

# ============================================================
# Step 1: Business Performance Dashboard
# ============================================================
echo -e "\n--- Step 1: Business Units ---"
post "$API/step1/business-units" '{"name":"Telstra Health","description":"Telstra Health — digital health subsidiary of Telstra Group"}'
BU2=$(post "$API/step1/business-units" '{"name":"Hospital & Clinical Systems","description":"Electronic health records, clinical decision support, patient administration for hospitals"}')
BU3=$(post "$API/step1/business-units" '{"name":"Pharmacy Solutions","description":"Pharmacy dispensing, clinical interventions, medication management systems (Fred IT)"}')
BU4=$(post "$API/step1/business-units" '{"name":"Aged & Community Care","description":"Residential aged care systems, community health, NDIS management, home care platforms"}')
BU5=$(post "$API/step1/business-units" '{"name":"Health Data & Analytics","description":"Health data exchange, population health analytics, clinical registries, interoperability"}')
BU6=$(post "$API/step1/business-units" '{"name":"Virtual Care & Telehealth","description":"Telehealth platform, remote patient monitoring, virtual consultation solutions"}')

BU_LIST=$(curl -s "$API/step1/business-units")
TH_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next((b['id'] for b in data if b['name']=='Telstra Health'),data[0]['id']))")
HCS_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if 'Hospital' in b['name']))")
PHARM_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if 'Pharmacy' in b['name']))")
AGED_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if 'Aged' in b['name']))")
DATA_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if 'Data' in b['name']))")
VC_BU_ID=$(echo "$BU_LIST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(next(b['id'] for b in data if 'Virtual' in b['name']))")

echo "BU IDs: TH=$TH_BU_ID HCS=$HCS_BU_ID PHARM=$PHARM_BU_ID AGED=$AGED_BU_ID DATA=$DATA_BU_ID VC=$VC_BU_ID"

echo -e "\n--- Step 1: Revenue Splits ---"
# Revenue by product (in AUD $M)
post "$API/step1/revenue-splits" "{\"business_unit_id\":$HCS_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Hospital & Clinical Systems\",\"revenue\":185,\"period\":\"FY2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$HCS_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Hospital & Clinical Systems\",\"revenue\":168,\"period\":\"FY2024\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$HCS_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Hospital & Clinical Systems\",\"revenue\":155,\"period\":\"FY2023\"}"

post "$API/step1/revenue-splits" "{\"business_unit_id\":$PHARM_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Pharmacy Solutions (Fred IT)\",\"revenue\":142,\"period\":\"FY2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$PHARM_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Pharmacy Solutions (Fred IT)\",\"revenue\":135,\"period\":\"FY2024\"}"

post "$API/step1/revenue-splits" "{\"business_unit_id\":$AGED_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Aged & Community Care\",\"revenue\":98,\"period\":\"FY2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$AGED_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Aged & Community Care\",\"revenue\":82,\"period\":\"FY2024\"}"

post "$API/step1/revenue-splits" "{\"business_unit_id\":$DATA_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Health Data & Analytics\",\"revenue\":65,\"period\":\"FY2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$DATA_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Health Data & Analytics\",\"revenue\":48,\"period\":\"FY2024\"}"

post "$API/step1/revenue-splits" "{\"business_unit_id\":$VC_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Virtual Care & Telehealth\",\"revenue\":45,\"period\":\"FY2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$VC_BU_ID,\"dimension\":\"product\",\"dimension_value\":\"Virtual Care & Telehealth\",\"revenue\":52,\"period\":\"FY2024\"}"

# Regional splits
post "$API/step1/revenue-splits" "{\"business_unit_id\":$TH_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"New South Wales\",\"revenue\":165,\"period\":\"FY2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$TH_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Victoria\",\"revenue\":138,\"period\":\"FY2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$TH_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Queensland\",\"revenue\":95,\"period\":\"FY2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$TH_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"Western Australia & SA\",\"revenue\":62,\"period\":\"FY2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$TH_BU_ID,\"dimension\":\"region\",\"dimension_value\":\"International (UK & Asia)\",\"revenue\":75,\"period\":\"FY2025\"}"

# Segment splits
post "$API/step1/revenue-splits" "{\"business_unit_id\":$TH_BU_ID,\"dimension\":\"segment\",\"dimension_value\":\"Recurring SaaS & Subscription\",\"revenue\":312,\"period\":\"FY2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$TH_BU_ID,\"dimension\":\"segment\",\"dimension_value\":\"Implementation & Professional Services\",\"revenue\":118,\"period\":\"FY2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$TH_BU_ID,\"dimension\":\"segment\",\"dimension_value\":\"License & Perpetual\",\"revenue\":45,\"period\":\"FY2025\"}"
post "$API/step1/revenue-splits" "{\"business_unit_id\":$TH_BU_ID,\"dimension\":\"segment\",\"dimension_value\":\"Managed Services & Support\",\"revenue\":60,\"period\":\"FY2025\"}"

echo " done"

echo -e "\n--- Step 1: Ops Efficiency ---"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$TH_BU_ID,\"metric_name\":\"Revenue Growth (YoY)\",\"metric_value\":0.102,\"target_value\":0.15,\"period\":\"FY2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$TH_BU_ID,\"metric_name\":\"Gross Margin\",\"metric_value\":0.58,\"target_value\":0.62,\"period\":\"FY2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$TH_BU_ID,\"metric_name\":\"EBITDA Margin\",\"metric_value\":0.12,\"target_value\":0.18,\"period\":\"FY2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$TH_BU_ID,\"metric_name\":\"Net Profit Margin\",\"metric_value\":0.04,\"target_value\":0.08,\"period\":\"FY2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$TH_BU_ID,\"metric_name\":\"Annual Recurring Revenue (ARR)\",\"metric_value\":312,\"target_value\":380,\"period\":\"FY2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$TH_BU_ID,\"metric_name\":\"ARR Growth Rate\",\"metric_value\":0.148,\"target_value\":0.20,\"period\":\"FY2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$TH_BU_ID,\"metric_name\":\"Net Revenue Retention\",\"metric_value\":1.08,\"target_value\":1.15,\"period\":\"FY2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$TH_BU_ID,\"metric_name\":\"Customer Churn Rate\",\"metric_value\":0.035,\"target_value\":0.02,\"period\":\"FY2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$TH_BU_ID,\"metric_name\":\"Implementation Success Rate\",\"metric_value\":0.87,\"target_value\":0.95,\"period\":\"FY2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$TH_BU_ID,\"metric_name\":\"R&D as % of Revenue\",\"metric_value\":0.21,\"target_value\":0.22,\"period\":\"FY2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$TH_BU_ID,\"metric_name\":\"Cloud Migration %\",\"metric_value\":0.42,\"target_value\":0.70,\"period\":\"FY2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$TH_BU_ID,\"metric_name\":\"System Uptime (SLA)\",\"metric_value\":0.9985,\"target_value\":0.999,\"period\":\"FY2025\"}"

# BU-specific metrics
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$HCS_BU_ID,\"metric_name\":\"Hospital Go-Lives Per Year\",\"metric_value\":12,\"target_value\":18,\"period\":\"FY2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$PHARM_BU_ID,\"metric_name\":\"Connected Pharmacies\",\"metric_value\":4850,\"target_value\":5200,\"period\":\"FY2025\"}"
post "$API/step1/ops-efficiency" "{\"business_unit_id\":$AGED_BU_ID,\"metric_name\":\"Aged Care Facilities Connected\",\"metric_value\":1450,\"target_value\":2000,\"period\":\"FY2025\"}"

echo " done"

echo -e "\n--- Step 1: Competitors ---"
post "$API/step1/competitors" '{"name":"Oracle Health (Cerner)","ticker":"ORCL","market_share":0.25,"revenue":6200,"profit_margin":0.22,"operating_margin":0.28,"return_on_equity":0.85,"return_on_assets":0.08,"pe_ratio":28.5,"eps":5.72,"market_cap_value":380000,"strengths":"Largest global EHR vendor, Oracle cloud infrastructure, massive R&D budget, government contracts (VA, DoD)","weaknesses":"Complex implementation, integration challenges post-acquisition, customer satisfaction declining, high total cost of ownership","data_source":"simulated"}'
post "$API/step1/competitors" '{"name":"Epic Systems","market_share":0.35,"revenue":4200,"profit_margin":0.35,"strengths":"Market-leading EHR in US hospitals (>50% US beds), highest customer satisfaction (KLAS), strong interoperability via Care Everywhere, deep clinical functionality","weaknesses":"Premium pricing excludes smaller facilities, limited international presence outside US/Canada, proprietary ecosystem, no cloud-native offering yet","data_source":"simulated"}'
post "$API/step1/competitors" '{"name":"Meditech","market_share":0.08,"revenue":620,"profit_margin":0.18,"strengths":"Strong in community hospitals, Expanse platform is cloud-ready, lower TCO than Epic/Cerner, loyal installed base","weaknesses":"Limited ambulatory functionality, smaller R&D investment, losing share to Epic in larger facilities, limited international presence","data_source":"simulated"}'
post "$API/step1/competitors" '{"name":"Dedalus (DXC)","market_share":0.06,"revenue":850,"profit_margin":0.08,"strengths":"Strong European presence, acquired DXC healthcare division, largest vendor in several EU markets, government health system expertise","weaknesses":"Fragmented product portfolio from acquisitions, integration challenges, limited AI/ML capabilities, legacy platform dependencies","data_source":"simulated"}'

echo " done"

echo -e "\n--- Step 1: Data URLs ---"
post "$API/step1/urls" '{"url":"https://www.telstrahealth.com/en/home.html","label":"Telstra Health Corporate Site","url_type":"external"}'
post "$API/step1/urls" '{"url":"https://www.telstra.com.au/aboutus/investors/financial-information/annual-reports","label":"Telstra Group Annual Report","url_type":"external"}'
post "$API/step1/urls" '{"url":"https://www.digitalhealth.gov.au/healthcare-providers/initiatives-and-programs","label":"Australian Digital Health Agency — Programs","url_type":"external"}'
post "$API/step1/urls" '{"url":"https://www.klasresearch.com/report/australia-new-zealand-ehr-market","label":"KLAS ANZ EHR Market Report 2025","url_type":"external"}'

echo " done"

# ============================================================
# Step 2: Value Stream Analysis
# ============================================================
echo -e "\n--- Step 2: Value Streams ---"
VS1=$(post "$API/step2/value-streams" "{\"business_unit_id\":$HCS_BU_ID,\"name\":\"Hospital EHR Implementation\",\"description\":\"End-to-end hospital EHR deployment from contract signing through configuration, data migration, training, to go-live\"}")
VS1_ID=$(echo "$VS1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

VS2=$(post "$API/step2/value-streams" "{\"business_unit_id\":$DATA_BU_ID,\"name\":\"Clinical Data Exchange\",\"description\":\"Health data flow from source systems through FHIR gateway, transformation, validation to consumer applications\"}")
VS2_ID=$(echo "$VS2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

VS3=$(post "$API/step2/value-streams" "{\"business_unit_id\":$VC_BU_ID,\"name\":\"Telehealth Consultation\",\"description\":\"Virtual care journey from patient booking through clinician matching, video consultation, to follow-up and billing\"}")
VS3_ID=$(echo "$VS3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

VS4=$(post "$API/step2/value-streams" "{\"business_unit_id\":$PHARM_BU_ID,\"name\":\"eScript Dispensing Workflow\",\"description\":\"Electronic prescription lifecycle from GP prescribing through PBS claims to patient medication collection\"}")
VS4_ID=$(echo "$VS4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "VS IDs: EHR=$VS1_ID, DataExchange=$VS2_ID, Telehealth=$VS3_ID, eScript=$VS4_ID"

echo -e "\n--- Step 2: Value Stream Steps (Hospital EHR Implementation) ---"
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":1,"step_name":"Discovery & Scoping","description":"Clinical workflow analysis, stakeholder interviews, integration requirements, gap analysis","step_type":"trigger","process_time_hours":120,"wait_time_hours":80,"resources":"Solutions Architects, Clinical Consultants"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":2,"step_name":"Environment Setup & Configuration","description":"Provision cloud environment, configure clinical modules, set up security, integration endpoints","step_type":"process","process_time_hours":240,"wait_time_hours":120,"resources":"Technical Delivery, Cloud Ops"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":3,"step_name":"Data Migration","description":"Extract from legacy systems, transform, validate, load into new EHR (patient demographics, clinical history, medications)","step_type":"process","process_time_hours":480,"wait_time_hours":160,"is_bottleneck":1,"notes":"Data quality issues in legacy systems cause 60% of project delays","resources":"Data Engineers, Clinical Informaticists"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":4,"step_name":"Integration Testing","description":"End-to-end testing of lab, radiology, pharmacy, ADT, pathology integrations","step_type":"decision","process_time_hours":200,"wait_time_hours":80,"resources":"Integration Team, Hospital IT"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":5,"step_name":"Clinical Training","description":"Role-based training for clinicians, nurses, admin staff — classroom + at-the-elbow","step_type":"process","process_time_hours":320,"wait_time_hours":40,"resources":"Clinical Trainers, Hospital Champions"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":6,"step_name":"UAT & Go-Live Readiness","description":"User acceptance testing, dress rehearsal, command center setup, go/no-go decision","step_type":"decision","process_time_hours":160,"wait_time_hours":80,"resources":"Project Team, Hospital Exec Sponsor"}'
post "$API/step2/value-streams/$VS1_ID/steps" '{"step_order":7,"step_name":"Go-Live & Hypercare","description":"System cutover, 24/7 support for first 2 weeks, issue triage, stabilization","step_type":"delivery","process_time_hours":336,"wait_time_hours":0,"resources":"Full Delivery Team, Support Desk"}'

echo -e "\n--- Step 2: Value Stream Steps (Clinical Data Exchange) ---"
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":1,"step_name":"Data Source Connection","description":"Establish HL7v2/FHIR connection to hospital PAS, lab, or GP system","step_type":"trigger","process_time_hours":8,"wait_time_hours":24,"resources":"Integration Engineers"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":2,"step_name":"Message Ingestion","description":"Receive clinical messages (ADT, ORU, CDA) into integration engine","step_type":"process","process_time_hours":0.01,"wait_time_hours":0,"resources":"Integration Engine, MirthConnect"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":3,"step_name":"FHIR Transformation","description":"Transform HL7v2/CDA to FHIR R4 resources with Australian Base profiles","step_type":"process","process_time_hours":0.02,"wait_time_hours":0,"resources":"FHIR Server, Transform Rules Engine"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":4,"step_name":"Clinical Validation","description":"Validate clinical terminology (SNOMED CT-AU, AMT), data quality checks, deduplication","step_type":"decision","process_time_hours":0.05,"wait_time_hours":0.5,"is_bottleneck":1,"notes":"Terminology mapping failures require manual clinical review — 15% of messages need intervention","resources":"Terminology Service, Clinical Validators"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":5,"step_name":"Consent & Privacy Check","description":"Verify patient consent for data sharing per My Health Record Act and Privacy Act","step_type":"decision","process_time_hours":0.01,"wait_time_hours":0,"resources":"Consent Service, Privacy Rules Engine"}'
post "$API/step2/value-streams/$VS2_ID/steps" '{"step_order":6,"step_name":"Data Delivery","description":"Route validated FHIR resources to consuming applications via subscription or API","step_type":"delivery","process_time_hours":0.01,"wait_time_hours":0,"resources":"FHIR API Gateway, Event Broker"}'

echo -e "\n--- Step 2: Value Stream Steps (Telehealth Consultation) ---"
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":1,"step_name":"Patient Booking","description":"Patient books virtual appointment via portal or app","step_type":"trigger","process_time_hours":0.1,"wait_time_hours":0,"resources":"Booking Platform"}'
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":2,"step_name":"Pre-Consultation Triage","description":"AI-assisted symptom checker and clinical priority assessment","step_type":"process","process_time_hours":0.15,"wait_time_hours":0.5,"resources":"Triage AI, Nursing Staff"}'
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":3,"step_name":"Clinician Matching","description":"Match patient to available clinician based on specialty, availability, and urgency","step_type":"process","process_time_hours":0.05,"wait_time_hours":2,"resources":"Scheduling Engine"}'
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":4,"step_name":"Video Consultation","description":"Secure video call with screen sharing, clinical notes, prescribing capability","step_type":"process","process_time_hours":0.33,"wait_time_hours":0,"resources":"Video Platform, Clinicians"}'
post "$API/step2/value-streams/$VS3_ID/steps" '{"step_order":5,"step_name":"Clinical Documentation & Billing","description":"Clinician completes notes, generates referrals, submits Medicare/PBS claims","step_type":"delivery","process_time_hours":0.17,"wait_time_hours":0.5,"resources":"Clinical Notes System, Medicare Claims"}'

# Recalculate metrics
post "$API/step2/value-streams/$VS1_ID/recalculate" '{}'
post "$API/step2/value-streams/$VS2_ID/recalculate" '{}'
post "$API/step2/value-streams/$VS3_ID/recalculate" '{}'

echo -e "\n--- Step 2: Value Stream Levers ---"
post "$API/step2/levers" "{\"value_stream_id\":$VS1_ID,\"lever_type\":\"efficiency\",\"opportunity\":\"AI-assisted data migration with automated mapping and quality remediation\",\"current_state\":\"60% of EHR projects delayed by data migration issues, avg 480 hours manual effort\",\"target_state\":\"AI auto-maps 85% of fields, reduces migration effort by 50%, auto-remediates data quality\",\"impact_estimate\":\"high\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS1_ID,\"lever_type\":\"experience\",\"opportunity\":\"Self-service configuration portal for hospital super-users\",\"current_state\":\"All configuration changes require Telstra Health professional services engagement\",\"target_state\":\"Hospital super-users handle 70% of configuration changes via guided portal\",\"impact_estimate\":\"medium\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS2_ID,\"lever_type\":\"efficiency\",\"opportunity\":\"Auto-learning terminology mapper using ML to handle unmapped clinical terms\",\"current_state\":\"15% of messages require manual clinical review for terminology mapping\",\"target_state\":\"ML model auto-maps 90% of previously-failed terms, reducing manual review to 5%\",\"impact_estimate\":\"high\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS2_ID,\"lever_type\":\"growth\",\"opportunity\":\"Expand data exchange to allied health, aged care, and mental health providers\",\"current_state\":\"Data exchange limited to hospitals, GPs, and pathology\",\"target_state\":\"Connected ecosystem including physio, OT, psychology, aged care, NDIS providers\",\"impact_estimate\":\"high\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS3_ID,\"lever_type\":\"effectiveness\",\"opportunity\":\"AI clinical documentation — auto-generate consultation notes from video transcript\",\"current_state\":\"Clinicians spend 8 min on documentation per 20 min consult\",\"target_state\":\"AI generates draft notes from conversation, clinician reviews in 2 min\",\"impact_estimate\":\"high\"}"
post "$API/step2/levers" "{\"value_stream_id\":$VS3_ID,\"lever_type\":\"growth\",\"opportunity\":\"Chronic disease management via continuous remote monitoring integration\",\"current_state\":\"Telehealth is episodic — individual consultations only\",\"target_state\":\"RPM devices feed data into telehealth platform, triggering proactive clinician interventions\",\"impact_estimate\":\"high\"}"

echo " done"

# ============================================================
# Step 3: SWOT to TOWS Action Engine
# ============================================================
echo -e "\n--- Step 3: SWOT Entries ---"
# Strengths
S1=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"strength\",\"description\":\"#1 health IT vendor in Australia — largest installed base across hospitals, pharmacies, and aged care (4,850+ pharmacies, 200+ hospitals)\",\"severity\":\"high\",\"confidence\":\"high\"}")
S1_ID=$(echo "$S1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

S2=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"strength\",\"description\":\"Telstra Group backing: access to Australia's largest telco network, data centres, and \$1.6B enterprise business\",\"severity\":\"high\",\"confidence\":\"high\"}")
S2_ID=$(echo "$S2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

S3=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"strength\",\"description\":\"Deep regulatory expertise in Australian health — My Health Record, PBS, Medicare, ADHA standards compliance\",\"severity\":\"high\",\"confidence\":\"high\"}")
S3_ID=$(echo "$S3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

S4=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"strength\",\"description\":\"Comprehensive portfolio spanning entire care continuum — hospitals, primary care, pharmacy, aged care, telehealth, data exchange\",\"severity\":\"medium\",\"confidence\":\"high\"}")
S4_ID=$(echo "$S4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Weaknesses
W1=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"weakness\",\"description\":\"Fragmented product portfolio from 15+ acquisitions — inconsistent UX, duplicated functionality, technical debt\",\"severity\":\"high\",\"confidence\":\"high\"}")
W1_ID=$(echo "$W1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

W2=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"weakness\",\"description\":\"Only 42% of workloads on cloud — many legacy on-premise installations limit scalability and SaaS margin\",\"severity\":\"high\",\"confidence\":\"high\"}")
W2_ID=$(echo "$W2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

W3=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"weakness\",\"description\":\"Implementation success rate at 87% — 13% of projects experience significant delays or scope issues\",\"severity\":\"medium\",\"confidence\":\"high\"}")
W3_ID=$(echo "$W3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

W4=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"weakness\",\"description\":\"EBITDA margin (12%) well below global health IT peers (18-25%) — investment phase but needs path to profitability\",\"severity\":\"high\",\"confidence\":\"high\"}")
W4_ID=$(echo "$W4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Opportunities
O1=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"opportunity\",\"description\":\"Australian Government \$2.4B Digital Health Strategy 2025-2030 — FHIR-first mandate, My Health Record expansion, interoperability funding\",\"severity\":\"high\",\"confidence\":\"high\"}")
O1_ID=$(echo "$O1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

O2=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"opportunity\",\"description\":\"AI in clinical decision support — Gen AI for clinical documentation, radiology, pathology, and population health analytics\",\"severity\":\"high\",\"confidence\":\"medium\"}")
O2_ID=$(echo "$O2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

O3=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"opportunity\",\"description\":\"Aged care reform (Royal Commission response) — mandatory digital care management, quality reporting, AN-ACC funding model\",\"severity\":\"high\",\"confidence\":\"high\"}")
O3_ID=$(echo "$O3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

O4=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"opportunity\",\"description\":\"International expansion into UK NHS, SE Asia markets where Australian health IT standards are recognized\",\"severity\":\"medium\",\"confidence\":\"medium\"}")
O4_ID=$(echo "$O4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Threats
T1=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"threat\",\"description\":\"Epic Systems expanding into Australia — won Royal Melbourne Hospital, actively targeting large health networks\",\"severity\":\"high\",\"confidence\":\"high\"}")
T1_ID=$(echo "$T1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

T2=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"threat\",\"description\":\"Cybersecurity threats to health data — Medibank breach (2022) raised bar for health data protection, increasing compliance costs\",\"severity\":\"high\",\"confidence\":\"high\"}")
T2_ID=$(echo "$T2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

T3=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"threat\",\"description\":\"Health workforce shortage — clinician burnout reducing willingness to adopt complex new systems\",\"severity\":\"medium\",\"confidence\":\"high\"}")
T3_ID=$(echo "$T3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

T4=$(post "$API/step3/swot" "{\"business_unit_id\":$TH_BU_ID,\"category\":\"threat\",\"description\":\"Global Big Tech entry: Google Health, Microsoft Cloud for Healthcare, Amazon HealthLake competing for health data platform\",\"severity\":\"medium\",\"confidence\":\"medium\"}")
T4_ID=$(echo "$T4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "SWOT IDs: S=$S1_ID,$S2_ID,$S3_ID,$S4_ID W=$W1_ID,$W2_ID,$W3_ID,$W4_ID O=$O1_ID,$O2_ID,$O3_ID,$O4_ID T=$T1_ID,$T2_ID,$T3_ID,$T4_ID"

echo -e "\n--- Step 3: TOWS Actions ---"
TOWS1=$(post "$API/step3/tows" "{\"strategy_type\":\"SO\",\"swot_entry_1_id\":$S1_ID,\"swot_entry_2_id\":$O1_ID,\"action_description\":\"Lead the FHIR-first national health data infrastructure — position Telstra Health as the interoperability backbone for Australian digital health\",\"priority\":\"critical\",\"impact_score\":10,\"rationale\":\"#1 market position + government mandate = capture national infrastructure role\"}")
TOWS1_ID=$(echo "$TOWS1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS2=$(post "$API/step3/tows" "{\"strategy_type\":\"SO\",\"swot_entry_1_id\":$S4_ID,\"swot_entry_2_id\":$O3_ID,\"action_description\":\"Build integrated aged care platform covering AN-ACC funding, quality indicators, clinical care, and workforce management\",\"priority\":\"high\",\"impact_score\":8,\"rationale\":\"Care continuum portfolio + aged care reform = dominant position in fastest-growing segment\"}")
TOWS2_ID=$(echo "$TOWS2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS3=$(post "$API/step3/tows" "{\"strategy_type\":\"WO\",\"swot_entry_1_id\":$W1_ID,\"swot_entry_2_id\":$O2_ID,\"action_description\":\"Use AI/Gen AI as the unifying layer across fragmented products — common AI services platform (clinical NLP, summarization, decision support) shared across all BUs\",\"priority\":\"critical\",\"impact_score\":9,\"rationale\":\"AI platform addresses fragmentation while leapfrogging competitors on clinical AI\"}")
TOWS3_ID=$(echo "$TOWS3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS4=$(post "$API/step3/tows" "{\"strategy_type\":\"WO\",\"swot_entry_1_id\":$W2_ID,\"swot_entry_2_id\":$O1_ID,\"action_description\":\"Accelerate cloud migration leveraging government digital health funding — migrate 70% of workloads to cloud-native by 2027\",\"priority\":\"high\",\"impact_score\":8,\"rationale\":\"Cloud migration improves margins, enables AI, and aligns with government cloud-first mandate\"}")
TOWS4_ID=$(echo "$TOWS4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS5=$(post "$API/step3/tows" "{\"strategy_type\":\"ST\",\"swot_entry_1_id\":$S3_ID,\"swot_entry_2_id\":$T1_ID,\"action_description\":\"Deepen regulatory moat — invest in Australian-specific features (PBS, Medicare, My Health Record) that global vendors like Epic cannot easily replicate\",\"priority\":\"high\",\"impact_score\":8,\"rationale\":\"Regulatory expertise is strongest defense against global entrants\"}")
TOWS5_ID=$(echo "$TOWS5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TOWS6=$(post "$API/step3/tows" "{\"strategy_type\":\"WT\",\"swot_entry_1_id\":$W4_ID,\"swot_entry_2_id\":$T4_ID,\"action_description\":\"Accelerate path to 18%+ EBITDA margin via cloud migration, product consolidation, and AI-driven services efficiency before Big Tech commoditizes infrastructure layer\",\"priority\":\"high\",\"impact_score\":7,\"rationale\":\"Must reach profitable scale before cloud giants undercut infrastructure pricing\"}")
TOWS6_ID=$(echo "$TOWS6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "TOWS IDs: $TOWS1_ID,$TOWS2_ID,$TOWS3_ID,$TOWS4_ID,$TOWS5_ID,$TOWS6_ID"

# ============================================================
# Step 4: Four-Layer Strategy & Strategic OKRs
# ============================================================
echo -e "\n--- Step 4: Strategy Inputs ---"
post "$API/step4/inputs" '{"input_type":"business_strategy","title":"Telstra Health 3-Year Strategic Plan FY2025-2028","content":"Grow from $535M to $900M revenue by FY2028 through: (1) Winning government digital health infrastructure contracts, (2) Aged care platform leadership, (3) Cloud migration driving SaaS margin expansion, (4) AI-powered clinical tools differentiation. Path to 18% EBITDA margin by FY2028."}'
post "$API/step4/inputs" '{"input_type":"digital_strategy","title":"Telstra Health Platform & Cloud Strategy","content":"Unified digital health platform on Azure/AWS. FHIR R4 as canonical data model. API-first architecture. Self-service configuration for customers. Mobile-first clinician experience. Cloud-native by 2027 for all new deployments."}'
post "$API/step4/inputs" '{"input_type":"data_strategy","title":"Health Data & Interoperability Strategy","content":"Build Australia national health data fabric. FHIR R4 + Australian Base profiles. SNOMED CT-AU and AMT terminology services. Real-time clinical data exchange. Privacy-preserving analytics using federated learning. Population health insights platform."}'
post "$API/step4/inputs" '{"input_type":"gen_ai_strategy","title":"Telstra Health AI & Gen AI Roadmap","content":"Clinical AI services platform shared across all products: (1) Clinical documentation AI — generate consultation notes from voice, (2) Diagnostic decision support — radiology, pathology AI, (3) Medication safety AI — drug interaction and allergy checking, (4) Population health AI — risk stratification and care gap identification. Governance: TGA compliance for clinical AI, explainability requirements, clinician-in-the-loop."}'
post "$API/step4/inputs" '{"input_type":"competitor_strategy","title":"Competitive Intelligence — Epic Expansion in ANZ","content":"Epic won Royal Melbourne Hospital (2024) and targeting 5 additional large health networks in ANZ. Key Epic advantages: proven US track record, single integrated platform, strong KLAS ratings. Key Epic disadvantages in ANZ: US-centric, no PBS/Medicare integration, limited aged care, high TCO, limited local support. Telstra Health must emphasize ANZ regulatory depth and care continuum breadth."}'
post "$API/step4/inputs" '{"input_type":"document_reference","title":"Australian Digital Health Agency — National Strategy 2025-2030","content":"Government mandates: FHIR-based interoperability by 2027, expanded My Health Record, digital prescriptions nationally, remote monitoring funding for chronic disease, AI safety framework for clinical decision support, data sovereignty requirements.","file_name":"adha_national_strategy_2025.pdf"}'
post "$API/step4/inputs" '{"input_type":"document_reference","title":"Royal Commission into Aged Care Quality and Safety — Digital Response","content":"Mandatory requirements: real-time quality reporting, AN-ACC digital assessment tools, connected care coordination, family portal access, workforce rostering compliance. Estimated $1.2B in aged care digital investment over 5 years.","file_name":"aged_care_rc_digital_response.pdf"}'
post "$API/step4/inputs" '{"input_type":"document_reference","title":"KLAS ANZ Provider Market Report 2025","content":"Telstra Health leads in pharmacy (95% market share) and aged care (40%). Hospital EHR market share 30% but declining in large facilities (Epic/Oracle winning). Telehealth fragmented. Data exchange growing 35% YoY. Customer satisfaction scores improving but below Epic.","file_name":"klas_anz_2025.pdf"}'

echo -e "\n--- Step 4: Strategies ---"
STR1=$(post "$API/step4/strategies" "{\"layer\":\"business\",\"name\":\"National Health Data Infrastructure\",\"description\":\"Position Telstra Health as the backbone of Australian digital health interoperability — operate the national FHIR data exchange, clinical registries, and population health analytics platform.\",\"tows_action_id\":$TOWS1_ID,\"risk_level\":\"high\",\"risks\":\"Government procurement cycles, political risk, competing consortiums, scale of infrastructure investment\"}")
STR1_ID=$(echo "$STR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR2=$(post "$API/step4/strategies" "{\"layer\":\"business\",\"name\":\"Aged Care Platform Leadership\",\"description\":\"Build the market-leading integrated aged care platform — AN-ACC funding, quality indicators, clinical care, workforce, and family engagement in a single SaaS platform.\",\"tows_action_id\":$TOWS2_ID,\"risk_level\":\"medium\",\"risks\":\"Aged care provider financial stress, regulatory changes, competitor consolidation\"}")
STR2_ID=$(echo "$STR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR3=$(post "$API/step4/strategies" "{\"layer\":\"digital\",\"name\":\"Unified Health Platform (Cloud-Native)\",\"description\":\"Consolidate 15+ acquired products into a unified cloud-native platform with shared services, consistent UX, and FHIR-based data model. Target 70% cloud workloads by 2027.\",\"tows_action_id\":$TOWS4_ID,\"risk_level\":\"high\",\"risks\":\"Customer disruption during migration, technical debt in legacy systems, cloud migration costs, team capability gaps\"}")
STR3_ID=$(echo "$STR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR4=$(post "$API/step4/strategies" "{\"layer\":\"data\",\"name\":\"FHIR-First Data Fabric\",\"description\":\"Build Australia-wide health data fabric using FHIR R4 and Australian Base profiles. Enable real-time clinical data exchange, patient-controlled sharing, and privacy-preserving population analytics.\",\"tows_action_id\":$TOWS1_ID,\"risk_level\":\"medium\",\"risks\":\"FHIR maturity gaps in Australian profiles, provider adoption speed, data quality variability\"}")
STR4_ID=$(echo "$STR4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR5=$(post "$API/step4/strategies" "{\"layer\":\"gen_ai\",\"name\":\"Clinical AI Services Platform\",\"description\":\"Build shared AI/Gen AI platform powering clinical documentation, decision support, medication safety, and population health across all Telstra Health products.\",\"tows_action_id\":$TOWS3_ID,\"risk_level\":\"high\",\"risks\":\"TGA regulatory framework for clinical AI, model safety and bias, clinician trust, training data quality\"}")
STR5_ID=$(echo "$STR5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

STR6=$(post "$API/step4/strategies" "{\"layer\":\"business\",\"name\":\"Regulatory Moat & ANZ Depth\",\"description\":\"Invest in Australian-specific capabilities (PBS, Medicare, My Health Record, AN-ACC) that global vendors cannot easily replicate, creating a regulatory moat against Epic and Oracle expansion.\",\"tows_action_id\":$TOWS5_ID,\"risk_level\":\"low\",\"risks\":\"Regulatory changes, cost of maintaining compliance, risk of over-indexing on local vs global\"}")
STR6_ID=$(echo "$STR6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Strategy IDs: $STR1_ID,$STR2_ID,$STR3_ID,$STR4_ID,$STR5_ID,$STR6_ID"

echo -e "\n--- Step 4: Strategic OKRs ---"
OKR1=$(post "$API/step4/okrs" "{\"strategy_id\":$STR1_ID,\"objective\":\"Win national health data infrastructure contract and connect 500+ health organisations by 2027\",\"time_horizon\":\"2025-2027\",\"status\":\"active\"}")
OKR1_ID=$(echo "$OKR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR2=$(post "$API/step4/okrs" "{\"strategy_id\":$STR2_ID,\"objective\":\"Grow aged care platform to 2,000 facilities and 60% market share by FY2027\",\"time_horizon\":\"2025-2027\",\"status\":\"active\"}")
OKR2_ID=$(echo "$OKR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR3=$(post "$API/step4/okrs" "{\"strategy_id\":$STR3_ID,\"objective\":\"Migrate 70% of customer workloads to cloud-native platform by FY2027\",\"time_horizon\":\"2025-2027\",\"status\":\"active\"}")
OKR3_ID=$(echo "$OKR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR4=$(post "$API/step4/okrs" "{\"strategy_id\":$STR5_ID,\"objective\":\"Launch clinical AI suite in 50 hospitals and 1,000 pharmacies with measurable clinical outcomes\",\"time_horizon\":\"2025-2027\",\"status\":\"active\"}")
OKR4_ID=$(echo "$OKR4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

OKR5=$(post "$API/step4/okrs" "{\"strategy_id\":$STR3_ID,\"objective\":\"Improve EBITDA margin from 12% to 18% by FY2028\",\"time_horizon\":\"2025-2028\",\"status\":\"active\"}")
OKR5_ID=$(echo "$OKR5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "OKR IDs: $OKR1_ID,$OKR2_ID,$OKR3_ID,$OKR4_ID,$OKR5_ID"

echo -e "\n--- Step 4: Key Results ---"
post "$API/step4/okrs/$OKR1_ID/key-results" '{"key_result":"Connect 500 health organisations to FHIR data exchange","metric":"connected_orgs","current_value":85,"target_value":500,"unit":"organisations"}'
post "$API/step4/okrs/$OKR1_ID/key-results" '{"key_result":"Process 100M clinical messages per month through data fabric","metric":"monthly_messages","current_value":18,"target_value":100,"unit":"million"}'
post "$API/step4/okrs/$OKR1_ID/key-results" '{"key_result":"Win 3 state/territory health data infrastructure contracts","metric":"govt_contracts","current_value":1,"target_value":3,"unit":"contracts"}'

post "$API/step4/okrs/$OKR2_ID/key-results" '{"key_result":"2,000 aged care facilities on platform","metric":"facilities","current_value":1450,"target_value":2000,"unit":"facilities"}'
post "$API/step4/okrs/$OKR2_ID/key-results" '{"key_result":"100% AN-ACC digital assessment tool coverage for connected facilities","metric":"anacc_coverage","current_value":45,"target_value":100,"unit":"%"}'

post "$API/step4/okrs/$OKR3_ID/key-results" '{"key_result":"70% of customer workloads on cloud","metric":"cloud_pct","current_value":42,"target_value":70,"unit":"%"}'
post "$API/step4/okrs/$OKR3_ID/key-results" '{"key_result":"Reduce on-premise support FTEs by 40%","metric":"onprem_support_reduction","current_value":0,"target_value":40,"unit":"%"}'

post "$API/step4/okrs/$OKR4_ID/key-results" '{"key_result":"Clinical AI deployed in 50 hospitals","metric":"hospital_ai_deployments","current_value":3,"target_value":50,"unit":"hospitals"}'
post "$API/step4/okrs/$OKR4_ID/key-results" '{"key_result":"AI documentation reduces clinician admin time by 40%","metric":"admin_time_reduction","current_value":0,"target_value":40,"unit":"%"}'
post "$API/step4/okrs/$OKR4_ID/key-results" '{"key_result":"Medication safety AI prevents 10,000 adverse drug events annually","metric":"prevented_ades","current_value":500,"target_value":10000,"unit":"events/yr"}'

post "$API/step4/okrs/$OKR5_ID/key-results" '{"key_result":"EBITDA margin reaches 18%","metric":"ebitda_margin","current_value":12,"target_value":18,"unit":"%"}'
post "$API/step4/okrs/$OKR5_ID/key-results" '{"key_result":"SaaS revenue reaches 70% of total revenue","metric":"saas_revenue_pct","current_value":58,"target_value":70,"unit":"%"}'

echo " done"

# ============================================================
# Step 5: Digital Initiatives & RICE Prioritization
# ============================================================
echo -e "\n--- Step 5: Product Groups & Digital Products ---"
PG1=$(post "$API/step5/product-groups" '{"name":"Clinical AI Platform","description":"AI/Gen AI services for clinical decision support, documentation, and analytics"}')
PG1_ID=$(echo "$PG1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

PG2=$(post "$API/step5/product-groups" '{"name":"Interoperability & Data","description":"FHIR data exchange, clinical registries, and health data analytics"}')
PG2_ID=$(echo "$PG2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

PG3=$(post "$API/step5/product-groups" '{"name":"Aged Care Suite","description":"Integrated aged care management platform"}')
PG3_ID=$(echo "$PG3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

PG4=$(post "$API/step5/product-groups" '{"name":"Cloud Platform","description":"Shared cloud-native platform services and infrastructure"}')
PG4_ID=$(echo "$PG4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP1=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG1_ID,\"name\":\"Clinical Documentation AI\",\"description\":\"AI-powered clinical note generation from voice/text input with SNOMED coding\"}")
DP1_ID=$(echo "$DP1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP2=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG1_ID,\"name\":\"Medication Safety Engine\",\"description\":\"Real-time drug interaction, allergy, and dosage checking with Gen AI explanations\"}")
DP2_ID=$(echo "$DP2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP3=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG2_ID,\"name\":\"FHIR Data Exchange Gateway\",\"description\":\"National-scale FHIR R4 data exchange with Australian Base profiles and consent management\"}")
DP3_ID=$(echo "$DP3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP4=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG3_ID,\"name\":\"Aged Care 360\",\"description\":\"Integrated aged care platform: AN-ACC, quality indicators, care plans, family portal, workforce\"}")
DP4_ID=$(echo "$DP4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP5=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG4_ID,\"name\":\"Health Cloud Platform\",\"description\":\"Shared cloud infrastructure, identity, configuration, and deployment services for all products\"}")
DP5_ID=$(echo "$DP5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DP6=$(post "$API/step5/digital-products" "{\"product_group_id\":$PG1_ID,\"name\":\"Population Health Analytics\",\"description\":\"AI-powered population health risk stratification, care gap identification, and outcomes tracking\"}")
DP6_ID=$(echo "$DP6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Product Group IDs: $PG1_ID,$PG2_ID,$PG3_ID,$PG4_ID | Digital Product IDs: $DP1_ID,$DP2_ID,$DP3_ID,$DP4_ID,$DP5_ID,$DP6_ID"

echo -e "\n--- Step 5: Initiatives ---"
INIT1=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP1_ID,\"strategy_id\":$STR5_ID,\"name\":\"Voice-to-Clinical-Note AI\",\"description\":\"Gen AI system that listens to patient consultations and generates structured clinical notes with SNOMED CT-AU coding\",\"reach\":5000,\"impact\":3,\"confidence\":0.8,\"effort\":12,\"value_score\":5,\"size_score\":5,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT1_ID=$(echo "$INIT1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT2=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP3_ID,\"strategy_id\":$STR4_ID,\"name\":\"National FHIR Data Exchange v2\",\"description\":\"Scale FHIR data exchange to support 500+ organisations with real-time clinical events, consent management, and AU Base profiles\",\"reach\":500,\"impact\":3,\"confidence\":0.8,\"effort\":14,\"value_score\":5,\"size_score\":5,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT2_ID=$(echo "$INIT2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT3=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP4_ID,\"strategy_id\":$STR2_ID,\"name\":\"AN-ACC Digital Assessment Platform\",\"description\":\"Digital tool for AN-ACC (Australian National Aged Care Classification) assessments, funding calculations, and quality reporting\",\"reach\":2000,\"impact\":3,\"confidence\":1.0,\"effort\":8,\"value_score\":5,\"size_score\":4,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT3_ID=$(echo "$INIT3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT4=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP2_ID,\"strategy_id\":$STR5_ID,\"name\":\"Real-Time Medication Safety with Gen AI Explanations\",\"description\":\"Upgrade medication safety engine with Gen AI-generated plain-language explanations of drug interactions and allergy alerts for clinicians and patients\",\"reach\":4850,\"impact\":3,\"confidence\":0.8,\"effort\":10,\"value_score\":5,\"size_score\":4,\"roadmap_phase\":\"Phase 1\",\"status\":\"approved\"}")
INIT4_ID=$(echo "$INIT4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT5=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP5_ID,\"strategy_id\":$STR3_ID,\"name\":\"Hospital EHR Cloud Migration\",\"description\":\"Migrate top 30 on-premise hospital EHR installations to cloud-native platform with zero-downtime cutover\",\"reach\":30,\"impact\":3,\"confidence\":0.8,\"effort\":18,\"value_score\":4,\"size_score\":5,\"roadmap_phase\":\"Phase 1\",\"status\":\"in_progress\"}")
INIT5_ID=$(echo "$INIT5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT6=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP6_ID,\"strategy_id\":$STR5_ID,\"name\":\"Population Health Risk Stratification\",\"description\":\"ML model for population-level risk stratification — identify high-risk patients for chronic disease, mental health, and hospital readmission\",\"reach\":200,\"impact\":3,\"confidence\":0.5,\"effort\":12,\"value_score\":4,\"size_score\":4,\"roadmap_phase\":\"Phase 2\",\"status\":\"proposed\"}")
INIT6_ID=$(echo "$INIT6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INIT7=$(post "$API/step5/initiatives" "{\"digital_product_id\":$DP4_ID,\"strategy_id\":$STR2_ID,\"name\":\"Family & Carer Portal\",\"description\":\"Web and mobile portal for aged care families — real-time updates on care, medication, activities, incident notifications\",\"reach\":50000,\"impact\":2,\"confidence\":1.0,\"effort\":6,\"value_score\":4,\"size_score\":3,\"roadmap_phase\":\"Phase 1\",\"status\":\"approved\"}")
INIT7_ID=$(echo "$INIT7" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Initiative IDs: $INIT1_ID,$INIT2_ID,$INIT3_ID,$INIT4_ID,$INIT5_ID,$INIT6_ID,$INIT7_ID"

# ============================================================
# Step 6: Epics & Teams + Product OKRs
# ============================================================
echo -e "\n--- Step 6: Teams ---"
TEAM1=$(post "$API/step6/teams" '{"name":"Clinical AI Engineering","capacity":20}')
TEAM1_ID=$(echo "$TEAM1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM2=$(post "$API/step6/teams" '{"name":"Interoperability & FHIR","capacity":18}')
TEAM2_ID=$(echo "$TEAM2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM3=$(post "$API/step6/teams" '{"name":"Aged Care Product","capacity":15}')
TEAM3_ID=$(echo "$TEAM3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM4=$(post "$API/step6/teams" '{"name":"Cloud Platform Engineering","capacity":22}')
TEAM4_ID=$(echo "$TEAM4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM5=$(post "$API/step6/teams" '{"name":"Hospital EHR Delivery","capacity":25}')
TEAM5_ID=$(echo "$TEAM5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

TEAM6=$(post "$API/step6/teams" '{"name":"Pharmacy & Medication","capacity":12}')
TEAM6_ID=$(echo "$TEAM6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Team IDs: $TEAM1_ID,$TEAM2_ID,$TEAM3_ID,$TEAM4_ID,$TEAM5_ID,$TEAM6_ID"

echo -e "\n--- Step 6: Product OKRs ---"
POKR1=$(post "$API/step6/product-okrs" "{\"strategic_okr_id\":$OKR4_ID,\"digital_product_id\":$DP1_ID,\"objective\":\"Deploy clinical documentation AI in 30 hospitals with 40% admin time reduction\",\"status\":\"active\"}")
POKR1_ID=$(echo "$POKR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

POKR2=$(post "$API/step6/product-okrs" "{\"strategic_okr_id\":$OKR1_ID,\"digital_product_id\":$DP3_ID,\"objective\":\"Scale FHIR data exchange to 300 connected organisations\",\"status\":\"active\"}")
POKR2_ID=$(echo "$POKR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

POKR3=$(post "$API/step6/product-okrs" "{\"strategic_okr_id\":$OKR2_ID,\"digital_product_id\":$DP4_ID,\"objective\":\"Launch Aged Care 360 with AN-ACC in 500 new facilities\",\"status\":\"active\"}")
POKR3_ID=$(echo "$POKR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

POKR4=$(post "$API/step6/product-okrs" "{\"strategic_okr_id\":$OKR3_ID,\"digital_product_id\":$DP5_ID,\"objective\":\"Migrate top 30 hospital EHR installations to cloud\",\"status\":\"active\"}")
POKR4_ID=$(echo "$POKR4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Product OKR IDs: $POKR1_ID,$POKR2_ID,$POKR3_ID,$POKR4_ID"

echo -e "\n--- Step 6: Epics ---"
EPIC1=$(post "$API/step6/epics" "{\"initiative_id\":$INIT1_ID,\"team_id\":$TEAM1_ID,\"product_okr_id\":$POKR1_ID,\"name\":\"Speech-to-Text Clinical Pipeline\",\"description\":\"Build real-time speech transcription pipeline for clinical consultations with medical vocabulary optimisation\",\"status\":\"in_progress\",\"start_date\":\"2025-07-01\",\"target_date\":\"2026-01-01\",\"value_score\":5,\"size_score\":4,\"effort_score\":4,\"risk_level\":\"high\",\"risks\":\"Medical terminology accuracy, accent handling for diverse Australian population, noise in clinical environments\",\"roadmap_phase\":\"Phase 1\"}")
EPIC1_ID=$(echo "$EPIC1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC2=$(post "$API/step6/epics" "{\"initiative_id\":$INIT1_ID,\"team_id\":$TEAM1_ID,\"product_okr_id\":$POKR1_ID,\"name\":\"Clinical Note Generation Engine\",\"description\":\"Gen AI model fine-tuned on Australian clinical notes to generate structured documentation with SNOMED CT-AU coding\",\"status\":\"in_progress\",\"start_date\":\"2025-09-01\",\"target_date\":\"2026-03-01\",\"value_score\":5,\"size_score\":5,\"effort_score\":5,\"risk_level\":\"high\",\"risks\":\"Clinical accuracy, TGA regulatory approval, hallucination of clinical findings\",\"roadmap_phase\":\"Phase 1\"}")
EPIC2_ID=$(echo "$EPIC2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC3=$(post "$API/step6/epics" "{\"initiative_id\":$INIT2_ID,\"team_id\":$TEAM2_ID,\"product_okr_id\":$POKR2_ID,\"name\":\"FHIR R4 Subscription Engine\",\"description\":\"Build scalable FHIR R4 subscription and notification system for real-time clinical events across connected organisations\",\"status\":\"in_progress\",\"start_date\":\"2025-06-01\",\"target_date\":\"2025-12-01\",\"value_score\":5,\"size_score\":4,\"effort_score\":4,\"risk_level\":\"medium\",\"risks\":\"Scale to millions of subscriptions, message ordering guarantees, consent propagation\",\"roadmap_phase\":\"Phase 1\"}")
EPIC3_ID=$(echo "$EPIC3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC4=$(post "$API/step6/epics" "{\"initiative_id\":$INIT3_ID,\"team_id\":$TEAM3_ID,\"product_okr_id\":$POKR3_ID,\"name\":\"AN-ACC Assessment Module\",\"description\":\"Digital AN-ACC assessment tool with automated funding class calculation and quality indicator reporting\",\"status\":\"in_progress\",\"start_date\":\"2025-08-01\",\"target_date\":\"2026-02-01\",\"value_score\":5,\"size_score\":4,\"effort_score\":3,\"risk_level\":\"medium\",\"risks\":\"AN-ACC model changes, integration with existing care plan systems\",\"roadmap_phase\":\"Phase 1\"}")
EPIC4_ID=$(echo "$EPIC4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC5=$(post "$API/step6/epics" "{\"initiative_id\":$INIT5_ID,\"team_id\":$TEAM4_ID,\"product_okr_id\":$POKR4_ID,\"name\":\"Cloud Migration Framework\",\"description\":\"Build repeatable migration framework: assess, containerize, migrate, validate for hospital EHR instances\",\"status\":\"in_progress\",\"start_date\":\"2025-06-01\",\"target_date\":\"2026-06-01\",\"value_score\":4,\"size_score\":5,\"effort_score\":5,\"risk_level\":\"high\",\"risks\":\"Data sovereignty (health data must stay in AU), downtime during migration, performance on shared infrastructure\",\"roadmap_phase\":\"Phase 1\"}")
EPIC5_ID=$(echo "$EPIC5" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC6=$(post "$API/step6/epics" "{\"initiative_id\":$INIT7_ID,\"team_id\":$TEAM3_ID,\"product_okr_id\":$POKR3_ID,\"name\":\"Family & Carer Portal\",\"description\":\"Build web and mobile portal for aged care families with real-time care updates, medication tracking, and incident notifications\",\"status\":\"backlog\",\"start_date\":\"2026-01-01\",\"target_date\":\"2026-06-01\",\"value_score\":4,\"size_score\":3,\"effort_score\":3,\"risk_level\":\"low\",\"roadmap_phase\":\"Phase 1\"}")
EPIC6_ID=$(echo "$EPIC6" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

EPIC7=$(post "$API/step6/epics" "{\"initiative_id\":$INIT4_ID,\"team_id\":$TEAM6_ID,\"name\":\"Gen AI Medication Interaction Explainer\",\"description\":\"Gen AI module that generates plain-language explanations of drug interactions, contraindications, and dosage adjustments for pharmacists and patients\",\"status\":\"backlog\",\"start_date\":\"2026-02-01\",\"target_date\":\"2026-07-01\",\"value_score\":4,\"size_score\":3,\"effort_score\":3,\"risk_level\":\"medium\",\"risks\":\"Clinical accuracy of generated explanations, TGA compliance for patient-facing AI\",\"roadmap_phase\":\"Phase 2\"}")
EPIC7_ID=$(echo "$EPIC7" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Epic IDs: $EPIC1_ID,$EPIC2_ID,$EPIC3_ID,$EPIC4_ID,$EPIC5_ID,$EPIC6_ID,$EPIC7_ID"

echo -e "\n--- Step 6: Epic Dependencies ---"
post "$API/step6/dependencies" "{\"epic_id\":$EPIC2_ID,\"depends_on_epic_id\":$EPIC1_ID,\"dependency_type\":\"blocks\",\"notes\":\"Note generation engine needs speech-to-text pipeline for audio input\"}"
post "$API/step6/dependencies" "{\"epic_id\":$EPIC6_ID,\"depends_on_epic_id\":$EPIC4_ID,\"dependency_type\":\"blocks\",\"notes\":\"Family portal needs AN-ACC module for care data\"}"
post "$API/step6/dependencies" "{\"epic_id\":$EPIC5_ID,\"depends_on_epic_id\":$EPIC3_ID,\"dependency_type\":\"relates_to\",\"notes\":\"Cloud migration benefits from FHIR subscription engine for data sync\"}"

echo " done"

# ============================================================
# Step 7: Features & Roadmap + Delivery OKRs
# ============================================================
echo -e "\n--- Step 7: Delivery OKRs ---"
DOKR1=$(post "$API/step7/delivery-okrs" "{\"product_okr_id\":$POKR1_ID,\"team_id\":$TEAM1_ID,\"objective\":\"Ship clinical documentation AI v1 with 95% SNOMED coding accuracy to 10 pilot hospitals\",\"status\":\"active\"}")
DOKR1_ID=$(echo "$DOKR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DOKR2=$(post "$API/step7/delivery-okrs" "{\"product_okr_id\":$POKR2_ID,\"team_id\":$TEAM2_ID,\"objective\":\"Scale FHIR exchange to handle 50M messages/month with 99.9% uptime\",\"status\":\"active\"}")
DOKR2_ID=$(echo "$DOKR2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DOKR3=$(post "$API/step7/delivery-okrs" "{\"product_okr_id\":$POKR3_ID,\"team_id\":$TEAM3_ID,\"objective\":\"Launch Aged Care 360 with AN-ACC to 200 facilities in first 6 months\",\"status\":\"active\"}")
DOKR3_ID=$(echo "$DOKR3" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

DOKR4=$(post "$API/step7/delivery-okrs" "{\"product_okr_id\":$POKR4_ID,\"team_id\":$TEAM4_ID,\"objective\":\"Complete cloud migration for 10 hospital EHR instances with zero data loss\",\"status\":\"active\"}")
DOKR4_ID=$(echo "$DOKR4" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Delivery OKR IDs: $DOKR1_ID,$DOKR2_ID,$DOKR3_ID,$DOKR4_ID"

echo -e "\n--- Step 7: Features ---"
# Features for Epic 1: Speech-to-Text
post "$API/step7/features" "{\"epic_id\":$EPIC1_ID,\"delivery_okr_id\":$DOKR1_ID,\"name\":\"Medical Vocabulary Speech Model\",\"description\":\"Fine-tuned speech recognition model for Australian medical terminology, drug names, and clinical abbreviations\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":18,\"start_date\":\"2025-07-15\",\"target_date\":\"2025-11-30\",\"roadmap_phase\":\"Phase 1\",\"acceptance_criteria\":\"95% word accuracy on Australian clinical speech corpus, supports 5 major accent groups\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC1_ID,\"delivery_okr_id\":$DOKR1_ID,\"name\":\"Real-Time Streaming Transcription\",\"description\":\"Low-latency streaming transcription with speaker diarization (clinician vs patient) and background noise filtering\",\"priority\":\"high\",\"status\":\"in_progress\",\"estimated_effort\":12,\"start_date\":\"2025-08-01\",\"target_date\":\"2025-12-15\",\"roadmap_phase\":\"Phase 1\"}"

# Features for Epic 2: Clinical Note Generation
post "$API/step7/features" "{\"epic_id\":$EPIC2_ID,\"delivery_okr_id\":$DOKR1_ID,\"name\":\"SNOMED CT-AU Auto-Coding Engine\",\"description\":\"Map free-text clinical concepts to SNOMED CT-AU codes with confidence scores and clinician override\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":16,\"start_date\":\"2025-09-15\",\"target_date\":\"2026-01-15\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC2_ID,\"delivery_okr_id\":$DOKR1_ID,\"name\":\"Clinical Note Template Library\",\"description\":\"Specialty-specific note templates (ED, surgical, GP, mental health) with AI-assisted section population\",\"priority\":\"high\",\"status\":\"backlog\",\"estimated_effort\":8,\"roadmap_phase\":\"Phase 1\"}"

# Features for Epic 3: FHIR Subscription
post "$API/step7/features" "{\"epic_id\":$EPIC3_ID,\"delivery_okr_id\":$DOKR2_ID,\"name\":\"FHIR R4 Topic-Based Subscriptions\",\"description\":\"Implement FHIR R4 topic-based subscription framework for real-time clinical event notifications\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":14,\"start_date\":\"2025-06-15\",\"target_date\":\"2025-10-15\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC3_ID,\"delivery_okr_id\":$DOKR2_ID,\"name\":\"Patient Consent Service\",\"description\":\"Consent management service integrated with My Health Record consent framework and Privacy Act requirements\",\"priority\":\"high\",\"status\":\"in_progress\",\"estimated_effort\":10,\"start_date\":\"2025-07-01\",\"target_date\":\"2025-11-01\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC3_ID,\"delivery_okr_id\":$DOKR2_ID,\"name\":\"Clinical Terminology Service\",\"description\":\"Hosted SNOMED CT-AU and AMT terminology server with version management and cross-map support\",\"priority\":\"high\",\"status\":\"backlog\",\"estimated_effort\":8,\"roadmap_phase\":\"Phase 1\"}"

# Features for Epic 4: AN-ACC
post "$API/step7/features" "{\"epic_id\":$EPIC4_ID,\"delivery_okr_id\":$DOKR3_ID,\"name\":\"AN-ACC Assessment Forms\",\"description\":\"Digital forms for all AN-ACC assessment domains with validation, auto-save, and offline capability\",\"priority\":\"critical\",\"status\":\"in_progress\",\"estimated_effort\":10,\"start_date\":\"2025-08-15\",\"target_date\":\"2025-12-15\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC4_ID,\"delivery_okr_id\":$DOKR3_ID,\"name\":\"Funding Class Calculator\",\"description\":\"Automated AN-ACC funding class calculation and comparison to historical funding levels\",\"priority\":\"high\",\"status\":\"backlog\",\"estimated_effort\":6,\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC4_ID,\"delivery_okr_id\":$DOKR3_ID,\"name\":\"Quality Indicator Dashboard\",\"description\":\"Real-time quality indicator tracking against National Aged Care Mandatory Quality Indicator Program requirements\",\"priority\":\"high\",\"status\":\"backlog\",\"estimated_effort\":8,\"roadmap_phase\":\"Phase 1\"}"

# Features for Epic 5: Cloud Migration
post "$API/step7/features" "{\"epic_id\":$EPIC5_ID,\"delivery_okr_id\":$DOKR4_ID,\"name\":\"Assessment & Containerization Toolkit\",\"description\":\"Automated assessment of on-prem EHR instances, dependency mapping, and containerization playbooks\",\"priority\":\"high\",\"status\":\"in_progress\",\"estimated_effort\":14,\"start_date\":\"2025-06-15\",\"target_date\":\"2025-11-15\",\"roadmap_phase\":\"Phase 1\"}"
post "$API/step7/features" "{\"epic_id\":$EPIC5_ID,\"delivery_okr_id\":$DOKR4_ID,\"name\":\"Zero-Downtime Cutover Engine\",\"description\":\"Data sync and cutover engine enabling live migration with <5min read-only window\",\"priority\":\"critical\",\"status\":\"backlog\",\"estimated_effort\":20,\"roadmap_phase\":\"Phase 1\"}"

echo " done"

# ============================================================
# Review Gates (HITL checkpoints)
# ============================================================
echo -e "\n--- Review Gates ---"
post "$API/gates/" '{"step_number":1,"gate_number":1,"gate_name":"Market & Financial Data Review","status":"approved","reviewer":"CFO","review_notes":"Financial data validated against Telstra Group annual report and internal management accounts."}'
post "$API/gates/" '{"step_number":2,"gate_number":1,"gate_name":"Value Stream Mapping Review","status":"approved","reviewer":"VP Delivery","review_notes":"EHR implementation VSM validated with delivery team. Data migration confirmed as primary bottleneck."}'
post "$API/gates/" '{"step_number":3,"gate_number":1,"gate_name":"SWOT & Competitive Analysis Review","status":"approved","reviewer":"Chief Strategy Officer","review_notes":"Epic competitive threat validated. Regulatory moat strategy endorsed."}'
post "$API/gates/" '{"step_number":4,"gate_number":1,"gate_name":"Strategy Alignment Gate","status":"approved","reviewer":"CEO","review_notes":"All strategies aligned with Telstra Group digital health vision. Government infrastructure play approved with investment committee."}'
post "$API/gates/" '{"step_number":5,"gate_number":1,"gate_name":"Initiative Prioritization Review","status":"approved","reviewer":"CTO","review_notes":"RICE scores reviewed. Clinical AI and FHIR exchange prioritized. Cloud migration timeline accepted."}'
post "$API/gates/" '{"step_number":6,"gate_number":1,"gate_name":"Epic & Team Allocation Review","status":"pending","reviewer":"VP Engineering","review_notes":"Pending capacity review — Clinical AI team may need 4 additional engineers."}'
post "$API/gates/" '{"step_number":7,"gate_number":1,"gate_name":"Feature Backlog & Roadmap Review","status":"pending","reviewer":"Product Council","review_notes":"Awaiting TGA guidance on clinical AI regulatory requirements before finalizing Phase 1 features."}'

echo -e "\n\n=== SEEDING COMPLETE FOR TELSTRA HEALTH ==="
echo "Summary:"
echo "  Organization: Telstra Health (Healthcare IT)"
echo "  Step 1: 6 BUs, 20 revenue splits, 15 ops metrics, 4 competitors, 4 data URLs"
echo "  Step 2: 4 value streams, 23 steps, 6 levers"
echo "  Step 3: 4 strengths, 4 weaknesses, 4 opportunities, 4 threats, 6 TOWS actions"
echo "  Step 4: 8 strategy inputs (incl 3 documents), 6 strategies, 5 OKRs, 13 key results"
echo "  Step 5: 4 product groups, 6 digital products, 7 initiatives (RICE scored)"
echo "  Step 6: 6 teams, 4 product OKRs, 7 epics, 3 dependencies"
echo "  Step 7: 4 delivery OKRs, 14 features"
echo "  Review Gates: 7 gates (5 approved, 2 pending)"
