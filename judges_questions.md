# Hackathon Q&A Prep: OsteoAI 🦴

This guide outlines the most likely questions judges will ask, categorized by focus area, with suggested "Winning Answers."

## 1. Technical & ML Questions 🧠
**Q: Why did you choose an Ensemble model (LR + RF) instead of just using one high-performing algorithm?**
*   **Winning Answer**: "We used an Ensemble approach because Logistic Regression provides great interpretability (showing how each factor contributes), while Random Forest captures non-linear relationships. By combining them, we achieved a more robust 92.5% accuracy that reduces the variance an individual model might have."

**Q: Your X-ray validation accuracy is ~73%. How do you plan to improve this for a clinical setting?**
*   **Winning Answer**: "The current accuracy is a baseline using preliminary data. In a real-world phase, we would implement **Data Augmentation** (flipping, rotating images) and use **Class Weighting** to handle data imbalance. We would also move from MobileNetV2 to more specialized architectures like **DenseNet-121**, which is state-of-the-art for medical imaging."

---

## 2. Product & UX Questions 🎨
**Q: How does a user know they can trust the result? AI in healthcare is sensitive.**
*   **Winning Answer**: "Trust is built through transparency. Our UI doesn't just give a 'Yes/No'—it provides a **Risk Percentage** and a **Confidence Interval**. We also integrated a clear disclaimer that this is a screening tool, not a diagnosis, and we provide a 'Find Nearby Hospitals' feature to bridge the gap between AI insight and professional medical consultation."

**Q: What is the unique value proposition compared to a standard online health calculator?**
*   **Winning Answer**: "Standard calculators are static. OsteoAI is **Dynamic**. We combine tabular health data with **Active Computer Vision (X-rays)** and **Real-time GenAI (Gemini)** to analyze medications. This multi-modal approach provides a depth of analysis that a simple form-based calculator cannot match."

---

## 3. GenAI & Architecture Questions ⚡
**Q: Why use Google Gemini? Could you have just used a hardcoded list of high-risk medicines?**
*   **Winning Answer**: "Hardcoded lists go out of date. New medications are released constantly. By using **Gemini**, we leverage a massive, updated knowledge base that can identify *compound* medication risks and even analyze the *interactions* of multiple medicines the user might be taking, which is impossible with a static list."

**Q: How do you handle cases where there is no internet connection for the Gemini API or MongoDB?**
*   **Winning Answer**: "We built a **'Hackathon Mode'** with robust local fallback. If the cloud connection fails, the system automatically switches to a local Mock Database and uses a pre-cached offline dictionary of high-risk medication keywords to ensure the user still gets a core assessment."

---

## 4. Scalability & Future 🚀
**Q: How would you scale this to be used by a government health department?**
*   **Winning Answer**: "Our architecture is **Modular**. The ML models are served as independent API endpoints. We use **MongoDB Atlas**, which allows for horizontal scaling (sharding) as the user base grows. For a government rollout, we would focus on **HIPAA/GDPR compliance** and integrate directly with existing EHR (Electronic Health Record) systems via FHIR standards."

**Q: What is your plan for data privacy?**
*   **Winning Answer**: "Security is baked in. We use **Environment Variables** for all API keys, and user authentication is handled via **Scrypt hashing**. In the next phase, we would implement **On-Device ML** (using TensorFlow Lite) so that sensitive X-ray data never even has to leave the user's phone for analysis."

---

## Pro-Tips for the Interview:
1.  **Mention Accuracy**: Always keep your "92.5% accuracy" figure ready.
2.  **Demo the Fallback**: If the internet is slow, proudly mention your "Local Fallback/Mock DB" logic—judges love "edge-case" thinking.
3.  **Human-in-the-Loop**: Remind them that the AI's goal is to *assist* doctors, not replace them.
