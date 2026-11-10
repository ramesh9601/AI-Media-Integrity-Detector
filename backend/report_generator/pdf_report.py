import os
import uuid
from datetime import datetime
from xml.sax.saxutils import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
)


# ============================================================
# CONFIGURATION
# ============================================================

REPORT_FOLDER = "reports"
os.makedirs(REPORT_FOLDER, exist_ok=True)

GREEN = colors.HexColor("#176B55")
DARK_GREEN = colors.HexColor("#123B32")
LIGHT_GREEN = colors.HexColor("#E8F5E9")
BORDER = colors.HexColor("#C8D6CC")
GREY = colors.HexColor("#666666")


# ============================================================
# STYLES
# ============================================================

styles = getSampleStyleSheet()

styles.add(
    ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=23,
        alignment=TA_CENTER,
        textColor=DARK_GREEN,
        spaceAfter=5,
    )
)

styles.add(
    ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Heading2"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        textColor=GREEN,
        spaceAfter=10,
    )
)

styles.add(
    ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=GREEN,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )
)

styles.add(
    ParagraphStyle(
        name="TableCell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        spaceBefore=0,
        spaceAfter=0,
        wordWrap="LTR",
    )
)

styles.add(
    ParagraphStyle(
        name="TableLabel",
        parent=styles["TableCell"],
        fontName="Helvetica-Bold",
    )
)

styles.add(
    ParagraphStyle(
        name="SmallText",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
        textColor=GREY,
        spaceBefore=2,
        spaceAfter=4,
    )
)

styles.add(
    ParagraphStyle(
        name="Finding",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=11,
        leftIndent=8,
        firstLineIndent=-8,
        spaceAfter=3,
    )
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_text(value, default="-"):
    """Convert a value to XML-safe text."""

    if value is None:
        value = default

    return escape(str(value))


def format_percentage(value):
    """Format a score between 0 and 1 as a percentage."""

    if value is None:
        return "Unavailable"

    try:
        score = float(value)

        if not 0 <= score <= 1:
            return "Unavailable"

        return f"{score * 100:.2f}%"

    except (TypeError, ValueError):
        return "Unavailable"


def format_file_size(value):
    """Convert bytes into a readable file size."""

    try:
        return f"{float(value) / (1024 * 1024):.2f} MB"
    except (TypeError, ValueError):
        return "Unavailable"


def get_styles():
    """Return the PDF paragraph styles."""

    return styles


# ============================================================
# PDF TABLE
# ============================================================

def create_table(data, col_widths=None, header=False):
    """
    Create a PDF table with wrapped text.

    Paragraph cells allow long filenames, project names,
    and forensic explanations to wrap within the table.
    """

    if col_widths is None:
        col_widths = [160, 300]

    wrapped_data = []

    for row_index, row in enumerate(data):
        wrapped_row = []

        for column_index, value in enumerate(row):

            if isinstance(value, Paragraph):
                wrapped_row.append(value)

            elif isinstance(value, str):

                if header and row_index == 0:
                    style = ParagraphStyle(
                        "TableHeader",
                        parent=styles["TableLabel"],
                        textColor=colors.black,
                    )

                elif column_index == 0:
                    style = styles["TableLabel"]

                else:
                    style = styles["TableCell"]

                wrapped_row.append(
                    Paragraph(value, style)
                )

            else:
                wrapped_row.append(value)

        wrapped_data.append(wrapped_row)

    table = Table(
        wrapped_data,
        colWidths=col_widths,
        repeatRows=1 if header else 0,
        hAlign="LEFT",
    )

    table_styles = [
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]

    if header:
        table_styles.append(
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GREEN)
        )
    else:
        table_styles.append(
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GREEN)
        )

    table.setStyle(TableStyle(table_styles))

    return table


def add_section(story, title):
    """Add a section heading."""

    story.append(
        Paragraph(
            safe_text(title),
            styles["SectionHeading"],
        )
    )


