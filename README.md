# Prototype-CPRS_NoPrivacyControls
A Micro-Prototype of a Campus Parking Registration System that is privacy enhanced



| Attribute Name | Privacy Classification | Technical Transformation | Privacy Control Layer | Engineering Justification |
| :--- | :--- | :--- | :--- | :--- |
| **student_name** | Direct Identifier | Full Masking ("REDACTED") | Disassociated Processing | Retains structural layout compatibility without tracking a specific data subject's identity. |
| **matric_no** | Direct Identifier | Deterministic Tokenization (HMAC-SHA256) | Disassociated Processing | Replaces the raw identity with a fixed pseudonym to allow data consistency checks while blocking linkability. |
| **phone_number** | Direct Identifier | Complete Schema Removal | Data Minimisation | Dropped entirely during API ingress payload parsing. The data controller can fulfill campus security validation without collecting telemetry fields. |
| **license_plate** | Direct Identifier | Suffix Masking ("WAA1***") | Disassociated Processing | Erases individual identifier markers while preserving regional state prefixes for campus traffic trend mapping. |
| **vehicle_model** | Quasi-Identifier | Category Generalisation | Disassociated Processing | Suppresses specific make/model specifics into broad physical classifications (e.g., Sedan, SUV) to prevent luxury-car targeting and unique profiling. |
| **registration_date** | Quasi-Identifier | Year Extraction & TTL Eviction | Automated Destruction / Generalisation | Truncates specific calendar timestamps down to coarse calendar years to prevent behavioral tracking. Implements a 365-day Time-To-Live expiration control. |
| **faculty** | Quasi-Identifier | Structural Clustering | Disassociated Processing | Standardizes separate operational departments into clustered administrative groupings (e.g., STEM vs Humanities). |
| **parking_hours** | Sensitive Metric | Quantization / Microaggregation | Disassociated Processing | Transforms high-precision individual numbers into discrete, aggregated interval blocks to block fine-grained routine analysis. |
