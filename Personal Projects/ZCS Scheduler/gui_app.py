import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import pytesseract
from dotenv import load_dotenv

from parsers import get_supported_schools, parse_schedule_text
from generators import generate_output_files
from mailer import send_email_with_attachments

# Load local environment variables from .env
load_dotenv()

# Point Python directly to your Tesseract installation
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preview_and_process():
    selected_school = school_var.get()
    if selected_school == "Other School (Please Specify)":
        custom_name = custom_school_entry.get().strip()
        if not custom_name:
            messagebox.showerror("Error", "Please enter your custom university name.")
            return
        school = custom_name
    else:
        school = selected_school

    recipient = recipient_entry.get().strip()
    if not recipient or "@" not in recipient:
        messagebox.showerror("Error", "Please enter a valid recipient email address.")
        return

    file_path = filedialog.askopenfilename(
        title="Select Schedule Image",
        filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
    )
    if not file_path:
        return

    try:
        # Save sample to test_submissions folder for data logging
        sub_dir = os.path.join(os.path.dirname(__file__), "test_submissions")
        os.makedirs(sub_dir, exist_ok=True)
        img = Image.open(file_path)
        img_copy_path = os.path.join(sub_dir, f"submission_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        img.save(img_copy_path)

        # Run OCR and Parse (passing recipient email into the parser for database indexing)
        raw_text = pytesseract.image_to_string(img)
        parsed_courses = parse_schedule_text(raw_text, school, image_path=file_path, email=recipient)
        
        output_dir = os.path.dirname(file_path)
        ics_path, pdf_path = generate_output_files(parsed_courses, output_dir)

        # --- PREVIEW WINDOW ---
        preview_win = tk.Toplevel(root)
        preview_win.title("Schedule Parsing Preview")
        preview_win.geometry("500x420")
        preview_win.configure(bg="#f8f9fa")

        tk.Label(preview_win, text=f"Preview for {school}", font=("Helvetica", 12, "bold"), bg="#f8f9fa").pack(pady=10)
        
        text_frame = tk.Frame(preview_win, bg="#ffffff")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        txt_box = tk.Text(text_frame, wrap=tk.WORD, font=("Helvetica", 9), height=12)
        txt_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Format display text with waitlist flag if status is Pending
        formatted_lines = []
        for c in parsed_courses:
            status_tag = " [WAITLIST]" if c.get("status") == "Pending" else ""
            formatted_lines.append(f"• {c['name']}{status_tag} | {c['days']} {c['time']} | {c['room']}")
            
        summary_text = "Detected Courses:\n" + "\n".join(formatted_lines)
        txt_box.insert(tk.END, summary_text)
        txt_box.config(state=tk.DISABLED)

        def confirm_and_send():
            html_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; color: #333333; line-height: 1.6;">
                <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
                  <h2 style="color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 8px;">Zodiac Custom Shop: Schedule Converter</h2>
                  <p>Hello,</p>
                  <p>Your schedule for <b>{school}</b> has been successfully parsed and generated.</p>
                  <p>Attached you will find your <b>.ics</b> calendar file and your print-friendly <b>PDF</b> schedule.</p>
                </div>
              </body>
            </html>
            """
            send_email_with_attachments(recipient, [ics_path, pdf_path], "ZCS Master Schedule & Calendar Files", html_body)
            preview_win.destroy()
            messagebox.showinfo("Success!", f"Schedule verified and emailed successfully to:\n{recipient}")

        def send_support_ticket():
            support_email = "sebasrivas@zodiaccustomshop.com"
            
            output_summary = "<br>".join([f"&bull; <b>{c['name']}</b>{' [WAITLIST]' if c.get('status') == 'Pending' else ''} | {c['days']} | {c['time']} | {c['room']}" for c in parsed_courses])
            
            ticket_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; color: #333333; line-height: 1.5;">
                <h3 style="color: #c0392b; border-bottom: 2px solid #c0392b; padding-bottom: 5px;">Support Ticket: Incorrect Schedule Format</h3>
                <p><b>School Selected:</b> {school}</p>
                <p><b>User Email:</b> {recipient}</p>
                
                <h4 style="color: #2c3e50; margin-top: 15px;">Attempted Parsed Output:</h4>
                <div style="background: #f8f9fa; border: 1px solid #ddd; padding: 10px; border-radius: 5px;">
                  {output_summary if output_summary else "No courses parsed."}
                </div>

                <h4 style="color: #2c3e50; margin-top: 15px;">Raw OCR Text:</h4>
                <pre style="background: #f1f1f1; padding: 10px; border-radius: 5px; font-size: 11px;">{raw_text}</pre>
                
                <p style="font-size: 12px; color: #666; margin-top: 20px;">* Attached to this email are the user's uploaded schedule image and the failed PDF output for your review.</p>
              </body>
            </html>
            """
            
            try:
                send_email_with_attachments(
                    support_email, 
                    [img_copy_path, pdf_path], 
                    f"SUPPORT TICKET: {school} Parsing Error", 
                    ticket_body
                )
                preview_win.destroy()
                messagebox.showinfo("Ticket Sent", f"Support ticket successfully sent to {support_email}.\nSebastian will review your format and update the database!")
            except Exception as ticket_err:
                messagebox.showerror("Ticket Error", f"Could not send support ticket:\n{str(ticket_err)}")

        btn_frame = tk.Frame(preview_win, bg="#f8f9fa")
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="Looks Correct! Send Files", command=confirm_and_send, font=("Helvetica", 10, "bold"), bg="#27ae60", fg="white", padx=10, pady=6).pack(side=tk.LEFT, padx=8)
        tk.Button(btn_frame, text="Report Incorrect Formatting", command=send_support_ticket, font=("Helvetica", 10, "bold"), bg="#c0392b", fg="white", padx=10, pady=6).pack(side=tk.LEFT, padx=8)

    except Exception as e:
        messagebox.showerror("Processing Error", f"An error occurred during analysis:\n{str(e)}")

