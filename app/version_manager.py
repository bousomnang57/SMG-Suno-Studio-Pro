"""
Multi-Take Version Manager for Songwriters and Music Producers.
Allows drafting, duplicating, comparing, and managing unlimited Takes of lyrics.
"""

class VersionManager:
    def __init__(self):
        self.takes = {
            "Take 1 (Main)": "",
            "Take 2 (Alternate)": "",
            "Take 3 (Draft)": ""
        }
        self.current_take = "Take 1 (Main)"

    def get_take(self, take_name: str) -> str:
        return self.takes.get(take_name, "")

    def save_take(self, take_name: str, lyrics: str):
        self.takes[take_name] = lyrics

    def list_takes(self) -> list:
        return list(self.takes.keys())

    def add_take(self, name: str, content: str = "") -> str:
        name = name.strip()
        if not name:
            idx = len(self.takes) + 1
            name = f"Take {idx}"
        # Ensure unique name
        base = name
        counter = 2
        while name in self.takes:
            name = f"{base} ({counter})"
            counter += 1
        self.takes[name] = content
        return name

    def duplicate_take(self, source_name: str) -> str:
        content = self.get_take(source_name)
        new_name = f"{source_name} (Copy)"
        return self.add_take(new_name, content)

    def delete_take(self, name: str) -> bool:
        if len(self.takes) <= 1:
            return False  # Always keep at least 1 take
        if name in self.takes:
            del self.takes[name]
            return True
        return False
