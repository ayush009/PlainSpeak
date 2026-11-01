"""
Generate a detailed fictional discharge PDF with intentional, layered ambiguities.

All names, places, clinical details are entirely fictional.
Run:  uv run python scripts/make_ambiguous_pdf.py

Output: fixtures/ambiguous_discharge.pdf  (overwrites)
"""

from __future__ import annotations
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "fixtures" / "ambiguous_discharge2.pdf"


def make() -> None:
    try:
        from fpdf import FPDF
    except ModuleNotFoundError:
        print("fpdf2 not installed. Run: uv sync --group dev")
        return

    # -- Layout helpers --------------------------------------------------------

    class Doc(FPDF):
        def header(self):
            self.set_font("Helvetica", "I", 7.5)
            self.set_text_color(140, 140, 140)
            self.cell(0, 5,
                      "FICTIONAL TRAINING DOCUMENT - NOT A REAL PRESCRIPTION OR MEDICAL RECORD",
                      align="C")
            self.ln(3)
            self.set_draw_color(200, 200, 200)
            self.set_line_width(0.3)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(2)
            self.set_text_color(0, 0, 0)

        def footer(self):
            self.set_y(-14)
            self.set_font("Helvetica", "I", 7.5)
            self.set_text_color(140, 140, 140)
            self.cell(0, 5, f"Page {self.page_no()} of {{nb}}", align="C")
            self.set_text_color(0, 0, 0)

    pdf = Doc()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(True, 20)
    pdf.set_margins(22, 18, 22)

    NAVY  = (18, 50, 79)
    GREY  = (90, 103, 117)
    BLACK = (0, 0, 0)

    def rule():
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.25)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(3)

    def h1(txt: str) -> None:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 9, _s(txt), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(*NAVY)
        pdf.set_line_width(0.6)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(3)
        pdf.set_text_color(*BLACK)

    def h2(txt: str) -> None:
        pdf.ln(1)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*NAVY)
        pdf.cell(0, 7, _s(txt), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*BLACK)

    CW = pdf.w - pdf.l_margin - pdf.r_margin  # content width (166 mm)

    def _s(t: str) -> str:
        return t.replace("—", " - ").replace("–", "-").replace("'", "'").replace("“", '"').replace("”", '"').replace("°", " degrees")

    def body(txt: str, size: int = 10) -> None:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", size)
        pdf.set_text_color(*BLACK)
        pdf.multi_cell(CW, 5.5, _s(txt), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1.5)

    KW = 48  # key column width
    VW = CW - KW  # value column width

    def kv(key: str, val: str) -> None:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*GREY)
        pdf.cell(KW, 6, _s(key), new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*BLACK)
        pdf.set_x(pdf.l_margin + KW)
        pdf.multi_cell(VW, 6, _s(val), new_x="LMARGIN", new_y="NEXT")

    # =========================================================================
    # PAGE 1 -- Cover / Patient details
    # =========================================================================
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 11, "DISCHARGE SUMMARY", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    rule()

    h2("Patient details")
    kv("Full name:", "Robert Ellis (fictional)")
    kv("Date of birth:", "14 March 1957  (age 69)")
    kv("MRN:", "FICTIONAL-001")
    kv("Ward:", "Orthopaedic Ward 7B, Riverside Demo Hospital (fictional)")
    kv("Admitted:", "21 October 2026")
    kv("Discharged:", "24 October 2026")
    kv("Primary contact:", "Margaret Ellis (wife) - caregiver")
    pdf.ln(3)

    h2("Procedure and diagnosis")
    kv("Procedure:", "Left total hip arthroplasty (cemented)")
    kv("Surgeon:", "Dr. A. Nkosi (fictional), Orthopaedic Surgery")
    kv("Anaesthetic:", "Spinal anaesthesia with sedation")
    kv("Diagnosis:", "Primary osteoarthritis of the left hip, end-stage")
    kv("Implant:", "Details on file with the surgical team (not reproduced here)")
    pdf.ln(3)

    h2("Discharge status")
    body(
        "Mr Ellis was discharged in a clinically stable condition following an uncomplicated "
        "left total hip arthroplasty. He is ambulatory with a walking frame. Oral analgesia "
        "has been commenced. All post-operative observations were within normal limits at "
        "the time of discharge. The patient was accompanied home by his wife."
    )

    # =========================================================================
    # PAGE 2 -- Medications
    # =========================================================================
    pdf.add_page()
    h1("Section 2 - Medications")

    h2("2.1  Prescribed anti-inflammatory (pain management)")
    body(
        "Mr Ellis has been prescribed an oral non-steroidal anti-inflammatory drug (NSAID) "
        "for post-operative pain management. The specific product and dose are documented on "
        "the pharmacy dispensing label attached to the medication packaging."
    )
    body(
        "Dosing schedule: take as required when pain is present, OR on a regular scheduled "
        "basis as directed by the dispensing pharmacist."
    )
    body(
        "Starting dose: adjust per individual tolerance and response. "
        "Do not exceed the maximum daily dose stated on the product label."
    )

    h2("2.2  Paracetamol (adjunct analgesia)")
    body(
        "Paracetamol 500 mg to 1 g may be taken as needed for additional pain relief. "
        "Frequency: every 4 to 6 hours as required."
    )

    h2("2.3  Existing home medications")
    body(
        "Continue ALL existing home medications unless otherwise instructed by the "
        "surgical team or GP."
    )

    h2("2.4  Weaning off anti-inflammatories")
    body(
        "The prescribed NSAID should be gradually reduced and discontinued as recovery "
        "progresses and pain subsides."
    )

    # =========================================================================
    # PAGE 3 -- Wound Care
    # =========================================================================
    pdf.add_page()
    h1("Section 3 - Wound Care")

    h2("3.1  Initial dry period")
    body(
        "The surgical wound must be kept completely dry for the first 48 hours "
        "following discharge."
    )

    h2("3.2  Showering and bathing")
    body(
        "The patient may take a light shower after day 3 post-discharge provided the "
        "wound area is adequately covered with a waterproof dressing."
    )
    body(
        "Do not submerge the wound site in water (baths, swimming pools) until "
        "the wound is fully healed and the skin is intact."
    )

    h2("3.3  Dressing changes")
    body(
        "Perform daily dressing changes until the wound is fully healed. "
        "Dressing materials have been included in the discharge pack provided at the ward."
    )
    body(
        "Do not disturb the primary wound dressing unless it becomes soiled or saturated. "
        "If in doubt, contact the district nursing team."
    )

    h2("3.4  Wound monitoring")
    body(
        "Inspect the wound at each dressing change. Contact the surgical team or attend "
        "the emergency department if any of the following are observed:"
    )
    body(
        "  - Redness, increasing warmth or swelling around the wound\n"
        "  - Any discharge (clear, yellow or blood-stained)\n"
        "  - Wound edges separating or sutures/clips appearing loose\n"
        "  - Fever above 38.0 degrees C\n"
        "  - Increasing rather than decreasing pain after the first 48 hours"
    )

    # =========================================================================
    # PAGE 4 -- Mobility and Activity
    # =========================================================================
    pdf.add_page()
    h1("Section 4 - Mobility and Activity")

    h2("4.1  Immediate post-discharge rest")
    body(
        "Strict bed rest is recommended for the first 24 to 48 hours following discharge "
        "to allow the surgical site to stabilise."
    )

    h2("4.2  Early mobilisation")
    body(
        "Early mobilisation is strongly encouraged to reduce the risk of complications "
        "including deep vein thrombosis (DVT), chest infection and pressure injury. "
        "Short, gentle walks with the walking frame should begin as soon as the patient "
        "feels able to do so."
    )

    h2("4.3  Hip precautions")
    body(
        "Standard hip precautions must be maintained throughout the recovery period. "
        "Refer to the physiotherapy instruction sheet provided on the ward."
    )

    h2("4.4  Weight bearing")
    body(
        "Weight bearing: as tolerated, using the walking frame provided."
    )
    body(
        "Note from physiotherapy assessment: protected weight bearing recommended until "
        "reviewed at follow-up. Do not progress beyond partial weight bearing without "
        "physiotherapist review."
    )

    h2("4.5  Stairs")
    body(
        "Stair use is permitted with caution once the patient has adequate strength "
        "and confidence. Always use the handrail and take one step at a time."
    )
    body(
        "Avoid stairs where possible during the initial recovery phase."
    )

    h2("4.6  Physical therapy")
    body(
        "A physiotherapy referral has been submitted. Community physiotherapy will make "
        "contact to arrange an initial assessment. Begin gentle range-of-motion exercises "
        "when the patient feels comfortable and ready."
    )

    h2("4.7  Driving")
    body(
        "Mr Ellis must not drive until he is able to perform an emergency stop safely "
        "and has received medical clearance from his GP or the surgical team."
    )

    h2("4.8  Return to work and domestic activities")
    body(
        "Light domestic activities are permitted when the patient feels comfortable. "
        "Return to work should be discussed with the surgeon at the follow-up appointment. "
        "Heavy lifting (over approximately 5 kg) should be avoided until cleared by the "
        "surgical team - no specific timeframe is given."
    )

    # =========================================================================
    # PAGE 5 -- Follow-up and Emergency
    # =========================================================================
    pdf.add_page()
    h1("Section 5 - Follow-up Appointments")

    h2("5.1  Surgical follow-up")
    body(
        "Attend a follow-up appointment at the Orthopaedic Outpatient Clinic in "
        "approximately 4 to 6 weeks post-discharge."
    )
    body(
        "A written appointment confirmation will be sent by post to the patient's "
        "registered home address. No specific date or time was confirmed at the point "
        "of discharge. If the letter has not arrived within 10 days, contact the "
        "outpatient booking team at the number on your clinic letter."
    )

    h2("5.2  GP review")
    body(
        "Mr Ellis should see his GP within 2 weeks of discharge if he has any concerns "
        "or if recovery is not progressing as expected."
    )

    h2("5.3  Blood tests")
    body(
        "Routine blood tests are required at the follow-up appointment. "
        "Fasting may be required - await further instruction from the clinic."
    )

    h1("Section 6 - Emergency Guidance")

    h2("6.1  When to seek urgent help")
    body(
        "Return IMMEDIATELY to the emergency department or call emergency services if "
        "experiencing any of the following:"
    )
    body(
        "  - High fever (above 38.5 degrees C)\n"
        "  - Severe or rapidly worsening pain not responding to prescribed medication\n"
        "  - Sudden significant swelling of the operated limb\n"
        "  - Signs of wound infection (redness, heat, discharge, unpleasant odour)\n"
        "  - Calf pain and/or swelling in either leg (possible DVT)\n"
        "  - Shortness of breath or chest pain (possible pulmonary embolism)\n"
        "  - Dislocation or suspected dislocation of the hip implant"
    )

    h2("6.2  Non-urgent queries")
    body(
        "For non-urgent post-discharge questions, contact the surgical team during "
        "working hours using the contact details provided on your discharge letter."
    )

    h2("6.3  General welfare")
    body(
        "If Mr Ellis appears generally unwell - such as confusion, unusual drowsiness, "
        "or significant deterioration in function - seek medical advice promptly."
    )

    # -- Output ----------------------------------------------------------------
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT))
    print(f"Written -> {OUT}  ({OUT.stat().st_size:,} bytes, {pdf.page_no()} pages)")


if __name__ == "__main__":
    make()
