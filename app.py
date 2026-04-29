from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ── Symptom definitions with scoring impact ──────────────────────────
SYMPTOMS = {
    "weight_gain":      {"hypo": 1,   "hyper": 0,   "label": "Weight gain"},
    "weight_loss":      {"hypo": 0,   "hyper": 1,   "label": "Weight loss"},
    "fatigue":          {"hypo": 1,   "hyper": 0.5, "label": "Fatigue"},
    "anxiety":          {"hypo": 0,   "hyper": 1,   "label": "Anxiety / Irritability"},
    "hair_loss":        {"hypo": 1,   "hyper": 0.5, "label": "Hair loss"},
    "heat_intolerance": {"hypo": 0,   "hyper": 1,   "label": "Heat intolerance"},
    "cold_intolerance": {"hypo": 1,   "hyper": 0,   "label": "Cold intolerance"},
    "rapid_heartbeat":  {"hypo": 0,   "hyper": 1,   "label": "Rapid heartbeat"},
    "tremors":          {"hypo": 0,   "hyper": 1,   "label": "Tremors / Shaking"},
    "constipation":     {"hypo": 1,   "hyper": 0,   "label": "Constipation"},
    "dry_skin":         {"hypo": 1,   "hyper": 0,   "label": "Dry skin"},
    "swelling":         {"hypo": 1,   "hyper": 0,   "label": "Neck swelling"},
}