def add_findings(story, findings):
    """Add a list of forensic findings."""

    if not isinstance(findings, list):
        findings = [findings]

    if not findings:
        findings = [
            "No findings were returned by the available analyses."
        ]

    for finding in findings:
        story.append(
            Paragraph(
                f"&bull; {safe_text(finding)}",
                styles["Finding"],
            )
        )


# ============================================================
# FOOTER
# ============================================================

def draw_page_footer(canvas_obj, document):
    """
    Draw a footer on every page.

    The footer is drawn directly on the page rather than
    being added to the story, so it cannot create a page
    by itself.
    """

    canvas_obj.saveState()

    page_width, _ = A4

    canvas_obj.setStrokeColor(BORDER)
    canvas_obj.setLineWidth(0.5)

    canvas_obj.line(
        document.leftMargin,
        32,
        page_width - document.rightMargin,
        32,
    )

    canvas_obj.setFont("Helvetica", 7.5)
    canvas_obj.setFillColor(GREY)

    canvas_obj.drawString(
        document.leftMargin,
        19,
        "Generated by AI Media Integrity Detector | © 2026",
    )

    canvas_obj.drawRightString(
        page_width - document.rightMargin,
        19,
        f"Page {document.page}",
    )

    canvas_obj.restoreState()


# ============================================================
# MAIN PDF REPORT
# ============================================================

