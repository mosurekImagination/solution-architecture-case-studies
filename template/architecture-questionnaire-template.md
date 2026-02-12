# Solution Architecture Questionnaire

> **Purpose:** Gather requirements and context before creating a solution design.
> Answers feed directly into the [Solution Design Template](solution-design-template.adoc).
>
> **Instructions:** Fill in all relevant sections. Leave blank if unknown — mark with `TBD`.
> Section cross-references (→ §N) point to the corresponding solution design section.

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

### 1.3 Business Drivers
- **What business problem does this solution solve?**

- **What are the key business goals?**

- **How will success be measured? (KPIs)**


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
- **List the main features/functionalities:**
  1.
  2.
  3.

- **What are the primary user personas and their use cases?**
  - Persona 1:
  - Persona 2:

### 3.2 User Interactions
- **How will users interact with the system?** (Web, Mobile, Desktop, API, CLI, etc.)

- **What are the main user workflows?**

- **Are there any batch processing requirements?**


## 4. Non-Functional Requirements

> → Maps to: **§12 Quality Scenarios**, **§17 Observability & Monitoring**

### 4.1 Performance
- **Expected number of concurrent users:**

- **Response time requirements:**
  - API response time:
  - Page/App load time:
  - Background job completion time:

- **Peak load expectations:**

### 4.2 Scalability
- **Expected growth over time:**
  - Year 1:
  - Year 2:
  - Year 3:

- **Scaling strategy preference:** (Auto-scaling, Horizontal, Vertical)

- **Geographic distribution requirements:** (Regions, latency targets)

### 4.3 Availability & Reliability
- **Required uptime (SLA):**
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
- **Time constraints:**
- **Technical constraints:**
- **Regulatory constraints:**
- **Team size / skill constraints:**

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

## Additional Notes

**Any other information that would be helpful for the architecture design:**




---

**Questionnaire completed by:** _________________
**Date:** _________________
**Version:** 2.0
