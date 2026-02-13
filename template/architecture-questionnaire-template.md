# Solution Architecture Questionnaire

> **Purpose:** Gather requirements and context before creating a solution design.
> Answers feed directly into the [Solution Design Template](solution-design-template.adoc).
>
> **Instructions:** Fill in all relevant sections. Leave blank if unknown — mark with `TBD`.
> Section cross-references (→ §N) point to the corresponding solution design section.
>
> **⚠️ Pre-Fill Guidance (for the architect):**
> Never hand a blank questionnaire to a stakeholder — it signals you haven't done your
> homework. Before sending, pre-fill with your best assumptions based on initial meetings,
> domain research, and similar projects. Let the client *correct* rather than *create*.
> Pre-filled answers dramatically improve response quality and save everyone time.
>
> **Priority Tags:** Mark questions with priority to focus discovery:
> - 🔴 **Must have** — blocks architecture decisions
> - 🟡 **Should have** — important but can assume a default
> - 🟢 **Nice to have** — refine later if time permits

---

## 1. Project & Stakeholders

> → Maps to: **§2 Stakeholders**, **§3 Executive Summary**

### 1.1 Project Overview
- **Project Name:**
- **Business Domain:**
- **Primary Business Objective:**
- **Project Sponsor:**
- **Target Start Date:**
- **Target Go-Live Date:**

### 1.2 Stakeholder Register

| Name / Role | Organization | Key Concerns | Communication Needs |
|-------------|-------------|--------------|---------------------|
|             |             |              |                     |
|             |             |              |                     |
|             |             |              |                     |

> 💡 **Hidden Stakeholder Check:** Have you identified everyone who can block or
> delay the project? Consider: compliance/legal, DBA team, network/firewall team,
> change advisory board, enterprise architects, union representatives, data privacy
> officers. "The person who wasn't invited to the meeting is the one who kills
> your project in month three."

### 1.3 Business Drivers
- **What business problem does this solution solve?**

- **What are the key business goals?**

- **How will success be measured? (KPIs)**

### 1.4 Team Topology & Organizational Context

