"""Generate ThyroCheck System Architecture PDF"""
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_fill_color(124, 58, 237)
        self.rect(0, 0, 210, 18, 'F')
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, 'ThyroCheck - System Architecture & Technical Documentation', align='C')
        self.ln(18)

    def footer(self):
        self.set_y(-10)
        self.set_font('Helvetica', '', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'ThyroCheck System Architecture | Page {self.page_no()}/{{nb}}', align='C')

    def section_title(self, title):
        self.ln(4)
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(124, 58, 237)
        self.cell(0, 8, title)
        self.ln(2)
        self.set_draw_color(124, 58, 237)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def sub_title(self, title):
        self.ln(2)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(60, 60, 80)
        self.cell(0, 6, title)
        self.ln(6)

    def body_text(self, text):
        self.set_font('Helvetica', '', 9)
        self.set_text_color(60, 60, 80)
        self.multi_cell(0, 4.5, text)
        self.ln(2)

    def mono_text(self, text):
        self.set_font('Courier', '', 8)
        self.set_text_color(80, 80, 100)
        self.multi_cell(0, 4, text)
        self.ln(1)

    def bullet(self, text, indent=10):
        x = self.get_x()
        self.set_font('Helvetica', '', 9)
        self.set_text_color(60, 60, 80)
        self.set_x(indent)
        self.cell(4, 4.5, chr(8226))
        self.multi_cell(180 - indent, 4.5, text)
        self.ln(1)

    def table_row(self, cols, widths, bold=False, fill=False):
        self.set_font('Helvetica', 'B' if bold else '', 8)
        if fill:
            self.set_fill_color(240, 238, 255)
        self.set_text_color(40, 40, 60)
        for i, (col, w) in enumerate(zip(cols, widths)):
            self.cell(w, 6, col, border=1, fill=fill)
        self.ln()


pdf = PDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

# 1. Overview
pdf.section_title('1. Project Overview')
pdf.body_text('ThyroCheck is an AI-assisted thyroid screening and monitoring dashboard that analyzes thyroid hormone levels (TSH, T3, T4) along with patient-reported symptoms to provide a comprehensive thyroid health assessment. It features real-time risk scoring, detailed medical explanations, trend tracking, and PDF report generation.')

# 2. Tech Stack
pdf.section_title('2. Technology Stack')
headers = ['Layer', 'Technology', 'Purpose']
widths = [35, 40, 115]
pdf.table_row(headers, widths, bold=True, fill=True)
rows = [
    ['Backend', 'Flask (Python 3)', 'REST API server, template rendering, routing'],
    ['Templating', 'Jinja2', 'Server-side HTML rendering with dynamic data'],
    ['Frontend', 'Vanilla HTML/CSS/JS', 'UI and interactivity, zero framework dependency'],
    ['Charts', 'Chart.js 4.4.4 (CDN)', 'Line charts for thyroid value trend visualization'],
    ['PDF Generation', 'jsPDF 2.5.1 (CDN)', 'Client-side multi-page PDF report creation'],
    ['Typography', 'Inter (Google Fonts)', 'Premium variable font (weights 300-900)'],
    ['Data Storage', 'localStorage', 'Test history, theme, custom ranges (no database)'],
    ['Prod Server', 'Gunicorn 22.0.0', 'WSGI server for cloud deployment'],
]
for r in rows:
    pdf.table_row(r, widths)

# 3. File Structure
pdf.section_title('3. File Structure')
pdf.mono_text("""E:\\Adi\\thyroid\\
+-- app.py                 # Flask backend - all API logic (400+ lines)
+-- requirements.txt       # Python deps: flask, gunicorn
+-- Procfile              # Deployment: web: gunicorn app:app
+-- static/
|   +-- style.css         # Design system: dark/light themes, glassmorphism
|   +-- script.js         # Frontend logic: charts, gauge, PDF, history
|   +-- logo.png          # Thyroid gland logo image
+-- templates/
    +-- index.html        # Single-page HTML template (Jinja2)""")

