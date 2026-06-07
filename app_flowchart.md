# OsteoAI Application Flowchart

This document provides a detailed technical architecture and user flow for the **OsteoAI** platform.

## 1. System Overview

The application is built on a **Flask (Python)** backend, a **MongoDB Atlas** database, and a **Vanilla JS/CSS/HTML** frontend with a focus on premium aesthetics and AI-driven clinical insights.

## 2. Technical Architecture Flow

```mermaid
graph TD
    %% Nodes
    User((User))
    Web[Frontend: HTML/CSS/JS]
    Flask[Flask Backend: api.py]
    Auth[Auth Handler: auth.py]
    DB[(MongoDB Atlas)]
    CSV[(Local Storage: data.csv)]
    
    subgraph AI_Intelligence_Layer [AI Intelligence Layer]
        ML[Ensemble ML: LR + RandomForest]
        Gemini[Google Gemini API: Medicine Decoding]
        DL[Deep Learning: MobileNetV2 X-ray Model]
    end

    %% Flow
    User -->|Interacts| Web
    Web -->|POST /login| Flask
    Flask -->|Verify Credentials| Auth
    Auth <-->|Query| DB

    Web -->|POST /predict| Flask
    Flask -->|Normalize Data| ML
    Flask -.->|Analyze Meds| Gemini
    Flask -->|Store Result| DB
    Flask -->|Append Row| CSV
    
    Web -->|POST /analyze-xray| Flask
    Flask -->|Process Image| DL
    
    Flask -->|Return JSON| Web
    Web -->|Display Results| User
```

## 3. Detailed User Journey

```mermaid
sequenceDiagram
    participant U as User / Patient
    participant F as Frontend (OsteoAI UI)
    participant B as Backend (Flask)
    participant G as Gemini AI
    participant M as ML Models
    participant D as Doctor Dashboard

    %% Registration
    U->>F: Register / Login
    F->>B: Auth Request
    B-->>F: JWT / Success Session

    %% Risk Assessment
    U->>F: Fill Clinical Metrics Form
    U->>F: (Optional) Upload X-ray
    F->>B: Send Data & Image
    
    par Clinical Analysis
        B->>M: Process Metrics (Ensemble)
        M-->>B: Risk Probability %
    and Medication Insight
        B->>G: Medication Name
        G-->>B: Bone Health Risks
    and Image Analysis
        B->>M: CNN (MobileNetV2)
        M-->>B: Scan Result (Normal/Osteopenia)
    end
    
    B-->>F: Consolidated Health Report
    F->>U: Show Dashboard & Recommendations

    %% Appointment
    U->>F: Book Appointment
    F->>B: Store Appointment
    B-->>D: Update Doctor UI (Real-time)
```

## 4. Component Interactions

| Component | Responsibility | Technologies |
| :--- | :--- | :--- |
| **Logic** | Core system orchestration | Flask, Python |
| **Prediction** | Clinical risk evaluation | Scikit-Learn (LR, RF) |
| **Vision** | X-ray analysis | PyTorch, MobileNetV2 |
| **Medication** | Medication hazard detection | Google Gemini API (Pro) |
| **Storage** | User data & History | MongoDB Atlas, CSV |
| **UI/UX** | Patient & Doctor Portals | CSS Grid/Flexbox, Glassmorphism |

---

> [!TIP]
> Each prediction is backed by an **Ensemble Engine** that averages probabilities from multiple models to ensure high-confidence results (currently ~92.5% accuracy).
