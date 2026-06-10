# Eval Report

LLM enabled: **False** (model: `meta-llama/llama-4-scout-17b-16e-instruct`)


**Result: 12/12 cases passed.**


## TC001 - Wrong Document Uploaded  ->  **PASS**

_Member submits two prescriptions for a consultation claim that requires a prescription and a hospital bill._

**Checks:**

- ✅ decision == None
- ✅ stops before decision (decision is null)
- ✅ halted at document verification
- ✅ names uploaded type PRESCRIPTION
- ✅ names required type HOSPITAL_BILL

**Decision output:**

```json
{
  "claim_id": "CLM-EMP001-2024-11-01-05227f",
  "member_id": "EMP001",
  "decision": null,
  "approved_amount": 0.0,
  "confidence_score": 0.0,
  "rejection_reasons": [],
  "member_message": "We could not start processing your CONSULTATION claim because the wrong documents were uploaded. You uploaded: 2 PRESCRIPTION. A CONSULTATION claim requires the following document type(s) which are missing: HOSPITAL_BILL. Please upload the missing HOSPITAL_BILL to proceed.",
  "notes": [],
  "required_action": {
    "type": "UPLOAD_DOCUMENT",
    "uploaded_types": [
      "PRESCRIPTION",
      "PRESCRIPTION"
    ],
    "missing_required_types": [
      "HOSPITAL_BILL"
    ],
    "required_types": [
      "PRESCRIPTION",
      "HOSPITAL_BILL"
    ]
  },
  "halted_stage": "DOCUMENT_VERIFICATION",
  "line_items": [],
  "financial": null,
  "findings": [],
  "component_failures": [],
  "trace": [
    {
      "seq": 1,
      "stage": "INTAKE",
      "component": "IntakeAgent",
      "message": "Received CONSULTATION claim for member EMP001 (amount 1500), 2 document(s).",
      "severity": "INFO",
      "data": {
        "claim_id": "CLM-EMP001-2024-11-01-05227f",
        "category": "CONSULTATION",
        "claimed_amount": 1500,
        "document_types": [
          "PRESCRIPTION",
          "PRESCRIPTION"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 2,
      "stage": "DOCUMENT_VERIFICATION",
      "component": "DocumentVerificationAgent",
      "message": "Wrong documents: uploaded [2 PRESCRIPTION], missing required [HOSPITAL_BILL].",
      "severity": "BLOCKER",
      "data": {
        "required_action": {
          "type": "UPLOAD_DOCUMENT",
          "uploaded_types": [
            "PRESCRIPTION",
            "PRESCRIPTION"
          ],
          "missing_required_types": [
            "HOSPITAL_BILL"
          ],
          "required_types": [
            "PRESCRIPTION",
            "HOSPITAL_BILL"
          ]
        }
      },
      "llm_used": false,
      "duration_ms": null
    }
  ]
}
```


## TC002 - Unreadable Document  ->  **PASS**

_Member uploads a valid prescription but a blurry, unreadable photo of their pharmacy bill._

**Checks:**

- ✅ decision == None
- ✅ does not reject (decision is null)
- ✅ identifies the pharmacy bill is unreadable
- ✅ asks to re-upload that specific document

**Decision output:**

```json
{
  "claim_id": "CLM-EMP004-2024-10-25-755b23",
  "member_id": "EMP004",
  "decision": null,
  "approved_amount": 0.0,
  "confidence_score": 0.0,
  "rejection_reasons": [],
  "member_message": "The PHARMACY_BILL you uploaded (blurry_bill.jpg) is unreadable / too blurry to process, so we cannot read the required details from it. Your claim has NOT been rejected - please simply re-upload a clearer photo or scan of your PHARMACY_BILL and we will continue processing.",
  "notes": [],
  "required_action": {
    "type": "REUPLOAD_DOCUMENT",
    "file_id": "F004",
    "file_name": "blurry_bill.jpg",
    "document_type": "PHARMACY_BILL",
    "reason": "UNREADABLE"
  },
  "halted_stage": "DOCUMENT_VERIFICATION",
  "line_items": [],
  "financial": null,
  "findings": [],
  "component_failures": [],
  "trace": [
    {
      "seq": 1,
      "stage": "INTAKE",
      "component": "IntakeAgent",
      "message": "Received PHARMACY claim for member EMP004 (amount 800), 2 document(s).",
      "severity": "INFO",
      "data": {
        "claim_id": "CLM-EMP004-2024-10-25-755b23",
        "category": "PHARMACY",
        "claimed_amount": 800,
        "document_types": [
          "PRESCRIPTION",
          "PHARMACY_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 2,
      "stage": "DOCUMENT_VERIFICATION",
      "component": "DocumentVerificationAgent",
      "message": "Unreadable required document: PHARMACY_BILL (blurry_bill.jpg).",
      "severity": "BLOCKER",
      "data": {
        "required_action": {
          "type": "REUPLOAD_DOCUMENT",
          "file_id": "F004",
          "file_name": "blurry_bill.jpg",
          "document_type": "PHARMACY_BILL",
          "reason": "UNREADABLE"
        }
      },
      "llm_used": false,
      "duration_ms": null
    }
  ]
}
```


## TC003 - Documents Belong to Different Patients  ->  **PASS**

_The prescription is for Rajesh Kumar but the hospital bill is for a different patient, Arjun Mehta._

**Checks:**

- ✅ decision == None
- ✅ does not proceed to a decision (null)
- ✅ surfaces both patient names

**Decision output:**

```json
{
  "claim_id": "CLM-EMP001-2024-11-01-ee6de2",
  "member_id": "EMP001",
  "decision": null,
  "approved_amount": 0.0,
  "confidence_score": 0.0,
  "rejection_reasons": [],
  "member_message": "The documents you submitted appear to belong to different patients: 'Rajesh Kumar' (on prescription_rajesh.jpg); 'Arjun Mehta' (on bill_arjun.jpg). All documents in a single claim must be for the same patient. Please check and re-upload documents for Rajesh Kumar (or submit a separate claim for Arjun Mehta).",
  "notes": [],
  "required_action": {
    "type": "PATIENT_MISMATCH",
    "names_found": [
      "Rajesh Kumar",
      "Arjun Mehta"
    ],
    "documents": [
      {
        "file": "prescription_rajesh.jpg",
        "patient": "Rajesh Kumar"
      },
      {
        "file": "bill_arjun.jpg",
        "patient": "Arjun Mehta"
      }
    ]
  },
  "halted_stage": "DOCUMENT_VERIFICATION",
  "line_items": [],
  "financial": null,
  "findings": [],
  "component_failures": [],
  "trace": [
    {
      "seq": 1,
      "stage": "INTAKE",
      "component": "IntakeAgent",
      "message": "Received CONSULTATION claim for member EMP001 (amount 1500), 2 document(s).",
      "severity": "INFO",
      "data": {
        "claim_id": "CLM-EMP001-2024-11-01-ee6de2",
        "category": "CONSULTATION",
        "claimed_amount": 1500,
        "document_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 2,
      "stage": "DOCUMENT_VERIFICATION",
      "component": "DocumentVerificationAgent",
      "message": "Patient mismatch across documents: Rajesh Kumar, Arjun Mehta.",
      "severity": "BLOCKER",
      "data": {
        "required_action": {
          "type": "PATIENT_MISMATCH",
          "names_found": [
            "Rajesh Kumar",
            "Arjun Mehta"
          ],
          "documents": [
            {
              "file": "prescription_rajesh.jpg",
              "patient": "Rajesh Kumar"
            },
            {
              "file": "bill_arjun.jpg",
              "patient": "Arjun Mehta"
            }
          ]
        }
      },
      "llm_used": false,
      "duration_ms": null
    }
  ]
}
```


## TC004 - Clean Consultation - Full Approval  ->  **PASS**

_Complete, valid consultation claim with correct documents, valid member, covered treatment, within all limits._

**Checks:**

- ✅ decision == APPROVED
- ✅ approved_amount == 1350
- ✅ confidence above 0.85
- ✅ confidence above 0.85

**Decision output:**

