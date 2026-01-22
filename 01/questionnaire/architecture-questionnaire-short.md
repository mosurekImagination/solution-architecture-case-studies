# Solution Architecture Questionnaire - SHORT VERSION
**For Client Meetings**

---

## 1. Business Overview

**Project:** Tourist Mobile Application  
**Domain:** AI-Powered Tourism & Attraction Discovery  
**Key Problem:** Users discover and learn about nearby attractions using AI-powered photo recognition, replacing manual ChatGPT/Wikipedia searches. Connects tourists with partner businesses for monetization.

**Business Goals:**
- Generate revenue through partner commissions (10-20% on transactions)
- Generate revenue through partner advertising
- Scale globally (Klook/Viator level: 50M+ users potential)
- Achieve 95% accuracy in attraction information
- Build partnership ecosystem for tourists + local businesses

---

## 2. Core Features

**MVP Phase (4 months):**
- AI photo recognition of attractions (text + audio descriptions)
- Partner recommendations near attractions
- User accounts (social login + email/password)
- Offline caching & favorites
- Deploy to US + China simultaneously

**Phase 2 (Full Features, 7 months):**
- Payment integration (Stripe) for tickets/tours
- Loyalty program with QR codes
- Partner self-service portal
- User ratings & trip stories
- Multi-language support

**Future (Year 2+):**
- ML-based personalization
- Database sharding for scale
- Full microservices architecture
- White-label solution for tourism boards

---

## 3. Key Requirements

| Category | Requirement |
|----------|-------------|
| **Users** | Start: 1k (Year 1) → 10k (Year 2) → 100k (Year 3) → Scale: 50M+ |
| **Uptime** | 99.9% SLA (~43 min downtime/month) |
| **Response Time** | <3 seconds for all user-facing operations |
| **AI Accuracy** | 95% for attraction recognition |
| **Regions** | US + China from Day 1; EU/APAC by Year 2-3 |
| **Offline Mode** | Core features work without internet |
| **Compliance** | PCI-DSS (payments), GDPR-ready, China data residency |

---

## 4. Technology Stack (Recommended)

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI (Python) or NestJS (Node.js) - Modular Monolith |
| **Mobile** | Swift (iOS) + Kotlin (Android) - Native |
| **AI Recognition** | Google Vision API → OpenAI GPT-4 Vision → Google Gemini (fallbacks) |
| **Database** | PostgreSQL + PostGIS (geolocation queries) |
| **Cache** | Redis (ElastiCache) |
| **Storage** | AWS S3 for photos + static assets |
| **Cloud** | AWS (US + China regions) |
| **CDN** | CloudFront (global) + Alibaba Cloud CDN (China) |
| **Payments** | Stripe |
| **Auth** | AWS Cognito or Auth0 |
| **Monitoring** | DataDog + Sentry |

---

## 5. Architecture Pattern

**Hybrid Approach:**
- **Modular Monolith** for core app (user mgmt, partner mgmt, payments, loyalty)
  - Simpler deployment & ops initially
  - Clear boundaries for future microservices extraction
- **Separate AR Microservice** for photo recognition
  - Independent scaling based on photo upload volume
  - Isolated expensive AI API calls
- **Migration Path:** Extract to full microservices by Year 2-3 as traffic grows

---

## 6. Budget Options Summary

| | **Option 1** | **Option 2** (⭐ RECOMMENDED) | **Option 3** | **Option 4** |
|---|---|---|---|---|
| **CAPEX** | $224k | $719k | $2.17M | +$1.22M (migration) |
| **Monthly** | $835 | $1,810-$2,260 | $4,665 | $130k |
| **Total Year 1** | $618k | $1.74M | $4.59M | $10.8M+ |
| **Timeline** | 4 mo | 4-7 mo | 10 mo | 4-5 years |
| **Features** | MVP only | MVP + Full | Complete | 50M+ scale |
| **Regions** | US only | **US + China** | US+China+EU | Global |
| **Risk** | High | Medium | Low | Long-term investment |
| **Team Size** | 5 people | 8 people | 16 people | 60+ people |

