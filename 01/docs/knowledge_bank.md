# Software Solution Architect Knowledge Bank & Strategy

This document serves as a knowledge base and strategic guide for the "Mobile Tourist Application" assignment. It covers the approach, architectural patterns, and best practices relevant to this specific problem.

## 1. Assignment Deconstruction & Strategy

### The Core Challenge
You are building a **multimodal AI application** (Image + Location -> Text + Audio + Recommendations) with a **two-sided marketplace component** (Tourists vs. Partners).

### Recommended Phased Approach

#### Phase 1: Discovery (The "Questions" Part)
Don't just ask random questions. Group them by "Risk" and "ambiguity".
*   **The "Magic" Box**: How exactly does the image recog work? DO NOT assume it's one magical API.
    *   *Question Strategy:* Ask about latency requirements vs. accuracy. Real-time vision on phone vs. Cloud processing?
*   **The Partner Ecosystem**: How do partners verify the QR code? Do they need a separate app?
    *   *Question Strategy:* Ask about the "Partner Portal" and "Scanner App" requirements.
*   **Monetization & Constraints**: Who pays for the LLM tokens?
    *   *Question Strategy:* Ask about cost per user interaction limits.

#### Phase 2: Solution Design
Use a standard architectural framework (like C4 Model) to structure your thinking.
1.  **Context**: Mobile App <-> Cloud Backend <-> 3rd Party AI <-> Partners.
2.  **Container**: API Gateway, Auth Service, Content Service, Partner Service.
3.  **Component**: Detailed breakdown of the "Image Processing Pipeline".

---

## 2. Key Architectural Patterns for this Solution

### A. The "Vision-to-Voice" Pipeline
*Pattern: Asynchronous Event-Driven Processing*
Direct HTTP request/response might be too slow for heavy image processing + LLM generation + TTS (Text-to-Speech).
*   **Mobile App** uploads image to Object Storage (S3/GCS) -> Returns "Job ID".
*   **Analysis Service** triggers on upload -> Calls Vision API (Google Lens/AWS Rekognition) to get "Tags" (e.g., "Eiffel Tower").
*   **Context Service** takes Tags + User Location -> Queries "Partner DB" for nearby deals.
*   **LLM Service** combines Tags + Partner Deals -> Generates natural language description.
*   **TTS Service** converts text to audio.
*   **Mobile App** polls or receives Push Notification when ready.
*   *Trade-off:* Async is complex UI but robust. Sync is simple user flow but high latency risk.

### B. Geo-Spatial Search (The "Near Me" Problem)
*Pattern: Geo-Hashing or Spatial Indexing*
*   Partners need to be found within a radius of the attraction.
*   **Technology**: PostGIS (PostgreSQL), Redis Geo, or Cloud Native (DynamoDB/CosmosDB with Geo libraries).
*   *Optimization:* Cache "Static Attractions" (Eiffel Tower doesn't move), but "Partners" might be dynamic.

### C. Partner Verification (The "Discount" System)
*Pattern: Signed Tokens (JWT)*
*   User App shows QR Code. What is in the QR code?
*   **Secure Approach**: The QR code contains a signed JWT with `user_id`, `deal_id`, and `expiration`.
*   **Partner App**: Scans QR, verifies signature offline or calls backend to mark "redeemed" to prevent replay attacks.

---

## 3. Best Practices for Solution Architects

### NFRs (Non-Functional Requirements) are King
Beginners focus on features. Architects focus on:
*   **Latency**: Users won't wait 30s for an answer. (Target < 3s? < 5s?)
*   **Cost**: LLM calls are expensive. Caching is mandatory. (Cache "Eiffel Tower" description globally, don't regenerate it for every tourist).
*   **Scalability**: What happens during the Olympics? Serverless/Auto-scaling groups.

### The "Buy vs. Build" Decision
*   **Don't build**: Custom object detection models (unless specifically required). Use off-the-shelf APIs (OpenAI GPT-4o, Google Gemini Pro Vision, AWS Rekognition).
*   **Do build**: The proprietary logic that matches "Attraction Context" with "Partner Inventory". That's the business value.

### Diagramming Standards (C4 Model)
*   **Level 1 (System Context)**: Who uses it? (Tourist, Partner). What external systems? (Maps API, Vision API, Payment Provider).
*   **Level 2 (Container)**: Mobile App (Flutter/React Native), Backend API, Database, Worker Queues.
*   **Level 3 (Component)**: Inside the backend—Controller, Service, Repository layers.

---

## 4. Draft Questions for Part 1 (Starter Pack)
Use these to inspire your "Questions" deliverable.

1.  **Operational**: "Do partners require a dedicated interface/app to scan QR codes and manage their profiles, or is that out of scope?" (Implies a whole separate frontend).
2.  **Commercial**: "Is the partner recommendation purely geo-based (closest), or is there a bidding/priority system for premium partners?" (Impacts database design).
3.  **Technical**: "What is the acceptable latency for the description response? Real-time conversation (<1s) or 'processing' state allowed (5-10s)?" (Decides Sync vs Async arch).
4.  **Edge Case**: "How should the system handle photos where no clear landmark is identified? Fallback to generic location info or error out?"