```json
{
  "claim_id": "CLM-EMP001-2024-11-01-55472f",
  "member_id": "EMP001",
  "decision": "APPROVED",
  "approved_amount": 1350.0,
  "confidence_score": 0.93,
  "rejection_reasons": [],
  "member_message": "Good news - your claim has been approved for 1350.",
  "notes": [
    "Eligible amount (covered items): 1500",
    "No network discount (non-network hospital or category has none).",
    "Co-pay 10% applied on 1500 = 150 deducted -> 1350"
  ],
  "required_action": null,
  "halted_stage": null,
  "line_items": [
    {
      "description": "Consultation Fee",
      "amount": 1000.0,
      "covered": true,
      "reason": "Covered (no specific exclusion applies)"
    },
    {
      "description": "CBC Test",
      "amount": 300.0,
      "covered": true,
      "reason": "Covered (no specific exclusion applies)"
    },
    {
      "description": "Dengue NS1 Test",
      "amount": 200.0,
      "covered": true,
      "reason": "Covered (no specific exclusion applies)"
    }
  ],
  "financial": {
    "claimed_amount": 1500.0,
    "eligible_amount": 1500.0,
    "network_discount_percent": 0.0,
    "network_discount_amount": 0.0,
    "after_network_discount": 1500.0,
    "copay_percent": 10.0,
    "copay_amount": 150.0,
    "approved_amount": 1350.0,
    "steps": [
      "Eligible amount (covered items): 1500",
      "No network discount (non-network hospital or category has none).",
      "Co-pay 10% applied on 1500 = 150 deducted -> 1350"
    ]
  },
  "findings": [
    {
      "code": "COVERAGE_OK",
      "component": "CoverageAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Treatment is covered and no exclusion applies.",
      "data": {}
    },
    {
      "code": "ELIGIBILITY_OK",
      "component": "EligibilityAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Member is active and outside all applicable waiting periods.",
      "data": {}
    },
    {
      "code": "FRAUD_OK",
      "component": "FraudAgent",
      "severity": "INFO",
      "passed": true,
      "message": "No fraud signals exceeded thresholds.",
      "data": {
        "fraud_score": 0.0
      }
    },
    {
      "code": "LIMITS_OK",
      "component": "LimitsAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Within per-claim (5000) and annual limits.",
      "data": {}
    },
    {
      "code": "MEDICAL_NECESSITY_OK",
      "component": "MedicalNecessityAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Treatment appears consistent with the diagnosis.",
      "data": {}
    },
    {
      "code": "PRE_AUTH_OK",
      "component": "PreAuthAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Pre-authorization not required.",
      "data": {}
    }
  ],
  "component_failures": [],
  "trace": [
    {
      "seq": 1,
      "stage": "INTAKE",
      "component": "IntakeAgent",
      "message": "Received CONSULTATION claim for member EMP001 (amount 1500), 2 document(s).",
      "severity": "INFO",
      "data": {
        "claim_id": "CLM-EMP001-2024-11-01-55472f",
        "category": "CONSULTATION",
        "claimed_amount": 1500,
        "document_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 2,
      "stage": "DOCUMENT_VERIFICATION",
      "component": "DocumentVerificationAgent",
      "message": "Document verification passed: required types ['PRESCRIPTION', 'HOSPITAL_BILL'] present, all readable, single patient.",
      "severity": "INFO",
      "data": {
        "required_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ],
        "present_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 3,
      "stage": "EXTRACTION",
      "component": "ExtractionAgent",
      "message": "Extracted 2 document(s). Diagnosis='Viral Fever', condition_key=None, 3 line item(s).",
      "severity": "INFO",
      "data": {
        "diagnosis": "Viral Fever",
        "treatment": "Consultation Fee CBC Test Dengue NS1 Test",
        "condition_key": null,
        "line_items": [
          {
            "description": "Consultation Fee",
            "amount": 1000.0
          },
          {
            "description": "CBC Test",
            "amount": 300.0
          },
          {
            "description": "Dengue NS1 Test",
            "amount": 200.0
          }
        ],
        "llm_enrichment": {}
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 4,
      "stage": "ADJUDICATION",
      "component": "CoverageAgent",
      "message": "All items covered under CONSULTATION.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 5,
      "stage": "ADJUDICATION",
      "component": "EligibilityAgent",
      "message": "Member Rajesh Kumar eligible; no waiting period applies.",
      "severity": "INFO",
      "data": {
        "condition_key": null
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 6,
      "stage": "FRAUD",
      "component": "FraudAgent",
      "message": "No fraud signals above threshold.",
      "severity": "INFO",
      "data": {
        "fraud_score": 0.0,
        "same_day_total": 1
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 7,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "Category sub-limit 2000 noted (advisory).",
      "severity": "INFO",
      "data": {
        "sub_limit": 2000
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 8,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "All monetary limits satisfied.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 9,
      "stage": "ADJUDICATION",
      "component": "MedicalNecessityAgent",
      "message": "Treatment appears consistent with the diagnosis.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 10,
      "stage": "ADJUDICATION",
      "component": "PreAuthAgent",
      "message": "No pre-auth rules apply to this category.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 11,
      "stage": "FINANCIAL",
      "component": "FinancialAgent",
      "message": "Computed payable amount: 1350. Eligible amount (covered items): 1500 | No network discount (non-network hospital or category has none). | Co-pay 10% applied on 1500 = 150 deducted -> 1350",
      "severity": "INFO",
      "data": {
        "claimed_amount": 1500.0,
        "eligible_amount": 1500.0,
        "network_discount_percent": 0.0,
        "network_discount_amount": 0.0,
        "after_network_discount": 1500.0,
        "copay_percent": 10.0,
        "copay_amount": 150.0,
        "approved_amount": 1350.0,
        "steps": [
          "Eligible amount (covered items): 1500",
          "No network discount (non-network hospital or category has none).",
          "Co-pay 10% applied on 1500 = 150 deducted -> 1350"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 12,
      "stage": "DECISION",
      "component": "DecisionAgent",
      "message": "Final decision: APPROVED | approved 1350 | confidence 0.93 | reasons []",
      "severity": "INFO",
      "data": {
        "decision": "APPROVED",
        "confidence": 0.93,
        "component_failures": 0
      },
      "llm_used": false,
      "duration_ms": null
    }
  ]
}
```


## TC005 - Waiting Period - Diabetes  ->  **PASS**

_Member joined 2024-09-01. Claims for diabetes treatment on 2024-10-15, which is within the 90-day waiting period for diabetes._

**Checks:**

- ✅ decision == REJECTED
- ✅ rejection_reasons superset of ['WAITING_PERIOD']
- ✅ rejected for waiting period
- ✅ states eligibility date 2024-11-30

**Decision output:**

```json
{
  "claim_id": "CLM-EMP005-2024-10-15-9dff49",
  "member_id": "EMP005",
  "decision": "REJECTED",
  "approved_amount": 0.0,
  "confidence_score": 0.95,
  "rejection_reasons": [
    "WAITING_PERIOD"
  ],
  "member_message": "Your claim has been rejected. This claim is for a 'diabetes' condition, which has a 90-day waiting period. The member joined on 2024-09-01 and the treatment was on 2024-10-15 (44 days later). Diabetes-related claims are only eligible from 2024-11-30.",
  "notes": [],
  "required_action": null,
  "halted_stage": null,
  "line_items": [],
  "financial": {
    "claimed_amount": 3000.0,
    "eligible_amount": 3000.0,
    "network_discount_percent": 0.0,
    "network_discount_amount": 0.0,
    "after_network_discount": 3000.0,
    "copay_percent": 10.0,
    "copay_amount": 300.0,
    "approved_amount": 2700.0,
    "steps": [
      "Eligible amount (covered items): 3000",
      "No network discount (non-network hospital or category has none).",
      "Co-pay 10% applied on 3000 = 300 deducted -> 2700"
    ]
  },
  "findings": [
    {
      "code": "COVERAGE_OK",
      "component": "CoverageAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Treatment is covered and no exclusion applies.",
      "data": {}
    },
    {
      "code": "WAITING_PERIOD",
      "component": "EligibilityAgent",
      "severity": "BLOCKER",
      "passed": false,
      "message": "This claim is for a 'diabetes' condition, which has a 90-day waiting period. The member joined on 2024-09-01 and the treatment was on 2024-10-15 (44 days later). Diabetes-related claims are only eligible from 2024-11-30.",
      "data": {
        "condition": "diabetes",
        "waiting_days": 90,
        "eligible_from": "2024-11-30",
        "elapsed_days": 44
      }
    },
    {
      "code": "FRAUD_OK",
      "component": "FraudAgent",
      "severity": "INFO",
      "passed": true,
      "message": "No fraud signals exceeded thresholds.",
      "data": {
        "fraud_score": 0.0
      }
    },
    {
      "code": "LIMITS_OK",
      "component": "LimitsAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Within per-claim (5000) and annual limits.",
      "data": {}
    },
    {
      "code": "MEDICAL_NECESSITY_OK",
      "component": "MedicalNecessityAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Treatment appears consistent with the diagnosis.",
      "data": {}
    },
    {
      "code": "PRE_AUTH_OK",
      "component": "PreAuthAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Pre-authorization not required.",
      "data": {}
    }
  ],
  "component_failures": [],
  "trace": [
    {
      "seq": 1,
      "stage": "INTAKE",
      "component": "IntakeAgent",
      "message": "Received CONSULTATION claim for member EMP005 (amount 3000), 2 document(s).",
      "severity": "INFO",
      "data": {
        "claim_id": "CLM-EMP005-2024-10-15-9dff49",
        "category": "CONSULTATION",
        "claimed_amount": 3000,
        "document_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 2,
      "stage": "DOCUMENT_VERIFICATION",
      "component": "DocumentVerificationAgent",
      "message": "Document verification passed: required types ['PRESCRIPTION', 'HOSPITAL_BILL'] present, all readable, single patient.",
      "severity": "INFO",
      "data": {
        "required_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ],
        "present_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 3,
      "stage": "EXTRACTION",
      "component": "ExtractionAgent",
      "message": "Extracted 2 document(s). Diagnosis='Type 2 Diabetes Mellitus', condition_key=diabetes, 0 line item(s).",
      "severity": "INFO",
      "data": {
        "diagnosis": "Type 2 Diabetes Mellitus",
        "treatment": "",
        "condition_key": "diabetes",
        "line_items": [],
        "llm_enrichment": {}
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 4,
      "stage": "ADJUDICATION",
      "component": "CoverageAgent",
      "message": "All items covered under CONSULTATION.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 5,
      "stage": "ADJUDICATION",
      "component": "EligibilityAgent",
      "message": "This claim is for a 'diabetes' condition, which has a 90-day waiting period. The member joined on 2024-09-01 and the treatment was on 2024-10-15 (44 days later). Diabetes-related claims are only eligible from 2024-11-30.",
      "severity": "BLOCKER",
      "data": {
        "eligible_from": "2024-11-30"
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 6,
      "stage": "FRAUD",
      "component": "FraudAgent",
      "message": "No fraud signals above threshold.",
      "severity": "INFO",
      "data": {
        "fraud_score": 0.0,
        "same_day_total": 1
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 7,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "Category sub-limit 2000 noted (advisory).",
      "severity": "INFO",
      "data": {
        "sub_limit": 2000
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 8,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "All monetary limits satisfied.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 9,
      "stage": "ADJUDICATION",
      "component": "MedicalNecessityAgent",
      "message": "Treatment appears consistent with the diagnosis.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 10,
      "stage": "ADJUDICATION",
      "component": "PreAuthAgent",
      "message": "No pre-auth rules apply to this category.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 11,
      "stage": "FINANCIAL",
      "component": "FinancialAgent",
      "message": "Computed payable amount: 2700. Eligible amount (covered items): 3000 | No network discount (non-network hospital or category has none). | Co-pay 10% applied on 3000 = 300 deducted -> 2700",
      "severity": "INFO",
      "data": {
        "claimed_amount": 3000.0,
        "eligible_amount": 3000.0,
        "network_discount_percent": 0.0,
        "network_discount_amount": 0.0,
        "after_network_discount": 3000.0,
        "copay_percent": 10.0,
        "copay_amount": 300.0,
        "approved_amount": 2700.0,
        "steps": [
          "Eligible amount (covered items): 3000",
          "No network discount (non-network hospital or category has none).",
          "Co-pay 10% applied on 3000 = 300 deducted -> 2700"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 12,
      "stage": "DECISION",
      "component": "DecisionAgent",
      "message": "Final decision: REJECTED | approved 0 | confidence 0.95 | reasons ['WAITING_PERIOD']",
      "severity": "INFO",
      "data": {
        "decision": "REJECTED",
        "confidence": 0.95,
        "component_failures": 0
      },
      "llm_used": false,
      "duration_ms": null
    }
  ]
}
```


