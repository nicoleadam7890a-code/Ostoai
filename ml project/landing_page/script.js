// --- Logout Logic ---
function logoutUser() {
    localStorage.removeItem('username');
    localStorage.removeItem('email');
    localStorage.removeItem('token');
    window.location.href = '/';
}

document.addEventListener("DOMContentLoaded", () => {
    // Check for username and update greeting
    const username = localStorage.getItem('username');
    const isLoginPage = window.location.pathname === '/' || window.location.pathname.endsWith('login.html');
    
    if (username) {
        const assessBtn = document.getElementById('assess-risk-btn');
        if (assessBtn) {
            assessBtn.textContent = `${username}, let's access your risk →`;
        }
    } else if (!isLoginPage) {
        // If not logged in AND not already on the login page, redirect
        window.location.href = '/';
    }

    // Smooth scrolling for navigation links
    document.querySelectorAll('.nav-links a').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href && href.startsWith('#') && href !== '#') {
                e.preventDefault();
                const targetId = href.substring(1);
                const targetSection = document.getElementById(targetId);
                if (targetSection) {
                    window.scrollTo({
                        top: targetSection.offsetTop - 80,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

    // Launch App button logic - Remove default redirect and rely on smooth scroll
    const launchBtns = document.querySelectorAll('.btn-primary, .btn-glow');
    launchBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const targetId = btn.getAttribute('href');
            if(targetId && targetId.startsWith('#')) return; // handled by smooth scroll
        });
    });

    // --- Clinical Analysis Logic ---
    const clinicalForm = document.getElementById('clinical-form');
    const ageSlider = document.getElementById('age');
    const ageVal = document.getElementById('age-val');
    const clinicalResult = document.getElementById('clinical-result');
    const clinicalRiskFill = document.getElementById('clinical-risk-fill');
    const clinicalRiskVal = document.getElementById('clinical-risk-value');
    const clinicalVerdict = document.getElementById('clinical-verdict');
    const medInsightBox = document.getElementById('medication-insight');

    if (ageSlider && ageVal) {
        ageSlider.addEventListener('input', (e) => {
            ageVal.textContent = e.target.value;
        });
    }

    let currentClinicalData = null;
    let currentClinicalResult = null;

    if (clinicalForm) {
        clinicalForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = document.getElementById('clinical-predict-btn');
            submitBtn.textContent = 'Processing...';
            submitBtn.disabled = true;

            const formData = new FormData(clinicalForm);
            const data = Object.fromEntries(formData.entries());
            
            // Clean up numeric values
            data.age = parseInt(data.age);
            
            // Inject user email for history tracking
            const userEmail = localStorage.getItem('email');
            if (userEmail) data.user_email = userEmail;

            try {
                const response = await fetch('/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.status === 'success') {
                    // Store for report generation
                    currentClinicalData = { ...data };
                    currentClinicalResult = { ...result };

                    // Update UI
                    clinicalResult.style.display = 'block';
                    
                    // Animate risk bar
                    setTimeout(() => {
                        clinicalRiskFill.style.width = result.risk_score + '%';
                        clinicalRiskVal.textContent = result.risk_score + '%';
                    }, 100);

                    clinicalVerdict.textContent = result.prediction;
                    
                    if (result.prediction === 'High Risk') {
                        clinicalVerdict.style.color = '#ff5f56';
                    } else {
                        clinicalVerdict.style.color = '#27c93f';
                    }

                    // Medicine impact
                    if (result.medicine_impact && result.medicine_impact.category !== 'None') {
                        medInsightBox.style.display = 'block';
                        medInsightBox.innerHTML = `
                            <p><strong>Medication Insight:</strong> ${result.medicine_impact.insight}</p>
                            <small>Confidence penalty: ${result.medicine_impact.error_margin}%</small>
                        `;
                    } else {
                        medInsightBox.style.display = 'none';
                    }

                    // Scroll to result
                    clinicalResult.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    
                    // Refresh history
                    if (typeof fetchUserHistory === 'function') fetchUserHistory();

                } else {
                    alert('Clinical analysis failed: ' + result.message);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred during clinical analysis.');
            } finally {
                submitBtn.textContent = 'Analyze Clinical Risk →';
                submitBtn.disabled = false;
            }
        });
    }

    // --- Clinical Report Generator ---
    window.generateClinicalReport = function() {
        if (!currentClinicalResult || !currentClinicalData) {
            alert('Please run a clinical analysis first.');
            return;
        }

        const modal = document.getElementById('clinical-report-modal');
        const body = document.getElementById('clinical-report-body');
        modal.style.display = 'flex';

        const name = localStorage.getItem('username') || 'Patient';
        const email = localStorage.getItem('email') || 'N/A';
        const date = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
        const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        const refId = 'OAI-CL-' + Math.random().toString(36).substr(2, 9).toUpperCase();

        const d = currentClinicalData;
        const r = currentClinicalResult;
        const score = r.risk_score;
        const lr = r.details ? r.details.logistic_regression : score;
        const rf = r.details ? r.details.random_forest : score;

        const riskClass = score > 60 ? 'high' : (score > 35 ? 'moderate' : 'low');
        const riskLabel = score > 60 ? 'High Risk' : (score > 35 ? 'Moderate Risk' : 'Low Risk');
        const riskColor = score > 60 ? '#ef4444' : (score > 35 ? '#f59e0b' : '#22c55e');
        const riskBg = score > 60 ? '#fef2f2' : (score > 35 ? '#fffbeb' : '#f0fdf4');

        // Risk factor analysis
        const riskFactors = [];
        if (parseInt(d.age) > 50) riskFactors.push({ factor: 'Advanced Age', detail: `Age ${d.age} (>50 increases risk)`, severity: 'warning' });
        if (d.gender === 'Female') riskFactors.push({ factor: 'Female Gender', detail: 'Higher biological predisposition', severity: 'info' });
        if (d.hormonalChanges === 'Postmenopausal') riskFactors.push({ factor: 'Postmenopausal Status', detail: 'Estrogen decline accelerates bone loss', severity: 'warning' });
        if (d.familyHistory === 'Yes') riskFactors.push({ factor: 'Family History Positive', detail: 'Genetic predisposition identified', severity: 'warning' });
        if (d.bodyWeight === 'Underweight') riskFactors.push({ factor: 'Low Body Weight', detail: 'Reduced mechanical loading on bones', severity: 'warning' });
        if (d.calciumIntake === 'Low') riskFactors.push({ factor: 'Low Calcium Intake', detail: 'Insufficient bone mineral support', severity: 'critical' });
        if (d.vitaminDIntake === 'Insufficient') riskFactors.push({ factor: 'Vitamin D Deficiency', detail: 'Impaired calcium absorption', severity: 'critical' });
        if (d.physicalActivity === 'Sedentary') riskFactors.push({ factor: 'Sedentary Lifestyle', detail: 'Lack of weight-bearing exercise', severity: 'warning' });
        if (d.smoking === 'Yes') riskFactors.push({ factor: 'Active Smoking', detail: 'Accelerates bone density loss', severity: 'critical' });
        if (d.priorFractures === 'Yes') riskFactors.push({ factor: 'Prior Fractures', detail: 'History of skeletal compromise', severity: 'critical' });
        if (d.alcoholConsumption === 'Yes') riskFactors.push({ factor: 'Heavy Alcohol Use', detail: 'Inhibits osteoblast activity', severity: 'warning' });

        const protectiveFactors = [];
        if (d.calciumIntake === 'Adequate') protectiveFactors.push('Adequate Calcium Intake');
        if (d.vitaminDIntake === 'Sufficient') protectiveFactors.push('Sufficient Vitamin D');
        if (d.physicalActivity === 'Active') protectiveFactors.push('Active Lifestyle');
        if (d.smoking === 'No') protectiveFactors.push('Non-Smoker');
        if (d.priorFractures === 'No') protectiveFactors.push('No Prior Fractures');
        if (d.bodyWeight === 'Normal') protectiveFactors.push('Normal Body Weight');

        let recommendations = '';
        if (score > 60) {
            recommendations = `
                <li>Urgent consultation with an Orthopedic Specialist or Rheumatologist</li>
                <li>DEXA bone mineral density scan recommended within 2 weeks</li>
                <li>Comprehensive blood panel: Serum Calcium, 25-OH Vitamin D, PTH</li>
                <li>Begin calcium (1200mg/day) and Vitamin D3 (2000 IU/day) supplementation</li>
                <li>Discuss bisphosphonate therapy (e.g., Alendronate) with physician</li>
                <li>Implement fall-prevention strategies at home</li>
            `;
        } else if (score > 35) {
            recommendations = `
                <li>Schedule orthopedic screening within the next 1-3 months</li>
                <li>Baseline DEXA scan recommended for monitoring</li>
                <li>Increase calcium-rich foods (dairy, leafy greens, fortified foods)</li>
                <li>Vitamin D assessment and supplementation if indicated</li>
                <li>Begin regular weight-bearing and resistance exercises</li>
                <li>Follow-up reassessment in 6-12 months</li>
            `;
        } else {
            recommendations = `
                <li>Continue current healthy lifestyle practices</li>
                <li>Maintain calcium-rich diet and adequate vitamin D exposure</li>
                <li>Regular physical activity (weight-bearing exercises preferred)</li>
                <li>Routine bone health screening every 2 years after age 50</li>
                <li>Avoid smoking and excessive alcohol consumption</li>
            `;
        }

        const riskFactorRows = riskFactors.length > 0 ? riskFactors.map(rf => {
            const sevColor = rf.severity === 'critical' ? '#ef4444' : (rf.severity === 'warning' ? '#f59e0b' : '#3b82f6');
            const sevIcon = rf.severity === 'critical' ? '🔴' : (rf.severity === 'warning' ? '🟡' : '🔵');
            return `<tr>
                <td style="font-weight: 600;">${sevIcon} ${rf.factor}</td>
                <td>${rf.detail}</td>
            </tr>`;
        }).join('') : '<tr><td colspan="2" style="text-align: center; color: #22c55e; font-weight: 600;">✅ No significant risk factors identified</td></tr>';

        body.innerHTML = `
            <!-- Report Header Banner -->
            <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #3b82f6; padding-bottom: 20px; margin-bottom: 30px;">
                <div>
                    <h3 style="color: #0f172a; margin: 0 0 4px 0; font-size: 1.3rem;">Clinical Risk Assessment Report</h3>
                    <p style="margin: 0; font-size: 0.82rem; color: #64748b;">Ensemble ML Diagnostic — Tabular Data Analysis</p>
                </div>
                <div style="text-align: right; font-size: 0.82rem; color: #64748b;">
                    <div><strong>Report ID:</strong> ${refId}</div>
                    <div><strong>Date:</strong> ${date} at ${time}</div>
                </div>
            </div>

            <!-- Patient Info -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                <div style="background: #f8fafc; padding: 18px; border-radius: 10px; border: 1px solid #e2e8f0;">
                    <h4 style="color: #3b82f6; margin: 0 0 12px 0; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px;">Patient Information</h4>
                    <div style="font-size: 0.88rem; color: #334155; display: grid; gap: 6px;">
                        <div><strong>Name:</strong> ${name}</div>
                        <div><strong>Email:</strong> ${email}</div>
                        <div><strong>Age:</strong> ${d.age} years</div>
                        <div><strong>Gender:</strong> ${d.gender}</div>
                    </div>
                </div>
                <div style="background: ${riskBg}; padding: 18px; border-radius: 10px; border: 1px solid ${riskColor}33;">
                    <h4 style="color: ${riskColor}; margin: 0 0 12px 0; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px;">Risk Assessment Summary</h4>
                    <div style="font-size: 2rem; font-weight: 800; color: ${riskColor}; margin-bottom: 4px;">${score}%</div>
                    <span class="risk-indicator-badge ${riskClass}">${riskLabel}</span>
                </div>
            </div>

            <!-- Section: Clinical Input Data Table -->
            <div style="margin-bottom: 30px;">
                <h4 style="color: #3b82f6; margin: 0 0 10px 0; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px;">1. Clinical Parameters — Input Data</h4>
                <table class="clinical-data-table">
                    <thead>
                        <tr>
                            <th style="width: 40%;">Parameter</th>
                            <th style="width: 30%;">Value</th>
                            <th style="width: 30%;">Clinical Context</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>Age</td><td><strong>${d.age}</strong> years</td><td>${parseInt(d.age) > 50 ? '⚠️ Elevated risk threshold' : '✅ Within normal range'}</td></tr>
                        <tr><td>Gender</td><td>${d.gender}</td><td>${d.gender === 'Female' ? '⚠️ Higher predisposition' : '➖ Standard risk profile'}</td></tr>
                        <tr><td>Hormonal Status</td><td>${d.hormonalChanges || 'Normal'}</td><td>${d.hormonalChanges === 'Postmenopausal' ? '⚠️ Estrogen decline' : '✅ Stable hormonal balance'}</td></tr>
                        <tr><td>Family History</td><td>${d.familyHistory || 'No'}</td><td>${d.familyHistory === 'Yes' ? '⚠️ Genetic predisposition' : '✅ No hereditary risk'}</td></tr>
                        <tr><td>Ethnicity / Race</td><td>${d.race || 'Not specified'}</td><td>Demographic factor</td></tr>
                        <tr><td>Body Weight</td><td>${d.bodyWeight || 'Normal'}</td><td>${d.bodyWeight === 'Underweight' ? '⚠️ Low bone loading' : '✅ Adequate skeletal support'}</td></tr>
                        <tr><td>Calcium Intake</td><td>${d.calciumIntake || 'Adequate'}</td><td>${d.calciumIntake === 'Low' ? '🔴 Mineral deficiency' : '✅ Sufficient intake'}</td></tr>
                        <tr><td>Vitamin D Level</td><td>${d.vitaminDIntake || 'Sufficient'}</td><td>${d.vitaminDIntake === 'Insufficient' ? '🔴 Absorption impairment' : '✅ Adequate levels'}</td></tr>
                        <tr><td>Physical Activity</td><td>${d.physicalActivity || 'Active'}</td><td>${d.physicalActivity === 'Sedentary' ? '⚠️ Low bone stimulation' : '✅ Active lifestyle'}</td></tr>
                        <tr><td>Smoking</td><td>${d.smoking || 'No'}</td><td>${d.smoking === 'Yes' ? '🔴 Bone loss accelerator' : '✅ Non-smoker'}</td></tr>
                        <tr><td>Alcohol Consumption</td><td>${d.alcoholConsumption || 'None'}</td><td>${d.alcoholConsumption === 'Yes' ? '⚠️ Inhibits bone formation' : '✅ Low/no intake'}</td></tr>
                        <tr><td>Prior Fractures</td><td>${d.priorFractures || 'No'}</td><td>${d.priorFractures === 'Yes' ? '🔴 Previous skeletal damage' : '✅ No fracture history'}</td></tr>
                        ${d.medicine ? `<tr><td>Current Medication</td><td>${d.medicine}</td><td>AI-analyzed for bone health impact</td></tr>` : ''}
                    </tbody>
                </table>
            </div>

            <!-- Section: Model Results -->
            <div style="margin-bottom: 30px;">
                <h4 style="color: #3b82f6; margin: 0 0 10px 0; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px;">2. AI Ensemble Predictions</h4>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 0.7rem; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; margin-bottom: 8px;">Logistic Regression</div>
                        <div style="font-size: 1.8rem; font-weight: 800; color: #0f172a;">${lr}%</div>
                        <div style="height: 4px; background: #e2e8f0; border-radius: 2px; margin-top: 10px; overflow: hidden;">
                            <div style="width: ${lr}%; height: 100%; background: ${riskColor}; border-radius: 2px;"></div>
                        </div>
                    </div>
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 0.7rem; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; margin-bottom: 8px;">Random Forest</div>
                        <div style="font-size: 1.8rem; font-weight: 800; color: #0f172a;">${rf}%</div>
                        <div style="height: 4px; background: #e2e8f0; border-radius: 2px; margin-top: 10px; overflow: hidden;">
                            <div style="width: ${rf}%; height: 100%; background: ${riskColor}; border-radius: 2px;"></div>
                        </div>
                    </div>
                    <div style="background: ${riskBg}; border: 2px solid ${riskColor}44; padding: 20px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 0.7rem; text-transform: uppercase; color: ${riskColor}; letter-spacing: 1px; margin-bottom: 8px;">Ensemble Average</div>
                        <div style="font-size: 1.8rem; font-weight: 800; color: ${riskColor};">${score}%</div>
                        <div style="height: 4px; background: #e2e8f0; border-radius: 2px; margin-top: 10px; overflow: hidden;">
                            <div style="width: ${score}%; height: 100%; background: ${riskColor}; border-radius: 2px;"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Section: Risk Factors -->
            <div style="margin-bottom: 30px;">
                <h4 style="color: #3b82f6; margin: 0 0 10px 0; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px;">3. Identified Risk Factors</h4>
                <table class="clinical-data-table">
                    <thead>
                        <tr><th>Risk Factor</th><th>Detail</th></tr>
                    </thead>
                    <tbody>
                        ${riskFactorRows}
                    </tbody>
                </table>
                ${protectiveFactors.length > 0 ? `
                    <div style="margin-top: 12px; padding: 14px 18px; background: #f0fdf4; border-radius: 8px; border-left: 4px solid #22c55e;">
                        <strong style="color: #166534; font-size: 0.82rem;">Protective Factors:</strong>
                        <span style="color: #166534; font-size: 0.85rem;"> ${protectiveFactors.join(' • ')}</span>
                    </div>
                ` : ''}
            </div>

            ${currentClinicalResult.medicine_impact && currentClinicalResult.medicine_impact.category !== 'None' ? `
            <div style="margin-bottom: 30px;">
                <h4 style="color: #3b82f6; margin: 0 0 10px 0; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px;">4. Medication Impact Analysis</h4>
                <div style="background: #eff6ff; border: 1px solid #bfdbfe; padding: 18px; border-radius: 10px;">
                    <div style="font-weight: 600; color: #1e40af; margin-bottom: 6px;">
                        <i class="fas fa-pills" style="margin-right: 6px;"></i>${d.medicine} — classified as ${currentClinicalResult.medicine_impact.category}
                    </div>
                    <p style="margin: 0; color: #334155; font-size: 0.88rem;">${currentClinicalResult.medicine_impact.insight}</p>
                    <div style="margin-top: 8px; font-size: 0.8rem; color: #64748b;">Prediction uncertainty introduced: <strong>${currentClinicalResult.medicine_impact.error_margin}%</strong></div>
                </div>
            </div>
            ` : ''}

            <!-- Section: Recommendations -->
            <div style="margin-bottom: 30px;">
                <h4 style="color: #3b82f6; margin: 0 0 10px 0; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px;">${currentClinicalResult.medicine_impact && currentClinicalResult.medicine_impact.category !== 'None' ? '5' : '4'}. Clinical Recommendations</h4>
                <div style="background: ${riskBg}; border-left: 4px solid ${riskColor}; padding: 20px; border-radius: 8px;">
                    <ul style="margin: 0; padding-left: 20px; color: #334155; font-size: 0.9rem; line-height: 2;">
                        ${recommendations}
                    </ul>
                </div>
            </div>

            <!-- Certification -->
            <div style="margin-top: 40px; padding: 25px; background: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h4 style="color: #1e293b; margin: 0 0 5px 0; font-size: 0.9rem;">Digital Certification</h4>
                        <p style="margin: 0; font-size: 0.8rem; color: #64748b;">Certified by OsteoAI Ensemble Diagnostic Engine v2.0</p>
                        <p style="margin: 10px 0 0 0; font-size: 0.75rem; color: #94a3b8;">Ref: ${refId}</p>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-family: 'Pacifico', cursive, sans-serif; font-size: 1.2rem; color: #3b82f6;">OsteoAI</div>
                        <div style="width: 120px; height: 1px; background: #cbd5e1; margin-left: auto; margin-top: 4px;"></div>
                        <p style="margin: 5px 0 0 0; font-size: 0.68rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;">Automated Clearance</p>
                    </div>
                </div>
                <div style="margin-top: 18px; padding-top: 14px; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0; font-size: 0.7rem; color: #94a3b8; line-height: 1.5;">
                        <strong>Disclaimer:</strong> This report is generated by an AI system for preliminary screening and research support only. It does not constitute a clinical diagnosis. For medical decisions, this report must be reviewed by a board-certified physician or orthopedic specialist.
                    </p>
                </div>
            </div>

            <div style="margin-top: 25px; text-align: center;">
                <button onclick="closeClinicalReport()" style="background: #0f172a; color: white; border: none; padding: 12px 30px; border-radius: 8px; cursor: pointer; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; font-size: 0.9rem; transition: background 0.3s;">
                    <i class="fas fa-arrow-left"></i> Close & Return
                </button>
            </div>
        `;
    }

    window.closeClinicalReport = function() {
        document.getElementById('clinical-report-modal').style.display = 'none';
    }

    window.downloadClinicalReportPDF = function() {
        window.print();
    }

    window.downloadReportPDF = function() {
        window.print();
    }


    // --- Hospital Locator Logic ---
    window.locateHospitals = function() {
        if ("geolocation" in navigator) {
            const btn = document.querySelector('.btn-secondary');
            const originalText = btn.innerHTML;
            btn.innerHTML = "Locating...";
            btn.disabled = true;

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const { latitude, longitude } = position.coords;
                    const url = `https://www.google.com/maps/search/orthopedic+hospitals/@${latitude},${longitude},15z`;
                    window.open(url, '_blank');
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                },
                (error) => {
                    console.warn("Geolocation error:", error);
                    // Fallback to general search if denied or failed
                    window.open('https://www.google.com/maps/search/orthopedic+hospitals+near+me', '_blank');
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                },
                { timeout: 5000 }
            );
        } else {
            window.open('https://www.google.com/maps/search/orthopedic+hospitals+near+me', '_blank');
        }
    };

    // Add scroll animations for elements
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = 1;
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.feature-card, .step').forEach((el) => {
        el.style.opacity = 0;
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.6s ease-out';
        observer.observe(el);
    });

    // --- X-ray Analysis Logic ---
    const dropArea = document.getElementById('drop-area');
    const xrayInput = document.getElementById('xray-file-input');
    const browseBtn = document.getElementById('browse-btn');
    const xrayResult = document.getElementById('xray-result');
    const xrayPreview = document.getElementById('xray-preview');
    const xrayPrediction = document.getElementById('xray-prediction');
    const xrayConfBar = document.getElementById('xray-confidence-bar');
    const xrayConfText = document.getElementById('xray-confidence-text');
    const reUploadBtn = document.getElementById('re-upload-btn');

    if (browseBtn) {
        browseBtn.addEventListener('click', () => xrayInput.click());
    }

    if (xrayInput) {
        xrayInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) handleXRayUpload(file);
        });
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Set up drag and drop for the regular drop area
    if (dropArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });

        dropArea.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const file = dt.files[0];
            if (file) handleXRayUpload(file);
        }, false);

        dropArea.addEventListener('dragenter', () => dropArea.style.borderColor = 'var(--secondary)');
        dropArea.addEventListener('dragover', () => dropArea.style.borderColor = 'var(--secondary)');
        dropArea.addEventListener('dragleave', () => dropArea.style.borderColor = 'var(--primary)');
        dropArea.addEventListener('drop', () => dropArea.style.borderColor = 'var(--primary)');
    }

    let currentXRayResult = null;

    async function handleXRayUpload(file) {
        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            xrayPreview.src = e.target.result;
            dropArea.style.display = 'none';
            xrayResult.style.display = 'flex';
            xrayPrediction.innerText = 'Analyzing...';
            xrayConfBar.style.width = '0%';
            xrayConfText.innerText = '0%';
        };
        reader.readAsDataURL(file);

        // Upload to API
        const formData = new FormData();
        formData.append('file', file);
        
        // Inject user email for history tracking
        const userEmail = localStorage.getItem('email');
        if (userEmail) formData.append('user_email', userEmail);

        try {
            const response = await fetch('/analyze-xray', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if (result.status === 'success') {
                currentXRayResult = result; // Store for report
                xrayPrediction.innerText = result.prediction;
                const confPct = (result.confidence * 100).toFixed(1);
                xrayConfBar.style.width = confPct + '%';
                xrayConfText.innerText = confPct + '%';
                
                // Add color based on condition
                xrayPrediction.style.color = result.prediction === 'Normal' ? '#27c93f' : (result.prediction === 'Osteopenia' ? '#ffbd2e' : '#ff5f56');
                
                // Refresh history
                if (typeof fetchUserHistory === 'function') fetchUserHistory();
                
                // Scroll to results
                xrayResult.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                alert('Analysis failed: ' + result.message);
                resetXrayUI();
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during analysis.');
            resetXrayUI();
        }
    }

    // Local Report Synthesis
    window.generateLocalReport = function() {
        if (!currentXRayResult) return;

        const prediction = currentXRayResult.prediction;
        const confidence = (currentXRayResult.confidence * 100).toFixed(1);
        const name = localStorage.getItem('username') || 'Patient';
        const date = new Date().toLocaleDateString();

        const modal = document.getElementById('report-modal');
        const loading = document.getElementById('report-loading');
        const content = document.getElementById('report-actual-content');
        
        modal.style.display = 'flex';
        loading.style.display = 'none';
        content.style.display = 'block';

        let findingText = "";
        let recommendationText = "";

        if (prediction === 'Normal') {
            findingText = `Bone texture in the scanned anatomical site appears consistent with normal age-adjusted density. No significant structural thinning or cortical irregularities are noted.`;
            recommendationText = "Continue regular physical activity and calcium-rich diet. Follow-up scan in 24 months recommended.";
        } else if (prediction === 'Osteopenia') {
            findingText = `Early signs of diminished bone mineral density are observed at the scan site. Some trabecular thinning may be present, indicating a mild increase in fracture risk.`;
            recommendationText = "Consult an orthopedic specialist. Consider vitamin D assessment and weight-bearing exercises to maintain bone health.";
        } else {
            findingText = `Significant structural thinning and reduced bone density are evident in the assessed bone area. The trabecular architecture shows marked porosity, indicating high susceptibility to fractures.`;
            recommendationText = "URGENT consultation with a Rheumatologist or Orthopedic specialist required. Discuss pharmaceutical interventions and fall-prevention strategies.";
        }

        content.innerHTML = `
            <div style="border-bottom: 2px solid #3b82f6; padding-bottom: 20px; margin-bottom: 30px;">
                <h3 style="color: #1e293b; margin: 0;">Diagnostic Assessment Report</h3>
                <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 0.9rem; color: #64748b;">
                    <span>Patient: <strong>${name}</strong></span>
                    <span>Date: <strong>${date}</strong></span>
                </div>
            </div>

            <div style="margin-bottom: 25px;">
                <h4 style="color: #3b82f6; margin-bottom: 10px; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px;">1. Clinical Indication</h4>
                <p>Routine screening for fracture risk and bone health assessment based on standard X-ray imaging.</p>
            </div>

            <div style="margin-bottom: 25px;">
                <h4 style="color: #3b82f6; margin-bottom: 10px; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px;">2. Findings & Observations</h4>
                <p>${findingText}</p>
                <p style="margin-top: 10px; font-style: italic;">AI Consensus Confidence: ${confidence}%</p>
            </div>

            <div style="margin-bottom: 25px;">
                <h4 style="color: #3b82f6; margin-bottom: 10px; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px;">3. Final Impression</h4>
                <div style="background: ${prediction === 'Normal' ? '#f0fdf4' : '#fff7ed'}; border-left: 4px solid ${prediction === 'Normal' ? '#22c55e' : '#f97316'}; padding: 15px; border-radius: 4px;">
                    <p style="margin: 0; font-weight: 600;">Diagnosis: ${prediction}</p>
                    <p style="margin: 5px 0 0; font-size: 0.9rem;">The consensus of the MobileNet-ResNet ensemble classifies this scan as <strong>${prediction}</strong>.</p>
                </div>
            </div>

            <div>
                <h4 style="color: #3b82f6; margin-bottom: 10px; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px;">4. Recommendations</h4>
                <p>${recommendationText}</p>
            </div>

            <div style="margin-top: 50px; padding: 25px; background: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h4 style="color: #1e293b; margin: 0 0 5px 0; font-size: 0.9rem;">Final Certification</h4>
                        <p style="margin: 0; font-size: 0.8rem; color: #64748b;">This document is digitally signed and certified by the OsteoAI Diagnostic Engine v2.0.</p>
                        <p style="margin: 15px 0 0 0; font-size: 0.75rem; color: #94a3b8;">Ref ID: OAI-${Math.random().toString(36).substr(2, 9).toUpperCase()}</p>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-family: 'Pacifico', cursive, sans-serif; font-size: 1.2rem; color: #3b82f6; margin-bottom: 5px;">OsteoAI Official</div>
                        <div style="width: 150px; height: 1px; background: #cbd5e1; margin-left: auto;"></div>
                        <p style="margin: 5px 0 0 0; font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">Automated Clearance</p>
                    </div>
                </div>
                <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0; font-size: 0.7rem; color: #94a3b8; line-height: 1.4;">
                        <strong>Disclaimer:</strong> This report is for initial screening and research support purposes only. It does not constitute a definitive medical diagnosis. For clinical management, this report MUST be reviewed by a board-certified radiologist or orthopedic specialist.
                    </p>
                </div>
            </div>

            <div style="margin-top: 30px; text-align: center;">
                <button onclick="closeReport()" class="btn-primary" style="background: #1e293b; color: white; border: none; padding: 12px 30px; border-radius: 8px; cursor: pointer; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; transition: background 0.3s;">
                    <i class="fas fa-arrow-left"></i> Close & Return Home
                </button>
            </div>
        `;
    }

    window.closeReport = function() {
        document.getElementById('report-modal').style.display = 'none';
    }

    // AI Consensus Verification Logic
    window.showConsensusVerification = function() {
        if (!currentXRayResult || !currentXRayResult.model_details) return;

        const modal = document.getElementById('consensus-modal');
        const container = document.getElementById('model-cards-container');
        const verdictEl = document.getElementById('consensus-verdict');
        
        modal.style.display = 'flex';
        container.innerHTML = ''; // Clear old

        const details = currentXRayResult.model_details;
        let matchCount = 0;
        const totalModels = Object.keys(details).length;

        Object.entries(details).forEach(([mName, data]) => {
            const isMatch = data.prediction === currentXRayResult.prediction;
            if (isMatch) matchCount++;

            const card = document.createElement('div');
            card.style.cssText = `
                background: #f8fafc;
                border: 1px solid ${isMatch ? '#e2e8f0' : '#fee2e2'};
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                transition: transform 0.3s ease;
            `;
            
            const confPct = (data.confidence * 100).toFixed(0);
            const statusColor = data.prediction === 'Normal' ? '#22c55e' : (data.prediction === 'Osteopenia' ? '#f59e0b' : '#ef4444');

            card.innerHTML = `
                <div style="font-size: 0.7rem; text-transform: uppercase; color: #64748b; letter-spacing: 1px; margin-bottom: 10px;">${mName.toUpperCase()}</div>
                <div style="font-weight: 700; color: ${statusColor}; font-size: 1.1rem; margin-bottom: 5px;">${data.prediction}</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">Confidence: ${confPct}%</div>
                <div style="margin-top: 15px; height: 4px; background: #e2e8f0; border-radius: 2px; overflow: hidden;">
                    <div style="width: ${confPct}%; height: 100%; background: ${statusColor};"></div>
                </div>
            `;
            container.appendChild(card);
        });

        // Verdict logic
        const agreementPct = (matchCount / totalModels) * 100;
        let verdictTitle = "";
        let verdictDesc = "";
        let verdictColor = "";

        if (agreementPct === 100) {
            verdictTitle = "Strong Clinical Consensus";
            verdictDesc = "All three architectural sub-systems have independently arrived at the same diagnostic conclusion. This indicates a high-reliability assessment.";
            verdictColor = "#f0fdf4";
        } else if (agreementPct >= 66) {
            verdictTitle = "Collaborative Diagnostic Agreement";
            verdictDesc = "The majority of the ensemble models are in agreement. Minor architectural variance detected, but the final consensus remains robust.";
            verdictColor = "#fdfcf0";
        } else {
            verdictTitle = "Edge-Case Analysis";
            verdictDesc = "Significant architectural variance detected. The final result represents the weighted mean, but manual specialist review is highly recommended for this case.";
            verdictColor = "#fef2f2";
        }

        verdictEl.style.background = verdictColor;
        verdictEl.innerHTML = `
            <h4 style="margin: 0 0 10px 0; color: #1e293b;">${verdictTitle}</h4>
            <p style="margin: 0; font-size: 0.85rem; color: #64748b;">${verdictDesc}</p>
        `;
    }

    window.closeConsensus = function() {
        document.getElementById('consensus-modal').style.display = 'none';
    }

    if (reUploadBtn) reUploadBtn.addEventListener('click', resetXrayUI);

    function resetXrayUI() {
        dropArea.style.display = 'flex';
        xrayResult.style.display = 'none';
        xrayInput.value = '';
    }


    // --- Booking Prompt Logic ---
    const bookYesBtn = document.getElementById('book-yes-btn');
    const bookNoBtn = document.getElementById('book-no-btn');
    const bookingPrompt = document.getElementById('booking-prompt');

    if (bookYesBtn) {
        bookYesBtn.addEventListener('click', () => {
            window.location.href = 'doctor_appoint.html';
        });
    }

    if (bookNoBtn) {
        bookNoBtn.addEventListener('click', () => {
            if (bookingPrompt) bookingPrompt.style.display = 'none';
        });
    }

    // --- Custom Cursor Logic ---
    const cursorDot = document.querySelector('.custom-cursor-dot');
    const cursorCircle = document.querySelector('.custom-cursor-circle');
    
    let mouseX = 0, mouseY = 0;
    let circleX = 0, circleY = 0;

    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
        
        // Dot follows instantly
        cursorDot.style.left = `${mouseX}px`;
        cursorDot.style.top = `${mouseY}px`;
    });

    // Smooth animation for the circle
    function animateCursor() {
        let distX = mouseX - circleX;
        let distY = mouseY - circleY;
        
        circleX = circleX + (distX * 0.15); // Adjust ease factor here
        circleY = circleY + (distY * 0.15);
        
        cursorCircle.style.left = `${circleX}px`;
        cursorCircle.style.top = `${circleY}px`;
        
        requestAnimationFrame(animateCursor);
    }
    
    animateCursor();

    // Add hover effects for interactive elements
    const interactables = document.querySelectorAll('a, button, input, select, .feature-card, .btn');
    interactables.forEach(el => {
        el.addEventListener('mouseenter', () => {
            cursorDot.classList.add('hovered');
            cursorCircle.classList.add('hovered');
        });
        el.addEventListener('mouseleave', () => {
            cursorDot.classList.remove('hovered');
            cursorCircle.classList.remove('hovered');
        });
    });

    // --- History Modal Logic ---
    const settingsBtn = document.getElementById('settings-btn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const modal = document.getElementById('history-modal');
            if(modal) modal.style.display = 'flex';
        });
    }

    window.closeHistoryModal = function() {
        const modal = document.getElementById('history-modal');
        if(modal) modal.style.display = 'none';
    }


    // --- System Status Sync ---
    async function syncSystemStatus() {
        try {
            const res = await fetch('/api/system/status');
            const config = await res.json();
            
            // 1. Clinical Analysis
            if (!config.clinical_analysis) {
                const clinicalBtn = document.getElementById('clinical-predict-btn');
                if (clinicalBtn) {
                    clinicalBtn.disabled = true;
                    clinicalBtn.innerHTML = '<i class="fas fa-pause-circle"></i> Clinical Analysis Paused';
                    clinicalBtn.style.background = 'rgba(255,255,255,0.05)';
                    clinicalBtn.title = "This feature is temporarily undergoing maintenance.";
                }
            }

            // 2. X-ray Analysis
            if (!config.xray_analysis) {
                const dropArea = document.getElementById('drop-area');
                if (dropArea) {
                    dropArea.style.pointerEvents = 'none';
                    dropArea.style.opacity = '0.5';
                    dropArea.innerHTML = `
                        <i class="fas fa-tools" style="font-size: 3rem; margin-bottom: 20px; color: var(--warning);"></i>
                        <h3>Scanning Unavailable</h3>
                        <p>Our X-ray AI engine is currently pausing for maintenance. We'll be back online shortly.</p>
                    `;
                }
            }

            // 3. Appointments
            if (!config.appointments) {
                const bookBtns = document.querySelectorAll('a[href="doctor_appoint.html"]');
                bookBtns.forEach(btn => {
                    btn.classList.add('disabled-nav');
                    btn.style.opacity = '0.5';
                    btn.style.pointerEvents = 'none';
                    btn.title = "Booking system is currently offline.";
                });
            }
        } catch (e) {
            console.error("Status sync failed", e);
        }
    }
    
    // --- User History Fetch Sync ---
    async function fetchUserHistory() {
        const userEmail = localStorage.getItem('email');
        if (!userEmail) return;
        
        try {
            const res = await fetch('/api/user/history', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_email: userEmail })
            });
            const data = await res.json();
            
            const historyContainer = document.getElementById('history-modal-container');
            const historyEmpty = document.getElementById('history-modal-empty');
            
            if (data.status === 'success' && data.data && data.data.length > 0) {
                if(historyContainer) historyContainer.innerHTML = '';
                if(historyEmpty) historyEmpty.style.display = 'none';
                
                data.data.forEach(record => {
                    const dateObj = new Date(record.timestamp);
                    const dateStr = dateObj.toLocaleDateString() + ' ' + dateObj.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                    
                    const isClinical = record.type.includes('Clinical');
                    const userName = localStorage.getItem('username') || 'Patient';
                    const cardTitle = isClinical ? `Patient: ${userName}` : `${record.type}`;
                    const iconName = isClinical ? 'fa-user' : 'fa-x-ray';
                    const isHighRisk = record.prediction === 'High Risk' || record.prediction === 'Osteoporosis';
                    const isMediumRisk = record.prediction === 'Osteopenia';
                    const statusColor = isHighRisk ? '#ff5f56' : (isMediumRisk ? '#ffbd2e' : '#27c93f');
                    
                    const cardHtml = `
                        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); transition: transform 0.2s;" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
                            <div style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 8px;">${dateStr}</div>
                            <h4 style="margin: 0 0 12px 0; color: #0f172a; font-size: 1.05rem;">
                                <i class="fas ${iconName}" style="margin-right: 6px; color: #3b82f6;"></i>
                                ${cardTitle}
                            </h4>
                            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f1f5f9; padding-top: 12px;">
                                <span style="font-size: 0.85rem; color: #64748b;">Diagnosis:</span>
                                <strong style="color: ${statusColor}; font-size: 0.95rem;">${record.prediction}</strong>
                            </div>
                            <div style="margin-top: 8px; font-size: 0.8rem; display: flex; justify-content: space-between;">
                                <span style="color: #94a3b8;">${isClinical ? 'Risk Score' : 'Confidence'}:</span> 
                                <span style="color: #475569; font-weight: 500;">${record.score}%</span>
                            </div>
                        </div>
                    `;
                    if(historyContainer) historyContainer.innerHTML += cardHtml;
                });
            } else {
                if(historyEmpty) historyEmpty.style.display = 'block';
            }
        } catch (e) {
            console.error("Failed to fetch history:", e);
        }
    }

    // Run status check
    syncSystemStatus();
    fetchUserHistory();
    if (window._statusInterval) clearInterval(window._statusInterval);
    window._statusInterval = setInterval(syncSystemStatus, 60000); // Check every 60s
});
