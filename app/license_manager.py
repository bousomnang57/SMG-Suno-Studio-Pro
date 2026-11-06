"""
Hardware-Locked Cryptographic License Management System for SMG Suno Studio Pro.
Generates unique, stable Windows Machine IDs (HWID) and verifies offline HMAC-SHA256 license signatures.
"""

import sys
import json
import hmac
import hashlib
import platform
from datetime import datetime, timedelta

from app.config import CONFIG_DIR

# Master Secret Seed for HMAC validation (Kept consistent between App and Keygen)
_MASTER_SALT = b"SMG_STUDIO_PRO_AUTH_SECURE_HMAC_SALT_2026_V2"
LICENSE_FILE = CONFIG_DIR / "license.json"

def get_machine_guid() -> str:
    """
    Retrieves the permanent Windows MachineGuid from registry.
    Falls back to platform/MAC hardware node if unavailable.
    """
    guid = ""
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
                guid, _ = winreg.QueryValueEx(key, "MachineGuid")
        except Exception:
            pass

    if not guid:
        # Fallback combining node MAC address and CPU architecture
        import uuid
        guid = f"{uuid.getnode():012x}-{platform.machine()}-{platform.processor()}"

    return guid.strip()

def get_machine_id() -> str:
    """
    Generates a clean, user-friendly 12-character Machine ID (HWID).
    Example format: 'SMG-8F2A-9C4B-11D0'
    """
    raw_guid = get_machine_guid()
    hasher = hashlib.sha256(raw_guid.encode("utf-8") + _MASTER_SALT)
    digest = hasher.hexdigest().upper()
    
    seg1 = digest[0:4]
    seg2 = digest[4:8]
    seg3 = digest[8:12]
    return f"SMG-{seg1}-{seg2}-{seg3}"

def generate_license_signature(hwid: str, plan_code: str, issue_date_str: str) -> str:
    """
    Computes an 8-character cryptographic signature for the given HWID, plan, and issue date.
    """
    norm_hwid = hwid.strip().upper()
    norm_plan = plan_code.strip().upper()
    data = f"{norm_hwid}|{norm_plan}|{issue_date_str}".encode("utf-8")
    sig = hmac.new(_MASTER_SALT, data, hashlib.sha256).hexdigest().upper()
    return sig[:8]

def format_license_key(hwid: str, plan_code: str, issue_date_str: str = "") -> str:
    """
    Constructs a full license key string:
    Format: SMG-{PLAN}-{HWID_PARTS}-{ISSUE_DATE}-{SIGNATURE}
    Example: SMG-LIFE-8F2A9C4B11D0-20261106-9E4F2A1C
    """
    if not issue_date_str:
        issue_date_str = datetime.now().strftime("%Y%m%d")
        
    clean_hwid_parts = hwid.replace("SMG-", "").replace("-", "").upper()
    sig = generate_license_signature(hwid, plan_code, issue_date_str)
    return f"SMG-{plan_code.upper()}-{clean_hwid_parts}-{issue_date_str}-{sig}"

