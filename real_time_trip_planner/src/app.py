# app.py - Streamlit UI for Travel Planning with LangGraph Integration
import streamlit as st
import json
from datetime import datetime, date
from io import BytesIO
import base64
from typing import Union, Any

# PDF generation imports - Using simpler fpdf2 library
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
    USING_REPORTLAB = False
except ImportError:
    PDF_AVAILABLE = False
    USING_REPORTLAB = False

# Try to import ReportLab for advanced features
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
    if not PDF_AVAILABLE:
        PDF_AVAILABLE = True
        USING_REPORTLAB = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    # Define dummy variables for when ReportLab is not available
    Table = Any
    SimpleDocTemplate = Any
    Paragraph = Any
    TableStyle = Any
    A4 = None
    TA_CENTER = None
    TA_JUSTIFY = None
    letter = None
    getSampleStyleSheet = None
    ParagraphStyle = Any
    Spacer = Any
    PageBreak = Any
    colors = None
    inch = None

# Import our classes
from models import TravelRequest, CompleteTravelPlan
from services import TravelPlanningService, SessionManager
from langgraph_agent import LangGraphTravelAgent
from config import config


class TravelPlanningApp:
    """Main Streamlit application class with LangGraph integration"""

    def __init__(self):
        self.travel_service = TravelPlanningService()
        self.session_manager = SessionManager()
        self.langgraph_agent = LangGraphTravelAgent()

        # Initialize session state
        if 'user_id' not in st.session_state:
            st.session_state.user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if 'current_session_id' not in st.session_state:
            st.session_state.current_session_id = None
        if 'travel_plan' not in st.session_state:
            st.session_state.travel_plan = None
        if 'budget_info' not in st.session_state:
            st.session_state.budget_info = None

    def render_header(self):
        """Render application header"""
        st.set_page_config(
            page_title="AI Travel Planner",
            page_icon="",
            layout="wide"
        )

        st.title("AI-Powered Travel Planner")
        st.markdown("Plan your perfect trip with AI assistance!")

        # Show PDF export capability info
        if not PDF_AVAILABLE:
            st.warning("Install reportlab for PDF export: pip install reportlab")

        # User info in sidebar
        with st.sidebar:
            st.markdown(f"**User ID:** {st.session_state.user_id}")
            if st.session_state.current_session_id:
                st.markdown(f"**Session:** {st.session_state.current_session_id[:8]}...")

    def render_travel_form(self):
        """Render travel planning form"""
        st.header("Tell us about your dream trip")

        with st.form("travel_form"):
            col1, col2 = st.columns(2)

            with col1:
                destination = st.text_input(
                    "Destination",
                    placeholder="e.g., Paris, France",
                    help="Where would you like to go?"
                )

                start_date = st.date_input(
                    "Start Date",
                    value=date.today(),
                    help="When does your trip start?"
                )

                budget = st.number_input(
                    "Budget",
                    min_value=100,
                    max_value=50000,
                    value=2000,
                    step=100,
                    help="Your estimated budget"
                )

                travel_style = st.selectbox(
                    "Travel Style",
                    ["budget", "mid-range", "luxury"],
                    help="Your preferred travel style"
                )

            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=date.today(),
                    help="When does your trip end?"
                )

                currency = st.selectbox(
                    "Currency",
                    list(config.exchange_rates.keys()),
                    index=list(config.exchange_rates.keys()).index("USD"),
                    help="Your preferred currency"
                )

                interests = st.text_area(
                    "Interests & Preferences",
                    placeholder="e.g., history, food, adventure sports, museums, beaches...",
                    help="What do you enjoy doing while traveling?"
                )

                special_requirements = st.text_area(
                    "Special Requirements",
                    placeholder="e.g., dietary restrictions, accessibility needs, transportation preferences...",
                    help="Any special needs or requirements?"
                )

            submitted = st.form_submit_button("Plan My Trip", type="primary")

            if submitted:
                # Validate form
                errors = self._validate_form(destination, start_date, end_date, budget, interests)

                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # Calculate number of days
                    num_days = (end_date - start_date).days + 1

                    # Create travel request
                    travel_request = TravelRequest(
                        destination=destination,
                        start_date=start_date.isoformat(),
                        end_date=end_date.isoformat(),
                        num_days=num_days,
                        budget=budget,
                        currency=currency,
                        preferences=[interests, travel_style, special_requirements]
                    )

                    # Process the request
                    self._process_travel_request(travel_request)

    def _validate_form(self, destination: str, start_date: date, end_date: date,
                      budget: float, interests: str) -> list:
        """Validate form inputs"""
        errors = []

        if not destination.strip():
            errors.append("Please enter a destination")

        if start_date >= end_date:
            errors.append("End date must be after start date")

        if budget <= 0:
            errors.append("Budget must be greater than 0")

        if not interests.strip():
            errors.append("Please share your interests and preferences")

        # Check if trip is too long (arbitrary limit)
        if (end_date - start_date).days > 30:
            errors.append("Trip duration cannot exceed 30 days")

        return errors

    def _process_travel_request(self, travel_request: TravelRequest):
        """Process travel planning request using LangGraph agent"""
        try:
            with st.spinner(" AI is planning your perfect trip using LangGraph workflow..."):
                # Use the LangGraph agent to plan the trip
                result = self.langgraph_agent.plan_trip(
                    destination=travel_request.destination,
                    start_date=travel_request.start_date,
                    end_date=travel_request.end_date,
                    origin_city="Unknown",  # You may want to add this to TravelRequest
                    preferred_currency=travel_request.currency,
                    preferences=" ".join(travel_request.preferences)
                )

                if result["success"]:
                    # Store the results in session state
                    st.session_state.travel_plan = result["travel_plan"]
                    st.session_state.budget_info = result["budget_info"]

                    # Create a session for tracking
                    session_id = self.session_manager.create_session(
                        st.session_state.user_id,
                        travel_request
                    )
                    st.session_state.current_session_id = session_id

                    st.success("Your travel plan is ready!")
                    st.rerun()
                else:
                    st.error(f"Error planning your trip: {result['error']}")
                    # Still store budget info if available
                    if result.get("budget_info"):
                        st.session_state.budget_info = result["budget_info"]

        except Exception as e:
            st.error(f"Error planning your trip: {str(e)}")

    def parse_markdown_table(self, lines: list) -> list:
        """Parse markdown table lines into cleaned cell data"""
        table_data = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if it's a table row
            if line.startswith('| ') and line.endswith(' |'):
                # Parse table row and clean each cell
                cells = [cell.strip() for cell in line.split('|')[1:-1]]

                # Skip separator rows (containing ---, ===, etc.)
                if all(set(cell.strip()) <= set('-=: ') for cell in cells if cell.strip()):
                    continue

                # Clean each cell content
                cleaned_cells = [self.clean_text_for_pdf(cell) for cell in cells]
                table_data.append(cleaned_cells)

        return table_data

    def create_pdf_table(self, table_data: list, available_width: float = 500) -> Any:
        """Create a properly formatted PDF table with auto-sizing and text wrapping"""
        if not table_data or len(table_data) < 1:
            return None

        # Clean and wrap table cell content
        wrapped_table_data = []
        for row_idx, row in enumerate(table_data):
            wrapped_row = []
            for cell in row:
                # Clean the cell content
                clean_cell = self.clean_text_for_pdf(str(cell))
                if clean_cell.strip():
                    # Create Paragraph objects for proper text wrapping
                    if row_idx == 0:  # Header row
                        cell_style = ParagraphStyle(
                            'CellHeader',
                            parent=getSampleStyleSheet()['Normal'],
                            fontSize=9,
                            textColor=colors.whitesmoke,
                            fontName='Helvetica-Bold',
                            alignment=0,
                            wordWrap='LTR',
                            encoding='utf-8'
                        )
                    else:  # Data rows
                        cell_style = ParagraphStyle(
                            'CellData',
                            parent=getSampleStyleSheet()['Normal'],
                            fontSize=8,
                            textColor=colors.black,
                            fontName='Helvetica',
                            alignment=0,
                            wordWrap='LTR',
                            leading=10,
                            encoding='utf-8'
                        )

                    # Create paragraph with proper line breaks
                    if len(clean_cell) > 40:
                        # Add line breaks for long content
                        clean_cell = clean_cell.replace(', ', ',<br/>')
                        clean_cell = clean_cell.replace('; ', ';<br/>')
                        clean_cell = clean_cell.replace(' - ', '<br/>◆ ')

                    wrapped_row.append(self.safe_paragraph(clean_cell, cell_style))
                else:
                    wrapped_row.append("")
            wrapped_table_data.append(wrapped_row)

        # Calculate column widths based on content
        num_cols = len(wrapped_table_data[0])

        # Set more reasonable column widths
        if num_cols == 2:
            col_widths = [available_width * 0.3, available_width * 0.7]
        elif num_cols == 3:
            col_widths = [available_width * 0.25, available_width * 0.35, available_width * 0.4]
        elif num_cols == 4:
            col_widths = [available_width * 0.2, available_width * 0.3, available_width * 0.25, available_width * 0.25]
        elif num_cols == 5:
            col_widths = [available_width * 0.15, available_width * 0.25, available_width * 0.2, available_width * 0.2, available_width * 0.2]
        else:
            col_widths = [available_width / num_cols] * num_cols

        # Create table with calculated widths
        table = Table(wrapped_table_data, colWidths=col_widths, repeatRows=1)

        # Enhanced table styling with text wrapping
        table.setStyle(TableStyle([
            # Header styling - colors only since text formatting is in Paragraph
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),

            # Data rows styling - colors only since text formatting is in Paragraph
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),

            # Borders and alignment
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),

            # Alternating row colors for better readability
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.lightgrey])
        ]))

        return table

    def safe_paragraph(self, text: str, style) -> Any:
        """Safely create a Paragraph with proper text cleaning"""
        import re
        try:
            # Clean the text thoroughly before creating paragraph
            clean_text = self.clean_text_for_pdf(str(text)) if text else ""

            # Additional safety cleaning for ReportLab
            clean_text = clean_text.replace('\x00', '')  # Remove null characters
            clean_text = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]', '', clean_text)  # Remove control characters

            # Ensure text is not empty
            if not clean_text.strip():
                clean_text = " "  # Use space for empty content

            return Paragraph(clean_text, style)
        except Exception as e:
            # Fallback to plain text if paragraph creation fails
            print(f"Warning: Paragraph creation failed for text: {str(text)[:100]}... Error: {e}")
            return Paragraph(str(text).replace('<', '&lt;').replace('>', '&gt;'), style)

    def clean_text_for_pdf(self, text: str) -> str:
        """Clean and escape text for PDF generation with proper markdown and bullet handling"""
        import re

        if not text or not isinstance(text, str):
            return ""

        # Start with the original text to preserve currency symbols
        clean_text = text

        # Fix currency symbol corruption - replace tilde with dollar sign
        # Only replace tilde when it appears before numbers (common corruption pattern)
        clean_text = re.sub(r'~(\d)', r'$\1', clean_text)

        # Handle square bullets (■) that are currency symbols vs actual bullets
        # If ■ appears before numbers, treat as currency symbol (convert to $)
        # If ■ appears at start of line with space, treat as bullet point
        clean_text = re.sub(r'■(\d)', r'$\1', clean_text)  # Currency: ■40 → $40

        # Fix euro symbol encoding issues
        clean_text = clean_text.replace('\u20ac', '€')  # Fix unicode euro symbol
        clean_text = clean_text.replace('€', 'EUR')  # Replace euro symbol with text for PDF compatibility

        # Replace square bullets and other bullet variants with attractive bullets
        # But only when they appear as bullet points (at start of line with space)
        clean_text = re.sub(r'^■\s+', '◆ ', clean_text, flags=re.MULTILINE)  # Start of line bullets
        clean_text = re.sub(r'\n■\s+', '\n◆ ', clean_text)  # Bullets after newlines

        # Replace other bullet variants with diamond bullet (◆)
        clean_text = re.sub(r'^[□▪▫●○◦‣⁃*+\-]\s+', '◆ ', clean_text, flags=re.MULTILINE)
        clean_text = re.sub(r'\n[□▪▫●○◦‣⁃*+\-]\s+', '\n◆ ', clean_text)

        # Handle checkbox patterns with better symbols
        clean_text = re.sub(r'\[\s*\]\s*', '☐ ', clean_text)  # Empty checkbox - use unicode
        clean_text = re.sub(r'\[x\]\s*', '✓ ', clean_text)    # Checked checkbox - use checkmark

        # Handle markdown bold (**text**) patterns comprehensively
        # Convert ** markdown syntax to <b> HTML tags

        # Pattern 1: **text:** followed by numbers (e.g., **Emergency:**911)
        clean_text = re.sub(r'\*\*([^*]+?):\*\*\s*(\d+)', r'<b>\1:</b> \2', clean_text)

        # Pattern 2: **text:** without closing ** followed by numbers
        clean_text = re.sub(r'\*\*([^*\n]+?:)\s*(\d+)', r'<b>\1</b> \2', clean_text)

        # Pattern 3: **text:** with colon (e.g., **Weather:**)
        clean_text = re.sub(r'\*\*([^*]+?):\*\*', r'<b>\1:</b>', clean_text)

        # Pattern 4: **text:** without closing ** (e.g., **Weather: or **Important:)
        clean_text = re.sub(r'\*\*([^*\n]+?:)(?!\*)', r'<b>\1</b>', clean_text)

        # Pattern 5: Standard **text** patterns
        clean_text = re.sub(r'\*\*([^*]+?)\*\*', r'<b>\1</b>', clean_text)

        # Pattern 6: **text at end of line without closing **
        clean_text = re.sub(r'\*\*([^*\n]+?)(?=\n|$)', r'<b>\1</b>', clean_text)

        # Pattern 7: Clean up any remaining double asterisks
        clean_text = re.sub(r'\*\*+', '', clean_text)

        # Handle markdown italic (*text*) - but not single asterisks that are bullets
        clean_text = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<i>\1</i>', clean_text)

        # Clean up markdown headers (remove # symbols)
        clean_text = re.sub(r'^#{1,6}\s*', '', clean_text, flags=re.MULTILINE)

        # Convert numbered lists to bullet points with diamond bullet
        clean_text = re.sub(r'^\d+\.\s+', '◆ ', clean_text, flags=re.MULTILINE)
        clean_text = re.sub(r'\n\d+\.\s+', '\n◆ ', clean_text)

        # Remove table separators and pipes
        clean_text = re.sub(r'^\|.*\|$', '', clean_text, flags=re.MULTILINE)
        clean_text = re.sub(r'^\s*[-=]{3,}\s*$', '', clean_text, flags=re.MULTILINE)

        # Clean up extra whitespace but preserve line breaks for bullets
        clean_text = re.sub(r'[ \t]+', ' ', clean_text)  # Replace multiple spaces/tabs with single space
        clean_text = re.sub(r'\n\s*\n', '\n', clean_text)  # Remove empty lines
        clean_text = clean_text.strip()

        # Ensure consistent bullet spacing with diamond bullet
        clean_text = re.sub(r'◆\s+', '◆ ', clean_text)

        # Clean up any leftover asterisks that might be orphaned
        clean_text = re.sub(r'^\*\s+', '◆ ', clean_text, flags=re.MULTILINE)  # Convert lone asterisks to bullets
        clean_text = re.sub(r'\n\*\s+', '\n◆ ', clean_text)  # Convert lone asterisks after newlines

        # Proper HTML escaping for XML parsing in ReportLab
        # First escape ampersands
        clean_text = clean_text.replace('&', '&amp;')

        # Escape < and > but preserve our intended HTML tags
        clean_text = re.sub(r'<(?![/]?[bi]>|br/?>)', '&lt;', clean_text)
        clean_text = re.sub(r'(?<![bi/])>(?![\s])', '&gt;', clean_text)

        # Fix any malformed br tags
        clean_text = re.sub(r'<br\s*>(?!</br>)', '<br/>', clean_text)  # Convert <br> to <br/>
        clean_text = re.sub(r'<br\s*/\s*>', '<br/>', clean_text)  # Normalize <br/> tags

        return clean_text

    def process_bullet_points(self, text: str) -> str:
        """Process bullet points specifically for better PDF formatting"""
        import re

        if not text:
            return ""

        lines = text.split('\n')
        processed_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Convert various bullet formats to consistent format using simple ASCII bullets
            # Handle square bullets (■) and other variants first
            # But first check if ■ is a currency symbol (followed by digits)
            if re.match(r'^[■□▪▫●○◦‣⁃•·*+\-]\s+', line):
                # Any kind of bullet point, convert to diamond bullet
                content = re.sub(r'^[■□▪▫●○◦‣⁃•·*+\-]\s+', '', line).strip()
                processed_lines.append(f"◆ {content}")
            elif re.match(r'^\d+\.\s+', line):
                # Numbered list, convert to diamond bullet
                content = re.sub(r'^\d+\.\s+', '', line).strip()
                processed_lines.append(f"◆ {content}")
            elif line.startswith('**') and line.endswith('**'):
                # Bold text, convert ** markdown to <b> tags
                content = line.replace('**', '').strip()
                processed_lines.append(f"<b>{content}</b>")
            else:
                # Regular text, but check for inline bold patterns
                # Convert ** markdown syntax to <b> tags (comprehensive patterns)

                # Pattern 1: **text:** with colon
                processed_line = re.sub(r'\*\*([^*]+?):\*\*', r'<b>\1:</b>', line)

                # Pattern 2: **text:** without closing **
                processed_line = re.sub(r'\*\*([^*\n]+?:)(?!\*)', r'<b>\1</b>', processed_line)

                # Pattern 3: Standard **text** patterns
                processed_line = re.sub(r'\*\*([^*]+?)\*\*', r'<b>\1</b>', processed_line)

                # Pattern 4: **text at end of line without closing **
                processed_line = re.sub(r'\*\*([^*\n]+?)(?=\n|$)', r'<b>\1</b>', processed_line)

                # Pattern 5: Clean up any remaining double asterisks
                processed_line = re.sub(r'\*\*+', '', processed_line)

                # Handle currency symbols vs bullets more carefully
                # Convert ■ to currency when followed by numbers: ■40 → $40
                processed_line = re.sub(r'■(\d)', r'$\1', processed_line)

                # Replace other bullet variants in the middle of text with better unicode bullets
                processed_line = re.sub(r'[□▪▫]', '◇ ', processed_line)

                processed_lines.append(processed_line)

        return '\n'.join(processed_lines)

    def generate_text_pdf_alternative(self, travel_plan_content: str, budget_info: dict = None) -> BytesIO:
        """Generate a plain text file as PDF alternative (no external dependencies)"""
        # Ensure travel_plan_content is a string
        if isinstance(travel_plan_content, list):
            travel_plan_content = "\n".join([
                item.content if hasattr(item, 'content') else str(item)
                for item in travel_plan_content
            ])
        elif not isinstance(travel_plan_content, str):
            travel_plan_content = str(travel_plan_content)

        try:
            # Clean the content
            clean_content = self.clean_text_for_simple_pdf(travel_plan_content)

            # Create formatted text content
            formatted_content = []
            formatted_content.append("=" * 60)
            formatted_content.append("AI TRAVEL PLAN")
            formatted_content.append("=" * 60)
            formatted_content.append("")
            formatted_content.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            formatted_content.append("")

            # Add main content
            lines = clean_content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    formatted_content.append("")
                    continue

                # Format different line types
                if line.startswith('# '):
                    formatted_content.append("")
                    formatted_content.append("=" * len(line))
                    formatted_content.append(line[2:].upper())
                    formatted_content.append("=" * len(line))
                    formatted_content.append("")
                elif line.startswith('## '):
                    formatted_content.append("")
                    formatted_content.append(line[3:].upper())
                    formatted_content.append("-" * len(line[3:]))
                    formatted_content.append("")
                elif line.startswith('- '):
                    formatted_content.append(f"  ◆ {line[2:]}")
                else:
                    # Handle bold text by converting <b></b> to uppercase
                    import re
                    line = re.sub(r'<b>(.*?)</b>', r'\1', line)
                    formatted_content.append(line)

            # Add budget info if available
            if budget_info:
                formatted_content.append("")
                formatted_content.append("=" * 30)
                formatted_content.append("BUDGET INFORMATION")
                formatted_content.append("=" * 30)
                formatted_content.append("")

                for key, value in budget_info.items():
                    formatted_content.append(f"{key}: {value}")

            formatted_content.append("")
            formatted_content.append("=" * 60)
            formatted_content.append("Generated by AI Travel Planner")
            formatted_content.append("=" * 60)

            # Create text file content
            text_content = "\n".join(formatted_content)

            # Save to buffer
            buffer = BytesIO()
            buffer.write(text_content.encode('utf-8'))
            buffer.seek(0)

            return buffer

        except Exception as e:
            st.error(f"Error generating text file: {str(e)}")
            return None

    def generate_simple_pdf(self, travel_plan_content: str, budget_info: dict = None) -> BytesIO:
        """Generate a simple PDF travel plan using fpdf2 (minimal implementation)"""
        if not PDF_AVAILABLE:
            st.error("PDF generation requires fpdf2. Install with: pip install fpdf2")
            return None

        # Ensure travel_plan_content is a string
        if isinstance(travel_plan_content, list):
            travel_plan_content = "\n".join([
                item.content if hasattr(item, 'content') else str(item)
                for item in travel_plan_content
            ])
        elif not isinstance(travel_plan_content, str):
            travel_plan_content = str(travel_plan_content)

        try:
            # Create PDF document
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)

            # Title
            pdf.cell(0, 10, 'AI Travel Plan', 0, 1, 'C')
            pdf.ln(10)

            # Clean and process the content
            clean_content = self.clean_text_for_simple_pdf(travel_plan_content)

            # Add content
            pdf.set_font('Arial', '', 11)

            # Split content into lines and process each line
            lines = clean_content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    pdf.ln(3)
                    continue

                # Handle different line types
                if line.startswith('# '):
                    # Main heading
                    pdf.set_font('Arial', 'B', 14)
                    pdf.cell(0, 8, line[2:], 0, 1)
                    pdf.ln(2)
                    pdf.set_font('Arial', '', 11)
                elif line.startswith('## '):
                    # Sub heading
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(0, 7, line[3:], 0, 1)
                    pdf.ln(1)
                    pdf.set_font('Arial', '', 11)
                elif line.startswith('- '):
                    # Bullet point with diamond bullet
                    pdf.cell(10, 6, '◆', 0, 0)
                    pdf.cell(0, 6, line[2:], 0, 1)
                else:
                    # Regular text
                    # Handle bold text (marked with <b></b>)
                    if '<b>' in line and '</b>' in line:
                        # Simple bold handling - extract and format
                        import re
                        parts = re.split(r'<b>(.*?)</b>', line)

                        for i, part in enumerate(parts):
                            if i % 2 == 0:  # Regular text
                                pdf.set_font('Arial', '', 11)
                            else:  # Bold text
                                pdf.set_font('Arial', 'B', 11)

                            if part.strip():
                                pdf.cell(0, 6, part, 0, 1 if i == len(parts)-1 else 0)
                    else:
                        # Regular line
                        pdf.cell(0, 6, line, 0, 1)

            # Add budget info if available
            if budget_info:
                pdf.ln(10)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 8, 'Budget Information', 0, 1)
                pdf.ln(2)
                pdf.set_font('Arial', '', 11)

                for key, value in budget_info.items():
                    pdf.cell(0, 6, f"{key}: {value}", 0, 1)

            # Save to buffer
            buffer = BytesIO()
            pdf_output = pdf.output(dest='S').encode('latin-1')
            buffer.write(pdf_output)
            buffer.seek(0)

            return buffer

        except Exception as e:
            st.error(f"Error generating simple PDF: {str(e)}")
            return None

    def clean_text_for_simple_pdf(self, text: str) -> str:
        """Simple text cleaning for fpdf2 PDF generation with modern formatting"""
        import re

        if not text or not isinstance(text, str):
            return ""

        clean_text = text

        # Fix currency symbols
        clean_text = re.sub(r'~(\d)', r'$\1', clean_text)
        clean_text = re.sub(r'■(\d)', r'$\1', clean_text)

        # Fix euro symbol encoding issues
        clean_text = clean_text.replace('\u20ac', '€')  # Fix unicode euro symbol
        clean_text = clean_text.replace('€', 'EUR')  # Replace euro symbol with text for PDF compatibility

        # Convert bullets to attractive diamond bullets (consistent with main function)
        clean_text = re.sub(r'^■\s+', '◆ ', clean_text, flags=re.MULTILINE)
        clean_text = re.sub(r'\n■\s+', '\n◆ ', clean_text)
        clean_text = re.sub(r'^[□▪▫●○◦‣⁃•·*+\-]\s+', '◆ ', clean_text, flags=re.MULTILINE)
        clean_text = re.sub(r'\n[□▪▫●○◦‣⁃•·*+\-]\s+', '\n◆ ', clean_text)

        # Handle markdown bold - convert to HTML tags (comprehensive patterns)
        # Process multiple times to handle multiple bold words in a line

        # Pattern 1: Standard **text** patterns (handles multiline text)
        while '**' in clean_text:
            old_text = clean_text
            # Allow text to span multiple lines by including \n in the character class
            clean_text = re.sub(r'\*\*([^*]+?)\*\*', r'<b>\1</b>', clean_text, flags=re.DOTALL)
            # Break if no changes to avoid infinite loop
            if old_text == clean_text:
                break

        # Pattern 2: **text:** with colon (multiline support)
        clean_text = re.sub(r'\*\*([^*]+?):\*\*', r'<b>\1:</b>', clean_text, flags=re.DOTALL)

        # Pattern 3: **text:** followed by numbers (multiline support)
        clean_text = re.sub(r'\*\*([^*]+?):\*\*\s*(\d+)', r'<b>\1:</b> \2', clean_text, flags=re.DOTALL)

        # Pattern 4: **text:** without closing ** followed by numbers
        clean_text = re.sub(r'\*\*([^*]+?:)\s*(\d+)', r'<b>\1</b> \2', clean_text, flags=re.DOTALL)

        # Pattern 5: **text:** without closing ** (multiline support)
        clean_text = re.sub(r'\*\*([^*]+?:)(?!\*)', r'<b>\1</b>', clean_text, flags=re.DOTALL)

        # Pattern 6: **text at end of line without closing ** (multiline support)
        clean_text = re.sub(r'\*\*([^*]+?)(?=\n|$)', r'<b>\1</b>', clean_text, flags=re.DOTALL)

        # Pattern 7: Clean up any remaining double asterisks
        clean_text = re.sub(r'\*\*+', '', clean_text)

        # Handle markdown italic
        clean_text = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<i>\1</i>', clean_text)

        # Convert numbered lists to bullets
        clean_text = re.sub(r'^\d+\.\s+', '◆ ', clean_text, flags=re.MULTILINE)
        clean_text = re.sub(r'\n\d+\.\s+', '\n◆ ', clean_text)

        # Handle checkboxes
        clean_text = re.sub(r'\[\s*\]\s*', '☐ ', clean_text)
        clean_text = re.sub(r'\[x\]\s*', '✓ ', clean_text)

        # Clean up extra whitespace
        clean_text = re.sub(r'[ \t]+', ' ', clean_text)
        clean_text = re.sub(r'\n\s*\n', '\n', clean_text)
        clean_text = clean_text.strip()

        # Proper HTML escaping for XML parsing
        clean_text = clean_text.replace('&', '&amp;')
        clean_text = re.sub(r'<(?![/]?[bi]>|br/?>)', '&lt;', clean_text)
        clean_text = re.sub(r'(?<![bi/])>(?![\s])', '&gt;', clean_text)

        # Fix any malformed br tags
        clean_text = re.sub(r'<br\s*>(?!</br>)', '<br/>', clean_text)
        clean_text = re.sub(r'<br\s*/\s*>', '<br/>', clean_text)

        return clean_text

    def generate_expert_pdf(self, travel_plan_content: str, budget_info: dict = None) -> BytesIO:
        """Generate a professional PDF travel plan"""
        if not PDF_AVAILABLE:
            st.error("PDF generation requires reportlab. Install with: pip install reportlab")
            return None

        # Ensure travel_plan_content is a string
        if isinstance(travel_plan_content, list):
            travel_plan_content = "\n".join([
                item.content if hasattr(item, 'content') else str(item)
                for item in travel_plan_content
            ])
        elif not isinstance(travel_plan_content, str):
            travel_plan_content = str(travel_plan_content)

        buffer = BytesIO()

        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        # Get styles
        styles = getSampleStyleSheet()

        # Create custom styles
        # Define custom styles with proper encoding for currency symbols
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,  # Slightly larger but more consistent
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold',
            encoding='utf-8'
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold',
            encoding='utf-8'
        )

        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=styles['Heading3'],
            fontSize=16,  # Same size as heading
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue,  # Same color as heading
            fontName='Helvetica-Bold',
            encoding='utf-8'
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            encoding='utf-8'
        )

        # Story elements
        story = []

        # Title page
        story.append(Paragraph("AI TRAVEL PLANNER", title_style))
        story.append(Paragraph("Expert Travel Plan", heading_style))
        story.append(Spacer(1, 20))

        # Extract destination from travel plan content
        destination = "Your Destination"
        if "TRAVEL PLAN FOR" in travel_plan_content:
            try:
                dest_line = [line for line in travel_plan_content.split('\n') if 'TRAVEL PLAN FOR' in line][0]
                destination = dest_line.replace('## TRAVEL PLAN FOR', '').replace('#', '').strip()
            except IndexError:
                pass

        story.append(Paragraph(f"Destination: <b>{destination}</b>", heading_style))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", body_style))
        story.append(Spacer(1, 30))

        # Budget summary if available
        if budget_info:
            story.append(Paragraph("BUDGET SUMMARY", heading_style))

            budget_data = [
                ['Category', 'Amount', 'Currency'],
                ['Total Budget', f"{budget_info.get('total_budget', 0):.0f}", budget_info.get('currency', 'USD')],
                ['Daily Budget', f"{budget_info.get('daily_budget', 0):.0f}", budget_info.get('currency', 'USD')]
            ]

            if 'breakdown' in budget_info:
                breakdown = budget_info['breakdown']
                budget_data.extend([
                    ['Accommodation', f"{breakdown.get('accommodation', 0):.0f}", budget_info.get('currency', 'USD')],
                    ['Food', f"{breakdown.get('food', 0):.0f}", budget_info.get('currency', 'USD')],
                    ['Activities', f"{breakdown.get('activities', 0):.0f}", budget_info.get('currency', 'USD')],
                    ['Transport', f"{breakdown.get('transport', 0):.0f}", budget_info.get('currency', 'USD')]
                ])

            budget_table = Table(budget_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
            budget_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(budget_table)
            story.append(Spacer(1, 20))

        # Process travel plan content
        story.append(PageBreak())
        story.append(Paragraph("DETAILED TRAVEL PLAN", heading_style))

        # Improved table and content processing
        sections = travel_plan_content.split('\n\n')

        for section in sections:
            if section.strip():
                lines = section.strip().split('\n')
                section_has_table = False

                # Check if this section contains a table
                for line in lines:
                    if line.strip().startswith('| ') and line.strip().endswith(' |'):
                        section_has_table = True
                        break

                if section_has_table:
                    # Process as table section
                    table_data = self.parse_markdown_table(lines)
                    if table_data:
                        table = self.create_pdf_table(table_data)
                        if table:
                            story.append(table)
                            story.append(Spacer(1, 15))
                else:
                    # Process as regular content
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue

                        # Handle different markdown elements
                        if line.startswith('### '):
                            clean_heading = self.clean_text_for_pdf(line.replace('### ', ''))
                            story.append(Paragraph(clean_heading, subheading_style))
                        elif line.startswith('## '):
                            clean_heading = self.clean_text_for_pdf(line.replace('## ', ''))
                            story.append(Paragraph(clean_heading, heading_style))
                        elif line.startswith('# '):
                            clean_heading = self.clean_text_for_pdf(line.replace('# ', ''))
                            story.append(Paragraph(clean_heading, heading_style))
                        elif line.startswith('**') and line.endswith('**'):
                            clean_bold_text = self.clean_text_for_pdf(line)
                            story.append(Paragraph(clean_bold_text, body_style))
                        elif any(line.startswith(marker) for marker in ['- ', '* ', '+ ', '• ', '1. ', '2. ', '3. ', '4. ', '5. ']):
                            # Handle all bullet point formats consistently
                            processed_bullet = self.process_bullet_points(line)
                            if processed_bullet.strip():
                                story.append(Paragraph(processed_bullet, body_style))
                        elif line.startswith('```'):
                            # Skip code blocks
                            continue
                        else:
                            if len(line) > 10:  # Only add substantial content
                                # Check if line contains multiple bullet points
                                if '\n' in line or any(marker in line for marker in [' - ', ' * ', ' • ']):
                                    processed_text = self.process_bullet_points(line)
                                    clean_line = self.clean_text_for_pdf(processed_text)
                                else:
                                    clean_line = self.clean_text_for_pdf(line)

                                if clean_line.strip():  # Only add non-empty content
                                    story.append(Paragraph(clean_line, body_style))

                    story.append(Spacer(1, 10))

        # Footer information
        story.append(Spacer(1, 30))
        story.append(Paragraph("TRAVEL CHECKLIST", heading_style))

        checklist_items = [
            "Verify passport and visa requirements",
            "Check vaccination requirements",
            "Purchase travel insurance",
            "Notify bank of travel dates",
            "Download offline maps",
            "Pack weather-appropriate clothing",
            "Confirm accommodation bookings",
            "Research local customs and etiquette",
            "Prepare emergency contact information",
            "Check local weather forecast"
        ]

        for item in checklist_items:
            story.append(Paragraph(f"{item}", body_style))

        # Final footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            "Generated by AI Travel Planner - Professional Travel Planning Service",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=colors.grey)
        ))

        # Build PDF with error handling
        try:
            doc.build(story)
            buffer.seek(0)
            return buffer
        except Exception as e:
            # If PDF generation fails, create a simple error PDF
            buffer = BytesIO()
            error_doc = SimpleDocTemplate(buffer, pagesize=letter)
            error_story = []
            error_story.append(Paragraph("PDF Generation Error", heading_style))
            error_story.append(Paragraph(f"Error: {str(e)}", body_style))
            error_story.append(Paragraph("Please try again or contact support.", body_style))
            error_doc.build(error_story)
            buffer.seek(0)
            return buffer

    def render_travel_plan(self, travel_plan_content: str):
        """Render the generated travel plan from LangGraph"""
        # Ensure travel_plan_content is a string
        if isinstance(travel_plan_content, list):
            travel_plan_content = "\n".join([
                item.content if hasattr(item, 'content') else str(item)
                for item in travel_plan_content
            ])
        elif not isinstance(travel_plan_content, str):
            travel_plan_content = str(travel_plan_content)

        st.header("Your Personalized Travel Plan")

        # Display the travel plan content (markdown tables from LangGraph)
        st.markdown(travel_plan_content)

        # If we have budget info, display it separately
        if st.session_state.budget_info:
            budget_info = st.session_state.budget_info

            st.header("Budget Summary")
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Total Budget", f"{budget_info['total_budget']:.0f} {budget_info['currency']}")
                st.metric("Daily Budget", f"{budget_info['daily_budget']:.0f} {budget_info['currency']}")

            with col2:
                st.subheader("Budget Breakdown")
                st.write(f"Accommodation: {budget_info['breakdown']['accommodation']:.0f} {budget_info['currency']}")
                st.write(f"Food: {budget_info['breakdown']['food']:.0f} {budget_info['currency']}")
                st.write(f"Activities: {budget_info['breakdown']['activities']:.0f} {budget_info['currency']}")
                st.write(f"Transport: {budget_info['breakdown']['transport']:.0f} {budget_info['currency']}")

        # Additional actions
        st.header("Actions")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("Export as JSON"):
                # Create export data
                export_data = {
                    "travel_plan": travel_plan_content,
                    "budget_info": st.session_state.budget_info,
                    "generated_at": datetime.now().isoformat()
                }
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"travel_plan_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )

        with col2:
            if st.button("Export as PDF"):
                try:
                    with st.spinner("Generating PDF travel plan..."):
                        # Try to generate PDF using best available library
                        pdf_buffer = None

                        # First try advanced PDF with ReportLab (best quality)
                        pdf_buffer = self.generate_expert_pdf(travel_plan_content, st.session_state.budget_info)
                        if pdf_buffer:
                            st.download_button(
                                label="Download PDF",
                                data=pdf_buffer.getvalue(),
                                file_name=f"travel_plan_{datetime.now().strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                help="Professional PDF with budget breakdown and formatted content"
                            )
                            st.success("PDF generated successfully!")
                        else:
                            # Fallback to simple PDF if ReportLab not available
                            pdf_buffer = self.generate_simple_pdf(travel_plan_content, st.session_state.budget_info)
                            if pdf_buffer:
                                st.download_button(
                                    label="Download PDF",
                                    data=pdf_buffer.getvalue(),
                                    file_name=f"travel_plan_{datetime.now().strftime('%Y%m%d')}.pdf",
                                    mime="application/pdf",
                                    help="PDF with clean text formatting"
                                )
                                st.success("PDF generated successfully!")
                            else:
                                # If no PDF library available, show error
                                st.error("PDF libraries not available. Please install ReportLab or fpdf2:")
                                st.code("pip install reportlab fpdf2")

                except ImportError as e:
                    st.error(f"PDF library import error: {str(e)}")
                    st.info("Please install PDF libraries: pip install reportlab fpdf2")
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
                    st.info("Please ensure PDF libraries are installed: pip install reportlab fpdf2")

        with col3:
            if st.button("Plan Another Trip"):
                # Clear session state
                for key in ['travel_plan', 'current_session_id', 'budget_info']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

        with col4:
            if st.button("Share Plan"):
                st.info("Sharing functionality would be implemented here")

    def render_sidebar(self):
        """Render sidebar with additional options"""
        with st.sidebar:
            st.header("Options")

            # Session management
            if st.session_state.current_session_id:
                st.subheader("Current Session")
                session = self.session_manager.get_session(st.session_state.current_session_id)
                if session:
                    st.write(f"Destination: {session.travel_request.destination}")
                    st.write(f"Duration: {session.travel_request.num_days} days")

                    if st.button("Delete Session"):
                        self.session_manager.delete_session(st.session_state.current_session_id)
                        for key in ['travel_plan', 'current_session_id']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()

            # User sessions
            st.subheader("Your Sessions")
            user_sessions = self.session_manager.get_user_sessions(st.session_state.user_id)

            if user_sessions:
                for session_id, session in user_sessions.items():
                    if st.button(f"{session.travel_request.destination} ({session_id[:8]}...)",
                               key=f"session_{session_id}"):
                        st.session_state.current_session_id = session_id
                        st.session_state.travel_plan = session.travel_plan
                        st.rerun()
            else:
                st.write("No previous sessions")

            # About
            st.subheader("About")
            st.write("""
            This AI Travel Planner uses advanced AI to create personalized travel itineraries
            based on your preferences, budget, and interests.
            """)

    def run(self):
        """Main application runner"""
        self.render_header()
        self.render_sidebar()

        # Main content
        if st.session_state.travel_plan:
            self.render_travel_plan(st.session_state.travel_plan)
        else:
            self.render_travel_form()

            # Show budget estimation in sidebar if we have partial info
            if hasattr(st.session_state, 'last_destination') and hasattr(st.session_state, 'last_days'):
                with st.sidebar:
                    try:
                        budget_preview = self.langgraph_agent.calculate_budget_estimate(
                            st.session_state.last_destination,
                            st.session_state.last_days,
                            "Unknown City",
                            "USD"
                        )
                        st.subheader("Budget Preview")
                        st.write(f"Estimated: ${budget_preview['total_budget']:.0f} USD")
                    except Exception:
                        pass


def main():
    """Main function to run the Streamlit app"""
    app = TravelPlanningApp()
    app.run()


if __name__ == "__main__":
    main()