## TC006 - Dental Partial Approval - Cosmetic Exclusion  ->  **PASS**

_Bill includes root canal treatment (covered) and teeth whitening (cosmetic, excluded). System must approve only the covered procedure._

**Checks:**

- ✅ decision == PARTIAL
- ✅ approved_amount == 8000
- ✅ root canal approved
- ✅ teeth whitening rejected
- ✅ itemized reasons present

**Decision output:**

```json
{
  "claim_id": "CLM-EMP002-2024-10-15-7b994f",
  "member_id": "EMP002",
  "decision": "PARTIAL",
  "approved_amount": 8000.0,
  "confidence_score": 0.9,
  "rejection_reasons": [],
  "member_message": "Your claim has been partially approved for 8000. Approved items were covered; the following were excluded and not paid: Teeth Whitening (Excluded procedure (not covered under policy): Teeth Whitening).",
  "notes": [
    "Excluded line items: Teeth Whitening - Excluded procedure (not covered under policy): Teeth Whitening",
    "Eligible amount (covered items): 8000",
    "No network discount (non-network hospital or category has none).",
    "No co-pay for this category -> 8000"
  ],
  "required_action": null,
  "halted_stage": null,
  "line_items": [
    {
      "description": "Root Canal Treatment",
      "amount": 8000.0,
      "covered": true,
      "reason": "Covered procedure: Root Canal Treatment"
    },
    {
      "description": "Teeth Whitening",
      "amount": 4000.0,
      "covered": false,
      "reason": "Excluded procedure (not covered under policy): Teeth Whitening"
    }
  ],
  "financial": {
    "claimed_amount": 12000.0,
    "eligible_amount": 8000.0,
    "network_discount_percent": 0.0,
    "network_discount_amount": 0.0,
    "after_network_discount": 8000.0,
    "copay_percent": 0.0,
    "copay_amount": 0.0,
    "approved_amount": 8000.0,
    "steps": [
      "Eligible amount (covered items): 8000",
      "No network discount (non-network hospital or category has none).",
      "No co-pay for this category -> 8000"
    ]
  },
  "findings": [
    {
      "code": "PARTIAL_EXCLUSION",
      "component": "CoverageAgent",
      "severity": "WARNING",
      "passed": false,
      "message": "Some line items are excluded and were removed: Teeth Whitening (Excluded procedure (not covered under policy): Teeth Whitening)",
      "data": {
        "excluded_items": [
          {
            "description": "Teeth Whitening",
            "amount": 4000.0,
            "covered": false,
            "reason": "Excluded procedure (not covered under policy): Teeth Whitening"
          }
        ]
      }
    },
    {
      "code": "ELIGIBILITY_OK",
      "component": "EligibilityAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Member is active and outside all applicable waiting periods.",
      "data": {}
    },
    {
      "code": "FRAUD_OK",
      "component": "FraudAgent",
      "severity": "INFO",
      "passed": true,
      "message": "No fraud signals exceeded thresholds.",
      "data": {
        "fraud_score": 0.0
      }
    },
    {
      "code": "LIMITS_OK",
      "component": "LimitsAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Within per-claim (5000) and annual limits.",
      "data": {}
    },
    {
      "code": "MEDICAL_NECESSITY_OK",
      "component": "MedicalNecessityAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Treatment appears consistent with the diagnosis.",
      "data": {}
    },
    {
      "code": "PRE_AUTH_OK",
      "component": "PreAuthAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Pre-authorization not required.",
      "data": {}
    }
  ],
  "component_failures": [],
  "trace": [
    {
      "seq": 1,
      "stage": "INTAKE",
      "component": "IntakeAgent",
      "message": "Received DENTAL claim for member EMP002 (amount 12000), 1 document(s).",
      "severity": "INFO",
      "data": {
        "claim_id": "CLM-EMP002-2024-10-15-7b994f",
        "category": "DENTAL",
        "claimed_amount": 12000,
        "document_types": [
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 2,
      "stage": "DOCUMENT_VERIFICATION",
      "component": "DocumentVerificationAgent",
      "message": "Document verification passed: required types ['HOSPITAL_BILL'] present, all readable, single patient.",
      "severity": "INFO",
      "data": {
        "required_types": [
          "HOSPITAL_BILL"
        ],
        "present_types": [
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 3,
      "stage": "EXTRACTION",
      "component": "ExtractionAgent",
      "message": "Extracted 1 document(s). Diagnosis='N/A', condition_key=None, 2 line item(s).",
      "severity": "INFO",
      "data": {
        "diagnosis": "",
        "treatment": "Root Canal Treatment Teeth Whitening",
        "condition_key": null,
        "line_items": [
          {
            "description": "Root Canal Treatment",
            "amount": 8000.0
          },
          {
            "description": "Teeth Whitening",
            "amount": 4000.0
          }
        ],
        "llm_enrichment": {}
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 4,
      "stage": "ADJUDICATION",
      "component": "CoverageAgent",
      "message": "Some line items are excluded and were removed: Teeth Whitening (Excluded procedure (not covered under policy): Teeth Whitening)",
      "severity": "WARNING",
      "data": {
        "excluded": [
          {
            "description": "Teeth Whitening",
            "amount": 4000.0,
            "covered": false,
            "reason": "Excluded procedure (not covered under policy): Teeth Whitening"
          }
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 5,
      "stage": "ADJUDICATION",
      "component": "EligibilityAgent",
      "message": "Member Priya Singh eligible; no waiting period applies.",
      "severity": "INFO",
      "data": {
        "condition_key": null
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 6,
      "stage": "FRAUD",
      "component": "FraudAgent",
      "message": "No fraud signals above threshold.",
      "severity": "INFO",
      "data": {
        "fraud_score": 0.0,
        "same_day_total": 1
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 7,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "Category sub-limit 10000 noted (advisory).",
      "severity": "INFO",
      "data": {
        "sub_limit": 10000
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 8,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "All monetary limits satisfied.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 9,
      "stage": "ADJUDICATION",
      "component": "MedicalNecessityAgent",
      "message": "Treatment appears consistent with the diagnosis.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 10,
      "stage": "ADJUDICATION",
      "component": "PreAuthAgent",
      "message": "No pre-auth rules apply to this category.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 11,
      "stage": "FINANCIAL",
      "component": "FinancialAgent",
      "message": "Computed payable amount: 8000. Eligible amount (covered items): 8000 | No network discount (non-network hospital or category has none). | No co-pay for this category -> 8000",
      "severity": "INFO",
      "data": {
        "claimed_amount": 12000.0,
        "eligible_amount": 8000.0,
        "network_discount_percent": 0.0,
        "network_discount_amount": 0.0,
        "after_network_discount": 8000.0,
        "copay_percent": 0.0,
        "copay_amount": 0.0,
        "approved_amount": 8000.0,
        "steps": [
          "Eligible amount (covered items): 8000",
          "No network discount (non-network hospital or category has none).",
          "No co-pay for this category -> 8000"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 12,
      "stage": "DECISION",
      "component": "DecisionAgent",
      "message": "Final decision: PARTIAL | approved 8000 | confidence 0.90 | reasons []",
      "severity": "INFO",
      "data": {
        "decision": "PARTIAL",
        "confidence": 0.9,
        "component_failures": 0
      },
      "llm_used": false,
      "duration_ms": null
    }
  ]
}
```


