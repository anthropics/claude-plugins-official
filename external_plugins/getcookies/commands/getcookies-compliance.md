# GetCookies Compliance Checker

Check if a domain meets GDPR, CCPA, and other privacy regulation requirements.

## Usage

```
/getcookies-compliance [domain]
```

## Arguments

- `domain` (optional): The domain to check compliance for

## What This Does

1. Analyzes the domain's cookie setup against regulatory requirements
2. Checks for required consent mechanisms
3. Verifies cookie classifications are complete
4. Generates a compliance report with recommendations

## Compliance Checks

### GDPR (EU)
- [ ] Consent banner is displayed before setting non-essential cookies
- [ ] Users can reject all non-essential cookies easily
- [ ] Cookie purposes are clearly explained
- [ ] Consent is granular (by category)
- [ ] Consent can be withdrawn at any time
- [ ] Consent records are stored for audit

### CCPA (California)
- [ ] "Do Not Sell My Personal Information" link is present
- [ ] Opt-out mechanism is functional
- [ ] Privacy policy discloses cookie usage

### ePrivacy
- [ ] Prior consent for non-essential cookies
- [ ] Clear information about cookie purposes

### IAB TCF v2.2
- [ ] TCF-compliant CMP string is generated
- [ ] Vendor consents are properly managed
- [ ] Global Vendor List integration

## Example Output

```
Compliance Report: example.com
Generated: 2024-01-15

GDPR Compliance: 85% ⚠️
├── ✅ Consent banner present
├── ✅ Granular consent options
├── ⚠️ 3 cookies missing classification
└── ❌ No consent withdrawal option visible

CCPA Compliance: 100% ✅
├── ✅ Opt-out mechanism present
├── ✅ Privacy policy link found
└── ✅ DNSMPI link present

Recommendations:
1. Classify the 3 unknown cookies
2. Add a "Manage Preferences" link in footer
3. Enable consent withdrawal in widget settings
```

---

When the user runs this command:

1. Fetch domain data and latest scan results
2. Check consent widget configuration
3. Analyze cookies against regulatory requirements
4. Generate compliance score for each regulation
5. List specific issues and recommendations
6. Offer to fix issues automatically where possible