**Option 2 Recommendation Rationale:**
- Balanced cost/features ratio
- US + China from Day 1 (major markets)
- Architecture built to scale without major refactoring
- Market validation before full investment
- Can iterate based on user feedback

---

## 7. AI Strategy (Hybrid Multi-Provider)

```
User uploads photo
    ↓
Google Vision API (Fast landmark detection)
    ↓
Found landmark → OpenAI GPT-4 Vision (Primary LLM)
    ↓
OpenAI fails → Google Gemini (Fallback LLM)
    ↓
Both fail or offline → On-device ML model (70-80% accuracy)
    ↓
Return result + Cache for future
```

**Why:** Cost optimization + resilience + offline capability + 95% target accuracy

---

## 8. Deployment Strategy

**Cloud:** AWS (Primary: us-east-1, Secondary: cn-north-1)  
**Deployment Method:** Canary Deployment (5% → 25% → 50% → 100% over 24-48 hours)  
**Infrastructure as Code:** Terraform or CloudFormation  
**CI/CD:** GitHub Actions + Docker containers  
**Container Orchestration:** ECS Fargate (Year 1) → EKS Kubernetes (Year 2+)

---

## 9. Key Decisions & Trade-offs

| Decision | Why |
|----------|-----|
| **Modular Monolith vs Microservices** | Start simple, extract as you grow. Microservices overhead not justified for small team. |
| **PostgreSQL** | ACID guarantees for payments + PostGIS for geosearch + JSONB for flexibility > scaling complexity. |
| **Multi-LLM Fallback Chain** | No single AI provider 100% reliable. Hybrid approach ensures service availability. |
| **Separate AR Microservice** | Photo processing is stateless + compute-intensive. Needs independent scaling. |
| **US + China from Day 1** | Option 2 adds only ~$30k vs Option 1, but opens major market. Worth it. |
| **Native Mobile** | Swift/Kotlin perform better than React Native for camera-heavy app. Photography is core. |
| **On-Device ML Models** | Enable offline features + reduce cloud API costs + improve privacy (user choice). |

---

## 10. Risks & Mitigation

| Risk | Mitigation |
|------|-----------|
| **OpenAI API blocked in China** | Use Google Gemini as primary for China region. Have on-device fallback. |
| **AI accuracy <95%** | Build training dataset during dev. User feedback loop. Continuous tuning. |
| **Scale beyond DB capacity** | Plan sharding strategy early (Phase 2). PostgreSQL scales to 100k+ users with proper indexing. |
| **Payment processing failures** | Stripe retry logic + SQS queue for async processing. 99.99% success rate. |
| **Regulatory changes** | GDPR/CCPA ready from Day 1 (easier to add than retrofit). China residency = separate infra. |
| **Market doesn't adopt** | Option 1 lowest risk. Option 2 adds US+China for minimal cost. Can pivot. |

---

## 11. Success Metrics

**Technical:**
- 95%+ attraction recognition accuracy
- <3 second API response time (p95)
- 99.9% uptime
- >80% cache hit ratio

**Business:**
- 1,000 users Year 1
- 10,000 users Year 2
- 100,000 users Year 3
- 20%+ conversion rate (user → purchase)
- 10-20% user retention (Day 7)

**Partnership:**
- 100 partners Year 1
- 1,000 partners Year 2
- 10,000+ partners by Year 3

---

## 12. Next Steps

1. **Approve budget option** (recommend Option 2)
2. **Confirm team size** (recommend 8 people for Option 2)
3. **Select technology stack** (approve recommended Python/Swift/Kotlin or propose alternatives)
4. **Agree on timeline** (MVP in 4 months, full features in 7 months)
5. **Define success metrics** (confirm KPIs above)
6. **Allocate resources & start hiring**
7. **Week 1: Requirements gathering & design sprints**
8. **Week 2: Infrastructure setup (AWS, CI/CD, databases)**
9. **Week 3: Sprint 1 begins (backend API + mobile shell)**

---

**Meeting Date:** January 22, 2026  
**Prepared by:** Solution Architecture Team  
**Full Questionnaire:** Available in `architecture-questionnaire.md`  
**Detailed Breakdown:** See cost section for line-item budget analysis
