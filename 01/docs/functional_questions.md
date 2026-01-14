# Functional Requirements (Feature) Options

This document outlines key *behavioral* choices for the application. These define the user experience and feature set.

## 1. Core Experience: Image Capture
### Question: "How 'magical' should the object detection be?"
*   **Description**: Should the app guess what the user is looking at, or ask for help?
*   **Option A: Fully Autonomous (Point & Shoot)**
    *   *Benefit:* True "Magic Lens" experience. Minimal friction for the user.
    *   *Disadvantage:* Higher error rate if scene is cluttered (e.g., photo of a street with 5 shops).
    *   *Cost:* **High** (Complex tuning of AI models).
*   **Option B: User-Assisted (Tap to Focus / Crop)**
    *   *Benefit:* Much higher accuracy. User clarifies intent ("I want the statue, not the building").
    *   *Disadvantage:* More clicks required.
    *   *Cost:* **Low** (Offloads complexity to user).

## 2. The "Voice-Over" Experience
### Question: "How does the audio guide behave?"
*   **Description**: The style of the generated description.
*   **Option A: Standard "Wikipedia" Summary**
    *   *Benefit:* Safe, factual, consistent.
    *   *Disadvantage:* Boring. Feels like reading a textbook.
    *   *Cost:* **Low** (Simple prompting).
*   **Option B: "Persona" Mode (Tour Guide)**
    *   *Benefit:* Fun, engaging (e.g., "Hi! I'm Napoleon, let me tell you about this arch...").
    *   *Disadvantage:* Risk of hallucinations or inappropriate jokes.
    *   *Cost:* **Medium** (Complex prompt engineering & testing).

## 3. Partner Discovery (The Ads)
### Question: "How aggressive are the partner recommendations?"
*   **Description**: When do we show the "Coffee Shop nearby"?
*   **Option A: Contextual Only (After Scan)**
    *   *Benefit:* Non-intrusive. "Since you're at Eiffel Tower, here is a café."
    *   *Disadvantage:* Lower conversion rate (fewer ads shown).
    *   *Cost:* **Low**.
*   **Option B: Proactive Push (Geo-Fencing)**
    *   *Benefit:* High visibility. "You simply walked past a partner!"
    *   *Disadvantage:* Annoying. High battery usage (Background GPS).
    *   *Cost:* **High** (Complex mobile implementation).

## 4. Discount Redemption
### Question: "How secure must the coupon system be?"
*   **Description**: Preventing fraud (people using screenshots of coupons).
*   **Option A: Rotating QR Code (Banking Style)**
    *   *Benefit:* Impossible to screenshot/share. 100% accurate attribution.
    *   *Disadvantage:* Requires internet connection at the shop.
    *   *Cost:* **Medium**.
*   **Option B: Static "Show Screen"**
    *   *Benefit:* Works offline. Fast.
    *   *Disadvantage:* High fraud risk (screenshots shared in groups).
    *   *Cost:* **Very Low**.

## 5. User History
### Question: "Do we save the user's photos?"
*   **Description**: Storing the original images.
*   **Option A: Digital Scrapbook (Save everything)**
    *   *Benefit:* Users love revisiting their trip gallery. Sticky feature.
    *   *Disadvantage:* Massive storage costs. Privacy liability (GDPR).
    *   *Cost:* **High** (Storage fees).
*   **Option B: Flight Log (Save metadata only)**
    *   *Benefit:* Cheap. "You visited Eiffel Tower on July 14th" (Generic thumbnail).
    *   *Disadvantage:* Less personal.
    *   *Cost:* **Low**.
