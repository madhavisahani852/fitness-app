/* =======================================================================
   AI FITNESS & DIET RECOMMENDATION SYSTEM
   Frontend Application Script — Vanilla JS + Chart.js
   ======================================================================= */

document.addEventListener('DOMContentLoaded', () => {

    // ── Element References ───────────────────────────────────────────────
    const form = document.getElementById('fitness-form');
    const submitBtn = document.getElementById('submit-btn');
    const reanalyzeBtn = document.getElementById('reanalyze-btn');
    const formError = document.getElementById('form-error');
    const formErrorText = document.getElementById('form-error-text');

    const inputSection = document.getElementById('input-section');
    const loaderSection = document.getElementById('loader-section');
    const resultsSection = document.getElementById('results-section');

    const sleepInput = document.getElementById('sleep');
    const sleepVal = document.getElementById('sleep-val');
    const workoutInput = document.getElementById('workout_hours');
    const workoutVal = document.getElementById('workout-val');

    // Config modal
    const configBtn = document.getElementById('config-btn');
    const configModal = document.getElementById('config-modal');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const backendInput = document.getElementById('backend-url-input');
    const saveConfigBtn = document.getElementById('save-config-btn');

    // Chart instances
    let chartMacros = null, chartWeight = null, chartProj = null;

    // ── Backend URL (dynamic detect + localStorage) ──────────────────────
    function getDefaultUrl() {
        const DEV_API = "http://localhost:5000";
        const PROD_API = "https://fitness-and-diet-recommendation-app-1.onrender.com";

        const API =
            window.location.hostname === "localhost"
                ? DEV_API
                : PROD_API;
    }

    let API = localStorage.getItem('fit_api_url') || getDefaultUrl();
    backendInput.value = API;

    // ── Slider Live Labels ───────────────────────────────────────────────
    sleepInput.addEventListener('input', () => { sleepVal.textContent = sleepInput.value; });
    workoutInput.addEventListener('input', () => { workoutVal.textContent = workoutInput.value; });

    // ── Config Modal ─────────────────────────────────────────────────────
    configBtn.addEventListener('click', () => configModal.classList.add('open'));

    function closeModal() { configModal.classList.remove('open'); }
    modalCloseBtn.addEventListener('click', closeModal);
    configModal.addEventListener('click', e => { if (e.target === configModal) closeModal(); });

    saveConfigBtn.addEventListener('click', () => {
        let url = backendInput.value.trim().replace(/\/$/, '');
        if (!url) { alert('Enter a valid URL'); return; }
        API = url;
        localStorage.setItem('fit_api_url', url);
        closeModal();
        showToast(`✅ Backend URL saved: ${url}`);
    });

    // ── Re-analyze Button → scroll back to form ──────────────────────────
    reanalyzeBtn.addEventListener('click', () => {
        resultsSection.classList.add('hidden');
        inputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    // ── Form Submit ──────────────────────────────────────────────────────
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearError();

        // Collect payload
        const payload = {
            name: document.getElementById('name').value.trim(),
            age: parseInt(document.getElementById('age').value),
            gender: document.getElementById('gender').value,
            height: parseFloat(document.getElementById('height').value),
            weight: parseFloat(document.getElementById('weight').value),
            sleep: parseFloat(sleepInput.value),
            workout_hours: parseFloat(workoutInput.value),
            steps: parseInt(document.getElementById('steps').value),
            goal: document.getElementById('goal').value,
            diet_pref: document.getElementById('diet_pref').value,
            medical: document.getElementById('medical').value,
        };

        // Show loader
        showLoader();

        try {
            const res = await fetch(`${API}/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.error || `HTTP ${res.status}`);
            }

            hideLoader();
            renderResults(data);

        } catch (err) {
            hideLoader();
            showError(`❌ ${err.message}. Check that your backend is running at: ${API}. Use the ⚙️ gear icon to change it.`);
            console.error('[FitnessAI] Fetch error:', err);
        }
    });

    // ── State Helpers ────────────────────────────────────────────────────
    function showLoader() {
        resultsSection.classList.add('hidden');
        formError.classList.add('hidden');
        loaderSection.classList.remove('hidden');
        // Scroll to loader so user sees progress
        loaderSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
        submitBtn.disabled = true;
    }

    function hideLoader() {
        loaderSection.classList.add('hidden');
        submitBtn.disabled = false;
    }

    function showError(msg) {
        formErrorText.textContent = msg;
        formError.classList.remove('hidden');
        formError.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function clearError() {
        formError.classList.add('hidden');
    }

    // ── Toast Notification ───────────────────────────────────────────────
    function showToast(msg) {
        const t = document.createElement('div');
        t.style.cssText = `
            position:fixed; bottom:24px; right:24px; z-index:999;
            background:#1e293b; border:1px solid rgba(255,255,255,0.1);
            color:#f1f5f9; padding:12px 20px; border-radius:8px;
            font-family:'Outfit',sans-serif; font-size:13px;
            box-shadow:0 8px 24px rgba(0,0,0,0.4);
            animation:fadeSlideUp .3s ease;
        `;
        t.textContent = msg;
        document.body.appendChild(t);
        setTimeout(() => t.remove(), 3000);
    }

    // ── Render Results ────────────────────────────────────────────────────
    function renderResults(d) {
        // Greeting
        document.getElementById('greeting-name').textContent = `Hello, ${d.name}! 👋`;

        // ── Metric Cards ────
        document.getElementById('m-bmi').textContent = d.bmi;
        document.getElementById('m-calories').textContent = `${d.ml_calories} kcal`;
        document.getElementById('m-bmr').textContent = `${d.bmr_calories} kcal`;
        document.getElementById('m-sleep').textContent = `${d.sleep_hours} hrs`;

        // BMI status tag
        const bmiTag = document.getElementById('m-bmi-tag');
        bmiTag.textContent = d.bmi_status;
        bmiTag.className = 'metric-tag';
        if (d.bmi_status === 'Normal Weight') bmiTag.classList.add('tag-good');
        else if (d.bmi_status === 'Underweight') bmiTag.classList.add('tag-warn');
        else bmiTag.classList.add('tag-alert');

        // Sleep tag
        const sleepTag = document.getElementById('m-sleep-tag');
        sleepTag.textContent = d.sleep_status === 'Good' ? 'Good Quality ✓' : 'Low — aim for 7+ hrs';
        sleepTag.className = 'metric-tag';
        sleepTag.classList.add(d.sleep_status === 'Good' ? 'tag-good' : 'tag-warn');

        // ── Medical Warning ────
        const warnBox = document.getElementById('warning-box');
        if (d.warning) {
            document.getElementById('warning-text').textContent = d.warning;
            warnBox.classList.remove('hidden');
        } else {
            warnBox.classList.add('hidden');
        }

        // ── Recommendations ────
        document.getElementById('workout-tag').textContent = d.workout_plan;
        document.getElementById('workout-display').textContent = d.workout_display;
        document.getElementById('diet-tag').textContent = d.meal_plan;
        document.getElementById('diet-display').textContent = d.diet_display;

        // ── Macro Pills ────
        document.getElementById('pill-protein').textContent = `${d.protein_g}g`;
        document.getElementById('pill-carbs').textContent = `${d.carb_g}g`;
        document.getElementById('pill-fat').textContent = `${d.fat_g}g`;

        // ── BMI Scale Pointer ────
        const bmi = d.bmi;
        let pct = 0;
        if (bmi <= 10) pct = 0;
        else if (bmi >= 40) pct = 100;
        else if (bmi < 18.5) pct = ((bmi - 10) / 8.5) * 28.3;
        else if (bmi < 25) pct = 28.3 + ((bmi - 18.5) / 6.5) * 21.7;
        else if (bmi < 30) pct = 50 + ((bmi - 25) / 5) * 16.7;
        else pct = 66.7 + ((bmi - 30) / 10) * 33.3;
        document.getElementById('bmi-pointer').style.left = `${Math.min(pct, 99)}%`;
        document.getElementById('bmi-detail-val').textContent = bmi;

        // BMI advice
        const advice = document.getElementById('bmi-advice');
        if (bmi < 18.5) advice.textContent = 'Increase calorie intake with nutrient-dense foods and strength training to gain healthy mass.';
        else if (bmi < 25) advice.textContent = 'You are in the healthy range! Keep up a balanced diet and regular workouts. ✅';
        else if (bmi < 30) advice.textContent = 'Consider a moderate caloric deficit, increase daily steps, and add more cardio sessions.';
        else advice.textContent = 'Consult a physician or certified dietitian for a structured, safe weight-loss plan.';

        // ── Charts ────
        renderCharts(d);

        // ── Show Results & Scroll ────
        resultsSection.classList.remove('hidden');
        // Small delay so the DOM paints first
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 80);
    }

    // ── Chart Rendering ──────────────────────────────────────────────────
    function renderCharts(d) {
        if (chartMacros) chartMacros.destroy();
        if (chartWeight) chartWeight.destroy();
        if (chartProj) chartProj.destroy();

        const gridColor = 'rgba(148,163,184,0.08)';
        const tickColor = '#64748b';
        const fontFamily = 'Outfit';

        const commonScales = {
            x: { grid: { color: gridColor }, ticks: { color: tickColor, font: { family: fontFamily, size: 11 } } },
            y: { grid: { color: gridColor }, ticks: { color: tickColor, font: { family: fontFamily, size: 11 } } },
        };

        // 1. Macros Doughnut
        const protCal = d.protein_g * 4;
        const carbsCal = d.carb_g * 4;
        const fatCal = d.fat_g * 9;

        chartMacros = new Chart(
            document.getElementById('chart-macros').getContext('2d'),
            {
                type: 'doughnut',
                data: {
                    labels: ['Protein', 'Carbs', 'Fat'],
                    datasets: [{
                        data: [protCal, carbsCal, fatCal],
                        backgroundColor: ['#38bdf8', '#fb923c', '#34d399'],
                        borderColor: 'rgba(10,15,30,0.6)',
                        borderWidth: 2,
                        hoverOffset: 6,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '68%',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label(ctx) {
                                    const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                    const pct = Math.round((ctx.raw / total) * 100);
                                    return `  ${ctx.label}: ${ctx.raw} kcal (${pct}%)`;
                                }
                            }
                        }
                    }
                }
            }
        );

        // 2. Weight History + LSTM Prediction
        const histLabels = d.weight_history.map((_, i) => `Day ${i + 1}`);
        const histData = [...d.weight_history];
        const predLabels = [...histLabels, 'Prediction'];
        const predData = [...Array(histData.length).fill(null), d.lstm_next_weight];
        const lineData = [...histData, null];

        chartWeight = new Chart(
            document.getElementById('chart-weight').getContext('2d'),
            {
                type: 'line',
                data: {
                    labels: predLabels,
                    datasets: [
                        {
                            label: 'Weight History (kg)',
                            data: lineData,
                            borderColor: '#38bdf8',
                            backgroundColor: 'rgba(56,189,248,0.08)',
                            borderWidth: 2.5,
                            pointBackgroundColor: '#38bdf8',
                            pointBorderColor: '#fff',
                            pointRadius: 4,
                            tension: 0.3,
                            fill: true,
                        },
                        {
                            label: 'LSTM Predicted (kg)',
                            data: predData,
                            borderColor: 'transparent',
                            pointStyle: 'star',
                            pointBackgroundColor: '#f87171',
                            pointBorderColor: '#fff',
                            pointRadius: 12,
                            pointHoverRadius: 14,
                            showLine: false,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: tickColor, font: { family: fontFamily, size: 11 } } } },
                    scales: commonScales,
                }
            }
        );

        // 3. 4-Week Projection
        chartProj = new Chart(
            document.getElementById('chart-projection').getContext('2d'),
            {
                type: 'line',
                data: {
                    labels: d.projection_weeks,
                    datasets: [{
                        label: 'Projected Weight (kg)',
                        data: d.projection_weights,
                        borderColor: '#c084fc',
                        backgroundColor: 'rgba(192,132,252,0.08)',
                        borderWidth: 2.5,
                        pointBackgroundColor: '#c084fc',
                        pointBorderColor: '#fff',
                        pointRadius: 5,
                        tension: 0.2,
                        fill: true,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: tickColor, font: { family: fontFamily, size: 11 } } } },
                    scales: commonScales,
                }
            }
        );
    }

}); // DOMContentLoaded