class LicenseManager:
    """
    Manages active license state, HWID verification, expiry checks, and local activation persistence.
    """
    PLAN_NAMES = {
        "LIFE": "💎 Lifetime Studio Pro",
        "365D": "⏳ 1-Year Studio Pro",
        "180D": "⏳ 6-Month Studio Pro",
        "30D":  "⏳ 30-Day Studio Pro",
        "TRIAL": "🎁 7-Day Free Trial"
    }

    PLAN_DURATIONS = {
        "LIFE": None,
        "365D": 365,
        "180D": 180,
        "30D": 30,
        "TRIAL": 7
    }

    def __init__(self):
        self.machine_id = get_machine_id()
        self._license_data = self._load_license()

    def get_machine_id(self) -> str:
        return self.machine_id

    def _load_license(self) -> dict:
        """Loads and decrypts local license record."""
        if not LICENSE_FILE.exists():
            return {}
        try:
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception:
            return {}

    def _save_license(self, data: dict):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._license_data = data
        except Exception as e:
            print(f"Error saving license: {e}")

    def activate(self, key_str: str) -> tuple[bool, str]:
        """
        Validates the key against current machine ID and activates if valid.
        Returns (success: bool, message: str)
        """
        clean_key = key_str.strip().upper()
        parts = clean_key.split("-")
        
        # Expected format: SMG-{PLAN}-{HWID_12_CHARS}-{ISSUED_8_CHARS}-{SIG_8_CHARS}
        if len(parts) != 5 or parts[0] != "SMG":
            return False, "ទម្រង់ Key មិនត្រឹមត្រូវទេ (Invalid Key Format. Example: SMG-LIFE-XXXX...)"

        plan_code = parts[1]
        raw_hwid_parts = parts[2]
        issue_date_str = parts[3]
        provided_sig = parts[4]

        # 1. Verify Plan
        if plan_code not in self.PLAN_NAMES:
            return False, f"កញ្ចប់អាជ្ញាប័ណ្ណមិនត្រឹមត្រូវ: '{plan_code}' (Invalid plan code)"

        # 2. Verify HWID matching
        expected_raw_hwid = self.machine_id.replace("SMG-", "").replace("-", "").upper()
        if raw_hwid_parts != expected_raw_hwid:
            return False, "License Key នេះមិនត្រូវជាមួយកុំព្យូទ័ររបស់អ្នកទេ (Key is locked to another PC HWID)"

        # 3. Verify Cryptographic Signature
        expected_sig = generate_license_signature(self.machine_id, plan_code, issue_date_str)
        if not hmac.compare_digest(provided_sig, expected_sig):
            return False, "កូដបញ្ជាក់សុវត្ថិភាពមិនត្រឹមត្រូវ (Signature verification failed)"

        # 4. Calculate Expiry Date
        duration_days = self.PLAN_DURATIONS.get(plan_code)
        try:
            issue_dt = datetime.strptime(issue_date_str, "%Y%m%d")
        except ValueError:
            return False, "កាលបរិច្ឆេទក្នុង Key មិនត្រឹមត្រូវ (Invalid issue date)"

        if duration_days is None:
            expiry_str = "PERMANENT"
        else:
            expiry_dt = issue_dt + timedelta(days=duration_days)
            expiry_str = expiry_dt.strftime("%Y-%m-%d")
            # Check if already expired at time of activation
            if datetime.now() > expiry_dt:
                return False, f"Key នេះបានផុតកំណត់តាំងពីថ្ងៃ {expiry_str} (License has expired)"

        # 5. Save activation state
        record = {
            "key": clean_key,
            "machine_id": self.machine_id,
            "plan_code": plan_code,
            "plan_name": self.PLAN_NAMES.get(plan_code, "Studio Pro"),
            "issued_date": issue_date_str,
            "expiry_date": expiry_str,
            "activated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save_license(record)
        return True, f"ការធ្វើឱ្យសកម្មជោគជ័យ! (Activated {record['plan_name']})"

    def is_activated(self) -> bool:
        """Checks if current PC has a valid, non-expired license."""
        if not self._license_data:
            return False

        # Verify HWID integrity
        saved_hwid = self._license_data.get("machine_id", "")
        if saved_hwid != self.machine_id:
            return False

        # Verify cryptographic signature of saved key
        key = self._license_data.get("key", "")
        parts = key.split("-")
        if len(parts) != 5:
            return False

        plan_code = parts[1]
        issue_date_str = parts[3]
        provided_sig = parts[4]

        expected_sig = generate_license_signature(self.machine_id, plan_code, issue_date_str)
        if not hmac.compare_digest(provided_sig, expected_sig):
            return False

        # Verify expiration
        expiry_date = self._license_data.get("expiry_date", "")
        if expiry_date != "PERMANENT":
            try:
                exp_dt = datetime.strptime(expiry_date, "%Y-%m-%d")
                if datetime.now() > exp_dt:
                    return False
            except Exception:
                return False

        return True

    def get_license_info(self) -> dict:
        """Returns structured details about active license or trial status."""
        active = self.is_activated()
        if active:
            plan = self._license_data.get("plan_name", "Studio Pro")
            exp = self._license_data.get("expiry_date", "PERMANENT")
            exp_text = "អចិន្ត្រៃយ៍ (Lifetime - No Expiry)" if exp == "PERMANENT" else f"ផុតកំណត់: {exp}"
            return {
                "is_active": True,
                "plan_code": self._license_data.get("plan_code", "LIFE"),
                "plan_name": plan,
                "machine_id": self.machine_id,
                "expiry": exp,
                "expiry_text": exp_text,
                "badge_text": f"💎 {plan}"
            }
        else:
            return {
                "is_active": False,
                "plan_code": "FREE",
                "plan_name": "Free Demo Mode",
                "machine_id": self.machine_id,
                "expiry": "N/A",
                "expiry_text": "មិនទាន់ Activate នៅឡើយ",
                "badge_text": "🟡 Free Demo (Activate Pro)"
            }

    def deactivate(self):
        """Removes the local license record."""
        if LICENSE_FILE.exists():
            try:
                LICENSE_FILE.unlink()
            except Exception:
                pass
        self._license_data = {}

# Global singleton
license_manager = LicenseManager()