## TC007 - MRI Without Pre-Authorization  ->  **PASS**

_MRI scan costing 15,000 submitted without pre-authorization. Policy requires pre-auth for MRI above 10,000._

**Checks:**

- ✅ decision == REJECTED
- ✅ rejection_reasons superset of ['PRE_AUTH_MISSING']
- ✅ explains pre-auth was required and missing
- ✅ tells member how to resubmit

**Decision output:**

```json
{
  "claim_id": "CLM-EMP007-2024-11-02-3c79c6",
  "member_id": "EMP007",
  "decision": "REJECTED",
  "approved_amount": 0.0,
  "confidence_score": 0.95,
  "rejection_reasons": [
    "WAITING_PERIOD",
    "PRE_AUTH_MISSING",
    "PER_CLAIM_EXCEEDED"
  ],
  "member_message": "Your claim has been rejected. This claim is for a 'hernia' condition, which has a 365-day waiting period. The member joined on 2024-04-01 and the treatment was on 2024-11-02 (215 days later). Hernia-related claims are only eligible from 2025-04-01. MRI costing 15000 requires pre-authorization because it exceeds the 10000 threshold, and no pre-authorization was found on this claim. To resubmit: obtain pre-authorization from the insurer for the MRI BEFORE the procedure (or attach the approved pre-auth reference if you already have one), then submit the claim again. The claimed amount of 15000 exceeds the per-claim limit of 10000 that applies to this claim. It cannot be approved as submitted.",
  "notes": [],
  "required_action": null,
  "halted_stage": null,
  "line_items": [
    {
      "description": "MRI Lumbar Spine",
      "amount": 15000.0,
      "covered": true,
      "reason": "Covered (no specific exclusion applies)"
    }
  ],
  "financial": {
    "claimed_amount": 15000.0,
    "eligible_amount": 15000.0,
    "network_discount_percent": 0.0,
    "network_discount_amount": 0.0,
    "after_network_discount": 15000.0,
    "copay_percent": 0.0,
    "copay_amount": 0.0,
    "approved_amount": 15000.0,
    "steps": [
      "Eligible amount (covered items): 15000",
      "Eligible 15000 exceeds per-claim cap 10000 -> rejected.",
      "No network discount (non-network hospital or category has none).",
      "No co-pay for this category -> 15000"
    ]
  },
  "findings": [
    {
      "code": "COVERAGE_OK",
      "component": "CoverageAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Treatment is covered and no exclusion applies.",
      "data": {}
    },
    {
      "code": "WAITING_PERIOD",
      "component": "EligibilityAgent",
      "severity": "BLOCKER",
      "passed": false,
      "message": "This claim is for a 'hernia' condition, which has a 365-day waiting period. The member joined on 2024-04-01 and the treatment was on 2024-11-02 (215 days later). Hernia-related claims are only eligible from 2025-04-01.",
      "data": {
        "condition": "hernia",
        "waiting_days": 365,
        "eligible_from": "2025-04-01",
        "elapsed_days": 215
      }
    },
    {
      "code": "FRAUD_OK",
      "component": "FraudAgent",
      "severity": "INFO",
      "passed": true,
      "message": "No fraud signals exceeded thresholds.",
      "data": {
        "fraud_score": 0.0
      }
    },
    {
      "code": "LIMITS_OK",
      "component": "LimitsAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Within per-claim (5000) and annual limits.",
      "data": {}
    },
    {
      "code": "MEDICAL_NECESSITY_OK",
      "component": "MedicalNecessityAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Treatment appears consistent with the diagnosis.",
      "data": {}
    },
    {
      "code": "PRE_AUTH_MISSING",
      "component": "PreAuthAgent",
      "severity": "BLOCKER",
      "passed": false,
      "message": "MRI costing 15000 requires pre-authorization because it exceeds the 10000 threshold, and no pre-authorization was found on this claim. To resubmit: obtain pre-authorization from the insurer for the MRI BEFORE the procedure (or attach the approved pre-auth reference if you already have one), then submit the claim again.",
      "data": {
        "test": "MRI",
        "amount": 15000.0,
        "threshold": 10000
      }
    },
    {
      "code": "PER_CLAIM_EXCEEDED",
      "component": "FinancialAgent",
      "severity": "BLOCKER",
      "passed": false,
      "message": "The claimed amount of 15000 exceeds the per-claim limit of 10000 that applies to this claim. It cannot be approved as submitted.",
      "data": {
        "claimed": 15000.0,
        "eligible": 15000.0,
        "per_claim_limit": 10000.0
      }
    }
  ],
  "component_failures": [],
  "trace": [
    {
      "seq": 1,
      "stage": "INTAKE",
      "component": "IntakeAgent",
      "message": "Received DIAGNOSTIC claim for member EMP007 (amount 15000), 3 document(s).",
      "severity": "INFO",
      "data": {
        "claim_id": "CLM-EMP007-2024-11-02-3c79c6",
        "category": "DIAGNOSTIC",
        "claimed_amount": 15000,
        "document_types": [
          "PRESCRIPTION",
          "LAB_REPORT",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 2,
      "stage": "DOCUMENT_VERIFICATION",
      "component": "DocumentVerificationAgent",
      "message": "Document verification passed: required types ['PRESCRIPTION', 'LAB_REPORT', 'HOSPITAL_BILL'] present, all readable, single patient.",
      "severity": "INFO",
      "data": {
        "required_types": [
          "PRESCRIPTION",
          "LAB_REPORT",
          "HOSPITAL_BILL"
        ],
        "present_types": [
          "PRESCRIPTION",
          "LAB_REPORT",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 3,
      "stage": "EXTRACTION",
      "component": "ExtractionAgent",
      "message": "Extracted 3 document(s). Diagnosis='Suspected Lumbar Disc Herniation', condition_key=hernia, 1 line item(s).",
      "severity": "INFO",
      "data": {
        "diagnosis": "Suspected Lumbar Disc Herniation",
        "treatment": "MRI Lumbar Spine MRI Lumbar Spine",
        "condition_key": "hernia",
        "line_items": [
          {
            "description": "MRI Lumbar Spine",
            "amount": 15000.0
          }
        ],
        "llm_enrichment": {}
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 4,
      "stage": "ADJUDICATION",
      "component": "CoverageAgent",
      "message": "All items covered under DIAGNOSTIC.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 5,
      "stage": "ADJUDICATION",
      "component": "EligibilityAgent",
      "message": "This claim is for a 'hernia' condition, which has a 365-day waiting period. The member joined on 2024-04-01 and the treatment was on 2024-11-02 (215 days later). Hernia-related claims are only eligible from 2025-04-01.",
      "severity": "BLOCKER",
      "data": {
        "eligible_from": "2025-04-01"
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 6,
      "stage": "FRAUD",
      "component": "FraudAgent",
      "message": "No fraud signals above threshold.",
      "severity": "INFO",
      "data": {
        "fraud_score": 0.0,
        "same_day_total": 1
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 7,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "Category sub-limit 10000 noted (advisory).",
      "severity": "INFO",
      "data": {
        "sub_limit": 10000
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 8,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "All monetary limits satisfied.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 9,
      "stage": "ADJUDICATION",
      "component": "MedicalNecessityAgent",
      "message": "Treatment appears consistent with the diagnosis.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 10,
      "stage": "ADJUDICATION",
      "component": "PreAuthAgent",
      "message": "MRI costing 15000 requires pre-authorization because it exceeds the 10000 threshold, and no pre-authorization was found on this claim. To resubmit: obtain pre-authorization from the insurer for the MRI BEFORE the procedure (or attach the approved pre-auth reference if you already have one), then submit the claim again.",
      "severity": "BLOCKER",
      "data": {
        "test": "MRI",
        "amount": 15000.0,
        "threshold": 10000
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 11,
      "stage": "FINANCIAL",
      "component": "FinancialAgent",
      "message": "Computed payable amount: 15000. Eligible amount (covered items): 15000 | Eligible 15000 exceeds per-claim cap 10000 -> rejected. | No network discount (non-network hospital or category has none). | No co-pay for this category -> 15000",
      "severity": "INFO",
      "data": {
        "claimed_amount": 15000.0,
        "eligible_amount": 15000.0,
        "network_discount_percent": 0.0,
        "network_discount_amount": 0.0,
        "after_network_discount": 15000.0,
        "copay_percent": 0.0,
        "copay_amount": 0.0,
        "approved_amount": 15000.0,
        "steps": [
          "Eligible amount (covered items): 15000",
          "Eligible 15000 exceeds per-claim cap 10000 -> rejected.",
          "No network discount (non-network hospital or category has none).",
          "No co-pay for this category -> 15000"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 12,
      "stage": "DECISION",
      "component": "DecisionAgent",
      "message": "Final decision: REJECTED | approved 0 | confidence 0.95 | reasons ['WAITING_PERIOD', 'PRE_AUTH_MISSING', 'PER_CLAIM_EXCEEDED']",
      "severity": "INFO",
      "data": {
        "decision": "REJECTED",
        "confidence": 0.95,
        "component_failures": 0
      },
      "llm_used": false,
      "duration_ms": null
    }
  ]
}
```


