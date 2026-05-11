# M&A Diligence — Standard Column Set

The default schema for a buy-side target contract review. Start here, then add or cut columns based on the deal. This is a starting point, not a checklist — the purchase agreement's reps and the request list drive what actually matters.

```yaml
schema:
  name: "M&A Diligence — Standard"
  columns:
    - id: counterparty
      label: "Counterparty"
      type: verbatim
      prompt: "Name the contracting party other than the target entity, exactly as it appears."

    - id: agreement_type
      label: "Agreement Type"
      type: classify
      options: [msa, purchase_order, license_in, license_out, lease, services, supply, distribution, nda, joint_venture, loan, guaranty, employment, other]
      prompt: "What kind of agreement is this?"

    - id: effective_date
      label: "Effective Date"
      type: date
      prompt: "When did this agreement become effective?"

    - id: term
      label: "Term"
      type: duration
      prompt: "What is the initial term?"

    - id: auto_renewal
      label: "Auto-Renewal"
      type: classify
      options: [none, annual, fixed_period, evergreen]
      prompt: "Does the agreement auto-renew? On what cycle?"

    - id: termination_for_convenience
      label: "Termination for Convenience"
      type: classify
      options: [none, either_party, target_only, counterparty_only]
      prompt: "Can either party terminate without cause? Who?"

    - id: termination_notice
      label: "Termination Notice Period"
      type: duration
      prompt: "How much notice is required to terminate?"

    - id: change_of_control
      label: "Change of Control"
      type: classify
      options: [silent, consent_required, consent_not_unreasonably_withheld, automatic_termination, notice_only, counterparty_right_to_terminate]
      prompt: "Does the agreement address a change of control of the target? What triggers and what happens?"

    - id: assignment
      label: "Assignment"
      type: classify
      options: [silent, consent_required, consent_not_unreasonably_withheld, freely_assignable, assignable_to_affiliates, non_assignable]
      prompt: "Can the target assign this agreement? What restrictions apply?"

    - id: exclusivity
      label: "Exclusivity / Non-Compete"
      type: classify
      options: [none, exclusive_supplier, exclusive_customer, non_compete, non_solicit, territory_restriction, most_favored_nation]
      prompt: "Does the agreement restrict either party from competing or contracting with others?"

    - id: liability_cap
      label: "Liability Cap"
      type: currency
      prompt: "Is there a cap on liability? What is the amount or multiplier?"

    - id: indemnification
      label: "Indemnification"
      type: classify
      options: [none, mutual, target_indemnifies, counterparty_indemnifies, ip_only, third_party_claims_only]
      prompt: "Who indemnifies whom, and for what?"

    - id: governing_law
      label: "Governing Law"
      type: verbatim
      prompt: "What jurisdiction's law governs?"

    - id: dispute_resolution
      label: "Dispute Resolution"
      type: classify
      options: [litigation, arbitration_binding, arbitration_nonbinding, mediation_first, silent]
      prompt: "How are disputes resolved?"

    - id: most_favored_nation
      label: "MFN / Pricing Protection"
      type: classify
      options: [none, mfn_pricing, price_matching, benchmarking_right]
      prompt: "Is there a most-favored-nation or pricing protection clause?"

    - id: minimum_commitments
      label: "Minimum Purchase / Volume Commitments"
      type: currency
      prompt: "Are there minimum purchase, volume, or spend commitments?"

    - id: ip_ownership
      label: "IP Ownership"
      type: classify
      options: [each_owns_own, target_owns_work_product, counterparty_owns_work_product, joint, license_only, silent]
      prompt: "Who owns intellectual property created or used under the agreement?"

    - id: confidentiality_term
      label: "Confidentiality Survival"
      type: duration
      prompt: "How long do confidentiality obligations survive termination?"

    - id: insurance_requirements
      label: "Insurance Requirements"
      type: classify
      options: [none, general_liability, professional_liability, cyber, workers_comp, umbrella]
      prompt: "What insurance must be maintained?"

    - id: audit_rights
      label: "Audit Rights"
      type: classify
      options: [none, counterparty_may_audit_target, target_may_audit_counterparty, mutual]
      prompt: "Does either party have audit rights?"

    - id: notices
      label: "Notice Requirements"
      type: verbatim
      prompt: "What is the notice address and method for the target?"
```

## Common additions by deal type

- **Tech / IP-heavy targets:** source code escrow, open source restrictions, data rights, model training rights, API access
- **Healthcare / life sciences:** BAA presence, regulatory filing obligations, FDA correspondence, clinical trial obligations
- **Government contractors:** novation consent requirements, flow-down clauses, security clearance, FAR/DFARS citations
- **Real estate:** renewal options, rent escalation, CAM provisions, subordination, estoppel requirements
- **Regulated financial:** regulatory approval conditions, capital requirements, FINRA/SEC filing triggers

## Common cuts for a fast first pass

For a time-pressured initial screen, these 6 columns answer 80% of the early deal questions: counterparty, effective_date, term, change_of_control, assignment, termination_for_convenience. Run those first, expand the schema once the deal team has prioritized.