# 4. Architecture
pdf.section_title('4. System Architecture')
pdf.sub_title('4.1 Request Flow')
pdf.body_text('1. User opens http://127.0.0.1:5000 -> Flask serves index.html via Jinja2 template engine, injecting the SYMPTOMS dictionary into the HTML for checkbox rendering.')
pdf.body_text('2. User enters lab values (TSH, T3, T4) via number inputs or sliders. Live color-coding validates values in real-time (red border = abnormal, green = normal).')
pdf.body_text('3. User optionally checks symptom checkboxes (12 available symptoms).')
pdf.body_text('4. User clicks "Analyse thyroid function" -> JavaScript sends POST request to /predict endpoint with JSON payload: {tsh, t3, t4, symptoms[], custom_ranges}.')
pdf.body_text('5. Flask backend runs predict_thyroid() function: calculates score, determines diagnosis, generates all content (explanation, logic, causes, diet, etc.).')
pdf.body_text('6. Backend returns comprehensive JSON response (20+ fields).')
pdf.body_text('7. Frontend showResult() renders all UI sections: gauge, comparison bars, flags, explanation, symptom analysis, causes, diet, lifestyle, alerts.')
pdf.body_text('8. Result is saved to localStorage history. Trend chart updates.')

pdf.sub_title('4.2 Two-Layer Architecture')
pdf.body_text('CLIENT LAYER (Browser): HTML template rendered by Jinja2, styled with CSS custom properties for theming. JavaScript handles all interactivity, chart rendering, localStorage persistence, and PDF generation. No state is stored on the server.')
pdf.body_text('SERVER LAYER (Flask): Stateless REST API. Single POST endpoint /predict receives lab values and symptoms, runs the scoring algorithm, generates all textual content, and returns JSON. The GET / endpoint serves the HTML template with symptom definitions injected.')

# 5. Scoring Algorithm
pdf.section_title('5. Thyroid Scoring Algorithm')
pdf.sub_title('5.1 Base Score Calculation')
pdf.body_text('The diagnostic engine uses a weighted rule-based scoring system. TSH is weighted 3x because it is the primary screening marker used by endocrinologists.')
pdf.mono_text("""TSH > 4.5 mIU/L  ->  +3 points  (strong hypothyroid signal)
TSH < 0.4 mIU/L  ->  -3 points  (strong hyperthyroid signal)
T3  < 0.8 nmol/L  ->  +1 point   (supports hypothyroid)
T3  > 2.0 nmol/L  ->  -1 point   (supports hyperthyroid)
T4  < 58  nmol/L  ->  +1 point   (supports hypothyroid)
T4  > 161 nmol/L  ->  -1 point   (supports hyperthyroid)

Score Range: -5 to +5
  score >= +2  ->  Hypothyroidism
  score <= -2  ->  Hyperthyroidism
  -1 to +1     ->  Normal""")

pdf.sub_title('5.2 Symptom Adjustment')
pdf.body_text('Each of the 12 symptoms has a hypo and hyper weight (0 or 1). When checked, the symptom contributes +/- 0.5 points based on the direction the score is already leaning. This prevents symptoms from flipping a diagnosis but allows them to strengthen confidence.')
pdf.mono_text("""Symptoms tracked: Weight gain, Weight loss, Fatigue, Anxiety,
Hair loss, Heat intolerance, Cold intolerance, Rapid heartbeat,
Tremors, Constipation, Dry skin, Neck swelling

Each symptom also gets a CORRELATION ANALYSIS with a detailed
medical explanation of WHY it does/doesn't match the diagnosis.
36 unique explanations (12 symptoms x 3 conditions).""")

pdf.sub_title('5.3 Severity & Risk')
pdf.mono_text("""Severity Classification:
  |adjusted_score| >= 5    ->  Severe
  |adjusted_score| >= 3.5  ->  Moderate
  |adjusted_score| >= 2    ->  Mild

Risk Score (percentage):
  Hypo:   min(95, 50 + score * 10)
  Hyper:  min(95, 50 + |score| * 10)
  Normal: max(5, 30 - |score| * 5)""")

# 6. Frontend
pdf.section_title('6. Frontend Architecture')
pdf.sub_title('6.1 Design System')
pdf.body_text('The CSS uses custom properties (CSS variables) for theming. The dark theme is default, using deep purple/blue tones (#06081a background) with glassmorphism cards (backdrop-filter: blur). The light theme overrides these variables. Theme preference is persisted in localStorage.')
pdf.bullet('Glassmorphism: backdrop-filter: blur(24px) on all cards')
pdf.bullet('Gradient accents: linear-gradient(135deg, #a78bfa, #6366f1, #06b6d4)')
pdf.bullet('Custom checkboxes: CSS-only with gradient fill and checkmark pseudo-element')
pdf.bullet('Custom range sliders: Styled thumb with gradient, glow shadow, scale-on-hover')
pdf.bullet('Micro-animations: fadeUp, slideIn keyframes on result appearance')
pdf.bullet('Live input validation: Red glow for abnormal, green glow for normal values')
pdf.bullet('Responsive: 2-column grid collapses to 1 column at 740px')

