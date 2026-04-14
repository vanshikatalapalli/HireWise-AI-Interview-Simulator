import hashlib

TRACK_GROUPS = {
    "software engineer": ["core_technical"],
    "backend developer": ["core_technical"],
    "full stack developer": ["core_technical", "frontend"],
    "frontend developer": ["frontend"],
    "data analyst": ["data"],
    "data scientist": ["data", "ml"],
    "machine learning engineer": ["ml", "core_technical"],
    "devops engineer": ["devops"],
    "cybersecurity analyst": ["cyber"],
    "product manager": ["product_business"],
    "business analyst": ["product_business", "data"],
    "ui/ux designer": ["uiux", "product_business"],
    "hr recruiter": ["people_hr"],
    "hr manager": ["people_hr"],
    "sales executive": ["sales_marketing"],
    "marketing specialist": ["sales_marketing"],
    "qa engineer": ["qa"],
}

COMPANY_QUESTION_BANK = {
    "core_technical": [
        {"company": "Google", "type": "technical", "difficulty": "medium", "question": "How would you design a rate limiter for a global API service?", "keywords": ["rate limiter", "distributed", "token bucket"], "ideal_answer": "Algorithm choice, consistency model, storage strategy, and performance trade-offs.", "model_answer": "I would use token bucket with Redis-backed counters, regional fallback, and latency monitoring.", "skills": ["API", "System Design", "Scalability"]},
        {"company": "Amazon", "type": "technical", "difficulty": "hard", "question": "Explain how you would design an idempotent order creation API.", "keywords": ["idempotency", "api", "retries", "consistency"], "ideal_answer": "Idempotency key handling, race condition control, and consistent responses.", "model_answer": "I would store idempotency keys with request hash and return original response for retries.", "skills": ["Backend", "API", "Database"]},
        {"company": "Netflix", "type": "technical", "difficulty": "hard", "question": "How would you debug intermittent latency spikes in a microservice chain?", "keywords": ["latency", "tracing", "profiling", "bottleneck"], "ideal_answer": "Trace bottlenecks, compare dependencies, and apply targeted mitigations.", "model_answer": "I would use distributed traces and p99 trends to isolate slow dependencies and tune timeouts/caching.", "skills": ["Debugging", "Microservices", "Observability"]},
        {"company": "Uber", "type": "technical", "difficulty": "medium", "question": "What data model would you use for real-time location updates at scale?", "keywords": ["real-time", "partitioning", "throughput"], "ideal_answer": "Write-optimized model with partitioning, retention strategy, and fast reads.", "model_answer": "I would use time-bucketed partition keys, TTL retention, and a cache for latest location lookups.", "skills": ["Database", "Scalability", "Backend"]},
    ],
    "frontend": [
        {"company": "Airbnb", "type": "technical", "difficulty": "medium", "question": "How would you optimize a slow React page with heavy component trees?", "keywords": ["react", "render", "memoization", "performance"], "ideal_answer": "Profile re-renders, reduce prop churn, and validate performance improvements.", "model_answer": "I would profile render paths, apply memoization where needed, and use code splitting/lazy loading.", "skills": ["Frontend", "React", "Performance"]},
        {"company": "Meta", "type": "technical", "difficulty": "hard", "question": "How would you design a reusable component system across multiple product teams?", "keywords": ["design system", "components", "versioning"], "ideal_answer": "Strong API contracts, token system, versioning policy, and adoption strategy.", "model_answer": "I would define token-driven components, version the library, and support migration guidelines.", "skills": ["Frontend", "Design System", "Architecture"]},
        {"company": "Google", "type": "technical", "difficulty": "medium", "question": "What approach would you use to improve accessibility in an existing UI?", "keywords": ["accessibility", "aria", "keyboard", "contrast"], "ideal_answer": "Audit current issues and improve semantic, keyboard, and visual accessibility.", "model_answer": "I would run an accessibility audit, fix semantic/keyboard gaps, and automate checks in CI.", "skills": ["Frontend", "Accessibility", "UI"]},
    ],
    "data": [
        {"company": "Google", "type": "technical", "difficulty": "medium", "question": "How would you analyze a sudden drop in daily active users for a product?", "keywords": ["sql", "segmentation", "funnel", "root cause"], "ideal_answer": "Validate data integrity, segment users, inspect funnel and release events.", "model_answer": "I would segment DAU by channel and platform, then inspect funnel and release impact to isolate root cause.", "skills": ["SQL", "Analytics", "Product Metrics"]},
        {"company": "Amazon", "type": "technical", "difficulty": "medium", "question": "How would you detect duplicate transactions in a large dataset?", "keywords": ["sql", "window function", "deduplication"], "ideal_answer": "Business keys, ranking logic, and canonical record selection.", "model_answer": "I would use window functions over business keys to identify duplicates and keep canonical records.", "skills": ["SQL", "Data Quality", "Analytics"]},
        {"company": "Meta", "type": "mixed", "difficulty": "hard", "question": "How do you decide if a new feed-ranking experiment should be launched?", "keywords": ["experiment", "metrics", "significance", "tradeoff"], "ideal_answer": "Primary metrics, guardrails, significance, and cohort-level impact analysis.", "model_answer": "I would evaluate metric lift with guardrails and only launch if cohort-level trade-offs are acceptable.", "skills": ["Experimentation", "Metrics", "Decision Making"]},
    ],
    "ml": [
        {"company": "Google", "type": "technical", "difficulty": "hard", "question": "How would you monitor model drift in a production recommendation model?", "keywords": ["model drift", "monitoring", "feature distribution", "retraining"], "ideal_answer": "Track feature/label drift, alert thresholds, and retraining triggers.", "model_answer": "I would track drift metrics and trigger retraining when thresholds are crossed with rollback-safe deployment.", "skills": ["Machine Learning", "MLOps", "Monitoring"]},
        {"company": "Netflix", "type": "technical", "difficulty": "hard", "question": "Describe an offline and online evaluation strategy for recommendation models.", "keywords": ["offline metrics", "ab testing", "online metrics"], "ideal_answer": "Use offline ranking metrics plus online A/B testing and guardrails.", "model_answer": "I would shortlist by offline metrics, then validate with A/B tests using retention and engagement guardrails.", "skills": ["ML", "Experimentation", "Recommender Systems"]},
    ],
    "devops": [
        {"company": "Amazon", "type": "technical", "difficulty": "medium", "question": "How would you design CI/CD gates for high-risk production deployments?", "keywords": ["ci/cd", "deployment", "rollback", "quality gates"], "ideal_answer": "Layered checks, canary rollout, and automated rollback thresholds.", "model_answer": "I would enforce test/security gates, deploy canaries, and auto-rollback on SLO breaches.", "skills": ["DevOps", "CI/CD", "Reliability"]},
        {"company": "Google", "type": "technical", "difficulty": "hard", "question": "What is your strategy to improve SLO compliance for a flaky service?", "keywords": ["slo", "error budget", "incident", "reliability"], "ideal_answer": "Incident pattern analysis and reliability roadmap tied to error-budget policy.", "model_answer": "I would prioritize fixes by reliability ROI and enforce error-budget governance.", "skills": ["SRE", "Reliability", "Monitoring"]},
    ],
    "cyber": [
        {"company": "Microsoft", "type": "technical", "difficulty": "hard", "question": "How do you prioritize vulnerabilities when hundreds are open?", "keywords": ["vulnerability", "risk", "exploitability", "prioritization"], "ideal_answer": "Risk-based ranking using exploitability, exposure, and asset criticality.", "model_answer": "I rank by exploitability and business impact, then assign remediation SLAs by risk tier.", "skills": ["Security", "Risk Management", "Prioritization"]},
        {"company": "Cisco", "type": "technical", "difficulty": "medium", "question": "What controls reduce lateral movement risk in enterprise networks?", "keywords": ["lateral movement", "segmentation", "least privilege"], "ideal_answer": "Segmentation, least privilege, identity controls, and behavior monitoring.", "model_answer": "I combine segmentation and least privilege with east-west anomaly detection and hardening.", "skills": ["Network Security", "Zero Trust"]},
    ],
    "product_business": [
        {"company": "Meta", "type": "mixed", "difficulty": "hard", "question": "How would you improve engagement for a declining social feature?", "keywords": ["product sense", "engagement", "metrics", "hypothesis"], "ideal_answer": "Problem framing, metric tree, hypothesis prioritization, and experiment plan.", "model_answer": "I would segment users, identify drop points, and prioritize experiments by impact and effort.", "skills": ["Product Sense", "Metrics", "Prioritization"]},
        {"company": "Google", "type": "mixed", "difficulty": "medium", "question": "Tell me about a product decision you made with incomplete data.", "keywords": ["decision making", "tradeoff", "stakeholders"], "ideal_answer": "Structured assumptions, stakeholder alignment, and validation strategy.", "model_answer": "I made assumptions explicit, aligned on risks, and shipped a reversible MVP to learn quickly.", "skills": ["Decision Making", "Leadership", "Communication"]},
        {"company": "Uber", "type": "mixed", "difficulty": "medium", "question": "How would you prioritize roadmap items when every team has urgent requests?", "keywords": ["prioritization", "roadmap", "impact", "tradeoff"], "ideal_answer": "Use impact-effort framework, align on goals, and communicate tradeoffs transparently.", "model_answer": "I rank requests by user/business impact and effort, align with quarterly goals, and publish transparent prioritization criteria.", "skills": ["Roadmap", "Stakeholder Management", "Prioritization"]},
        {"company": "Amazon", "type": "mixed", "difficulty": "medium", "question": "How do you define success metrics before launching a new feature?", "keywords": ["metrics", "north star", "guardrails", "launch"], "ideal_answer": "Define primary outcome, guardrails, baseline, and rollout decision thresholds.", "model_answer": "I define one primary metric, supporting guardrails, and baseline targets before launch so post-launch decisions are objective.", "skills": ["Product Metrics", "Execution", "Decision Making"]},
    ],
    "people_hr": [
        {"company": "Google", "type": "hr", "difficulty": "medium", "question": "How do you assess culture fit without introducing bias?", "keywords": ["bias", "structured interview", "fairness"], "ideal_answer": "Structured rubrics, role-relevant criteria, and panel calibration.", "model_answer": "I use structured scorecards and evidence-based evaluation tied to role outcomes.", "skills": ["Hiring", "Fairness", "Communication"]},
        {"company": "Amazon", "type": "hr", "difficulty": "hard", "question": "Describe your approach to hiring under aggressive timelines.", "keywords": ["hiring", "timeline", "pipeline", "quality"], "ideal_answer": "Pipeline planning, stakeholder alignment, and quality guardrails.", "model_answer": "I run parallel sourcing and strict scorecards while accelerating scheduling and feedback loops.", "skills": ["Recruitment", "Execution", "Planning"]},
    ],
    "sales_marketing": [
        {"company": "HubSpot", "type": "mixed", "difficulty": "medium", "question": "How would you recover a pipeline quarter that is 30% behind target?", "keywords": ["pipeline", "forecast", "conversion", "prioritization"], "ideal_answer": "Stage-wise recovery plan with measurable conversion improvements.", "model_answer": "I would segment deals by probability and run focused recovery plays with weekly conversion tracking.", "skills": ["Sales", "Execution", "Analytics"]},
        {"company": "Google", "type": "mixed", "difficulty": "medium", "question": "How do you prove a marketing campaign drove incremental growth?", "keywords": ["incrementality", "attribution", "roi", "experiment"], "ideal_answer": "Use control groups and business-outcome metrics, not only attribution reports.", "model_answer": "I would measure incremental lift with experiments and compare ROI after baseline adjustment.", "skills": ["Marketing Analytics", "Experimentation", "ROI"]},
    ],
    "qa": [
        {"company": "Microsoft", "type": "technical", "difficulty": "medium", "question": "How would you design a risk-based test strategy for a major release?", "keywords": ["test strategy", "risk", "coverage", "release"], "ideal_answer": "Risk-prioritized coverage, automation strategy, and release exit criteria.", "model_answer": "I prioritize tests by user impact and defect risk, automate critical paths, and gate release with quality criteria.", "skills": ["Testing", "Quality", "Automation"]},
    ],
    "uiux": [
        {"company": "Airbnb", "type": "mixed", "difficulty": "medium", "question": "How would you redesign a booking flow with high drop-off after step 2?", "keywords": ["ux", "drop-off", "research", "iteration"], "ideal_answer": "Combine behavior data and usability research to remove friction points.", "model_answer": "I would inspect funnel analytics, run usability sessions, and test simplified flows for lift.", "skills": ["UX", "Research", "Product Thinking"]},
    ],
}


def _stable_company_question_id(track, company, question):
    raw = f"{track}::{company}::{question}".encode("utf-8")
    digest = hashlib.md5(raw).hexdigest()[:8]
    return 100000 + int(digest, 16)


def get_company_questions_for_profession(profession):
    if not profession:
        return []

    p = profession.lower().strip()
    groups = TRACK_GROUPS.get(p, ["core_technical"])
    rows = []

    for group in groups:
        for item in COMPANY_QUESTION_BANK.get(group, []):
            row = dict(item)
            row["id"] = _stable_company_question_id(group, item["company"], item["question"])
            row["question"] = f"[{item['company']}] {item['question']}"
            row["skills"] = row.get("skills", []) + [item["company"], profession.title()]
            rows.append(row)

    return rows