## TC008 - Per-Claim Limit Exceeded  ->  **PASS**

_Claimed amount of 7,500 exceeds the per-claim limit of 5,000._

**Checks:**

- ✅ decision == REJECTED
- ✅ rejection_reasons superset of ['PER_CLAIM_EXCEEDED']
- ✅ states the per-claim limit (5000)
- ✅ states the claimed amount (7500)

**Decision output:**

```json
{
  "claim_id": "CLM-EMP003-2024-10-20-3c1ad7",
  "member_id": "EMP003",
  "decision": "REJECTED",
  "approved_amount": 0.0,
  "confidence_score": 0.95,
  "rejection_reasons": [
    "PER_CLAIM_EXCEEDED"
  ],
  "member_message": "Your claim has been rejected. The claimed amount of 7500 exceeds the per-claim limit of 5000 that applies to this claim. It cannot be approved as submitted.",
  "notes": [],
  "required_action": null,
  "halted_stage": null,
  "line_items": [
    {
      "description": "Consultation Fee",
      "amount": 2000.0,
      "covered": true,
      "reason": "Covered (no specific exclusion applies)"
    },
    {
      "description": "Medicines",
      "amount": 5500.0,
      "covered": true,
      "reason": "Covered (no specific exclusion applies)"
    }
  ],
  "financial": {
    "claimed_amount": 7500.0,
    "eligible_amount": 7500.0,
    "network_discount_percent": 0.0,
    "network_discount_amount": 0.0,
    "after_network_discount": 7500.0,
    "copay_percent": 10.0,
    "copay_amount": 750.0,
    "approved_amount": 6750.0,
    "steps": [
      "Eligible amount (covered items): 7500",
      "Eligible 7500 exceeds per-claim cap 5000 -> rejected.",
      "No network discount (non-network hospital or category has none).",
      "Co-pay 10% applied on 7500 = 750 deducted -> 6750"
    ]
  },
  "findings": [
    {
      "code": "COVERAGE_OK",
      "component": "CoverageAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Treatment is covered and no exclusion applies.",
      "data": {}
    },
    {
      "code": "ELIGIBILITY_OK",
      "component": "EligibilityAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Member is active and outside all applicable waiting periods.",
      "data": {}
    },
    {
      "code": "FRAUD_OK",
      "component": "FraudAgent",
      "severity": "INFO",
      "passed": true,
      "message": "No fraud signals exceeded thresholds.",
      "data": {
        "fraud_score": 0.0
      }
    },
    {
      "code": "LIMITS_OK",
      "component": "LimitsAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Within per-claim (5000) and annual limits.",
      "data": {}
    },
    {
      "code": "MEDICAL_NECESSITY_OK",
      "component": "MedicalNecessityAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Treatment appears consistent with the diagnosis.",
      "data": {}
    },
    {
      "code": "PRE_AUTH_OK",
      "component": "PreAuthAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Pre-authorization not required.",
      "data": {}
    },
    {
      "code": "PER_CLAIM_EXCEEDED",
      "component": "FinancialAgent",
      "severity": "BLOCKER",
      "passed": false,
      "message": "The claimed amount of 7500 exceeds the per-claim limit of 5000 that applies to this claim. It cannot be approved as submitted.",
      "data": {
        "claimed": 7500.0,
        "eligible": 7500.0,
        "per_claim_limit": 5000.0
      }
    }
  ],
  "component_failures": [],
  "trace": [
    {
      "seq": 1,
      "stage": "INTAKE",
      "component": "IntakeAgent",
      "message": "Received CONSULTATION claim for member EMP003 (amount 7500), 2 document(s).",
      "severity": "INFO",
      "data": {
        "claim_id": "CLM-EMP003-2024-10-20-3c1ad7",
        "category": "CONSULTATION",
        "claimed_amount": 7500,
        "document_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 2,
      "stage": "DOCUMENT_VERIFICATION",
      "component": "DocumentVerificationAgent",
      "message": "Document verification passed: required types ['PRESCRIPTION', 'HOSPITAL_BILL'] present, all readable, single patient.",
      "severity": "INFO",
      "data": {
        "required_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ],
        "present_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 3,
      "stage": "EXTRACTION",
      "component": "ExtractionAgent",
      "message": "Extracted 2 document(s). Diagnosis='Gastroenteritis', condition_key=None, 2 line item(s).",
      "severity": "INFO",
      "data": {
        "diagnosis": "Gastroenteritis",
        "treatment": "Consultation Fee Medicines",
        "condition_key": null,
        "line_items": [
          {
            "description": "Consultation Fee",
            "amount": 2000.0
          },
          {
            "description": "Medicines",
            "amount": 5500.0
          }
        ],
        "llm_enrichment": {}
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 4,
      "stage": "ADJUDICATION",
      "component": "CoverageAgent",
      "message": "All items covered under CONSULTATION.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 5,
      "stage": "ADJUDICATION",
      "component": "EligibilityAgent",
      "message": "Member Amit Verma eligible; no waiting period applies.",
      "severity": "INFO",
      "data": {
        "condition_key": null
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 6,
      "stage": "FRAUD",
      "component": "FraudAgent",
      "message": "No fraud signals above threshold.",
      "severity": "INFO",
      "data": {
        "fraud_score": 0.0,
        "same_day_total": 1
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 7,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "Category sub-limit 2000 noted (advisory).",
      "severity": "INFO",
      "data": {
        "sub_limit": 2000
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 8,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "All monetary limits satisfied.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 9,
      "stage": "ADJUDICATION",
      "component": "MedicalNecessityAgent",
      "message": "Treatment appears consistent with the diagnosis.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 10,
      "stage": "ADJUDICATION",
      "component": "PreAuthAgent",
      "message": "No pre-auth rules apply to this category.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 11,
      "stage": "FINANCIAL",
      "component": "FinancialAgent",
      "message": "Computed payable amount: 6750. Eligible amount (covered items): 7500 | Eligible 7500 exceeds per-claim cap 5000 -> rejected. | No network discount (non-network hospital or category has none). | Co-pay 10% applied on 7500 = 750 deducted -> 6750",
      "severity": "INFO",
      "data": {
        "claimed_amount": 7500.0,
        "eligible_amount": 7500.0,
        "network_discount_percent": 0.0,
        "network_discount_amount": 0.0,
        "after_network_discount": 7500.0,
        "copay_percent": 10.0,
        "copay_amount": 750.0,
        "approved_amount": 6750.0,
        "steps": [
          "Eligible amount (covered items): 7500",
          "Eligible 7500 exceeds per-claim cap 5000 -> rejected.",
          "No network discount (non-network hospital or category has none).",
          "Co-pay 10% applied on 7500 = 750 deducted -> 6750"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 12,
      "stage": "DECISION",
      "component": "DecisionAgent",
      "message": "Final decision: REJECTED | approved 0 | confidence 0.95 | reasons ['PER_CLAIM_EXCEEDED']",
      "severity": "INFO",
      "data": {
        "decision": "REJECTED",
        "confidence": 0.95,
        "component_failures": 0
      },
      "llm_used": false,
      "duration_ms": null
    }
  ]
}
```


## TC009 - Fraud Signal - Multiple Same-Day Claims  ->  **PASS**

_Member EMP008 has already submitted 3 claims today before this one arrives. This is the 4th claim from the same member on the same day._

**Checks:**

- ✅ decision == MANUAL_REVIEW
- ✅ routed to manual review (not rejected)
- ✅ includes the same-day signal

**Decision output:**

