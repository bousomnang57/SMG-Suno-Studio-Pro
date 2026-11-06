"""
SMG Suno Studio Pro — Admin License Key Generator Tool.
Run this script to generate hardware-locked license keys for customers.
Supports CLI terminal mode and standalone GUI window mode.
"""

import sys
import os
import csv
from pathlib import Path
from datetime import datetime, timedelta

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.license_manager import format_license_key, LicenseManager, get_machine_id

CSV_DATABASE = Path(__file__).resolve().parent / "customer_licenses.csv"

def log_customer_license(customer_name: str, hwid: str, plan_code: str, plan_name: str, key: str, notes: str = ""):
    """
    Appends generated license records to customer_licenses.csv for admin tracking.
    """
    file_exists = CSV_DATABASE.exists()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate expiry
    durations = LicenseManager.PLAN_DURATIONS
    days = durations.get(plan_code)
    if days:
        exp_str = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    else:
        exp_str = "LIFETIME (Permanent)"

    try:
        with open(CSV_DATABASE, mode="a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Date Created", "Customer Name / Contact", "Machine ID", "Plan Code", "Plan Name", "License Key", "Expiry Date", "Notes"])
            writer.writerow([now_str, customer_name or "N/A", hwid, plan_code, plan_name, key, exp_str, notes or ""])
    except Exception as e:
        print(f"[!] Warning: Could not log to CSV: {e}")

def cli_keygen():
    print("=" * 65)
    print("      SMG SUNO STUDIO PRO — ADMIN LICENSE KEY GENERATOR       ")
    print("=" * 65)
    print(f"Current Host Machine ID: {get_machine_id()}\n")

    cust_name = input("Customer Name / Telegram (optional): ").strip()
    hwid = input("Enter Customer Machine ID (e.g. SMG-8F2A-9C4B-11D0): ").strip()
    if not hwid:
        print("[!] Error: Machine ID cannot be empty.")
        return

    print("\nSelect License Plan:")
    print("  1) 💎 Lifetime Studio Pro (No Expiry - ប្រើបានរហូត)")
    print("  2) ⏳ 1-Year Studio Pro (365 Days)")
    print("  3) ⏳ 6-Month Studio Pro (180 Days)")
    print("  4) ⏳ 30-Day Studio Pro (30 Days)")
    print("  5) 🎁 7-Day Free Trial (7 Days)")

    choice = input("\nSelect plan [1-5, default=1]: ").strip() or "1"
    plan_map = {
        "1": "LIFE",
        "2": "365D",
        "3": "180D",
        "4": "30D",
        "5": "TRIAL"
    }
    plan_code = plan_map.get(choice, "LIFE")
    plan_title = LicenseManager.PLAN_NAMES.get(plan_code, "Studio Pro")

    key = format_license_key(hwid, plan_code)
    log_customer_license(cust_name, hwid, plan_code, plan_title, key)

    print("\n" + "=" * 65)
    print(f"Customer:    {cust_name or 'N/A'}")
    print(f"Plan:        {plan_title}")
    print(f"Customer ID: {hwid}")
    print(f"LICENSE KEY: {key}")
    print(f"Saved to:    {CSV_DATABASE.name}")
    print("=" * 65)

    msg = f"""
🌟 សួស្តីបង! នេះជា License Key សម្រាប់កម្មវិធី SMG Suno Studio Pro របស់អ្នក៖
🔑 License Key: {key}
💻 ភ្ជាប់ជាមួយ Machine ID: {hwid}
💎 កញ្ចប់៖ {plan_title}

របៀបប្រើ៖
1. បើកកម្មវិធី SMG Suno Studio Pro
2. ចុចប៊ូតុង "🔑 Activate Pro" (នៅខាងលើស្តាំ)
3. Paste License Key ខាងលើចូល រួចចុច "Activate" ជាការស្រេច!
សូមអរគុណសម្រាប់ការគាំទ្រ! 🙏
"""
    print("\n[📋 Customer Delivery Message ready to copy to Telegram/FB]:")
    print(msg)

