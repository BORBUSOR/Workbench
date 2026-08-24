import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from icalendar import Calendar, Event

def generate_output_files(parsed_courses, output_dir):
    ics_path = os.path.join(output_dir, "ZCS_Schedule.ics")
    pdf_path = os.path.join(output_dir, "ZCS_Schedule_Printable.pdf")
    
    # 1. Generate ICS File (Excludes Pending/Waitlisted courses from active calendar sync)
    cal = Calendar()
    cal.add('prodid', '-//Zodiac Custom Shop//ZCS Schedule Tool//EN')
    cal.add('version', '2.0')
    
    for course in parsed_courses:
        if course.get("status", "Active") == "Active":
            event = Event()
            event.add('summary', course["name"])
            event.add('description', f'Parsed by ZCS Tool.\nDays: {course["days"]}\nTime: {course["time"]}')
            event.add('location', course["room"])
            event.add('dtstart', datetime.now())
            event.add('dtend', datetime.now())
            cal.add_component(event)
        
    with open(ics_path, 'wb') as f:
        f.write(cal.to_ical())
        
    # 2. Generate Landscape Weekly Grid PDF File (Monday through Sunday)
    doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=25, bottomMargin=25)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=15, textColor=colors.HexColor('#1a1a1a'), spaceAfter=8)
    cell_style = ParagraphStyle('GridCell', parent=styles['Normal'], fontSize=7.5, leading=9.5, textColor=colors.HexColor('#2c3e50'))
    header_style = ParagraphStyle('GridHeader', parent=styles['Normal'], fontSize=8.5, leading=10.5, fontName='Helvetica-Bold', textColor=colors.whitesmoke, alignment=1)
    time_style = ParagraphStyle('TimeCell', parent=styles['Normal'], fontSize=7.5, leading=9.5, fontName='Helvetica-Bold', textColor=colors.HexColor('#555555'), alignment=1)

    story.append(Paragraph("<b>ZODIAC CUSTOM SHOP: WEEKLY MASTER SCHEDULE (MON - SUN)</b>", title_style))
    story.append(Spacer(1, 4))
    
    # Define time slots (Rows from 8:00 AM to 7:00 PM)
    hours = [
        "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", 
        "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM", "6:00 PM", "7:00 PM"
    ]
    
    # Days map covering Monday through Sunday abbreviations
    days_map = {
        "Mo": 1, "Tu": 2, "We": 3, "Th": 4, "Fr": 5, "Sa": 6, "Su": 7,
        "Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5, "Sat": 6, "Sun": 7
    }
    
    # Initialize grid matrix: 12 rows for hours + 1 header row. Columns: Time, Mon-Sun (8 columns total)
    grid_data = [["Time", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]]
    
    row_mapping = {}
    for i, hour in enumerate(hours):
        grid_data.append([hour, "", "", "", "", "", "", ""])
        row_mapping[hour] = i + 1

    pending_courses = []
    
    for course in parsed_courses:
        status = course.get("status", "Active")
        if status != "Active":
            pending_courses.append(course)
            continue
            
        c_name = course["name"]
        c_days = course["days"]
        c_time = course["time"]
        c_room = course["room"]
        
        start_hour_key = None
        c_time_upper = c_time.upper()
        for hour in hours:
            h_prefix = hour.split(":")[0]
            if f"{h_prefix}:" in c_time_upper or f"{h_prefix} " in c_time_upper:
                start_hour_key = hour
                break
        
        if not start_hour_key:
            continue
            
        row_idx = row_mapping[start_hour_key]
        cell_content = f"<b>{c_name}</b><br/>{c_time}<br/>{c_room}"
        
        placed_cols = set()
        for day_code, col_idx in days_map.items():
            if day_code in c_days and col_idx not in placed_cols:
                existing = grid_data[row_idx][col_idx]
                if existing:
                    grid_data[row_idx][col_idx] = existing + "<br/><br/>" + cell_content
                else:
                    grid_data[row_idx][col_idx] = cell_content
                placed_cols.add(col_idx)

    formatted_grid = []
    for r_idx, row in enumerate(grid_data):
        new_row = []
        for c_idx, cell in enumerate(row):
            if r_idx == 0:
                new_row.append(Paragraph(cell, header_style))
            elif c_idx == 0:
                new_row.append(Paragraph(cell, time_style))
            else:
                new_row.append(Paragraph(cell, cell_style))
        formatted_grid.append(new_row)

    # Column widths tailored for 8 columns across landscape letter width (~752 pt printable area)
    col_widths = [56, 99, 99, 99, 99, 99, 99, 99]
    
    t = Table(formatted_grid, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    story.append(t)
    
    if pending_courses:
        story.append(Spacer(1, 10))
        story.append(Paragraph("<b>PENDING / WAITLISTED COURSES (Excluded from Active Calendar)</b>", ParagraphStyle('SubHeader', parent=styles['Heading2'], fontSize=10, textColor=colors.HexColor('#c0392b'))))
        story.append(Spacer(1, 3))
        
        pending_data = [["Course Code", "Meeting Days & Time", "Location", "Status"]]
        for pc in pending_courses:
            pending_data.append([pc["name"], f"{pc['days']} {pc['time']}".strip(), pc["room"], "Waitlist / Pending"])
            
        pt = Table(pending_data, colWidths=[150, 250, 150, 152])
        pt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c0392b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fdfefe')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f5b7b1')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(pt)

    doc.build(story)
    return ics_path, pdf_path