pdf.sub_title('6.2 SVG Gauge')
pdf.body_text('The risk gauge is a custom SVG semicircular arc drawn programmatically. A gray background arc (180 degrees) sits behind a colored foreground arc that animates from 0 to the risk score percentage. Color is determined by risk level: green (Low), yellow (Medium), red (High). SVG animate element provides smooth arc growth.')

pdf.sub_title('6.3 Chart.js Trend Graph')
pdf.body_text('Uses Chart.js 4.x to render a line chart showing TSH, T3, and T4 values over time from localStorage history. TSH and T3 share the left Y-axis, T4 uses the right Y-axis (different scale). The chart updates automatically after each analysis.')

pdf.sub_title('6.4 PDF Report Generation')
pdf.body_text('Uses jsPDF to programmatically write text, shapes, and colors directly to a PDF document. This approach was chosen over html2canvas because it works reliably regardless of CSS themes. The report includes: purple header banner, color-coded diagnosis box, lab values table, marker analysis, interpretation, confidence, diagnostic reasoning, symptom correlation, possible causes, diet, lifestyle, health guidance, and page-numbered footer.')

# 7. API
pdf.section_title('7. API Reference')
pdf.sub_title('GET /')
pdf.body_text('Serves the main HTML page. Injects the SYMPTOMS dictionary into the Jinja2 template for checkbox rendering.')

pdf.sub_title('POST /predict')
pdf.body_text('Accepts JSON body: { tsh: float, t3: float, t4: float, symptoms: string[], custom_ranges: object|null }')
pdf.body_text('Returns JSON with 20+ fields: result, risk, risk_score, severity, flags, tips, possible_causes, explanation, logic, confidence_explanation, diet, lifestyle, values, ranges, symptom_analysis, symptom_summary.')

# 8. Features
pdf.section_title('8. Complete Feature List (24 Features)')
features = [
    ['1', 'Thyroid Screening', 'Rule-based scoring (TSH*3 + T3 + T4)'],
    ['2', 'Symptom Adjustment', '12 checkboxes, +/-0.5 pts, correlation analysis'],
    ['3', 'SVG Risk Gauge', 'Animated semicircular arc visualization'],
    ['4', 'Comparison Bars', 'Value vs normal range horizontal bars'],
    ['5', 'Trend Chart', 'Chart.js line chart from localStorage history'],
    ['6', 'Dark/Light Mode', 'CSS custom properties + data-theme toggle'],
    ['7', 'Explain My Report', 'Plain-English medical explanation'],
    ['8', 'Diagnostic Reasoning', 'Step-by-step logic chain display'],
    ['9', 'Confidence Level', 'Score-based confidence explanation'],
    ['10', 'Possible Causes', 'Condition-specific medical causes'],
    ['11', 'Symptom Correlation', 'Per-symptom YES/NO with medical reasoning'],
    ['12', 'Diet Recommendations', 'Condition + Indian diet specific tips'],
    ['13', 'Lifestyle Suggestions', 'Exercise, stress, sleep guidance'],
    ['14', 'Smart Alerts', 'Severity-based urgency notifications'],
    ['15', 'Doctor Mode', 'Clinical view with units and refs'],
    ['16', 'PDF Report', 'jsPDF multi-page medical report'],
    ['17', 'Custom Lab Ranges', 'Editable reference intervals'],
    ['18', 'Test History', 'localStorage, 20 entries max'],
    ['19', 'Trend Tracking', 'Rising/Improving/Stable indicators'],
    ['20', 'Live Validation', 'Red/green input border coloring'],
    ['21', 'Slider Inputs', 'Synced with number fields'],
    ['22', 'Tooltips', 'Hover explanations for markers'],
    ['23', 'Preset Cases', 'Quick-fill hypo/hyper/normal'],
    ['24', 'Severity Badges', 'Mild/Moderate/Severe classification'],
]
fw = [8, 45, 137]
pdf.table_row(['#', 'Feature', 'Implementation'], fw, bold=True, fill=True)
for f in features:
    pdf.table_row(f, fw)

# 9. Deployment
pdf.section_title('9. How to Run & Deploy')
pdf.sub_title('Local Development')
pdf.mono_text("""cd E:\\Adi\\thyroid
pip install flask
python app.py
# Open: http://127.0.0.1:5000""")
pdf.sub_title('Cloud Deployment')
pdf.body_text('The app includes Procfile and requirements.txt for one-click deployment to Heroku, Railway, Render, or Fly.io. Simply push the code to a Git repository and connect it to any platform supporting Python WSGI apps.')

# Save
output_path = r'E:\Adi\thyroid\ThyroCheck_Architecture.pdf'
pdf.output(output_path)
print(f'PDF saved to: {output_path}')