def gui_keygen():
    from PyQt6.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QLineEdit, QPushButton, QComboBox, QTextEdit, QMessageBox
    )
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon

    app = QApplication.instance() or QApplication(sys.argv)
    dlg = QDialog()
    dlg.setWindowTitle("SMG Suno Studio Pro — Admin Key Generator")
    dlg.setFixedSize(560, 520)
    dlg.setStyleSheet("""
        QDialog {
            background-color: #0c0f1d;
            color: #f1f5f9;
            font-family: 'Segoe UI', system-ui, sans-serif;
        }
        QLabel {
            color: #e2e8f0;
            font-size: 11px;
            font-weight: 600;
        }
        QLineEdit, QComboBox, QTextEdit {
            background-color: #161b2e;
            border: 1px solid #283256;
            border-radius: 6px;
            padding: 8px 10px;
            color: #ffffff;
            font-size: 11.5px;
        }
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
            border-color: #8b5cf6;
        }
        QPushButton {
            background-color: #1e293b;
            color: #ffffff;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 8px 14px;
            font-weight: 700;
            font-size: 11px;
        }
        QPushButton:hover {
            border-color: #8b5cf6;
        }
        #btnGenerate {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #ec4899);
            border: 1px solid #ffffff;
            font-weight: 800;
        }
    """)

    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(12)

    title = QLabel("🔑 SMG Studio Pro — Key Generator")
    title.setStyleSheet("font-size: 16px; font-weight: 800; color: #ffffff;")
    layout.addWidget(title)

    layout.addWidget(QLabel("1. Customer Name / Telegram Contact (Optional):"))
    input_name = QLineEdit()
    input_name.setPlaceholderText("e.g. John Doe / @johndoe_telegram")
    layout.addWidget(input_name)

    layout.addWidget(QLabel("2. Customer Machine ID (e.g. SMG-8F2A-9C4B-11D0):"))
    input_hwid = QLineEdit()
    input_hwid.setPlaceholderText("Paste customer's Machine ID here...")
    layout.addWidget(input_hwid)

    layout.addWidget(QLabel("3. Select License Plan:"))
    combo_plan = QComboBox()
    combo_plan.addItem("💎 Lifetime Studio Pro (No Expiry)", "LIFE")
    combo_plan.addItem("⏳ 1-Year Studio Pro (365 Days)", "365D")
    combo_plan.addItem("⏳ 6-Month Studio Pro (180 Days)", "180D")
    combo_plan.addItem("⏳ 30-Day Studio Pro (30 Days)", "30D")
    combo_plan.addItem("🎁 7-Day Free Trial", "TRIAL")
    layout.addWidget(combo_plan)

    btn_gen = QPushButton("⚡ Generate License Key")
    btn_gen.setObjectName("btnGenerate")
    btn_gen.setCursor(Qt.CursorShape.PointingHandCursor)
    layout.addWidget(btn_gen)

    lbl_csv_status = QLabel("")
    lbl_csv_status.setStyleSheet("color: #34d399; font-size: 10.5px; font-weight: 700;")
    layout.addWidget(lbl_csv_status)

    layout.addWidget(QLabel("4. Generated License Key:"))
    output_key = QLineEdit()
    output_key.setReadOnly(True)
    output_key.setStyleSheet("font-weight: 800; color: #34d399; font-size: 12px; background-color: #0f172a;")
    layout.addWidget(output_key)

    layout.addWidget(QLabel("5. Customer Delivery Message (Ready to send):"))
    output_msg = QTextEdit()
    output_msg.setReadOnly(True)
    layout.addWidget(output_msg, stretch=1)

    def on_generate():
        cust_name = input_name.text().strip()
        raw_hwid = input_hwid.text().strip().upper()
        if not raw_hwid:
            QMessageBox.warning(dlg, "Missing ID", "Please enter customer's Machine ID.")
            return
        plan_code = combo_plan.currentData()
        plan_name = combo_plan.currentText()
        key = format_license_key(raw_hwid, plan_code)
        output_key.setText(key)

        log_customer_license(cust_name, raw_hwid, plan_code, plan_name, key)
        lbl_csv_status.setText(f"✓ Key generated & logged into customer_licenses.csv ({datetime.now().strftime('%H:%M:%S')})")

        msg = f"""🌟 សួស្តីបង! នេះជា License Key សម្រាប់កម្មវិធី SMG Suno Studio Pro របស់អ្នក៖
🔑 License Key: {key}
💻 ភ្ជាប់ជាមួយ Machine ID: {raw_hwid}
💎 កញ្ចប់៖ {plan_name}

របៀបប្រើ៖
1. បើកកម្មវិធី SMG Suno Studio Pro
2. ចុចប៊ូតុង "🔑 Activate Pro" (នៅខាងលើស្តាំ)
3. Paste License Key ខាងលើចូល រួចចុច "⚡ ធ្វើឱ្យសកម្មឥឡូវនេះ (Activate Now)" ជាការស្រេច!
សូមអរគុណសម្រាប់ការគាំទ្រ! 🙏"""
        output_msg.setText(msg)

    btn_gen.clicked.connect(on_generate)
    dlg.exec()

