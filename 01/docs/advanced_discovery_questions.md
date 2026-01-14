# Advanced Product Discovery & Architecture Questions

This document contains "deep dive" questions that go beyond the basics. These demonstrate senior-level architectural thinking by uncovering hidden risks in compliance, operations, and long-term maintenance.

## 1. Compliance, Legal & Regional (The "Global" Trap)
*   **GDPR & Data Residency:** Since the app has "Global Ambitions", do we need to store European user data in EU data centers? (Impacts: Multi-region architecture vs single global region).
*   **Right to be Forgotten:** If a user requests deletion, how do we scrub their data from the "Partner Discount" history if that data has already been shared with third-party partners?
*   **Accessibility (WCAG):** Are there specific legal requirements for accessibility? (e.g., The "Voice-over" feature suggests a strong use case for visually impaired users. Do we need a "High Contrast" UI for the partner marketplace?)

## 2. Analytics & Data Strategy
*   **The "Data Lake" Question:** Are we just building an app, or are we building a data platform? Is the *real* value the map of "where tourists go"?
    *   *Follow-up:* Do we need to capture "failed" photos (what users tried to photograph but failed) to improve future models?
*   **Conversion Tracking:** How do we prove to partners that *we* sent the customer?
    *   *Deep Dive:* If a user sees the recommendation but doesn't scan the QR code (just pays cash), do we lose attribution? Do we need "Geo-fenced verification" (User was at location for > 15 mins)?

## 3. Operational Maturity & SLOs
*   **Degraded State:** If the LLM provider is down (e.g., OpenAI outage), does the entire app crash? Or do we fallback to a "ReadOnly" mode where users can still see their history and map?
*   **Support & Admin:** Who handles "Bad Data" reports? (e.g., User reports "This restaurant is closed"). Do we need an "Admin Dashboard" for operations staff to manually disable partners or override descriptions?

## 5. Security - Advanced Vectors
*   **Jailbroken Devices:** Do we allow the app to run on rooted/jailbroken devices? (Risk: Users could spoof GPS to unlock discounts for expensive vineyards while sitting at home).
*   **Content Safety:** What if a user takes a photo of something illegal or inappropriate and asks for a description? Does the LLM need a "Safety Filter" layer before generating audio?

## 6. Development Logistics
*   **Beta Testing:** Do you have an existing pool of beta testers (e.g., "power tourists"), or is setting up a TestFlight/Beta program part of our scope?
*   **App Store Management:** Who owns the Apple/Google Developer accounts? Do we need to manage the submission and review process (which can take days)?
