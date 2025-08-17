import pynput.keyboard as keyboard
import datetime
import time
import pyautogui
import re
from google import genai
from pathlib import Path
import base64
import requests
import io
import os
from gui_alert import SafetyAlertGUI

ID_FILE = Path(__file__).parent / "data/parent_id.txt"
if ID_FILE.exists():
    parent_id = ID_FILE.read_text().strip()
else:
    parent_id = "DESCONOCIDO"

print(f"Keylogger iniciado por: {parent_id}")


class SmartChatKeylogger:
    def __init__(self):
        self.captured_text = ""
        self.current_sequence = ""
        self.listener = None
        self.running = False
        self.last_key_time = time.time()

        self.base_dir = Path(__file__).resolve().parent
        self.base_dir.mkdir(parents=True, exist_ok=True)
        # Gaming keys that create noise
        self.gaming_keys = {
            "w",
            "a",
            "s",
            "d",
            "q",
            "e",
            "r",
            "f",
            "g",
            "h",
            "z",
            "x",
            "c",
            "v",
        }

        # Chat indicators
        self.chat_indicators = {
            "enter_pressed": False,
            "has_spaces": False,
            "has_letters": False,
            "sequence_length": 0,
            "typing_speed": 0,
        }

        self.client = genai.Client(api_key="AIzaSyCWIli5rPeOLSQz-pc1SFTfDX8lBHYLjk0")

    def analyze_typing_pattern(self, sequence):
        """Analyze if the sequence looks like chat vs gaming"""
        if len(sequence) < 4:
            return False

        # Split into words and filter out WASD-only words
        words = sequence.split()
        wasd_chars = {"w", "a", "s", "d"}

        # Filter out words that only contain W, A, S, D characters
        real_words = []
        for word in words:
            word_chars = set(word.lower())
            # If word contains any character other than W,A,S,D, it's potentially real
            if not word_chars.issubset(wasd_chars):
                real_words.append(word)

        # If no real words remain after filtering, it's gaming noise
        if not real_words:
            return False

        # Reconstruct sequence without WASD-only words
        filtered_sequence = " ".join(real_words)
        if len(filtered_sequence) < 3:
            return False

        # Analyze the filtered sequence
        chars_only = filtered_sequence.replace(" ", "").lower()

        # Check for actual text patterns
        has_vowels = any(c in "aeiou" for c in chars_only)
        has_consonants = any(c in "bcdfghjklmnpqrtvxyz" for c in chars_only)
        has_multiple_words = len(real_words) > 1
        has_numbers = any(c.isdigit() for c in filtered_sequence)

        # Check if it's just repetitive characters
        is_repetitive = len(set(chars_only)) < max(2, len(chars_only) * 0.3)

        # Chat likelihood scoring
        chat_score = 0
        if has_vowels:
            chat_score += 3
        if has_consonants:
            chat_score += 2
        if has_multiple_words:
            chat_score += 4
        if has_numbers:
            chat_score += 1
        if len(filtered_sequence) > 6:
            chat_score += 2
        if not is_repetitive:
            chat_score += 2

        # Must have both vowels and consonants for real text
        if not (has_vowels and has_consonants):
            return False

        return chat_score >= 6

    def on_key_press(self, key):
        """Process each keystroke"""
        current_time = time.time()

        try:
            # Regular character
            char = key.char
            self.current_sequence += char

        except AttributeError:
            # Special keys
            if key == keyboard.Key.space:
                self.current_sequence += " "
                char = " "
            elif key == keyboard.Key.enter:
                # End of chat message - always save if it passes the filter
                if len(
                    self.current_sequence.strip()
                ) > 0 and self.analyze_typing_pattern(self.current_sequence):
                    self.save_chat_message(self.current_sequence)
                self.current_sequence = ""
                return
            elif key == keyboard.Key.backspace:
                if self.current_sequence:
                    self.current_sequence = self.current_sequence[:-1]
                return
            elif key == keyboard.Key.tab:
                self.current_sequence += "\t"
                return
            elif key == keyboard.Key.esc:
                print("\nESC pressed - stopping capture...")
                self.stop_capture()
                return False
            else:
                # Other special keys - don't end sequence immediately
                # Kids might pause while typing
                return

        # Only save very long sequences (likely spam)
        if len(self.current_sequence) > 100:
            if self.analyze_typing_pattern(self.current_sequence):
                self.save_chat_message(self.current_sequence)
            self.current_sequence = ""

        # Clear old sequences only after much longer inactivity
        time_since_last = current_time - self.last_key_time
        if time_since_last > 10:  # 10 seconds of inactivity
            if len(self.current_sequence) > 5 and self.analyze_typing_pattern(
                self.current_sequence
            ):
                self.save_chat_message(self.current_sequence)
            self.current_sequence = ""

        self.last_key_time = current_time

    def clean_wasd_noise(self, text):
        """Remove words that only contain W, A, S, D characters"""
        wasd_chars = {"w", "a", "s", "d"}
        words = text.split()

        # Filter out words that only contain WASD characters
        clean_words = []
        for word in words:
            word_chars = set(word.lower())
            # Keep word only if it contains characters other than W,A,S,D
            if not word_chars.issubset(wasd_chars) and word_chars:
                clean_words.append(word)

        # Join back and clean up extra spaces
        cleaned_text = " ".join(clean_words)
        # Remove multiple spaces
        cleaned_text = " ".join(cleaned_text.split())

        return cleaned_text.strip()

    def save_chat_message(self, message):
        """Save detected chat message with timestamp"""
        # First clean up WASD noise
        cleaned_message = self.clean_wasd_noise(message)

        # Don't save if nothing remains after cleaning
        if not cleaned_message or len(cleaned_message) < 3:
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat_entry = f"[{timestamp}] CHAT: {cleaned_message}\n"

        self.captured_text += chat_entry
        print(f"Chat detected: {cleaned_message[:50]}...")  # Preview

        # Evaluate chat
        evaluation = self.evaluate_chats(cleaned_message)

        # Solo tomar screenshot si la evaluación indica riesgo o relevante
        if evaluation != "normal/none":
            # Take screenshot of entire screen
            screenshot = pyautogui.screenshot()

            # Guardar localmente
            timestamp_screenshot = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = self.base_dir / f"screenshot_{timestamp_screenshot}.png"
            screenshot.save(screenshot_path)

            # Convertir a bytes para enviar
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            screenshot_bytes = buffered.getvalue()

            # Codificar a base64
            encoded_screenshot = base64.b64encode(screenshot_bytes).decode("utf-8")

            # Enviar al servidor
            self.send_screenshot(encoded_screenshot)

            alert_message = f"Se ha detectado un mensaje potencialmente riesgoso:\n\n{cleaned_message}"
            required_phrase = "ACEPTO REGLAS"

            gui = SafetyAlertGUI(
                on_timeout_or_no_understanding=lambda: print(
                    "Acción de seguridad ejecutada"
                ),
                message_text=alert_message,
                required_phrase=required_phrase,
            )
            gui.show_alert()

    def send_screenshot(self, screenshot):
        """Send screenshot to server"""
        url = "http://127.0.0.1:8000/api/get_screenshot/"
        try:
            response = requests.post(url, json={"screenshot": screenshot})
            print(response.text)
        except Exception as e:
            print(f"No se pudo enviar el screenshot: {e}")

    def start_monitoring(self):
        """Start the keylogger"""
        if self.running:
            print("Keylogger is already running!")
            return

        print("Starting smart chat detection...")
        print("This will filter out gaming noise and capture actual conversations")
        print("Press ESC to stop monitoring")

        self.running = True

        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()

        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_capture()

    def stop_capture(self):
        """Stop capturing and display results"""
        print("\nStopping chat monitoring...")
        self.running = False
        if self.listener:
            self.listener.stop()

        print("\n" + "=" * 60)
        print("DETECTED CHAT MESSAGES:")
        print("=" * 60)
        if self.captured_text:
            print(self.captured_text)
        else:
            print("No chat messages detected.")
        print("=" * 60)

    def get_chat_messages(self):
        """Return all detected chat messages"""
        return self.captured_text

    def get_recent_chats(self, minutes=30):
        """Get chats from the last X minutes"""
        lines = self.captured_text.split("\n")
        recent_chats = []

        current_time = datetime.datetime.now()
        cutoff_time = current_time - datetime.timedelta(minutes=minutes)

        for line in lines:
            if line.strip() and "CHAT:" in line:
                try:
                    # Extract timestamp
                    timestamp_str = line.split("]")[0][1:]
                    msg_time = datetime.datetime.strptime(
                        timestamp_str, "%Y-%m-%d %H:%M:%S"
                    )

                    if msg_time >= cutoff_time:
                        recent_chats.append(line)
                except:
                    continue

        return "\n".join(recent_chats)

    def evaluate_chats(self, msg):
        """Evaluate chat message using Gemini AI"""
        try:
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=f"""
                You are a text pattern analyzer. Analyze the following message for potentially concerning communication patterns.

                Text to analyze: "{msg}"

                Classification categories:
                1. image_request - Requests for photos or images
                2. meeting_request - Requests to meet in person
                3. location_request - Asking for address, location, or personal details
                4. secrecy_request - Asking to keep conversations private or secret
                5. manipulation - Excessive compliments, "special" language, emotional pressure
                6. gift_offer - Offering money, gifts, or rewards
                7. boundary_test - Testing limits or pushing boundaries

                Risk levels: low, medium, high

                Respond ONLY in this format: [category]/[level] or normal/none

                Examples:
                Input: "can you send me a picture"
                Output: image_request/medium

                Input: "we should meet up sometime"
                Output: meeting_request/medium

                Input: "what's your address"
                Output: location_request/high

                Input: "don't tell your parents we talk"
                Output: secrecy_request/high

                Input: "hello how are you today"
                Output: normal/none

                Input: "you're so mature for your age"
                Output: manipulation/medium

                Analyze the message and respond with the format above.
                """,
            )

            if response and hasattr(response, "text") and response.text:
                response_text = response.text.strip().lower()
                if "/" in response_text:
                    parts = response_text.split("/")
                    if len(parts) >= 2:
                        category = parts[0].strip()
                        severity = parts[1].strip()
                        print(f"For {msg}: {category}/{severity}")
                        return f"{category}/{severity}"

        except Exception as e:
            print(f"AI Error: {e}")

        # Fallback to rule-based if AI fails
        result = self.rule_based_analysis(msg)
        if result != "NA/NA":
            print(f"For {msg}: {result}")
        return result

    def rule_based_analysis(self, msg):
        """Rule-based analysis for concerning patterns"""
        msg_lower = msg.lower().strip()

        # Define concerning patterns and keywords
        photo_keywords = [
            "foto",
            "photo",
            "pic",
            "picture",
            "imagen",
            "selfie",
            "manda",
            "send",
            "envia",
        ]
        meeting_keywords = [
            "vemos",
            "meet",
            "encuentro",
            "reunion",
            "conocer",
            "verse",
            "quedar",
            "salir",
        ]
        location_keywords = [
            "donde vives",
            "direccion",
            "casa",
            "escuela",
            "where do you live",
            "address",
            "location",
        ]
        secrecy_keywords = [
            "secreto",
            "no digas",
            "entre nosotros",
            "secret",
            "dont tell",
            "between us",
            "privado",
        ]
        manipulation_keywords = [
            "especial",
            "madura",
            "diferente",
            "special",
            "mature",
            "unique",
            "regalo",
            "gift",
        ]
        inappropriate_keywords = [
            "sexy",
            "linda",
            "hermosa",
            "cuerpo",
            "body",
            "intimate",
            "beautiful",
            "attractive",
        ]

        # Check for photo requests
        photo_score = sum(1 for keyword in photo_keywords if keyword in msg_lower)
        if photo_score >= 1 and any(
            word in msg_lower for word in ["tu", "tuya", "your", "you"]
        ):
            return "photo_request/high"
        elif photo_score >= 1:
            return "photo_request/medium"

        # Check for meeting requests
        meeting_score = sum(1 for keyword in meeting_keywords if keyword in msg_lower)
        location_score = sum(1 for keyword in location_keywords if keyword in msg_lower)

        if meeting_score >= 1 and location_score >= 1:
            return "meeting_request/high"
        elif meeting_score >= 1:
            return "meeting_request/medium"
        elif location_score >= 1:
            return "personal_info/high"

        # Check for secrecy requests
        secrecy_score = sum(1 for keyword in secrecy_keywords if keyword in msg_lower)
        if secrecy_score >= 1:
            return "secrecy_request/high"

        # Check for manipulation
        manipulation_score = sum(
            1 for keyword in manipulation_keywords if keyword in msg_lower
        )
        if manipulation_score >= 2:
            return "manipulation/medium"
        elif manipulation_score >= 1 and len(msg) > 20:  # Longer manipulative messages
            return "manipulation/low"

        # Check for inappropriate content
        inappropriate_score = sum(
            1 for keyword in inappropriate_keywords if keyword in msg_lower
        )
        if inappropriate_score >= 1:
            return "inappropriate_content/medium"

        # Check for gift/incentive offers
        if any(
            word in msg_lower
            for word in ["regalo", "dinero", "money", "gift", "buy", "comprar"]
        ):
            return "incentive_offer/medium"

        return "NA/NA"


# Usage
if __name__ == "__main__":
    parend_id = os.environ.get("PARENT_ID")
    print(f"Parent ID: {parend_id}")
    print("Smart Chat Detection Keylogger")
    print("Filters out gaming noise (WASD, etc.) and captures actual conversations")
    print("Install with: pip install pynput")
    print()

    monitor = SmartChatKeylogger()
    monitor.start_monitoring()
