from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import os


# =====================================================
# PDF TABLE STYLE
# =====================================================

def create_table(data):

    table = Table(
        data,
        colWidths=[170, 300]
    )

    table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#E8F5E9")
            ),

            (
                "FONTNAME",
                (0, 0),
                (0, -1),
                "Helvetica-Bold"
            ),

            (
                "FONTNAME",
                (1, 0),
                (1, -1),
                "Helvetica"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            )
        ])
    )

    return table


# =====================================================
# MAIN REPORT
# =====================================================

def generate_pdf_report(filename, analysis, decision):

    os.makedirs("reports", exist_ok=True)

    pdf_name = (
        f"REPORT_{os.path.splitext(filename)[0]}.pdf"
    )

    pdf_path = os.path.join(
        "reports",
        pdf_name
    )

    doc = SimpleDocTemplate(
        pdf_path,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()

    styles["Heading1"].alignment = TA_CENTER

    story = []

    # =================================================
    # TITLE
    # =================================================

    story.append(
        Paragraph(
            "<font color='#1B5E20'>"
            "<b>AI MEDIA INTEGRITY DETECTOR</b>"
            "</font>",
            styles["Heading1"]
        )
    )

    story.append(
        Paragraph(
            "<b>Digital Forensic Analysis Report</b>",
            styles["Heading2"]
        )
    )

    story.append(
        Spacer(1, 0.15 * inch)
    )

    # =================================================
    # HEADER
    # =================================================

    now = datetime.now()

    color_map = {
        "Authentic": "green",
        "Probably Authentic": "#2E8B57",
        "Needs Manual Review": "#DAA520",
        "Suspicious": "#FF8C00",
        "High Risk": "red",
        "Likely Deepfake": "#8B0000",
        "Confirmed Manipulation": "black"
    }

    prediction_text = decision.get(
        "prediction",
        "Unknown"
    )

    prediction = Paragraph(
        (
            f"<font color='"
            f"{color_map.get(prediction_text, 'black')}"
            f"'><b>{prediction_text}</b></font>"
        ),
        styles["BodyText"]
    )

    integrity_score = decision.get(
        "integrity_score",
        "-"
    )

    header_data = [
        ["Original File", filename],

        ["Prediction", prediction],

        [
            "Integrity Score",
            f"{integrity_score} / 100"
        ],

        [
            "Generated",
            now.strftime(
                "%d-%b-%Y  %I:%M %p"
            )
        ]
    ]

    story.append(
        create_table(header_data)
    )

    story.append(
        Spacer(1, 0.12 * inch)
    )

    # =================================================
    # IMAGE ANALYSIS
    # =================================================

    story.append(
        Paragraph(
            "<b>Image Analysis</b>",
            styles["Heading2"]
        )
    )

    image_data = [
        [
            "Width",
            f"{analysis.get('width', '-')} px"
        ],
        [
            "Height",
            f"{analysis.get('height', '-')} px"
        ],
        [
            "Channels",
            str(analysis.get('channels', "-"))
        ],
        [
            "Image Type",
                analysis.get("image_type", "-")
        ],
        [
            "Aspect Ratio",
            str(analysis.get("aspect_ratio", "-"))
        ],
        [
            "Resolution",
            analysis.get("resolution_status", "-")
        ],
            [
            "File Size",
            f"{analysis.get('file_size_bytes', 0) / (1024 * 1024):.2f} MB"
            ]
    ]

    story.append(
        create_table(image_data)
    )

    story.append(
        Spacer(1, 0.10 * inch)
    )

    # =================================================
    # EXIF METADATA
    # =================================================

    story.append(
        Paragraph(
            "<b>EXIF Metadata</b>",
            styles["Heading2"]
        )
    )

    exif = analysis.get(
        "exif",
        {}
    )

    if exif:

        exif_data = [
            [
                "Camera Make",
                exif.get("Make", "-")
            ],

            [
                "Camera Model",
                exif.get("Model", "-")
            ],

            [
                "Date Taken",
                exif.get("DateTime", "-")
            ],

            [
                "ISO",
                exif.get("ISOSpeedRatings", "-")
            ],

            [
                "Aperture",
                exif.get("FNumber", "-")
            ],

            [
                "Exposure",
                exif.get("ExposureTime", "-")
            ],

            [
                "Focal Length",
                exif.get("FocalLength", "-")
            ]
        ]

    else:

        exif_data = [
            [
                "Status",
                "No EXIF metadata found."
            ]
        ]

    story.append(
        create_table(exif_data)
    )

    story.append(
        Spacer(1, 0.10 * inch)
    )

    # =================================================
    # FORENSIC ANALYSIS
    # =================================================

    story.append(
        Paragraph(
            "<b>Forensic Analysis</b>",
            styles["Heading2"]
        )
    )

    ela = analysis.get(
        "ela",
        {}
    )

    noise = analysis.get(
        "noise",
        {}
    )

    copy_move = analysis.get(
        "copy_move",
        {}
    )

    forensic_data = [
        [
            "Error Level Analysis",
            ela.get("status", "Not available")
        ],

        [
            "ELA Details",
            ela.get("details", "-")
        ],

        [
            "Noise Analysis",
            noise.get("status", "Not available")
        ],

        [
            "Noise Details",
            noise.get("details", "-")
        ],

        [
            "Copy-Move Detection",
            copy_move.get(
                "status",
                "Not available"
            )
        ],

        [
            "Copy-Move Details",
            copy_move.get("details", "-")
        ],

        [
            "Copy-Move Matches",
            str(copy_move.get("matches", "-"))
        ]
    ]

    story.append(
        create_table(forensic_data)
    )

    story.append(
        Spacer(1, 0.10 * inch)
    )

    # =================================================
    # FINAL DECISION
    # =================================================

    story.append(
        Paragraph(
            "<b>Final Decision</b>",
            styles["Heading2"]
        )
    )

    final_data = [
        [
            "Prediction",
            prediction
        ],

        [
            "Integrity Score",
            f"{integrity_score} / 100"
        ]
    ]

    story.append(
        create_table(final_data)
    )

    story.append(
        Spacer(1, 0.10 * inch)
    )

    # =================================================
    # REASONS
    # =================================================

    story.append(
        Paragraph(
            "<b>Forensic Findings</b>",
            styles["Heading2"]
        )
    )

    reasons = decision.get(
        "reasons",
        []
    )

    if reasons:

        for reason in reasons:

            story.append(
                Paragraph(
                    f"• {reason}",
                    styles["BodyText"]
                )
            )

            story.append(
                Spacer(1, 0.03 * inch)
            )

    else:

        story.append(
            Paragraph(
                "No findings were returned by the "
                "available forensic analyses.",
                styles["BodyText"]
            )
        )

    story.append(
        Spacer(1, 0.12 * inch)
    )

    # =================================================
    # ASSESSMENT NOTE
    # =================================================

    story.append(
        Paragraph(
            "<b>Assessment Note</b>",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            "The result is based on the forensic indicators "
            "available to the system. Individual indicators "
            "such as compression differences, noise "
            "variation, metadata, or repeated features do "
            "not by themselves prove that an image is "
            "manipulated or generated by AI. The result "
            "should be considered an automated assessment "
            "and may require manual review.",
            styles["BodyText"]
        )
    )

    story.append(
        Spacer(1, 0.12 * inch)
    )

    # =================================================
    # PROJECT INFORMATION
    # =================================================

    story.append(
        Paragraph(
            "<b>Project Information</b>",
            styles["Heading2"]
        )
    )

    project_data = [
        [
            "Project",
            "AI Media Integrity Detector"
        ],

        [
            "Version",
            "2.0"
        ],

        [
            "Developer",
            "NALLABELLI RAMESH"
        ]
    ]

    story.append(
        create_table(project_data)
    )

    story.append(
        Spacer(1, 0.12 * inch)
    )

    # =================================================
    # FOOTER
    # =================================================

    story.append(
        Paragraph(
            "<font size='8' color='grey'>"
            "Generated by AI Media Integrity Detector "
            "© 2026"
            "</font>",
            styles["BodyText"]
        )
    )

    # =================================================
    # BUILD PDF
    # =================================================

    doc.build(story)

    return pdf_path