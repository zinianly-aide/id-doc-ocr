# Approval Verification REVIEW SOP

## Audience

This document is for real approvers, REVIEW owners, and pilot operations support.

It answers one practical question:
- when the system returns REVIEW, what should the approver actually do next?

This is an operating SOP, not a model-design note.

Core rule:
- the system is approval assistance only
- the human approver keeps final decision authority
- REVIEW never means “auto reject” and never means “safe to pass without checking”

---

## 1. REVIEW means what

Operational meaning of REVIEW:
- the system sees enough risk or uncertainty that the case is not safe for direct pass-through
- the approver must manually inspect the case before making the final decision

REVIEW is expected when any of the following happens:
- key document fields are missing
- document semantics look suspicious
- applicant / holder / spouse relationship does not match expected business context
- OCR is weak or unstable
- analysis or verification fails technically
- stale or previous result is still visible after a retry failure

Approver rule:
- do not treat REVIEW as a suggestion to “approve later anyway”
- treat REVIEW as “manual decision required now”

---

## 2. Common REVIEW reasons and what they usually mean

| REVIEW reason | What it usually means | Typical approver concern |
|---|---|---|
| title missing | Marriage certificate title was not extracted or is absent | Is the uploaded material really the expected document? |
| authority suspect | Issuing / registration authority does not look like a valid marriage-registration authority | Is the document source trustworthy and complete? |
| holder mismatch | Holder name is not consistent with the named couple or applicant context | Is this the correct person’s certificate? |
| OCR weak | Core fields may exist but extraction confidence is weak | Can a human still confirm the document safely from the image? |
| validation rejected | Minimum required field set is incomplete or structurally unsafe | Is the case too incomplete to rely on system assistance? |
| analyze fail | Upstream analysis step failed | No usable machine reading result exists |
| verify fail | Business verification step failed | Prior result must not be trusted as the current basis |

Operational note:
- one case may contain more than one REVIEW reason
- the approver should read the summary first, then inspect the visible evidence and the uploaded image itself

---

## 3. Approver action standard

### A. When to return for correction / supplementary upload

Use “return for correction” when:
- the uploaded file is not a supported image
- the image is too blurry, cropped, or blocked to verify manually
- title, authority, or key person fields are unreadable
- the wrong document appears to have been uploaded
- the case could become approvable if the employee re-uploads a clearer or correct attachment

Typical approver wording:
- please re-upload a clear image of the marriage certificate
- current attachment is incomplete or core fields are unreadable
- uploaded material does not match the required leave attachment type

### B. When manual confirmation may still allow release

Manual confirmation may allow approval only when all of the following are true:
- the system returned REVIEW rather than REJECT-level business stop
- the approver can visually confirm the document is authentic enough for pilot policy
- key business facts are still human-readable from the image
- there is no strong policy contradiction
- the approver is authorized to make the final approval decision under current pilot rules

Examples:
- OCR weak but the image is still clearly readable by a human
- authority wording is partially unusual, but the approver can confirm the official marriage-registration authority from the image
- system cannot safely PASS because of extraction uncertainty, but the human reviewer can confirm the case

### C. When to directly reject

Direct rejection is appropriate when:
- the uploaded attachment is clearly the wrong document type
- the document is clearly inconsistent with the applicant or leave scenario
- there is obvious material mismatch and no reasonable correction path within the current request
- policy interpretation is clear and the document does not satisfy the requirement

Examples:
- marriage leave request uploaded a non-marriage document
- holder / spouse information is clearly unrelated to the request and cannot be explained
- image is unusable and the request cannot proceed without valid supporting material

---

## 4. Override rule

## Whether override is allowed
- yes, but only as a controlled manual action
- override is for business continuity and policy-based human judgment, not for bypassing the review process silently

## Who may override
- named pilot approvers within their approval authority
- REVIEW owner or escalation owner for disputed cases
- no anonymous or undocumented override is allowed

## Mandatory conditions for override
An override must include all of the following:
1. approver name
2. case id / request_id
3. override direction:
   - REVIEW -> approve
   - REVIEW -> reject
   - REJECT -> manual exception handling if policy explicitly allows
4. short reason note
5. supporting evidence reference if the case is high risk or disputed

## Whether override must be recorded
- yes, always
- every override enters the pilot risk / issue ledger
- no override is considered complete until it is recorded

## When override should escalate first
Escalate before overriding when:
- a possible false-pass risk exists
- policy interpretation is disputed
- repeated same-pattern overrides are appearing
- the approver is unsure whether the issue is technical, policy, or user-error related

---

## 5. Misjudgment handling

## False positive definition
- system returned REVIEW / REJECT, but business review concludes the case should have passed cleanly

## False negative definition
- system returned PASS, but business review concludes the case should have required REVIEW or rejection

## How to record false positive
Record:
- date
- case id / request_id
- leave_type
- REVIEW reason
- final human decision
- why the system was too conservative
- whether the same pattern has happened before

## How to record false negative
Record immediately and escalate same day:
- date
- case id / request_id
- leave_type
- what passed incorrectly
- actual business risk
- containment action taken
- whether similar live cases may exist

## How to feed rule optimization
Weekly review should classify each misjudgment into one of these buckets:
- OCR weakness
- parser / extraction gap
- validator rule too weak
- validator rule too strict
- business policy nuance missing
- UI misunderstanding / operator misuse
- upstream integration problem

Rule change principle:
- do not hot-fix rules in the middle of pilot traffic without explicit owner decision
- first classify, then discuss, then schedule a controlled fix

---

## 6. REVIEW handling flow

1. Read verify_status and summary message
2. Read the main reason shown in warnings / rule results
3. Inspect the uploaded image directly
4. Decide one of four actions:
   - approve after manual confirmation
   - return for correction / re-upload
   - reject
   - escalate
5. If override happened, record it immediately
6. If the case is a misjudgment candidate, add it to the weekly review ledger

Do not:
- approve from a stale result after verify failure
- ignore a REVIEW without checking the image
- rely only on one warning string without reading the visible case context
- make undocumented overrides

---

## 7. Example cases

### Example 1: clean PASS case
Case:
- leave_type = MARRIAGE
- certificate title present
- holder matches one spouse
- registration date present
- authority looks valid
- verify_status = PASS

Approver action:
- continue standard approval review
- no additional document investigation required by default
- still retain final human authority if broader business context looks unusual

### Example 2: REVIEW because OCR is weak
Case:
- leave_type = SICK or MARRIAGE
- image is slightly blurred
- key fields look human-readable but extraction is unstable
- verify_status = REVIEW

Approver action:
- manually inspect the image
- if human-readable and policy-compliant, approval may continue with manual confirmation
- if not safely readable, return for clearer upload
- record override if the human approves despite REVIEW

### Example 3: marriage mismatch case
Case:
- leave_type = MARRIAGE
- holder name is not in named couple
- verify_status = REVIEW
- warning indicates holder mismatch

Approver action:
- do not directly approve
- first confirm whether the uploaded certificate belongs to the applicant / spouse pair
- if mismatch is real, reject or return for correct document
- if business context explains the mismatch, escalate or override with mandatory note

---

## 8. Pilot operating language for approvers

Use these simple interpretations in training:
- PASS = system sees no blocking issue, proceed with normal review
- REVIEW = system is uncertain or sees risk, human must decide
- REJECT = strong stop signal, human should not pass without explicit policy-backed exception
- Error / fail / stale result = treat the system result as unusable, continue manually

Final rule:
- if the system is uncertain, the human must be certain before releasing the case
