import csv
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class ReportGenerator:
    
    @staticmethod
    def generate_csv(analysis_result, violations, entries):
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['MED-THERM-2026 Compliance Report'])
        writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])
        
        writer.writerow(['=== COMPLIANCE SUMMARY ==='])
        writer.writerow(['Status:', 'PASS' if analysis_result.get('compliant') else 'FAIL'])
        writer.writerow(['Total Violations:', len(violations)])
        
        stats = analysis_result.get('stats', {})
        sev_stats = stats.get('violations_by_severity', {})
        writer.writerow(['Critical Violations:', sev_stats.get('critical', 0)])
        writer.writerow(['Major Violations:', sev_stats.get('major', 0)])
        writer.writerow(['Warnings:', sev_stats.get('warning', 0)])
        writer.writerow([])
        
        writer.writerow(['=== VIOLATION DETAILS ==='])
        if violations:
            writer.writerow(['Line', 'Regulation Code', 'Severity', 'Title', 'Description', 'Evidence'])
            for v in violations:
                writer.writerow([
                    v.get('line_number', ''),
                    v.get('regulation_code', ''),
                    v.get('severity', ''),
                    v.get('regulation_title', ''),
                    v.get('description', ''),
                    v.get('evidence', '')
                ])
        else:
            writer.writerow(['No violations detected'])
        writer.writerow([])
        
        writer.writerow(['=== REGULATORY REFERENCES ==='])
        from compliance_rules import REGULATORY_RULES
        for code, rule in REGULATORY_RULES.items():
            writer.writerow([code, rule['title'], rule['text']])
        
        return output.getvalue()
    
    @staticmethod
    def generate_pdf(analysis_result, violations, entries):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=18,
            spaceAfter=12,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor('#2c3e50')
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=3
        )
        
        story = []
        
        story.append(Paragraph('MED-THERM-2026 Compliance Report', title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                               ParagraphStyle('Center', parent=normal_style, alignment=TA_CENTER)))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph('Compliance Summary', heading_style))
        
        compliant = analysis_result.get('compliant', False)
        status_color = colors.green if compliant else colors.red
        status_text = 'PASS' if compliant else 'FAIL'
        
        summary_data = [
            ['Overall Status', status_text],
            ['Total Violations', str(len(violations))],
        ]
        
        stats = analysis_result.get('stats', {})
        sev_stats = stats.get('violations_by_severity', {})
        summary_data.extend([
            ['Critical Violations', str(sev_stats.get('critical', 0))],
            ['Major Violations', str(sev_stats.get('major', 0))],
            ['Warnings', str(sev_stats.get('warning', 0))],
        ])
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (1, 0), (1, 0), status_color),
            ('FONTWEIGHT', (1, 0), (1, 0), 'BOLD'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(summary_table)
        
        story.append(Spacer(1, 15))
        story.append(Paragraph('Violation Details', heading_style))
        
        if violations:
            violation_data = [['Line', 'Code', 'Severity', 'Title', 'Description']]
            
            for v in violations:
                severity = v.get('severity', '')
                line_num = str(v.get('line_number', ''))
                code = v.get('regulation_code', '')
                title = (v.get('regulation_title', '')[:50] + '...') if len(v.get('regulation_title', '')) > 50 else v.get('regulation_title', '')
                desc = (v.get('description', '')[:80] + '...') if len(v.get('description', '')) > 80 else v.get('description', '')
                
                violation_data.append([line_num, code, severity, title, desc])
            
            col_widths = [0.6*inch, 1*inch, 0.8*inch, 2*inch, 3*inch]
            violation_table = Table(violation_data, colWidths=col_widths)
            
            table_style = [
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]
            
            for i, row in enumerate(violation_data[1:], 1):
                if row[2] == 'critical':
                    table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ffcccc')))
                elif row[2] == 'major':
                    table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fff2cc')))
                elif row[2] == 'warning':
                    table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#e5f6ff')))
            
            violation_table.setStyle(TableStyle(table_style))
            story.append(violation_table)
        else:
            story.append(Paragraph('No violations detected.', normal_style))
        
        story.append(PageBreak())
        story.append(Paragraph('Regulatory References (MED-THERM-2026)', heading_style))
        
        from compliance_rules import REGULATORY_RULES
        for code, rule in REGULATORY_RULES.items():
            severity_color = {
                'critical': colors.HexColor('#e74c3c'),
                'major': colors.HexColor('#f39c12'),
                'warning': colors.HexColor('#3498db')
            }.get(rule['severity'], colors.black)
            
            story.append(Paragraph(
                f"<b>{code}</b> - <font color={severity_color.hexval()}>[{rule['severity'].upper()}]</font> {rule['title']}",
                ParagraphStyle('RuleTitle', parent=normal_style, fontSize=11, spaceBefore=10, spaceAfter=3)
            ))
            story.append(Paragraph(rule['text'], ParagraphStyle('RuleText', parent=normal_style, leftIndent=20)))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