# ── Symptom-thyroid correlation explanations ──────────────────────────
SYMPTOM_EXPLANATIONS = {
    "weight_gain": {
        "Hypothyroidism": {"correlates": True, "reason": "Low thyroid hormones slow metabolism, causing the body to store more calories as fat. Weight gain is one of the hallmark signs of hypothyroidism."},
        "Hyperthyroidism": {"correlates": False, "reason": "Weight gain is unusual in hyperthyroidism since excess hormones speed up metabolism. This symptom contradicts an overactive thyroid."},
        "Normal": {"correlates": False, "reason": "Weight gain can have many causes unrelated to thyroid — diet, lifestyle, or other hormonal factors. Your thyroid levels appear normal."},
    },
    "weight_loss": {
        "Hypothyroidism": {"correlates": False, "reason": "Weight loss is uncommon with hypothyroidism. An underactive thyroid typically slows metabolism, making weight loss difficult."},
        "Hyperthyroidism": {"correlates": True, "reason": "Excess thyroid hormones accelerate metabolism dramatically, causing the body to burn calories faster than you can consume them — leading to unintentional weight loss."},
        "Normal": {"correlates": False, "reason": "Unexplained weight loss with normal thyroid levels may have other causes — consult a doctor if it persists."},
    },
    "fatigue": {
        "Hypothyroidism": {"correlates": True, "reason": "Low T3/T4 means every cell gets less energy. The body enters 'conservation mode' — muscles weaken, energy drops, and you feel constantly tired."},
        "Hyperthyroidism": {"correlates": True, "reason": "Though the thyroid is overactive, the body's resources get depleted from running too fast. Muscles can weaken and you feel exhausted despite feeling 'wired'."},
        "Normal": {"correlates": False, "reason": "Fatigue with normal thyroid levels is likely from sleep, stress, iron deficiency, or other factors — not thyroid dysfunction."},
    },
    "anxiety": {
        "Hypothyroidism": {"correlates": False, "reason": "Anxiety is less common with hypothyroidism. Underactive thyroid more typically causes depression and brain fog rather than anxiety."},
        "Hyperthyroidism": {"correlates": True, "reason": "Excess thyroid hormones overstimulate the nervous system, triggering the 'fight or flight' response — causing anxiety, nervousness, and irritability."},
        "Normal": {"correlates": False, "reason": "Anxiety with normal thyroid levels is likely from stress, mental health factors, or other causes — your thyroid is not the source."},
    },
    "hair_loss": {
        "Hypothyroidism": {"correlates": True, "reason": "Thyroid hormones regulate hair follicle cycling. Low hormones push more follicles into the resting (telogen) phase, causing diffuse hair thinning."},
        "Hyperthyroidism": {"correlates": True, "reason": "Both excess and deficient thyroid hormones disrupt the hair growth cycle. Hyperthyroidism can cause fine, thinning hair across the scalp."},
        "Normal": {"correlates": False, "reason": "Hair loss with normal thyroid levels may be from genetics, stress, iron deficiency, or other hormonal imbalances."},
    },
    "heat_intolerance": {
        "Hypothyroidism": {"correlates": False, "reason": "Heat intolerance contradicts hypothyroidism. Underactive thyroid typically causes cold intolerance, not heat sensitivity."},
        "Hyperthyroidism": {"correlates": True, "reason": "Excess thyroid hormones increase metabolic rate and heat production. Your body generates more heat than it can dissipate, making you feel overheated."},
        "Normal": {"correlates": False, "reason": "Heat intolerance with normal thyroid levels may be from other causes like menopause, medication, or autonomic issues."},
    },
    "cold_intolerance": {
        "Hypothyroidism": {"correlates": True, "reason": "Low thyroid hormones reduce metabolic heat production. Your body can't generate enough warmth, making you sensitive to cold temperatures."},
        "Hyperthyroidism": {"correlates": False, "reason": "Cold intolerance is unusual with hyperthyroidism. Overactive thyroid increases body heat — you'd typically feel warm, not cold."},
        "Normal": {"correlates": False, "reason": "Cold intolerance with normal thyroid may be from poor circulation, low iron, low body weight, or other factors."},
    },
    "rapid_heartbeat": {
        "Hypothyroidism": {"correlates": False, "reason": "Rapid heartbeat contradicts hypothyroidism. Underactive thyroid typically causes slow heart rate (bradycardia), not tachycardia."},
        "Hyperthyroidism": {"correlates": True, "reason": "Thyroid hormones directly affect heart rate. Excess T3/T4 overstimulate cardiac muscle, causing palpitations, rapid heartbeat, and sometimes atrial fibrillation."},
        "Normal": {"correlates": False, "reason": "Rapid heartbeat with normal thyroid may be from caffeine, stress, anxiety, dehydration, or cardiac conditions."},
    },
    "tremors": {
        "Hypothyroidism": {"correlates": False, "reason": "Tremors are not typical of hypothyroidism. Underactive thyroid causes sluggishness and slow reflexes, not shaking."},
        "Hyperthyroidism": {"correlates": True, "reason": "Excess thyroid hormones overstimulate the nervous system, causing fine tremors especially visible when you extend your hands. This is a classic hyperthyroid sign."},
        "Normal": {"correlates": False, "reason": "Tremors with normal thyroid levels may be from caffeine, essential tremor, stress, or neurological factors."},
    },
    "constipation": {
        "Hypothyroidism": {"correlates": True, "reason": "Low thyroid hormones slow down gut motility (peristalsis). Food moves through the digestive tract more slowly, leading to constipation."},
        "Hyperthyroidism": {"correlates": False, "reason": "Constipation contradicts hyperthyroidism. Overactive thyroid speeds up digestion, typically causing frequent bowel movements or diarrhea."},
        "Normal": {"correlates": False, "reason": "Constipation with normal thyroid levels is likely from diet (low fiber), dehydration, medication, or gut motility issues."},
    },
    "dry_skin": {
        "Hypothyroidism": {"correlates": True, "reason": "Thyroid hormones regulate skin cell turnover and oil production. Low hormones reduce sweating and sebum production, causing dry, flaky, rough skin."},
        "Hyperthyroidism": {"correlates": False, "reason": "Dry skin is uncommon with hyperthyroidism. Overactive thyroid typically causes warm, moist, smooth skin due to increased blood flow."},
        "Normal": {"correlates": False, "reason": "Dry skin with normal thyroid is likely environmental (cold weather, low humidity), from skin conditions, or dehydration."},
    },
    "swelling": {
        "Hypothyroidism": {"correlates": True, "reason": "Neck swelling (goiter) can occur when the thyroid enlarges in response to high TSH levels. The pituitary keeps stimulating the gland to produce more hormones."},
        "Hyperthyroidism": {"correlates": True, "reason": "Neck swelling can occur in Graves' disease (diffuse goiter) or thyroid nodules, both common causes of hyperthyroidism."},
        "Normal": {"correlates": False, "reason": "Neck swelling with normal thyroid levels should be evaluated by a doctor — it may be from lymph nodes, other glands, or benign thyroid changes."},
    },
}