def generate_pdf_report(filename, analysis, decision):
    """
    Generate a PDF forensic report for image or video analysis.

    The function signature is preserved for compatibility
    with the existing FastAPI backend.
    """

    os.makedirs(REPORT_FOLDER, exist_ok=True)

    # --------------------------------------------------------
    # OUTPUT FILE
    # --------------------------------------------------------

    base_name = os.path.splitext(
        os.path.basename(filename)
    )[0]

    pdf_name = f"REPORT_{base_name}.pdf"

    pdf_path = os.path.join(
        REPORT_FOLDER,
        pdf_name,
    )

    # --------------------------------------------------------
    # DOCUMENT CONFIGURATION
    # --------------------------------------------------------

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=38,
        bottomMargin=48,
        title="Digital Media Forensic Analysis Report",
        author="AI Media Integrity Detector",
        subject="Digital media integrity and forensic analysis",
    )

    story = []

    # --------------------------------------------------------
    # DETECT FILE TYPE
    # --------------------------------------------------------

    if not isinstance(analysis, dict):
        analysis = {}

    if not isinstance(decision, dict):
        decision = {}

    video = analysis.get("video", {})

    if not isinstance(video, dict):
        video = {}

    is_video = any(
    key in video
    for key in (
        "video_width",
        "video_height",
        "width",
        "height",
        "frame_analysis",
        "detection_summary",
    )
)

    # --------------------------------------------------------
    # REPORT TITLE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "AI MEDIA INTEGRITY DETECTOR",
            styles["ReportTitle"],
        )
    )

    story.append(
        Paragraph(
            "Digital Forensic Analysis Report",
            styles["ReportSubtitle"],
        )
    )

    # --------------------------------------------------------
    # REPORT HEADER
    # --------------------------------------------------------

    prediction_text = str(
        decision.get("prediction", "Unknown")
    )

    integrity_score = decision.get("integrity_score")

    if integrity_score is None:
        integrity_score_text = "Not calculated"
    else:
        integrity_score_text = (
            f"{integrity_score} / 100"
        )

    report_id = "AMI-" + uuid.uuid4().hex[:8].upper()

    prediction_colors = {
        "Authentic": "#238636",
        "Probably Authentic": "#2E8B57",
        "Needs Manual Review": "#B8860B",
        "Suspicious": "#FF8C00",
        "High Risk": "#B91C1C",
        "Likely Deepfake": "#8B0000",
        "Confirmed Manipulation": "#8B0000",
        "Unknown": "#666666",
    }

    prediction_color = prediction_colors.get(
        prediction_text,
        "#333333",
    )

    prediction_paragraph = Paragraph(
        (
            f"<font color='{prediction_color}'>"
            f"<b>{safe_text(prediction_text)}</b>"
            "</font>"
        ),
        styles["TableCell"],
    )

    header_data = [
        ["Report ID", report_id],
        ["Original File", safe_text(os.path.basename(filename))],
        ["Prediction", prediction_paragraph],
        ["Integrity Score", integrity_score_text],
        [
            "Generated",
            datetime.now().strftime("%d-%b-%Y %I:%M %p"),
        ],
    ]

    story.append(
        create_table(
            header_data,
            col_widths=[140, 320],
        )
    )

    story.append(Spacer(1, 8))

    # ========================================================
    # IMAGE ANALYSIS
    # ========================================================

    if not is_video:

        add_section(story, "Image Analysis")

        file_size = format_file_size(
            analysis.get("file_size_bytes", 0)
        )

        image_data = [
            ["Width", f"{safe_text(analysis.get('width'))} px"],
            ["Height", f"{safe_text(analysis.get('height'))} px"],
            ["Channels", safe_text(analysis.get("channels"))],
            ["Image Type", safe_text(analysis.get("image_type"))],
            ["Aspect Ratio", safe_text(analysis.get("aspect_ratio"))],
            [
                "Resolution",
                safe_text(analysis.get("resolution_status")),
            ],
            ["File Size", file_size],
        ]

        story.append(
            create_table(
                image_data,
                col_widths=[140, 320],
            )
        )

        story.append(Spacer(1, 6))

        # ----------------------------------------------------
        # EXIF METADATA
        # ----------------------------------------------------

        add_section(story, "EXIF Metadata")

        exif = analysis.get("exif", {})

        if not isinstance(exif, dict):
            exif = {}

        if exif:

            exif_data = [
                ["Camera Make", safe_text(exif.get("Make"))],
                ["Camera Model", safe_text(exif.get("Model"))],
                ["Date Taken", safe_text(exif.get("DateTime"))],
                [
                    "ISO",
                    safe_text(exif.get("ISOSpeedRatings")),
                ],
                ["Aperture", safe_text(exif.get("FNumber"))],
                [
                    "Exposure",
                    safe_text(exif.get("ExposureTime")),
                ],
                [
                    "Focal Length",
                    safe_text(exif.get("FocalLength")),
                ],
            ]

        else:
            exif_data = [
                ["Status", "No EXIF metadata found."]
            ]

        story.append(
            create_table(
                exif_data,
                col_widths=[140, 320],
            )
        )

        story.append(Spacer(1, 6))

        # ----------------------------------------------------
        # FORENSIC ANALYSIS
        # ----------------------------------------------------

        add_section(story, "Forensic Analysis")

        ela = analysis.get("ela", {})
        noise = analysis.get("noise", {})
        copy_move = analysis.get("copy_move", {})

        if not isinstance(ela, dict):
            ela = {}

        if not isinstance(noise, dict):
            noise = {}

        if not isinstance(copy_move, dict):
            copy_move = {}

        forensic_data = [
            [
                "Error Level Analysis",
                safe_text(ela.get("status", "Not available")),
            ],
            [
                "ELA Details",
                safe_text(ela.get("details")),
            ],
            [
                "Noise Analysis",
                safe_text(noise.get("status", "Not available")),
            ],
            [
                "Noise Details",
                safe_text(noise.get("details")),
            ],
            [
                "Copy-Move Detection",
                safe_text(
                    copy_move.get("status", "Not available")
                ),
            ],
            [
                "Copy-Move Details",
                safe_text(copy_move.get("details")),
            ],
            [
                "Copy-Move Matches",
                safe_text(copy_move.get("matches")),
            ],
        ]

        story.append(
            create_table(
                forensic_data,
                col_widths=[140, 320],
            )
        )

        story.append(Spacer(1, 6))

        # ----------------------------------------------------
        # AI-GENERATED IMAGE SCREENING
        # ----------------------------------------------------

        ai_detection = analysis.get("ai_detection", {})

        if not isinstance(ai_detection, dict):
            ai_detection = {}

        add_section(
            story,
            "AI-Generated Image Screening",
        )

        ai_data = [
            ["Property", "Result"],
            [
                "Prediction",
                safe_text(ai_detection.get("prediction", "Unavailable")),
            ],
            [
                "AI-Generated-Like Score",
                format_percentage(
                    ai_detection.get("fake_probability")
                ),
            ],
            [
                "Complementary Score*",
                format_percentage(
                    ai_detection.get("real_probability")
                ),
            ],
            [
                "Model",
                safe_text(ai_detection.get("model", "Unavailable")),
            ],
            [
                "Analysis Type",
                safe_text(
                    ai_detection.get(
                        "analysis_type",
                        "Not available",
                    )
                ),
            ],
        ]

        if ai_detection.get("error"):
            ai_data.append(
                [
                    "Status",
                    "AI screening could not be completed.",
                ]
            )

        story.append(
            create_table(
                ai_data,
                col_widths=[180, 280],
                header=True,
            )
        )

        warning = ai_detection.get(
            "warning",
            (
                "Model scores are screening indicators, not proof "
                "of authenticity or manipulation."
            ),
        )

        story.append(
            Paragraph(
                f"<b>AI Screening Warning:</b> {safe_text(warning)}",
                styles["SmallText"],
            )
        )

        story.append(
            Paragraph(
                "* The complementary score is not a validated "
                "probability that the image is authentic.",
                styles["SmallText"],
            )
        )

    # ========================================================
    # VIDEO ANALYSIS
    # ========================================================

    if is_video:

        add_section(story, "Video Analysis")

        summary = video.get("detection_summary", {})

        if not isinstance(summary, dict):
            summary = {}

        video_data = [
            ["Video Property", "Result"],
            [
                "Resolution",
                (
                    f"{video.get('video_width', '-')} x "
                    f"{video.get('video_height', '-')} pixels"
                ),
            ],
            ["Frame Rate", f"{video.get('fps', '-')} FPS"],
            [
                "Total Frames",
                safe_text(video.get("total_frames")),
            ],
            [
                "Duration",
                f"{video.get('duration_seconds', '-')} seconds",
            ],
            [
                "Frames Extracted",
                safe_text(video.get("frames_extracted", 0)),
            ],
            [
                "Analysis Type",
                safe_text(video.get("analysis_type")),
            ],
            [
                "Analysis Status",
                safe_text(summary.get("analysis_status", "Unavailable")),
            ],
            [
                "Frames Analyzed",
                safe_text(summary.get("frames_analyzed", 0)),
            ],
            [
                "Frames Failed",
                safe_text(summary.get("frames_failed", 0)),
            ],
        ]

        if summary.get("analysis_status") in (
            "completed",
            "partial",
        ):

            video_data.extend(
                [
                    [
                        "Average AI-Generated-Like Score",
                        format_percentage(
                            summary.get("average_fake_probability")
                        ),
                    ],
                    [
                        "Complementary Score*",
                        format_percentage(
                            summary.get("average_real_probability")
                        ),
                    ],
                    [
                        "AI-Generated-Like Frames",
                        safe_text(
                            summary.get("ai_generated_like_frames", 0)
                        ),
                    ],
                    [
                        "Provisional Classification Threshold",
                        format_percentage(
                            summary.get(
                                "provisional_classification_threshold"
                            )
                        ),
                    ],
                    [
                        "Frames Above Provisional Threshold",
                        safe_text(
                            summary.get(
                                "frames_above_provisional_threshold",
                                "Unavailable",
                            )
                        ),
                    ],
                    [
                        "Threshold Validation",
                        "Provisional — not validated",
                    ],
                    [
                        "Highest-Scoring Frame",
                        safe_text(
                            summary.get("highest_scoring_frame")
                        ),
                    ],
                    [
                        "Highest Frame Score",
                        format_percentage(
                            summary.get(
                                "highest_frame_fake_probability"
                            )
                        ),
                    ],
                    [
                        "Model",
                        safe_text(summary.get("model")),
                    ],
                ]
            )

        story.append(
            create_table(
                video_data,
                col_widths=[180, 280],
                header=True,
            )
        )

        story.append(
            Paragraph(
                "* The complementary score is not a validated "
                "probability that the video is authentic.",
                styles["SmallText"],
            )
        )

        # ----------------------------------------------------
        # INDIVIDUAL FRAME RESULTS
        # ----------------------------------------------------

        add_section(
            story,
            "Frame-Level Screening Results",
        )

        frame_analysis = video.get("frame_analysis", [])

        if not isinstance(frame_analysis, list):
            frame_analysis = []

        frame_data = [
            [
                "Frame",
                "Timestamp",
                "Prediction",
                "AI-Generated-Like Score",
            ]
        ]

        for frame in frame_analysis:

            if not isinstance(frame, dict):
                continue

            timestamp = frame.get("timestamp_seconds")

            if timestamp is None:
                timestamp_text = "Unavailable"
            else:
                try:
                    timestamp_text = f"{float(timestamp):.2f} sec"
                except (TypeError, ValueError):
                    timestamp_text = "Unavailable"

            frame_data.append(
                [
                    safe_text(frame.get("frame")),
                    safe_text(timestamp_text),
                    safe_text(frame.get("prediction", "Unknown")),
                    format_percentage(
                        frame.get("fake_probability")
                    ),
                ]
            )

        if len(frame_data) > 1:

            frame_table = create_table(
                frame_data,
                col_widths=[105, 75, 120, 160],
                header=True,
            )

            story.append(frame_table)

            # ------------------------------------------------
            # FRAME SCORE CHART
            # ------------------------------------------------

            valid_frames = []

            for frame in frame_analysis:

                if not isinstance(frame, dict):
                    continue

                try:
                    score = float(frame.get("fake_probability"))

                    if 0 <= score <= 1:
                        valid_frames.append((frame, score))

                except (TypeError, ValueError):
                    continue

            if valid_frames:

                labels = []
                scores = []

                for index, (frame, score) in enumerate(valid_frames):

                    timestamp = frame.get("timestamp_seconds")

                    if timestamp is None:
                        label = str(frame.get("frame", index))
                    else:
                        try:
                            label = f"{float(timestamp):g}s"
                        except (TypeError, ValueError):
                            label = str(frame.get("frame", index))

                    labels.append(label)
                    scores.append(score * 100)

                chart_path = os.path.join(
                    REPORT_FOLDER,
                    f"frame_score_chart_{uuid.uuid4().hex[:8]}.png",
                )

                fig, ax = plt.subplots(figsize=(7, 3.2))

                bars = ax.bar(labels, scores)

                ax.set_xlabel("Timestamp in Video")
                ax.set_ylabel("AI-Generated-Like Score (%)")
                ax.set_title("Frame-Level Screening Scores")
                ax.set_ylim(0, 100)

                for bar, score in zip(bars, scores):
                    ax.annotate(
                        f"{score:.1f}%",
                        (
                            bar.get_x() + bar.get_width() / 2,
                            bar.get_height(),
                        ),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha="center",
                        fontsize=7,
                    )

                fig.tight_layout()
                fig.savefig(chart_path, dpi=130)
                plt.close(fig)

                story.append(Spacer(1, 6))

                add_section(story, "Frame Score Chart")

                story.append(
                    Image(
                        chart_path,
                        width=6.3 * inch,
                        height=2.8 * inch,
                        kind="proportional",
                    )
                )

        else:
            story.append(
                Paragraph(
                    "No frame-level model results are available.",
                    styles["BodyText"],
                )
            )



        # ========================================================
    # SUSPICIOUS VIDEO FRAME DETAILS
    # ========================================================

    if is_video:

        summary = video.get("detection_summary", {})

        if not isinstance(summary, dict):
            summary = {}

        frame_analysis = video.get("frame_analysis", [])

        if not isinstance(frame_analysis, list):
            frame_analysis = []

        threshold = summary.get(
            "provisional_classification_threshold",
            0.50,
        )

        try:
            threshold = float(threshold)

            if not 0 <= threshold <= 1:
                threshold = 0.50

        except (TypeError, ValueError):
            threshold = 0.50

        suspicious_frames = []

        for frame in frame_analysis:

            if not isinstance(frame, dict):
                continue

            try:
                fake_probability = float(
                    frame.get("fake_probability")
                )
            except (TypeError, ValueError):
                continue

            if 0 <= fake_probability <= 1 and fake_probability >= threshold:
                suspicious_frames.append(frame)

        add_section(
            story,
            "Frames Requiring Manual Review",
        )

        story.append(
            Paragraph(
                (
                    "The following frames met or exceeded the "
                    f"provisional threshold of {threshold * 100:.0f}%. "
                    "They are flagged for further examination."
                ),
                styles["SmallText"],
            )
        )

        if suspicious_frames:

            suspicious_data = [
                [
                    "Frame Number",
                    "Timestamp",
                    "AI Score",
                    "Prediction",
                ]
            ]

            for frame in suspicious_frames:

                frame_number = frame.get(
                    "frame_number",
                    frame.get("frame", "Unavailable"),
                )

                timestamp = frame.get(
                    "timestamp_seconds",
                    frame.get("timestamp"),
                )

                try:
                    timestamp_text = (
                        f"{float(timestamp):.2f} sec"
                    )
                except (TypeError, ValueError):
                    timestamp_text = "Unavailable"

                suspicious_data.append(
                    [
                        safe_text(frame_number),
                        timestamp_text,
                        format_percentage(
                            frame.get("fake_probability")
                        ),
                        safe_text(
                            frame.get("prediction", "Unknown")
                        ),
                    ]
                )

            story.append(
                create_table(
                    suspicious_data,
                    col_widths=[85, 100, 100, 175],
                    header=True,
                )
            )

        else:

            story.append(
                Paragraph(
                    "No analyzed frames met the provisional "
                    "screening threshold.",
                    styles["BodyText"],
                )
            )

        story.append(Spacer(1, 8))

    # ========================================================
    # FAILED FRAME DETAILS
    # ========================================================

    if is_video:

        failed_frames = video.get(
            "failed_frame_details",
            [],
        )

        if not isinstance(failed_frames, list):
            failed_frames = []

        add_section(
            story,
            "Failed Frame Analysis Details",
        )

        if failed_frames:

            failed_data = [
                ["Frame Number", "Error Details"]
            ]

            for failed in failed_frames:

                if not isinstance(failed, dict):
                    continue

                frame_number = failed.get(
                    "frame_number",
                    failed.get("frame", "Unavailable"),
                )

                error_message = failed.get(
                    "error",
                    failed.get("reason", "Analysis failed"),
                )

                failed_data.append(
                    [
                        safe_text(frame_number),
                        safe_text(error_message),
                    ]
                )

            if len(failed_data) > 1:

                story.append(
                    create_table(
                        failed_data,
                        col_widths=[110, 350],
                        header=True,
                    )
                )

            else:

                story.append(
                    Paragraph(
                        "Failed frame records were present, "
                        "but no valid frame details were available.",
                        styles["BodyText"],
                    )
                )

        else:

            story.append(
                Paragraph(
                    "No failed frame details were reported.",
                    styles["BodyText"],
                )
            )

        story.append(Spacer(1, 8))
    # ========================================================
    # FINAL DECISION
    # ========================================================

    add_section(story, "Final Decision")

    final_data = [
        ["Prediction", prediction_paragraph],
        ["Integrity Score", integrity_score_text],
    ]

    story.append(
        create_table(
            final_data,
            col_widths=[140, 320],
        )
    )

    story.append(Spacer(1, 5))

    # ========================================================
    # FORENSIC FINDINGS
    # ========================================================

    add_section(story, "Forensic Findings")

    if is_video:

        summary = video.get("detection_summary", {})

        if not isinstance(summary, dict):
            summary = {}

        status = summary.get("analysis_status", "unavailable")

        if status in ("completed", "partial"):

            reasons = [
                (
                    f"Video frame screening status: {status}. "
                    f"{summary.get('frames_analyzed', 0)} frames "
                    "were analyzed."
                ),
                (
                    "Average AI-generated-like model score: "
                    f"{format_percentage(summary.get('average_fake_probability'))}."
                ),
                (
                    "Highest frame score: "
                    f"{format_percentage(summary.get('highest_frame_fake_probability'))}."
                ),
                (
                    "The threshold is provisional and has not "
                    "been independently validated."
                ),
                (
                    "Frame-level model scores do not establish "
                    "whether the complete video is authentic "
                    "or manipulated."
                ),
            ]

            if status == "partial":
                reasons.append(
                    "Some frames could not be analyzed, so "
                    "the results may be incomplete."
                )

        else:
            reasons = [
                "Video frame screening did not complete successfully.",
                safe_text(
                    video.get(
                        "message",
                        "Review the analysis status and available errors.",
                    )
                ),
            ]

    else:

        reasons = decision.get("reasons", [])

        if not isinstance(reasons, list):
            reasons = [str(reasons)]

        if not reasons:

            reasons = [
                (
                    "No detailed findings were returned by the "
                    "decision module."
                )
            ]

    add_findings(story, reasons)

    # ========================================================
    # ASSESSMENT NOTE
    # ========================================================

    add_section(story, "Assessment Note")

    if is_video:

        summary = video.get("detection_summary", {})

        if not isinstance(summary, dict):
            summary = {}

        if summary.get("analysis_status") in (
            "completed",
            "partial",
        ):

            assessment_note = (
                "This report presents preliminary frame-level "
                "screening results from an AI-generated-image "
                "detection model. The model scores are indicators "
                "for further examination, not proof that the "
                "complete video is authentic or manipulated. "
                "The detector may not reliably identify every "
                "type of deepfake or unseen generator. "
                "Manual review and additional forensic examination "
                "may be required."
            )

        else:

            assessment_note = (
                "Video frame screening did not complete "
                "successfully or produced incomplete results. "
                "No reliable conclusion about the video's "
                "authenticity can be made from incomplete results."
            )

    else:

        assessment_note = (
            "This report presents preliminary image forensic "
            "analysis results. Automated detection results are "
            "indicators for further examination and should not "
            "be treated as definitive proof of authenticity "
            "or manipulation. The integrity score is a preliminary "
            "heuristic, not a probability of authenticity. "
            "The AI screening score is a separate model output."
        )

    story.append(
        Paragraph(
            safe_text(assessment_note),
            styles["BodyText"],
        )
    )

    # ========================================================
    # PROJECT INFORMATION
    # ========================================================

    add_section(story, "Project Information")

    project_data = [
        [
            "Project",
            (
                "AI-Powered Digital Media Integrity, Deepfake "
                "Detection and Forensic Reporting System"
            ),
        ],
        ["Version", "2.0"],
        [
            "Developed by",
            (
                "Nallabelli Ramesh, Bukke Sai Kumar Naik, "
                "Gadeerappa Gari Eresh"
            ),
        ],
    ]

    story.append(
        create_table(
            project_data,
            col_widths=[140, 320],
        )
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    doc.build(
        story,
        onFirstPage=draw_page_footer,
        onLaterPages=draw_page_footer,
    )

    return pdf_path