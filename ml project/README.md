# OsteoAI - Advanced Bone Health Analytics 🦴

OsteoAI 2.0 is a deep-tech healthcare platform that leverages dual-mode AI to predict and screen for Osteoporosis risks using clinical data and X-ray imaging.

## 🚀 Key Features (v2.0)
- **AI X-ray Analysis**: Multi-Model CNN Ensemble (MobileNetV2, ResNet-50, DenseNet-121) for high-accuracy, consensus-based bone density assessment.
- **AI Consensus Verification**: Transparent diagnostic deep-dive exposing individual CNN model predictions for doctor verification.
- **Diagnostic History Tracking**: Secure MongoDB logging of past clinical and X-ray assessments for longitudinal patient review.
- **Doctor & Admin Dashboards**: Dedicated administrative portals for reviewing global patient data and system health metrics.
- **IoT Healthcare Dashboard**: ESP32-based smart clinical environment monitoring (Temperature, Humidity, Motion) and hardware automation.
- **Ensemble Risk Prediction**: High-performance combination of **Logistic Regression** and **Random Forest** (92.5% accuracy).
- **Gemini AI Integration**: Uses Google Gemini to analyze medication names and provide real-time clinical insights and risk adjustments.
- **Patient Clustering**: K-Means unsupervised learning for automated risk segmentation.
- **Production-Ready Architecture**: 
  - **Waitress WSGI**: High-stability server for production environments.
  - **Hackathon Mode**: Built-in automatic fallback to Mock DB if cloud connection is unavailable.
  - **Environment Security**: Sensitive keys managed via `.env` files.

## 🛠 Tech Stack
- **Frontend**: HTML5, CSS3 (Glassmorphism), JavaScript (Vanilla)
- **Backend**: Python (Flask)
- **AI/ML**: PyTorch (CNN), Scikit-learn (Ensemble), Google Gemini (LLM)
- **Persistence**: MongoDB Atlas & Local CSV Logging

## 📊 Application Flow
```mermaid
graph TD
    %% Entry Point
    A["User (Browser)"] --> B{"Login / Signup"}
    
    %% Auth Flow
    B -- "Auth Request" --> C["Flask API (/login, /register)"]
    C -- "Verify" --> D[("MongoDB Atlas / Mock DB")]
    D -- "Success" --> E["Landing Page (Dashboard)"]
    
    %% Main Paths
    E --> F{"Choose Analysis Type"}
    
    %% Path 1: Clinical Data
    F -- "Tabular Data" --> G["Clinical Risk Form"]
    G -- "POST /predict" --> H["Flask Backend"]
    
    subgraph "Clinical Analysis Engine"
        H --> I["Pre-processing & Scaling"]
        I --> J["Ensemble Model (LR + RF)"]
        H -- "Medicine Info" --> K["Gemini AI (Clinical Insights)"]
    end
    
    J --> L["Risk Score & Recommendations"]
    K --> L
    L --> M["Update UI (Progress Bars)"]
    L -- "Save" --> N[("data/data.csv")]
    
    %% Path 2: X-ray Analysis
    F -- "Image Upload" --> O["X-ray Analysis Section"]
    O -- "POST /analyze-xray" --> P["Flask Backend"]
    
    subgraph "Image Analysis Engine"
        P --> Q["Image Pre-processing"]
        Q --> R["Multi-Model CNN Ensemble"]
        R --> R1["MobileNetV2"]
        R --> R2["ResNet-50"]
        R --> R3["DenseNet-121"]
        R1 & R2 & R3 --> R4["Consensus Verification Engine"]
    end
    
    R4 --> S["Classification & Confidence"]
    S --> T["Update UI (Result Card)"]
    
    %% Final Actions
    M --> U["Find Nearby Hospitals"]
    T --> U
    U --> V["hospitals.html"]
```

## 📦 Project Structure
```text
├── data/                    # Local datasets (CSV & X-ray)
├── models/                  # Trained ML/DL model weights
├── src/                     # Core training & evaluation scripts
├── image_analysis/          # X-ray training & inference logic
├── landing_page/            # Web frontend (UI/UX)
├── ../admin_dashboard/      # Doctor & Admin Portal (Separate service)
├── ../iot_dashboard/        # ESP32 Smart Infrastructure Monitoring
├── api.py                   # Main Flask API
├── wsgi.py                  # Production server entry point
└── results.txt              # Performance history & logs
```

## 🛠 Installation & Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run in Production Mode (Recommended):**
   ```bash
   python wsgi.py
   ```

3. **Run in Development Mode:**
   ```bash
   python api.py
   ```
   The app will be available at `http://localhost:8000`.

## 📊 Performance Summary
- **Ensemble Accuracy**: 92.5% (Full Dataset)
- **X-ray Val Acc**: 72.82% (Preliminary Training)

## ⚖️ Disclaimer
This project is an AI-based screening tool and should not be used in place of professional medical advice or clinical diagnosis.