TIPS = {
    "Hypothyroidism": [
        "Consult an endocrinologist for TSH level evaluation",
        "Common symptoms: fatigue, weight gain, cold sensitivity",
        "Treatment usually involves levothyroxine medication",
        "Eat iodine-rich foods: fish, dairy, eggs",
        "Avoid excessive soy and raw cruciferous vegetables",
    ],
    "Hyperthyroidism": [
        "Seek medical attention — hyperthyroidism needs prompt care",
        "Common symptoms: rapid heartbeat, weight loss, anxiety",
        "Avoid iodine-rich foods and supplements",
        "Reduce caffeine intake",
        "Antithyroid medications or radioactive iodine may be prescribed",
    ],
    "Normal": [
        "Thyroid function appears normal based on inputs",
        "Maintain a balanced diet with adequate iodine",
        "Exercise regularly and manage stress",
        "Get thyroid levels checked annually as routine screening",
        "Watch for symptoms: fatigue, weight changes, mood swings",
    ],
}

POSSIBLE_CAUSES = {
    "Hypothyroidism": [
        {"name": "Hashimoto's Thyroiditis", "desc": "Autoimmune condition where immune system attacks the thyroid — most common cause."},
        {"name": "Iodine Deficiency", "desc": "Insufficient iodine impairs hormone production. Common without iodized salt."},
        {"name": "Thyroid Surgery", "desc": "Partial or total thyroidectomy reduces hormone production."},
        {"name": "Radiation Therapy", "desc": "Radiation to the head/neck area can damage the thyroid gland."},
        {"name": "Medications", "desc": "Lithium, amiodarone, and others can interfere with thyroid function."},
    ],
    "Hyperthyroidism": [
        {"name": "Graves' Disease", "desc": "Autoimmune disorder causing excess hormone production — most common cause."},
        {"name": "Thyroiditis", "desc": "Inflammation causing stored hormones to leak into the bloodstream."},
        {"name": "Thyroid Nodules", "desc": "Overactive nodules (toxic adenoma) producing excess hormones."},
        {"name": "Excess Iodine", "desc": "Too much iodine from diet or medications can overstimulate the thyroid."},
        {"name": "Pituitary Dysfunction", "desc": "Rare — pituitary produces excess TSH-stimulating hormones."},
    ],
    "Normal": [],
}

DIET = {
    "Hypothyroidism": [
        {"item": "Iodine-rich foods", "detail": "Seafood, iodized salt, dairy, eggs", "icon": "🐟"},
        {"item": "Selenium sources", "detail": "Brazil nuts, sunflower seeds, mushrooms", "icon": "🥜"},
        {"item": "Zinc-rich foods", "detail": "Chickpeas, lentils, cashews, pumpkin seeds", "icon": "🫘"},
        {"item": "Indian diet tips", "detail": "Coconut chutney, curd rice, fish curry, dal with iodized salt", "icon": "🍛"},
        {"item": "Avoid excess", "detail": "Limit raw cruciferous vegs, soy products, processed foods", "icon": "⚠️"},
    ],
    "Hyperthyroidism": [
        {"item": "Calcium-rich foods", "detail": "Milk, yogurt, paneer, ragi, sesame seeds", "icon": "🥛"},
        {"item": "Cruciferous vegetables", "detail": "Broccoli, cauliflower, cabbage — may help slow thyroid", "icon": "🥦"},
        {"item": "Anti-inflammatory", "detail": "Turmeric, berries, leafy greens, green tea", "icon": "🫖"},
        {"item": "Indian diet tips", "detail": "Ragi porridge, curd, buttermilk, coconut water, fruits", "icon": "🍛"},
        {"item": "Avoid", "detail": "Reduce iodine-rich foods, caffeine, spicy foods, processed sugars", "icon": "⚠️"},
    ],
    "Normal": [
        {"item": "Balanced iodine", "detail": "Use iodized salt, include seafood 2-3 times/week", "icon": "🧂"},
        {"item": "Antioxidant-rich", "detail": "Colorful fruits and vegetables, nuts, seeds", "icon": "🥗"},
        {"item": "Protein sources", "detail": "Lean meat, eggs, legumes, dairy", "icon": "🥚"},
        {"item": "Indian diet tips", "detail": "Dal-roti with seasonal vegs, curd, fresh fruit", "icon": "🍛"},
        {"item": "Hydration", "detail": "8-10 glasses water daily, coconut water, buttermilk", "icon": "💧"},
    ],
}

