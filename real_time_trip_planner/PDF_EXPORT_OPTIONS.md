# PDF Export Options

The Travel Planner now supports multiple export formats to handle different deployment environments and dependency requirements.

## Available Export Methods

### 1. Text File Export (Recommended - No Dependencies)
- **No external libraries required**
- Works in any Python environment
- Clean formatted text output
- Includes all travel plan content
- Perfect for environments with restricted package installation

### 2. Simple PDF (fpdf2)
- Requires: `pip install fpdf2`
- Lightweight PDF generation
- Basic formatting and layout
- Good for simple document needs

### 3. Advanced PDF (ReportLab)
- Requires: `pip install reportlab`
- Professional PDF with tables, styles, and layouts
- Budget breakdown tables
- Advanced formatting features

## Installation Instructions

### For Text Export (Default)
No installation required - works out of the box!

### For Simple PDF
```bash
pip install fpdf2
```

### For Advanced PDF
```bash
pip install reportlab
```

### For All Options
```bash
pip install fpdf2 reportlab
```

## Usage

1. Generate your travel plan using the AI Travel Planner
2. Click "Export as PDF"
3. Choose your preferred export method:
   - **Text File**: Always available, no setup needed
   - **Simple PDF**: If fpdf2 is installed
   - **Advanced PDF**: If reportlab is installed

## Deployment Considerations

### Streamlit Cloud / Railway / Render
Add to your `requirements.txt`:
```
fpdf2>=2.7.0          # For simple PDF
reportlab>=4.0.0      # For advanced PDF (optional)
```

### Local Development
Install dependencies as needed:
```bash
pip install fpdf2 reportlab
```

### Restricted Environments
Use the Text File export option - it requires no external dependencies and produces clean, formatted output that can be easily converted to PDF later if needed.

## Text File Format Features

- Clean ASCII formatting
- Currency symbol fixes (■40 → $40, ~50 → $50)
- Bullet point conversion
- Bold text handling
- Section headers with dividers
- Budget information formatting
- Professional layout

## Error Handling

If PDF libraries are not available, the app will:
1. Show available export options
2. Always offer text file as fallback
3. Provide installation instructions
4. Display helpful error messages

This ensures the travel planner remains functional regardless of the deployment environment.