```json
{
  "claim_id": "CLM-EMP008-2024-10-30-9bb990",
  "member_id": "EMP008",
  "decision": "MANUAL_REVIEW",
  "approved_amount": 0.0,
  "confidence_score": 0.7,
  "rejection_reasons": [],
  "member_message": "Your claim has been sent for manual review by our team because of unusual activity: 4 claims on the same day (2024-10-30) exceeds the same-day limit of 2. Providers: ['City Clinic A', 'City Clinic B', 'Wellness Center']. A reviewer will follow up shortly.",
  "notes": [
    "Routed to manual review (not auto-rejected)."
  ],
  "required_action": null,
  "halted_stage": null,
  "line_items": [],
  "financial": {
    "claimed_amount": 4800.0,
    "eligible_amount": 4800.0,
    "network_discount_percent": 0.0,
    "network_discount_amount": 0.0,
    "after_network_discount": 4800.0,
    "copay_percent": 10.0,
    "copay_amount": 480.0,
    "approved_amount": 4320.0,
    "steps": [
      "Eligible amount (covered items): 4800",
      "No network discount (non-network hospital or category has none).",
      "Co-pay 10% applied on 4800 = 480 deducted -> 4320"
    ]
  },
  "findings": [
    {
      "code": "COVERAGE_OK",
      "component": "CoverageAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Treatment is covered and no exclusion applies.",
      "data": {}
    },
    {
      "code": "ELIGIBILITY_OK",
      "component": "EligibilityAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Member is active and outside all applicable waiting periods.",
      "data": {}
    },
    {
      "code": "FRAUD_SUSPECTED",
      "component": "FraudAgent",
      "severity": "WARNING",
      "passed": false,
      "message": "Fraud signals detected: 4 claims on the same day (2024-10-30) exceeds the same-day limit of 2. Providers: ['City Clinic A', 'City Clinic B', 'Wellness Center'].",
      "data": {
        "fraud_score": 0.85,
        "signals": [
          "4 claims on the same day (2024-10-30) exceeds the same-day limit of 2. Providers: ['City Clinic A', 'City Clinic B', 'Wellness Center']."
        ],
        "same_day_total": 4,
        "monthly_total": 4
      }
    },
    {
      "code": "LIMITS_OK",
      "component": "LimitsAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Within per-claim (5000) and annual limits.",
      "data": {}
    },
    {
      "code": "MEDICAL_NECESSITY_OK",
      "component": "MedicalNecessityAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Treatment appears consistent with the diagnosis.",
      "data": {}
    },
    {
      "code": "PRE_AUTH_OK",
      "component": "PreAuthAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Pre-authorization not required.",
      "data": {}
    }
  ],
  "component_failures": [],
  "trace": [
    {
      "seq": 1,
      "stage": "INTAKE",
      "component": "IntakeAgent",
      "message": "Received CONSULTATION claim for member EMP008 (amount 4800), 2 document(s).",
      "severity": "INFO",
      "data": {
        "claim_id": "CLM-EMP008-2024-10-30-9bb990",
        "category": "CONSULTATION",
        "claimed_amount": 4800,
        "document_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 2,
      "stage": "DOCUMENT_VERIFICATION",
      "component": "DocumentVerificationAgent",
      "message": "Document verification passed: required types ['PRESCRIPTION', 'HOSPITAL_BILL'] present, all readable, single patient.",
      "severity": "INFO",
      "data": {
        "required_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ],
        "present_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 3,
      "stage": "EXTRACTION",
      "component": "ExtractionAgent",
      "message": "Extracted 2 document(s). Diagnosis='Migraine', condition_key=None, 0 line item(s).",
      "severity": "INFO",
      "data": {
        "diagnosis": "Migraine",
        "treatment": "",
        "condition_key": null,
        "line_items": [],
        "llm_enrichment": {}
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 4,
      "stage": "ADJUDICATION",
      "component": "CoverageAgent",
      "message": "All items covered under CONSULTATION.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 5,
      "stage": "ADJUDICATION",
      "component": "EligibilityAgent",
      "message": "Member Ravi Menon eligible; no waiting period applies.",
      "severity": "INFO",
      "data": {
        "condition_key": null
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 6,
      "stage": "FRAUD",
      "component": "FraudAgent",
      "message": "Fraud signals detected: 4 claims on the same day (2024-10-30) exceeds the same-day limit of 2. Providers: ['City Clinic A', 'City Clinic B', 'Wellness Center'].",
      "severity": "WARNING",
      "data": {
        "fraud_score": 0.85,
        "signals": [
          "4 claims on the same day (2024-10-30) exceeds the same-day limit of 2. Providers: ['City Clinic A', 'City Clinic B', 'Wellness Center']."
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 7,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "Category sub-limit 2000 noted (advisory).",
      "severity": "INFO",
      "data": {
        "sub_limit": 2000
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 8,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "All monetary limits satisfied.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 9,
      "stage": "ADJUDICATION",
      "component": "MedicalNecessityAgent",
      "message": "Treatment appears consistent with the diagnosis.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 10,
      "stage": "ADJUDICATION",
      "component": "PreAuthAgent",
      "message": "No pre-auth rules apply to this category.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 11,
      "stage": "FINANCIAL",
      "component": "FinancialAgent",
      "message": "Computed payable amount: 4320. Eligible amount (covered items): 4800 | No network discount (non-network hospital or category has none). | Co-pay 10% applied on 4800 = 480 deducted -> 4320",
      "severity": "INFO",
      "data": {
        "claimed_amount": 4800.0,
        "eligible_amount": 4800.0,
        "network_discount_percent": 0.0,
        "network_discount_amount": 0.0,
        "after_network_discount": 4800.0,
        "copay_percent": 10.0,
        "copay_amount": 480.0,
        "approved_amount": 4320.0,
        "steps": [
          "Eligible amount (covered items): 4800",
          "No network discount (non-network hospital or category has none).",
          "Co-pay 10% applied on 4800 = 480 deducted -> 4320"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 12,
      "stage": "DECISION",
      "component": "DecisionAgent",
      "message": "Final decision: MANUAL_REVIEW | approved 0 | confidence 0.70 | reasons []",
      "severity": "INFO",
      "data": {
        "decision": "MANUAL_REVIEW",
        "confidence": 0.7,
        "component_failures": 0
      },
      "llm_used": false,
      "duration_ms": null
    }
  ]
}
```


## TC010 - Network Hospital - Discount Applied  ->  **PASS**

_Valid claim at Apollo Hospitals, a network hospital. Network discount must be applied before co-pay._

**Checks:**

- ✅ decision == APPROVED
- ✅ approved_amount == 3240
- ✅ network discount applied first (shows 3600)
- ✅ co-pay shown (360)
- ✅ breakdown visible in output

**Decision output:**

```json
{
  "claim_id": "CLM-EMP010-2024-11-03-b8d316",
  "member_id": "EMP010",
  "decision": "APPROVED",
  "approved_amount": 3240.0,
  "confidence_score": 0.93,
  "rejection_reasons": [],
  "member_message": "Good news - your claim has been approved for 3240.",
  "notes": [
    "Eligible amount (covered items): 4500",
    "Network hospital 'Apollo Hospitals': 20% network discount on 4500 = 900 -> 3600",
    "Co-pay 10% applied on 3600 = 360 deducted -> 3240"
  ],
  "required_action": null,
  "halted_stage": null,
  "line_items": [
    {
      "description": "Consultation Fee",
      "amount": 1500.0,
      "covered": true,
      "reason": "Covered (no specific exclusion applies)"
    },
    {
      "description": "Medicines",
      "amount": 3000.0,
      "covered": true,
      "reason": "Covered (no specific exclusion applies)"
    }
  ],
  "financial": {
    "claimed_amount": 4500.0,
    "eligible_amount": 4500.0,
    "network_discount_percent": 20.0,
    "network_discount_amount": 900.0,
    "after_network_discount": 3600.0,
    "copay_percent": 10.0,
    "copay_amount": 360.0,
    "approved_amount": 3240.0,
    "steps": [
      "Eligible amount (covered items): 4500",
      "Network hospital 'Apollo Hospitals': 20% network discount on 4500 = 900 -> 3600",
      "Co-pay 10% applied on 3600 = 360 deducted -> 3240"
    ]
  },
  "findings": [
    {
      "code": "COVERAGE_OK",
      "component": "CoverageAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Treatment is covered and no exclusion applies.",
      "data": {}
    },
    {
      "code": "ELIGIBILITY_OK",
      "component": "EligibilityAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Member is active and outside all applicable waiting periods.",
      "data": {}
    },
    {
      "code": "FRAUD_OK",
      "component": "FraudAgent",
      "severity": "INFO",
      "passed": true,
      "message": "No fraud signals exceeded thresholds.",
      "data": {
        "fraud_score": 0.0
      }
    },
    {
      "code": "LIMITS_OK",
      "component": "LimitsAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Within per-claim (5000) and annual limits.",
      "data": {}
    },
    {
      "code": "MEDICAL_NECESSITY_OK",
      "component": "MedicalNecessityAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Treatment appears consistent with the diagnosis.",
      "data": {}
    },
    {
      "code": "PRE_AUTH_OK",
      "component": "PreAuthAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Pre-authorization not required.",
      "data": {}
    }
  ],
  "component_failures": [],
  "trace": [
    {
      "seq": 1,
      "stage": "INTAKE",
      "component": "IntakeAgent",
      "message": "Received CONSULTATION claim for member EMP010 (amount 4500), 2 document(s).",
      "severity": "INFO",
      "data": {
        "claim_id": "CLM-EMP010-2024-11-03-b8d316",
        "category": "CONSULTATION",
        "claimed_amount": 4500,
        "document_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 2,
      "stage": "DOCUMENT_VERIFICATION",
      "component": "DocumentVerificationAgent",
      "message": "Document verification passed: required types ['PRESCRIPTION', 'HOSPITAL_BILL'] present, all readable, single patient.",
      "severity": "INFO",
      "data": {
        "required_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ],
        "present_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 3,
      "stage": "EXTRACTION",
      "component": "ExtractionAgent",
      "message": "Extracted 2 document(s). Diagnosis='Acute Bronchitis', condition_key=None, 2 line item(s).",
      "severity": "INFO",
      "data": {
        "diagnosis": "Acute Bronchitis",
        "treatment": "Consultation Fee Medicines",
        "condition_key": null,
        "line_items": [
          {
            "description": "Consultation Fee",
            "amount": 1500.0
          },
          {
            "description": "Medicines",
            "amount": 3000.0
          }
        ],
        "llm_enrichment": {}
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 4,
      "stage": "ADJUDICATION",
      "component": "CoverageAgent",
      "message": "All items covered under CONSULTATION.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 5,
      "stage": "ADJUDICATION",
      "component": "EligibilityAgent",
      "message": "Member Deepak Shah eligible; no waiting period applies.",
      "severity": "INFO",
      "data": {
        "condition_key": null
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 6,
      "stage": "FRAUD",
      "component": "FraudAgent",
      "message": "No fraud signals above threshold.",
      "severity": "INFO",
      "data": {
        "fraud_score": 0.0,
        "same_day_total": 1
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 7,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "Category sub-limit 2000 noted (advisory).",
      "severity": "INFO",
      "data": {
        "sub_limit": 2000
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 8,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "All monetary limits satisfied.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 9,
      "stage": "ADJUDICATION",
      "component": "MedicalNecessityAgent",
      "message": "Treatment appears consistent with the diagnosis.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 10,
      "stage": "ADJUDICATION",
      "component": "PreAuthAgent",
      "message": "No pre-auth rules apply to this category.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 11,
      "stage": "FINANCIAL",
      "component": "FinancialAgent",
      "message": "Computed payable amount: 3240. Eligible amount (covered items): 4500 | Network hospital 'Apollo Hospitals': 20% network discount on 4500 = 900 -> 3600 | Co-pay 10% applied on 3600 = 360 deducted -> 3240",
      "severity": "INFO",
      "data": {
        "claimed_amount": 4500.0,
        "eligible_amount": 4500.0,
        "network_discount_percent": 20.0,
        "network_discount_amount": 900.0,
        "after_network_discount": 3600.0,
        "copay_percent": 10.0,
        "copay_amount": 360.0,
        "approved_amount": 3240.0,
        "steps": [
          "Eligible amount (covered items): 4500",
          "Network hospital 'Apollo Hospitals': 20% network discount on 4500 = 900 -> 3600",
          "Co-pay 10% applied on 3600 = 360 deducted -> 3240"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 12,
      "stage": "DECISION",
      "component": "DecisionAgent",
      "message": "Final decision: APPROVED | approved 3240 | confidence 0.93 | reasons []",
      "severity": "INFO",
      "data": {
        "decision": "APPROVED",
        "confidence": 0.93,
        "component_failures": 0
      },
      "llm_used": false,
      "duration_ms": null
    }
  ]
}
```