def generate_key_for_machine(hwid: str, plan_code: str = "LIFE") -> str:
    """Convenience helper function for programmatic generation."""
    return format_license_key(hwid, plan_code)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SMG Suno Studio Pro — Admin License Key Generator")
    parser.add_argument("--hwid", help="Customer Machine ID (e.g. SMG-CAEB-B503-642C)")
    parser.add_argument("--plan", default="LIFE", choices=["LIFE", "365D", "180D", "30D", "TRIAL"], help="License Plan (default: LIFE)")
    parser.add_argument("--name", default="", help="Customer Name or Contact (optional)")
    parser.add_argument("--notes", default="", help="Admin notes, transaction ID, payment info (optional)")
    parser.add_argument("--cli", action="store_true", help="Run interactive CLI mode")
    args, unknown = parser.parse_known_args()

    if args.hwid:
        plan_name = LicenseManager.PLAN_NAMES.get(args.plan, "Studio Pro")
        key = format_license_key(args.hwid, args.plan)
        log_customer_license(args.name, args.hwid, args.plan, plan_name, key, args.notes)
        print("=" * 65)
        print(f"Customer:    {args.name or 'N/A'}")
        print(f"Plan:        {plan_name}")
        print(f"Customer ID: {args.hwid.upper()}")
        print(f"LICENSE KEY: {key}")
        print(f"Database:    Saved to {CSV_DATABASE.name}")
        print("=" * 65)
        print(f"""
🌟 សួស្តីបង! នេះជា License Key សម្រាប់កម្មវិធី SMG Suno Studio Pro របស់អ្នក៖
🔑 License Key: {key}
💻 ភ្ជាប់ជាមួយ Machine ID: {args.hwid.upper()}
💎 កញ្ចប់៖ {plan_name}

របៀបប្រើ៖
1. បើកកម្មវិធី SMG Suno Studio Pro
2. ចុចប៊ូតុង "🔑 Activate Pro" (នៅខាងលើស្តាំ)
3. Paste License Key ខាងលើចូល រួចចុច "⚡ ធ្វើឱ្យសកម្មឥឡូវនេះ (Activate Now)" ជាការស្រេច!
សូមអរគុណសម្រាប់ការគាំទ្រ! 🙏
""")
    elif args.cli:
        cli_keygen()
    else:
        try:
            gui_keygen()
        except Exception as e:
            print(f"GUI failed ({e}), falling back to CLI mode...")
            cli_keygen()