> → Maps to: **§11 Team Composition**, **§7 Architecture** (Conway's Law)

- **How many teams will work on the solution?**
- **Are teams cross-functional (dev + QA + ops) or siloed?**
- **Communication between teams:** (Co-located / Same timezone / Distributed)
- **Existing team expertise:** (List key technologies the team knows well)
- **Knowledge concentration risk:** (Are there components only one person understands?)
- **Organizational boundaries that affect architecture:**
  (e.g., "Team A owns auth, Team B owns payments" → service boundary likely here)

> 💡 **Conway's Law reminder:** Your architecture will mirror your org structure.
> If two teams can't coordinate easily, don't design a component that requires them to.

### 1.5 Informal Discovery Notes

> Use this section for insights gathered during hallway conversations, coffee chats,
> and off-the-record discussions. These often reveal the *real* priorities and blockers
> that don't appear in formal requirements.

- **Unspoken priorities or political dynamics:**
- **Things stakeholders said "off the record":**
- **Observed workflows vs. documented workflows:** (what people *actually* do)
- **Team morale / change appetite observations:**


## 2. Architecture Principles

> → Maps to: **§4 Architecture Principles**

Which principles should guide the design? Check all that apply and add your own.

- [ ] API-First — all capabilities exposed via well-defined APIs
- [ ] Cloud-Native — design for cloud deployment, use managed services
- [ ] Security by Design — security controls built-in from the start
- [ ] Observability by Default — logs, metrics, traces from day one
- [ ] Data as an Asset — data quality, lineage, governance are first-class
- [ ] Mobile-First — prioritize mobile experience
- [ ] Offline-Capable — must function without network connectivity
- [ ] Cost-Optimized — minimize cloud spend without sacrificing reliability
- [ ] Vendor-Neutral — avoid lock-in, use abstraction layers
- [ ] Other:

**Are there any existing organizational architecture principles that must be followed?**


## 3. Functional Requirements

> → Maps to: **§5 Problem Statement**, **§9 Key Flows**, **§19 Business Process Flows**

### 3.1 Core Features
- **List the main features/functionalities with priority:**

  | # | Feature | MoSCoW | Notes |
  |---|---------|--------|-------|
  | 1 |         | Must / Should / Could / Won't |  |
  | 2 |         | Must / Should / Could / Won't |  |
  | 3 |         | Must / Should / Could / Won't |  |

  > 💡 MoSCoW helps scope options: "Must" = MVP, "Should" = full build.
  > "Won't" is the most important category — it sets explicit boundaries.

- **What are the primary user personas and their use cases?**
  - Persona 1:
  - Persona 2:

### 3.2 User Interactions
- **How will users interact with the system?** (Web, Mobile, Desktop, API, CLI, etc.)

- **What are the main user workflows?**

- **Are there any batch processing requirements?**

> 💡 **Workflow Observation:** If possible, watch users perform their current workflows
> before designing the new system. Documented processes rarely match reality.
> Ask: "Can you show me how you do [X] today?" instead of "How do you do [X]?"


## 4. Non-Functional Requirements

> → Maps to: **§12 Quality Scenarios**, **§17 Observability & Monitoring**

### 4.1 Performance
- **Expected number of concurrent users:**

- **Response time requirements:** _(defaults shown — adjust per project)_
  - API response time: _[default: < 200ms P95]_
  - Page/App load time: _[default: < 3s initial, < 1s subsequent]_
  - Background job completion time: _[default: < 30s for user-triggered]_

- **Peak load expectations:**

> 💡 If the client says "fast" — pin it down: "Do you mean < 200ms API response
> or < 3 seconds page load? For how many concurrent users?"

### 4.2 Scalability
- **Expected growth over time:**
  - Year 1:
  - Year 2:
  - Year 3:

- **Scaling strategy preference:** (Auto-scaling, Horizontal, Vertical)

- **Geographic distribution requirements:** (Regions, latency targets)

### 4.3 Availability & Reliability
- **Required uptime (SLA):** _[default: 99.9% = ~8.7h downtime/year]_
- **Maximum acceptable downtime:**
- **Recovery Time Objective (RTO):**
- **Recovery Point Objective (RPO):**

### 4.4 Security & Compliance

> → Maps to: **§14 Security Architecture**

- **Authentication requirements:** (OAuth2, SAML, MFA, SSO, Social login, etc.)

- **Authorization model:** (RBAC, ABAC, custom)

- **Data classification:** (Public, Internal, Confidential, Restricted)

- **Compliance requirements:** (GDPR, HIPAA, PCI-DSS, SOC 2, CCPA, etc.)

- **Data encryption requirements:**
  - At rest:
  - In transit:

- **Network security requirements:** (VPN, private endpoints, WAF, etc.)

### 4.5 Data Requirements

> → Maps to: **§8 Data Architecture**

- **Data volume:** (Current and projected)

- **Data retention policies:**

- **Data backup requirements:**

- **Data archival requirements:**

- **Data sovereignty / residency requirements:**


## 5. Technical Requirements

> → Maps to: **§6 C4 Context**, **§7 Architecture**, **§15 API Design**

### 5.1 Technology Stack Preferences
- **Programming languages:**
- **Frameworks:**
- **Database preferences:** (SQL, NoSQL, Graph, Time-series)
- **Cloud provider preference:** (AWS, Azure, GCP, Multi-cloud, On-premises)
- **Containerization:** (Docker, Kubernetes, Serverless)

### 5.2 Integration Requirements
- **External systems to integrate with:**

  | System | Protocol | Purpose | Direction (In/Out/Bidirectional) |
  |--------|----------|---------|----------------------------------|
  |        |          |         |                                  |
  |        |          |         |                                  |

- **Third-party services/APIs:**

- **API Verification Checklist:**
  > ⚠️ For each external integration, verify before committing to a timeline:

  | System | Sandbox Available? | Auth Method | Rate Limits | SLA | Documentation Quality |
  |--------|--------------------|-------------|-------------|-----|----------------------|
  |        | Yes / No / Unknown |             |             |     | Good / Poor / None   |
  |        | Yes / No / Unknown |             |             |     | Good / Poor / None   |

  > 💡 "The integration that 'should just work' will consume 60% of your timeline."
  > Budget 3× your initial estimate for any third-party integration.

- **Message queue/event streaming requirements:**

### 5.3 API Requirements

> → Maps to: **§15 API Design**

- **API style preference:** (REST, GraphQL, gRPC, WebSocket)
- **API versioning strategy:** (URL path, Header, Query parameter)
- **Expected number of API consumers:**
- **Rate limiting requirements:**

### 5.4 Data Flow
- **Describe the data flow through the system:**
- **Data sources:**
- **Data destinations:**
- **Real-time vs batch processing:**


## 6. Architecture Patterns

> → Maps to: **§7 Architecture**, **§22 ADRs**

### 6.1 Architecture Style
- **Preferred architecture pattern:** (Monolithic, Microservices, Serverless, Event-driven, Hybrid, etc.)
- **Reason for choice:**

> ⚠️ **Microservices Org-Check:** If the answer is "microservices," ask:
> - Does the team have experience operating distributed systems in production?
> - Is there a DevOps/platform team to manage service mesh, CI/CD per service?
> - Are there more than 5 developers? (below this, microservices add overhead without benefit)
> - Can you deploy services independently, or does everything ship together?
>
> If most answers are "no," recommend a modular monolith with clear module boundaries
> that can be extracted into services later. This is the safer default.

### 6.2 Components
- **Main application components:**
  1.
  2.
  3.

- **Shared services needed:** (Authentication, Logging, Monitoring, API Gateway, etc.)


## 7. Infrastructure & Deployment

> → Maps to: **§16 Deployment & Infrastructure**, **§6.3 Deployment Diagram**

### 7.1 Deployment Model
- **Deployment environment:** (Cloud, Hybrid, On-premises)
- **Deployment strategy:** (Blue-Green, Canary, Rolling, etc.)
- **CI/CD requirements:**
- **Infrastructure as Code tool:** (Terraform, CloudFormation, Pulumi, etc.)

### 7.2 Environment Strategy

| Environment | Purpose | Infrastructure Level | Data Strategy |
|-------------|---------|---------------------|---------------|
| Development |         |                     |               |
| Staging     |         |                     |               |
| Production  |         |                     |               |

### 7.3 Infrastructure Components
- **Compute requirements:**
  - Web servers:
  - Application servers:
  - Background workers:

- **Storage requirements:**
  - Database storage:
  - File storage:
  - Object storage:

- **Networking requirements:**
  - CDN needed: Yes / No
  - Load balancer: Yes / No
  - VPN requirements:


## 8. Observability & Monitoring

> → Maps to: **§17 Observability & Monitoring**

### 8.1 Logging
- **Log aggregation requirements:**
- **Log retention period:**
- **Log analysis needs:**

### 8.2 Monitoring
- **Key metrics to monitor:**
  - Application metrics:
  - Infrastructure metrics:
  - Business metrics:

- **Alerting requirements:**

### 8.3 Tracing
- **Distributed tracing needed:** Yes / No
- **Performance profiling requirements:**


## 9. Disaster Recovery & Business Continuity

> → Maps to: **§16 Deployment & Infrastructure**, **§12 Quality Scenarios**

### 9.1 Backup Strategy
- **Backup frequency:**
- **Backup retention:**
- **Backup testing requirements:**

### 9.2 Disaster Recovery
- **Disaster recovery plan requirements:**
- **Failover strategy:**
- **Multi-region deployment:** Yes / No


## 10. Testing Requirements

> → Maps to: **§12 Quality Scenarios**, **§11 Option Detail**

### 10.1 Testing Strategy
- **Unit test coverage target:**
- **Integration testing approach:**
- **Performance / load testing requirements:**
- **Security testing requirements:** (Pen testing, SAST, DAST, dependency scanning)

### 10.2 Acceptance Criteria
- **Who defines acceptance criteria?**
- **UAT process:**
- **Performance benchmarks:**


## 11. Migration (if applicable)

> → Maps to: **§21 Migration & Transition**

- **Is this a migration from an existing system?** Yes / No
- **Migration strategy preference:** (Big-bang, Strangler Fig, Parallel Run, Phased)
- **Data migration requirements:**
- **Feature parity requirements:**
- **Rollback plan:**


## 12. Constraints & Assumptions

> → Maps to: **§12 Assumptions, Constraints & Quality**

### 12.1 Constraints
- **Budget constraints:**
- **Budget structure preference:** (Time & Materials / Fixed Price / Hybrid)
  > ⚠️ **Fixed-Price Warning:** If fixed-price is selected, flag this early.
  > Fixed-price requires extremely detailed requirements *before* estimation.
  > Every ambiguity becomes a change request or absorbed loss. Recommend T&M
  > with a budget ceiling and monthly burn reporting as a safer alternative.
- **Is there a budget envelope or target range?** (Knowing this helps scope options honestly — we recommend sharing a range rather than a fixed number)
- **Time constraints:**
- **Technical constraints:**
- **Regulatory constraints:**
- **Team size / skill constraints:**
- **Organizational constraints:**
  - Procurement / approval lead times:
  - Change Advisory Board (CAB) requirements:
  - Deployment windows / blackout periods:
  - Cross-team dependencies that could block progress:

### 12.2 Assumptions
- **Technical assumptions:**
- **Business assumptions:**


## 13. Future Considerations

> → Maps to: **§13 Recommended Next Steps**, **§19 Feature Breakdown**

### 13.1 Roadmap
- **Planned features for future releases:**
- **Technology migration plans:**
- **Scaling plans:**

### 13.2 Technical Debt
- **Known technical debt:**
- **Refactoring plans:**


## 14. Options & Decision Factors

> → Maps to: **§10 Options Comparison**, **§11 Option Detail**

- **Are there already identified solution options to compare?**
  - Option 1:
  - Option 2:
  - Option 3:

- **What criteria matter most for option evaluation? (rank 1-5)**
  - Time to market:
  - Total cost:
  - Scalability:
  - Feature completeness:
  - Operational risk:
  - Team expertise fit:

---

## 15. Unanswered Questions → Architectural Implications

> → Maps to: **§12 Assumptions**, **§10 Options Comparison**
>
> Every unanswered question is a hidden architectural risk. Map them explicitly
> so stakeholders see the cost of delayed decisions.

| # | Unanswered Question | Assumed Answer | If Assumption Wrong → Impact | Decision Needed By |
|---|---------------------|----------------|------------------------------|--------------------|
| 1 |                     |                |                              |                    |
| 2 |                     |                |                              |                    |
| 3 |                     |                |                              |                    |

> 💡 "A TBD in the questionnaire becomes a risk in the design and a surprise in the invoice."

---

## Additional Notes

**Any other information that would be helpful for the architecture design:**




---

**Questionnaire completed by:** _________________
**Date:** _________________
**Version:** 3.0