## TC011 - Component Failure - Graceful Degradation  ->  **PASS**

_One component of your system fails mid-processing (simulate with the flag below). The overall pipeline must continue, produce a decision, and make the failure visible in the output with an appropriately reduced confidence score._

**Checks:**

- ✅ decision == APPROVED
- ✅ did not crash, produced a decision
- ✅ indicates a component failed/was skipped
- ✅ confidence lower than a normal approval (<0.93)
- ✅ recommends manual review due to incomplete processing

**Decision output:**

```json
{
  "claim_id": "CLM-EMP006-2024-10-28-686f6e",
  "member_id": "EMP006",
  "decision": "APPROVED",
  "approved_amount": 4000.0,
  "confidence_score": 0.68,
  "rejection_reasons": [],
  "member_message": "Good news - your claim has been approved for 4000. (Note: part of our automated check (MedicalNecessityAgent) could not run, so this decision is provisional and will be manually reviewed.)",
  "notes": [
    "Eligible amount (covered items): 4000",
    "No network discount (non-network hospital or category has none).",
    "No co-pay for this category -> 4000",
    "NOTE: 1 component(s) failed and were skipped (MedicalNecessityAgent). Processing was incomplete, so confidence is reduced and MANUAL REVIEW is recommended before final settlement."
  ],
  "required_action": null,
  "halted_stage": null,
  "line_items": [
    {
      "description": "Panchakarma Therapy (5 sessions)",
      "amount": 3000.0,
      "covered": true,
      "reason": "Covered (no specific exclusion applies)"
    },
    {
      "description": "Consultation",
      "amount": 1000.0,
      "covered": true,
      "reason": "Covered (no specific exclusion applies)"
    }
  ],
  "financial": {
    "claimed_amount": 4000.0,
    "eligible_amount": 4000.0,
    "network_discount_percent": 0.0,
    "network_discount_amount": 0.0,
    "after_network_discount": 4000.0,
    "copay_percent": 0.0,
    "copay_amount": 0.0,
    "approved_amount": 4000.0,
    "steps": [
      "Eligible amount (covered items): 4000",
      "No network discount (non-network hospital or category has none).",
      "No co-pay for this category -> 4000"
    ]
  },
  "findings": [
    {
      "code": "COVERAGE_OK",
      "component": "CoverageAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Treatment is covered and no exclusion applies.",
      "data": {}
    },
    {
      "code": "ELIGIBILITY_OK",
      "component": "EligibilityAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Member is active and outside all applicable waiting periods.",
      "data": {}
    },
    {
      "code": "FRAUD_OK",
      "component": "FraudAgent",
      "severity": "INFO",
      "passed": true,
      "message": "No fraud signals exceeded thresholds.",
      "data": {
        "fraud_score": 0.0
      }
    },
    {
      "code": "LIMITS_OK",
      "component": "LimitsAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Within per-claim (5000) and annual limits.",
      "data": {}
    },
    {
      "code": "PRE_AUTH_OK",
      "component": "PreAuthAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Pre-authorization not required.",
      "data": {}
    }
  ],
  "component_failures": [
    {
      "component": "MedicalNecessityAgent",
      "stage": "ADJUDICATION",
      "error": "Simulated failure in MedicalNecessityAgent (injected by test flag)."
    }
  ],
  "trace": [
    {
      "seq": 1,
      "stage": "INTAKE",
      "component": "IntakeAgent",
      "message": "Received ALTERNATIVE_MEDICINE claim for member EMP006 (amount 4000), 2 document(s).",
      "severity": "INFO",
      "data": {
        "claim_id": "CLM-EMP006-2024-10-28-686f6e",
        "category": "ALTERNATIVE_MEDICINE",
        "claimed_amount": 4000,
        "document_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 2,
      "stage": "DOCUMENT_VERIFICATION",
      "component": "DocumentVerificationAgent",
      "message": "Document verification passed: required types ['PRESCRIPTION', 'HOSPITAL_BILL'] present, all readable, single patient.",
      "severity": "INFO",
      "data": {
        "required_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ],
        "present_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 3,
      "stage": "EXTRACTION",
      "component": "ExtractionAgent",
      "message": "Extracted 2 document(s). Diagnosis='Chronic Joint Pain', condition_key=None, 2 line item(s).",
      "severity": "INFO",
      "data": {
        "diagnosis": "Chronic Joint Pain",
        "treatment": "Panchakarma Therapy Panchakarma Therapy (5 sessions) Consultation",
        "condition_key": null,
        "line_items": [
          {
            "description": "Panchakarma Therapy (5 sessions)",
            "amount": 3000.0
          },
          {
            "description": "Consultation",
            "amount": 1000.0
          }
        ],
        "llm_enrichment": {}
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 4,
      "stage": "ADJUDICATION",
      "component": "CoverageAgent",
      "message": "All items covered under ALTERNATIVE_MEDICINE.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 5,
      "stage": "ADJUDICATION",
      "component": "EligibilityAgent",
      "message": "Member Kavita Nair eligible; no waiting period applies.",
      "severity": "INFO",
      "data": {
        "condition_key": null
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 6,
      "stage": "FRAUD",
      "component": "FraudAgent",
      "message": "No fraud signals above threshold.",
      "severity": "INFO",
      "data": {
        "fraud_score": 0.0,
        "same_day_total": 1
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 7,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "Category sub-limit 8000 noted (advisory).",
      "severity": "INFO",
      "data": {
        "sub_limit": 8000
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 8,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "All monetary limits satisfied.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 9,
      "stage": "ADJUDICATION",
      "component": "MedicalNecessityAgent",
      "message": "Component failed and was skipped: Simulated failure in MedicalNecessityAgent (injected by test flag).",
      "severity": "WARNING",
      "data": {
        "error": "Simulated failure in MedicalNecessityAgent (injected by test flag).",
        "error_type": "RuntimeError"
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 10,
      "stage": "ADJUDICATION",
      "component": "PreAuthAgent",
      "message": "No pre-auth rules apply to this category.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 11,
      "stage": "FINANCIAL",
      "component": "FinancialAgent",
      "message": "Computed payable amount: 4000. Eligible amount (covered items): 4000 | No network discount (non-network hospital or category has none). | No co-pay for this category -> 4000",
      "severity": "INFO",
      "data": {
        "claimed_amount": 4000.0,
        "eligible_amount": 4000.0,
        "network_discount_percent": 0.0,
        "network_discount_amount": 0.0,
        "after_network_discount": 4000.0,
        "copay_percent": 0.0,
        "copay_amount": 0.0,
        "approved_amount": 4000.0,
        "steps": [
          "Eligible amount (covered items): 4000",
          "No network discount (non-network hospital or category has none).",
          "No co-pay for this category -> 4000"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 12,
      "stage": "DECISION",
      "component": "DecisionAgent",
      "message": "Final decision: APPROVED | approved 4000 | confidence 0.68 | reasons []",
      "severity": "INFO",
      "data": {
        "decision": "APPROVED",
        "confidence": 0.68,
        "component_failures": 1
      },
      "llm_used": false,
      "duration_ms": null
    }
  ]
}
```