LIFESTYLE = {
    "Hypothyroidism": [
        {"tip": "Regular exercise", "detail": "30 min moderate exercise daily — walking, yoga, swimming", "icon": "🏃"},
        {"tip": "Stress management", "detail": "Meditation, pranayama, deep breathing exercises", "icon": "🧘"},
        {"tip": "Quality sleep", "detail": "7-8 hours; maintain consistent sleep schedule", "icon": "😴"},
        {"tip": "Weight management", "detail": "Portion control and consistent meal timing", "icon": "⚖️"},
        {"tip": "Regular monitoring", "detail": "Check levels every 6-8 weeks until stable", "icon": "📋"},
    ],
    "Hyperthyroidism": [
        {"tip": "Gentle exercise", "detail": "Avoid intense workouts; opt for yoga, tai chi, walking", "icon": "🧘"},
        {"tip": "Stress reduction", "detail": "Critical — stress worsens symptoms. Try meditation", "icon": "🧠"},
        {"tip": "Adequate rest", "detail": "Extra rest may be needed; listen to your body", "icon": "😴"},
        {"tip": "Bone health", "detail": "Weight-bearing exercises to protect bone density", "icon": "🦴"},
        {"tip": "Avoid stimulants", "detail": "Reduce caffeine, nicotine, and stimulants", "icon": "🚫"},
    ],
    "Normal": [
        {"tip": "Stay active", "detail": "150 minutes moderate exercise per week", "icon": "🏃"},
        {"tip": "Balanced lifestyle", "detail": "Regular meals, adequate sleep, stress management", "icon": "⚖️"},
        {"tip": "Annual screening", "detail": "Check levels annually, especially with family history", "icon": "📋"},
        {"tip": "Neck awareness", "detail": "Self-check for neck swelling or lumps periodically", "icon": "🔍"},
        {"tip": "Stay informed", "detail": "Learn thyroid symptoms for early detection", "icon": "📚"},
    ],
}


def _build_explanation(result, tsh, t3, t4, severity):
    """Plain-English report explanation."""
    if result == "Hypothyroidism":
        body = (
            f"Your TSH is {tsh} mIU/L — elevated above normal (0.4–4.5). "
            "High TSH means your pituitary gland is 'shouting' at your thyroid to work harder "
            "because it isn't producing enough hormones. "
        )
        if t3 < 0.8:
            body += f"T3 is {t3} nmol/L (low), confirming reduced active hormone. "
        if t4 < 58:
            body += f"T4 is {t4} nmol/L (low), confirming reduced thyroid output. "
        body += (
            "With insufficient thyroid hormones your metabolism slows — causing fatigue, "
            "weight gain, cold sensitivity, and sluggishness. Your body enters 'energy conservation mode'. "
        )
        if severity == "Severe":
            body += "⚠️ Values are significantly abnormal — seek prompt medical attention."
        elif severity == "Moderate":
            body += "Consult an endocrinologist for evaluation and treatment."
        else:
            body += "Early intervention can prevent progression — schedule a doctor visit."
    elif result == "Hyperthyroidism":
        body = (
            f"Your TSH is {tsh} mIU/L — suppressed below normal (0.4–4.5). "
            "Low TSH means your pituitary has detected excess thyroid hormones and stopped sending signals. "
        )
        if t3 > 2.0:
            body += f"T3 is {t3} nmol/L (elevated), confirming excess active hormone. "
        if t4 > 161:
            body += f"T4 is {t4} nmol/L (elevated), confirming thyroid overproduction. "
        body += (
            "With excess hormones your metabolism goes into overdrive — rapid heartbeat, weight loss, "
            "anxiety, and overheating. Your body is stuck in 'high gear'. "
        )
        if severity == "Severe":
            body += "⚠️ Severely abnormal — risk of thyroid storm. Seek urgent care."
        elif severity == "Moderate":
            body += "Significant overactivity detected — consult an endocrinologist soon."
        else:
            body += "Mild overactivity — early treatment is highly effective."
    else:
        body = (
            f"TSH {tsh}, T3 {t3}, T4 {t4} — all within expected ranges. "
            "Your pituitary-thyroid feedback loop is working correctly. "
            "Metabolism, energy, and temperature regulation should be normal. "
            "Continue healthy habits and screen annually."
        )
    return body


