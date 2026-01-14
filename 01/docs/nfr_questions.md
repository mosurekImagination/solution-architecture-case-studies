# Non-Functional Requirements (NFR) Guide for Stakeholders

This document translates technical "Quality Attributes" into business decisions. For each area, we present the question, what it means for the user, and the trade-offs involved.

TOP 1 option: 1  second
TOP 3 options: 3 seconds
everything should appear with

1. Information about object (attractions stream) - ideally in parallel
2. Suggestions screen (immediately) - ideally in parallel

## 1. Performance & Latency

### Question: "How fast must the audio description start after taking a photo?"
*   **Description**: The delay between the user pressing "Shutter" and hearing the voice.
*   **Option A: Real-Time (< 3 seconds)**
    *   *Benefit:* Feels magical and conversational. High user engagement.
    *   *Disadvantage:* Extremely difficult with heavy AI models. Limits us to "smaller/dumber" AI or very expensive hardware.
    *   *Cost:* **High** (Requires specialized "GPU Inference" servers).
*   **Option B: Near-Real-Time (5-10 seconds)**
    *   *Benefit:* Allows usage of the smartest AI models (GPT-4) for better descriptions. Cheaper.
    *   *Disadvantage:* User has to wait; might get bored.
    *   *Cost:* **Medium/Low**.

You don't get options from technical
- use queue or direct requests

2 types of clients:
- we always want to be correct (LLM)
- ignore (blockchain transactions)
- clash in technicalities

correctnes 96% of higher. 
we should agree on dataset
you are here to advise,

Suggestions retained

### Question: "How should the app behave on slow networks (3G/Remote areas)?"
*   **Description**: What happens when a user is hiking and has 1 bar of signal.
*   **Option A: Aggressive Compression** (Upload blurry photo)
    *   *Benefit:* Works almost anywhere.
    *   *Disadvantage:* AI might miss details because the image is blurry.
    *   *Cost:* **Low** (Low bandwidth).
*   **Option B: High Fidelity Only**
    *   *Benefit:* Highest accuracy descriptions.
    *   *Disadvantage:* App fails/times out in remote areas.
    *   *Cost:* **Medium** (High bandwidth costs).
*   **Option C: GPS-Based Text Fallback** (Skip the photo)
    *   *Benefit:* Works on extremely weak signals (2G/EDGE). Instant feedback.
    *   *Disadvantage:* Loses the "Vision AI" magic factor. User selects from "Nearby List" instead of taking photo.
    *   *Cost:* **Very Low**.

---

Application should always have some benefits for clients
- offline, cache mode
- local LLM


- you don't need to have second infrastructure hot, it just need to be prepared to spin up
- low latency in US and in China etc.

## 2. Availability & Reliability

### Question: "Does the app need to work seamlessly if our cloud provider has a massive outage?"
*   **Description**: Reliability target (Uptime).
*   **Option A: 99.9% (Standard Commercial)**
    *   *Meaning:* Down ~9 hours per year.
    *   *Benefit:* Standard industry practice. Lowest complexity.
    *   *Cost:* **Base Cost**.
*   **Option B: 99.99% (High Availability)**
    *   *Meaning:* Down ~50 minutes per year.
    *   *Benefit:* Critical for reputation if we have millions of users.
    *   *Cons:* Requires complex "Multi-Region" setup (e.g., servers in US AND Europe).
    *   *Cost:* **Double (2x)** the infrastructure cost.

- Can we have everything in airplane mode?
- small LLM locally

### Question: "What features must work in 'Airplane Mode'?"
*   **Description**: Offline capabilities.
*   **Option A: Online Only**
    *   *Benefit:* App is very lightweight and simple to build.
    *   *Disadvantage:* Useless without internet (bad for travelers without roaming).
    *   *Cost:* **Low** (Development time).
*   **Option B: "Smart" Offline** (Cache recent places/coupons)
    *   *Benefit:* Travelers can still use coupons they saved.
    *   *Disadvantage:* Complex to build "sync" logic.
    *   *Cost:* **High** (Development time + 30% more engineering effort).
*   **Option C: Full Regional Download** (Google Maps Style)
    *   *Benefit:* Best UX for travelers without data. Everything works offline.
    *   *Disadvantage:* Large app size (hundreds of MBs). Complex "Sync Engine" required to keep data fresh.
    *   *Cost:* **Very High** (Significant engineering effort).

---

starting small,
milions of users
## 3. Scalability (Handling Success)

### Question: "Do we pay to keep capacity waiting for users, or do we wait for users to arrive?"
*   **Description**: Auto-scaling strategy.
*   **Option A: Reserved Capacity** (Always on)
    *   *Benefit:* No "cold starts" (app is always fast).
    *   *Disadvantage:* We pay for servers even at 3 AM when nobody is using them.
    *   *Cost:* **Medium/High** (Predictable but wasteful).
*   **Option B: Serverless / Auto-scale**
    *   *Benefit:* Pay $0 if nobody uses the app.
    *   *Disadvantage:* The first user after a quiet period might wait 5-10 seconds ("Cold Start").
    *   *Cost:* **Variable** (Cheapest for low usage, expensive for massive usage).

---

- recommendation systems
- credit cards 
- loyality programs
- personal invormations in applicaiton 

## 4. Security & Compliance

### Question: "How strictly must we protect the data?"
*   **Description**: Encryption and Audit requirements.
*   **Option A: Standard Cloud Security**
    *   *Benefit:* Secure enough for 99% of non-banking apps. Implementation is fast.
    *   *Cost:* **Low** (Built-in).
*   **Option B: Enterprise Grade (Customer Managed Keys + 7-year Audit Log)**
    *   *Benefit:* Required if we sell to governments or handle highly sensitive data.
    *   *Disadvantage:* Significant operational overhead.
    *   *Cost:* **Very High** (Ongoing management costs).

---

Start Europe and US and then increase forward

Translatio

## 5. Locality (Global Ambitions)

### Question: "Do we serve everyone from one location, or move servers close to users?"
*   **Description**: Hosting strategy (e.g., hosting in US vs. US + Europe + Asia).
*   **Option A: Single Region (e.g., US-East)**
    *   *Benefit:* Simple data management.
    *   *Disadvantage:* Users in Asia will have a 1-second delay on every click.
    *   *Cost:* **Low**.
*   **Option B: Global Edge Deployment**
    *   *Benefit:* Fast everywhere.
    *   *Disadvantage:* Data synchronization is a nightmare (GDPR issues).
    *   *Cost:* **High** (Complex data architecture).