## TC012 - Excluded Treatment  ->  **PASS**

_Member claims for bariatric consultation and a diet program. Obesity treatment is explicitly excluded under the policy._

**Checks:**

- ✅ decision == REJECTED
- ✅ rejection_reasons superset of ['EXCLUDED_CONDITION']
- ✅ confidence above 0.9
- ✅ confidence above 0.90

**Decision output:**

```json
{
  "claim_id": "CLM-EMP009-2024-10-18-317c55",
  "member_id": "EMP009",
  "decision": "REJECTED",
  "approved_amount": 0.0,
  "confidence_score": 0.95,
  "rejection_reasons": [
    "EXCLUDED_CONDITION",
    "WAITING_PERIOD"
  ],
  "member_message": "Your claim has been rejected. The claimed treatment falls under a policy exclusion: 'Obesity and weight loss programs'. Diagnosis/treatment text matched this exclusion, so the claim is not payable. This claim is for a 'obesity_treatment' condition, which has a 365-day waiting period. The member joined on 2024-04-01 and the treatment was on 2024-10-18 (200 days later). Obesity_treatment-related claims are only eligible from 2025-04-01.",
  "notes": [],
  "required_action": null,
  "halted_stage": null,
  "line_items": [
    {
      "description": "Bariatric Consultation",
      "amount": 3000.0,
      "covered": false,
      "reason": "Excluded: Obesity and weight loss programs"
    },
    {
      "description": "Personalised Diet and Nutrition Program",
      "amount": 5000.0,
      "covered": false,
      "reason": "Excluded: Obesity and weight loss programs"
    }
  ],
  "financial": {
    "claimed_amount": 8000.0,
    "eligible_amount": 0.0,
    "network_discount_percent": 0.0,
    "network_discount_amount": 0.0,
    "after_network_discount": 0.0,
    "copay_percent": 10.0,
    "copay_amount": 0.0,
    "approved_amount": 0.0,
    "steps": [
      "Eligible amount (covered items): 0",
      "No network discount (non-network hospital or category has none).",
      "Co-pay 10% applied on 0 = 0 deducted -> 0"
    ]
  },
  "findings": [
    {
      "code": "EXCLUDED_CONDITION",
      "component": "CoverageAgent",
      "severity": "BLOCKER",
      "passed": false,
      "message": "The claimed treatment falls under a policy exclusion: 'Obesity and weight loss programs'. Diagnosis/treatment text matched this exclusion, so the claim is not payable.",
      "data": {
        "exclusion": "Obesity and weight loss programs"
      }
    },
    {
      "code": "WAITING_PERIOD",
      "component": "EligibilityAgent",
      "severity": "BLOCKER",
      "passed": false,
      "message": "This claim is for a 'obesity_treatment' condition, which has a 365-day waiting period. The member joined on 2024-04-01 and the treatment was on 2024-10-18 (200 days later). Obesity_treatment-related claims are only eligible from 2025-04-01.",
      "data": {
        "condition": "obesity_treatment",
        "waiting_days": 365,
        "eligible_from": "2025-04-01",
        "elapsed_days": 200
      }
    },
    {
      "code": "FRAUD_OK",
      "component": "FraudAgent",
      "severity": "INFO",
      "passed": true,
      "message": "No fraud signals exceeded thresholds.",
      "data": {
        "fraud_score": 0.0
      }
    },
    {
      "code": "LIMITS_OK",
      "component": "LimitsAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Within per-claim (5000) and annual limits.",
      "data": {}
    },
    {
      "code": "MEDICAL_NECESSITY_OK",
      "component": "MedicalNecessityAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Treatment appears consistent with the diagnosis.",
      "data": {}
    },
    {
      "code": "PRE_AUTH_OK",
      "component": "PreAuthAgent",
      "severity": "INFO",
      "passed": true,
      "message": "Pre-authorization not required.",
      "data": {}
    }
  ],
  "component_failures": [],
  "trace": [
    {
      "seq": 1,
      "stage": "INTAKE",
      "component": "IntakeAgent",
      "message": "Received CONSULTATION claim for member EMP009 (amount 8000), 2 document(s).",
      "severity": "INFO",
      "data": {
        "claim_id": "CLM-EMP009-2024-10-18-317c55",
        "category": "CONSULTATION",
        "claimed_amount": 8000,
        "document_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 2,
      "stage": "DOCUMENT_VERIFICATION",
      "component": "DocumentVerificationAgent",
      "message": "Document verification passed: required types ['PRESCRIPTION', 'HOSPITAL_BILL'] present, all readable, single patient.",
      "severity": "INFO",
      "data": {
        "required_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ],
        "present_types": [
          "PRESCRIPTION",
          "HOSPITAL_BILL"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 3,
      "stage": "EXTRACTION",
      "component": "ExtractionAgent",
      "message": "Extracted 2 document(s). Diagnosis='Morbid Obesity - BMI 37', condition_key=obesity_treatment, 2 line item(s).",
      "severity": "INFO",
      "data": {
        "diagnosis": "Morbid Obesity - BMI 37",
        "treatment": "Bariatric Consultation and Customised Diet Plan Bariatric Consultation Personalised Diet and Nutrition Program",
        "condition_key": "obesity_treatment",
        "line_items": [
          {
            "description": "Bariatric Consultation",
            "amount": 3000.0
          },
          {
            "description": "Personalised Diet and Nutrition Program",
            "amount": 5000.0
          }
        ],
        "llm_enrichment": {}
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 4,
      "stage": "ADJUDICATION",
      "component": "CoverageAgent",
      "message": "The claimed treatment falls under a policy exclusion: 'Obesity and weight loss programs'. Diagnosis/treatment text matched this exclusion, so the claim is not payable.",
      "severity": "BLOCKER",
      "data": {
        "exclusion": "Obesity and weight loss programs"
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 5,
      "stage": "ADJUDICATION",
      "component": "EligibilityAgent",
      "message": "This claim is for a 'obesity_treatment' condition, which has a 365-day waiting period. The member joined on 2024-04-01 and the treatment was on 2024-10-18 (200 days later). Obesity_treatment-related claims are only eligible from 2025-04-01.",
      "severity": "BLOCKER",
      "data": {
        "eligible_from": "2025-04-01"
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 6,
      "stage": "FRAUD",
      "component": "FraudAgent",
      "message": "No fraud signals above threshold.",
      "severity": "INFO",
      "data": {
        "fraud_score": 0.0,
        "same_day_total": 1
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 7,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "Category sub-limit 2000 noted (advisory).",
      "severity": "INFO",
      "data": {
        "sub_limit": 2000
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 8,
      "stage": "ADJUDICATION",
      "component": "LimitsAgent",
      "message": "All monetary limits satisfied.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 9,
      "stage": "ADJUDICATION",
      "component": "MedicalNecessityAgent",
      "message": "Treatment appears consistent with the diagnosis.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 10,
      "stage": "ADJUDICATION",
      "component": "PreAuthAgent",
      "message": "No pre-auth rules apply to this category.",
      "severity": "INFO",
      "data": {},
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 11,
      "stage": "FINANCIAL",
      "component": "FinancialAgent",
      "message": "Computed payable amount: 0. Eligible amount (covered items): 0 | No network discount (non-network hospital or category has none). | Co-pay 10% applied on 0 = 0 deducted -> 0",
      "severity": "INFO",
      "data": {
        "claimed_amount": 8000.0,
        "eligible_amount": 0.0,
        "network_discount_percent": 0.0,
        "network_discount_amount": 0.0,
        "after_network_discount": 0.0,
        "copay_percent": 10.0,
        "copay_amount": 0.0,
        "approved_amount": 0.0,
        "steps": [
          "Eligible amount (covered items): 0",
          "No network discount (non-network hospital or category has none).",
          "Co-pay 10% applied on 0 = 0 deducted -> 0"
        ]
      },
      "llm_used": false,
      "duration_ms": null
    },
    {
      "seq": 12,
      "stage": "DECISION",
      "component": "DecisionAgent",
      "message": "Final decision: REJECTED | approved 0 | confidence 0.95 | reasons ['EXCLUDED_CONDITION', 'WAITING_PERIOD']",
      "severity": "INFO",
      "data": {
        "decision": "REJECTED",
        "confidence": 0.95,
        "component_failures": 0
      },
      "llm_used": false,
      "duration_ms": null
    }
  ]
}
```