def _build_logic(score, tsh, t3, t4, ranges):
    """Reasoning chain steps."""
    r = ranges
    steps = []
    if tsh > r["tsh_high"]:
        steps.append(f"TSH = {tsh} → HIGH (>{r['tsh_high']}) → +3 pts → underactive signal")
    elif tsh < r["tsh_low"]:
        steps.append(f"TSH = {tsh} → LOW (<{r['tsh_low']}) → −3 pts → overactive signal")
    else:
        steps.append(f"TSH = {tsh} → NORMAL ({r['tsh_low']}–{r['tsh_high']}) → 0 pts")
    if t3 < r["t3_low"]:
        steps.append(f"T3 = {t3} → LOW (<{r['t3_low']}) → +1 pt → supports hypo")
    elif t3 > r["t3_high"]:
        steps.append(f"T3 = {t3} → HIGH (>{r['t3_high']}) → −1 pt → supports hyper")
    else:
        steps.append(f"T3 = {t3} → NORMAL ({r['t3_low']}–{r['t3_high']}) → 0 pts")
    if t4 < r["t4_low"]:
        steps.append(f"T4 = {t4} → LOW (<{r['t4_low']}) → +1 pt → supports hypo")
    elif t4 > r["t4_high"]:
        steps.append(f"T4 = {t4} → HIGH (>{r['t4_high']}) → −1 pt → supports hyper")
    else:
        steps.append(f"T4 = {t4} → NORMAL ({r['t4_low']}–{r['t4_high']}) → 0 pts")
    steps.append(f"Total score = {score}")
    if score >= 2:
        steps.append("Score ≥ 2 → Hypothyroidism detected")
    elif score <= -2:
        steps.append("Score ≤ −2 → Hyperthyroidism detected")
    else:
        steps.append("Score near 0 → Normal thyroid function")
    return steps


def _confidence_text(score, result):
    a = abs(score)
    if result == "Normal":
        return ("Very high confidence — all markers within normal ranges."
                if a == 0 else
                "High confidence — slight variation but overall normal pattern.")
    if a >= 5:
        return "Very high confidence — all markers strongly deviate in a consistent pattern."
    if a >= 4:
        return "High confidence — strong TSH deviation with supporting T3/T4 evidence."
    if a >= 3:
        return "Moderate-high confidence — significant TSH deviation with partial support."
    return "Moderate confidence — suggestive pattern. Further testing recommended."


