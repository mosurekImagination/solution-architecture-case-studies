# Client Discovery Questions - Mobile Tourist Application

This document outlines the critical questions to ask the "client" to clarify scope, constraints, and technical requirements. They are categorized to help structure the Q&A session.

## 1. Core Product & Experience (The "Magic")
*   **Response Latency:** What is the maximum acceptable wait time from "Photo Taken" to "Audio Playing"? (e.g., Is < 3 seconds critical, or is < 10 seconds acceptable?)
*   **Vision Accuracy:** How should we handle "partial matches" or ambiguous images (e.g., a generic street in Paris)? Should the app guess based on location, or ask the user for clarification?
*   **Audio Quality:** Do we need standard text-to-speech (robotic is okay) or high-quality, neural-network-based voices (expensive, human-like)?
*   **Language Support:** Is the app English-only for MVP, or do we need multi-language support (translating descriptions on the fly)?

## 2. Partner Ecosystem (The Marketplace)
*   **Verification Flow:** How exactly does the "Discount System" work?
    *   *Option A:* Partner has a simple printed code they show the user?
    *   *Option B:* User shows app screen -> Partner visually verifies?
    *   *Option C:* Partner scans User's QR code with a dedicated "Partner App"? (This implies building a second app).
*   **Partner Onboarding:** How do partners get into the system? Is there a self-service portal (partners sign up themselves) or an internal admin tool (we manually enter them)?
*   **Recommendation Logic:** If 5 partners are nearby, which one do we show? Closest distance? Highest paid? Highest rated?

## 3. Technical Constraints & Infrastructure
*   **Cloud Preference:** Do you have an existing cloud provider preference (AWS vs Azure vs GCP) or existing credits we should use?
*   **LLM Choice:** Are there constraints on using public APIs (OpenAI/Anthropic) for processing user photos? (Privacy concerns?)
*   **Offline Capability:** Does the app need to work in areas with poor data service (e.g., remote hiking trails), or can we assume always-on internet?
*   **Image Storage:** Do we need to save user photos long-term (for training/history), or should they be processed and immediately discarded for privacy/cost?

## 4. Business & Operations (Cost vs. Value)
*   **Cost Per User:** processing an image + LLM analysis + Audio generation can cost $0.03 - $0.10 per interaction. Is this unit economy acceptable? Is there a monetization plan (Subscription/Eds) to offset this?
*   **Scale of Launch:** are we targeting 1,000 users or 1,000,000 users on day 1? (Influences "Serverless" vs "provisioned" architecture).
*   **Partner Revenue:** Do partners pay per click, per impression, or a flat monthly fee?

## 5. Security & Safety
*   **User Privacy:** How do we handle faces/license plates inadvertently captured in tourist photos? Do we need to blur them before sending to third-party AI APIs?
*   **Abuse Prevention:** What prevents a competitor or bot from sending 1,000,000 fake images to drain our API budget? (Rate limiting strategy).

## 6. Edge Cases
*   **Unknown Attractions:** What should the UI display if the AI cannot identify the landmark?
*   **No Partners Nearby:** If a user is at the Eiffel Tower but we have no signed partners, do we show nothing, or fallback to generic Google Maps places (non-partners)?