def on_school_change(event):
    if school_var.get() == "Other / Custom University":
        f_custom.pack(pady=5)
        root.geometry("440x370")
    else:
        f_custom.pack_forget()
        root.geometry("440x320")

# --- NATIVE WINDOW UI SETUP ---
root = tk.Tk()
root.title("ZCS Dynamic Schedule Maker")
root.geometry("440x320")
root.configure(bg="#f8f9fa")

tk.Label(root, text="ZCS Dynamic Schedule Dispatcher", font=("Helvetica", 13, "bold"), bg="#f8f9fa", fg="#1a1a1a").pack(pady=15)

# School Selection Dropdown
f_school = tk.Frame(root, bg="#f8f9fa")
f_school.pack(pady=5)
tk.Label(f_school, text="Select School:", font=("Helvetica", 9, "bold"), bg="#f8f9fa", width=14, anchor="w").pack(side=tk.LEFT, padx=5)
school_var = tk.StringVar(value="University of Central Florida (UCF)")
school_dropdown = ttk.Combobox(f_school, textvariable=school_var, values=get_supported_schools(), width=24, state="readonly")
school_dropdown.pack(side=tk.LEFT, padx=5)
school_dropdown.bind("<<ComboboxSelected>>", on_school_change)

# Custom School Name Frame (Hidden by default)
f_custom = tk.Frame(root, bg="#f8f9fa")
tk.Label(f_custom, text="University Name:", font=("Helvetica", 9, "bold"), bg="#f8f9fa", width=14, anchor="w").pack(side=tk.LEFT, padx=5)
custom_school_entry = tk.Entry(f_custom, width=26, font=("Helvetica", 10))
custom_school_entry.pack(side=tk.LEFT, padx=5)

# Recipient Email Entry
f_email = tk.Frame(root, bg="#f8f9fa")
f_email.pack(pady=5)
tk.Label(f_email, text="Recipient Email:", font=("Helvetica", 9, "bold"), bg="#f8f9fa", width=14, anchor="w").pack(side=tk.LEFT, padx=5)
recipient_entry = tk.Entry(f_email, width=26, font=("Helvetica", 10))
recipient_entry.pack(side=tk.LEFT, padx=5)

# Action Button
btn = tk.Button(root, text="Upload Schedule & Preview", command=preview_and_process, font=("Helvetica", 10, "bold"), bg="#2c3e50", fg="white", padx=12, pady=10)
btn.pack(pady=20)

root.mainloop()