def predict_thyroid(tsh, t3, t4, symptoms=None, custom_ranges=None):
    r = custom_ranges or {
        "tsh_low": 0.4, "tsh_high": 4.5,
        "t3_low": 0.8,  "t3_high": 2.0,
        "t4_low": 58,   "t4_high": 161,
    }
    score = 0
    flags = []

    # TSH (most important)
    if tsh > r["tsh_high"]:
        score += 3
        flags.append(f"TSH elevated ({tsh} mIU/L — normal: {r['tsh_low']}–{r['tsh_high']})")
    elif tsh < r["tsh_low"]:
        score -= 3
        flags.append(f"TSH suppressed ({tsh} mIU/L — normal: {r['tsh_low']}–{r['tsh_high']})")
    else:
        flags.append(f"TSH normal ({tsh} mIU/L)")

    # T3
    if t3 < r["t3_low"]:
        score += 1
        flags.append(f"T3 low ({t3} nmol/L — normal: {r['t3_low']}–{r['t3_high']})")
    elif t3 > r["t3_high"]:
        score -= 1
        flags.append(f"T3 elevated ({t3} nmol/L — normal: {r['t3_low']}–{r['t3_high']})")
    else:
        flags.append(f"T3 normal ({t3} nmol/L)")

    # T4
    if t4 < r["t4_low"]:
        score += 1
        flags.append(f"T4 low ({t4} nmol/L — normal: {r['t4_low']}–{r['t4_high']})")
    elif t4 > r["t4_high"]:
        score -= 1
        flags.append(f"T4 elevated ({t4} nmol/L — normal: {r['t4_low']}–{r['t4_high']})")
    else:
        flags.append(f"T4 normal ({t4} nmol/L)")

    # Symptom adjustment with detailed analysis
    adj = 0
    symptom_analysis = []
    if symptoms:
        for s in symptoms:
            if s in SYMPTOMS:
                sym_info = SYMPTOMS[s]
                sym_explain = SYMPTOM_EXPLANATIONS.get(s, {})
                # Calculate this symptom's contribution
                contribution = 0
                if score > 0:  # leaning hypo
                    contribution = sym_info["hypo"] * 0.5
                    adj += contribution
                elif score < 0:  # leaning hyper
                    contribution = -(sym_info["hyper"] * 0.5)
                    adj += contribution
                # Determine which condition we're leaning toward for explanation
                if score > 0:
                    condition = "Hypothyroidism"
                elif score < 0:
                    condition = "Hyperthyroidism"
                else:
                    condition = "Normal"
                explain_data = sym_explain.get(condition, {})
                correlates = explain_data.get("correlates", False)
                reason = explain_data.get("reason", "")
                symptom_analysis.append({
                    "symptom": sym_info["label"],
                    "key": s,
                    "correlates": correlates,
                    "status": "Supports diagnosis" if correlates else "Does not match typical pattern",
                    "reason": reason,
                    "score_impact": round(contribution, 1),
                    "condition_checked_against": condition,
                })
    total = score + adj

    # Determine result
    if total >= 2:
        result = "Hypothyroidism"
        risk = "High" if total >= 4 else "Medium"
        risk_score = min(95, 50 + int(total) * 10)
    elif total <= -2:
        result = "Hyperthyroidism"
        risk = "High" if total <= -4 else "Medium"
        risk_score = min(95, 50 + int(abs(total)) * 10)
    else:
        result = "Normal"
        risk = "Low"
        risk_score = max(5, 30 - int(abs(total)) * 5)

    # Severity
    at = abs(total)
    if result == "Normal":
        severity = "Normal"
    elif at >= 5:
        severity = "Severe"
    elif at >= 3.5:
        severity = "Moderate"
    else:
        severity = "Mild"

    return {
        "result": result,
        "risk": risk,
        "risk_score": risk_score,
        "score": score,
        "adjusted_score": round(total, 1),
        "severity": severity,
        "flags": flags,
        "tips": TIPS[result],
        "possible_causes": POSSIBLE_CAUSES[result],
        "explanation": _build_explanation(result, tsh, t3, t4, severity),
        "logic": _build_logic(score, tsh, t3, t4, r),
        "confidence_explanation": _confidence_text(int(total), result),
        "diet": DIET[result],
        "lifestyle": LIFESTYLE[result],
        "values": {"tsh": tsh, "t3": t3, "t4": t4},
        "ranges": r,
        "symptom_analysis": symptom_analysis,
        "symptom_summary": _build_symptom_summary(symptom_analysis, result, adj) if symptom_analysis else None,
    }


def _build_symptom_summary(analysis, result, adj):
    """Build an overall summary of symptom correlation."""
    total = len(analysis)
    supporting = sum(1 for a in analysis if a["correlates"])
    contradicting = total - supporting
    if total == 0:
        return None
    pct = int((supporting / total) * 100)
    if result == "Normal":
        summary = f"You reported {total} symptom(s). "
        if supporting > 0:
            summary += f"{supporting} could be thyroid-related in other conditions, but your lab values are normal. "
        summary += "Monitor these symptoms and mention them at your next doctor visit."
    else:
        summary = f"Of {total} symptom(s) reported, {supporting} ({pct}%) correlate with {result}. "
        if contradicting > 0:
            summary += f"{contradicting} symptom(s) don't match the typical pattern — this could indicate a mixed or early-stage presentation. "
        if adj != 0:
            summary += f"Symptoms adjusted risk score by {'+' if adj > 0 else ''}{round(adj, 1)} points."
    return summary


# ── Routes ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", symptoms=SYMPTOMS)


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    try:
        tsh = float(data["tsh"])
        t3  = float(data["t3"])
        t4  = float(data["t4"])
        if tsh < 0 or t3 < 0 or t4 < 0:
            return jsonify({"error": "Values cannot be negative"}), 400
        symptoms = data.get("symptoms", [])
        custom_ranges = data.get("custom_ranges", None)
        result = predict_thyroid(tsh, t3, t4, symptoms, custom_ranges)
        return jsonify(result)
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid input — please enter valid numbers"}), 400


if __name__ == "__main__":
    app.run(debug=True)
