# Sample Documents Guide

Reference for the document types the Extraction agent must handle (today from the
provided structured `content`; in production from images via a vision LLM).

## Document types & key fields

**1. Medical Prescription** — doctor name, registration number, specialization;
patient name/age/gender/date; diagnosis; medicines (dosage, duration); tests
ordered; clinic name/address.
Variations: handwritten, pre-printed templates with handwritten fill-ins, partially
visible registration numbers, medical shorthand (HTN, T2DM), regional-language
mixing, rubber stamps over text.

**2. Hospital Bill / Clinic Invoice** — hospital name/address/GSTIN; bill number,
date; patient name/age/gender; itemized line items with amounts; GST; total.
Variations: no GSTIN at small clinics, vague line items ("Medicines"), separate
pharmacy/consultation bills, handwritten bills, amounts in words vs figures,
corrections/cancellation marks.

**3. Diagnostic / Lab Report** — lab name, NABL status; patient details; referring
doctor; sample/report dates; per-test name/result/unit/normal range; pathologist
name + registration; remarks.

**4. Pharmacy Bill** — pharmacy name, drug license; bill number, date; patient +
prescribing doctor; per-medicine batch/expiry/qty/MRP/amount; discounts; net amount.

## Doctor registration number formats

State-specific: `KA/XXXXX/YYYY` (Karnataka), `MH/…`, `DL/…`, `TN/…`, `GJ/…`,
`AP/…`, `UP/…`, `WB/…`, `KL/…`. Ayurveda (national): `AYUR/[STATE]/XXXXX/YYYY`
(e.g. `AYUR/KL/2345/2019`).

## Common diagnoses

Infections (Viral Fever, URI, Gastroenteritis, UTI, Dengue, Typhoid); Chronic (HTN,
T2DM, Hypothyroidism); Respiratory (Acute Bronchitis, Asthma, COPD); Musculoskeletal
(Spondylosis, Knee OA); Neurological (Migraine, Vertigo); Dental (Caries, Abscess,
Gingivitis); GI (GERD, IBS, PUD).

## Quality variations & handling strategy

| Variation | Handling |
|-----------|----------|
| Handwritten Rx | vision model + explicit OCR prompt |
| Phone photo (skew/low contrast) | best-effort extraction, flag low-confidence fields |
| Stamp over text | flag field LOW confidence, do not fail the whole doc |
| Multilingual | extract English fields; flag regional fields unextracted |
| Partial / folded | extract available fields; flag missing explicitly |
| Crossed-out amounts | flag `DOCUMENT_ALTERATION` to fraud detection |
| ORIGINAL/DUPLICATE stamps | note and surface to fraud detection |
| Multi-page scanned PDF | process each page, aggregate line items |

> In this implementation, the Extraction agent's interface already returns this
> structured shape, so swapping the content source for a real vision call does not
> change any downstream contract.
