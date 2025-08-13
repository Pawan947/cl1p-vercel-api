from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import parse_qs
import cgi
import time
import requests
from bs4 import BeautifulSoup


# ──────────────────────────────────────────────
# Cl1pBoard class (Universal branch, Python)
# ──────────────────────────────────────────────
class Cl1pBoard():
    def __init__(self):
        self.Cl1pBoardDefaultURL = "https://cl1p.net/"
        self.Cl1pBoardDefaultAPIURL = "https://api.cl1p.net/"
        self.Cl1pBoardDeleteClipboardURL = "https://cl1p.net/sys/deleteCl1p.jsp"
        self.Cl1pBoardName = ""
        self.DeleteKey = ""
        self.ExpireDate = None

    def isClipboardAvailable(self):
        url = self.Cl1pBoardDefaultAPIURL + self.Cl1pBoardName
        r = requests.get(url)
        if r.status_code == 200:
            if r.text.strip() == "":
                return True
        return False

    def createClipboard(self, data: str, timeout: int):
        dataToSend = {
            'ttl': str(timeout),
            'content': data
        }
        url = self.Cl1pBoardDefaultURL + self.Cl1pBoardName
        r = requests.post(url, headers={}, data=dataToSend)
        soup = BeautifulSoup(r.text, 'html.parser')
        DeletionParagraph = soup.find('p', class_='smallerText')
        if DeletionParagraph:
            DeletionTag = DeletionParagraph.find('b')
            try:
                if DeletionTag:
                    self.DeleteKey = DeletionTag.get_text().strip()
            except UnboundLocalError:
                pass

        if timeout > 0:
            self.ExpireDate = time.time() + timeout * 60
        else:
            self.ExpireDate = 0

    def getClipboard(self):
        url = self.Cl1pBoardDefaultAPIURL + self.Cl1pBoardName
        r = requests.get(url)
        if r.status_code == 200:
            return r.text
        return False

    def deleteClipboard(self):
        payload = {'token': str(self.DeleteKey)}
        r = requests.post(self.Cl1pBoardDeleteClipboardURL, headers={}, data=payload)
        if r.status_code == 200:
            return True
        return False


# ──────────────────────────────────────────────
# Vercel API handler
# ──────────────────────────────────────────────
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_type = self.headers.get('content-type', '')

        # Handle multipart/form-data (for file uploads)
        if content_type.startswith("multipart/form-data"):
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': content_type,
                }
            )
            action = form.getvalue("action", "")
            board_name = form.getvalue("name", "")
            timeout = int(form.getvalue("timeout", 0))

            cb = Cl1pBoard()
            cb.Cl1pBoardName = board_name

            if action == "create_file":
                if "file" in form:
                    file_item = form["file"]
                    file_content = file_item.file.read().decode(errors="ignore")
                    cb.createClipboard(file_content, timeout)
                    response = {
                        "status": "created",
                        "deleteKey": cb.DeleteKey,
                        "expireTimestamp": cb.ExpireDate
                    }
                else:
                    response = {"error": "No file uploaded"}
            else:
                response = {"error": "Invalid action for multipart"}

        # Handle x-www-form-urlencoded
        else:
            length = int(self.headers.get('content-length', 0))
            body = self.rfile.read(length).decode()
            data = parse_qs(body)

            action = data.get("action", [""])[0]
            board_name = data.get("name", [""])[0]
            content = data.get("content", [""])[0]
            timeout = int(data.get("timeout", [0])[0])
            delete_key = data.get("deleteKey", [""])[0]

            cb = Cl1pBoard()
            cb.Cl1pBoardName = board_name

            if action == "create":
                cb.createClipboard(content, timeout)
                response = {
                    "status": "created",
                    "deleteKey": cb.DeleteKey,
                    "expireTimestamp": cb.ExpireDate
                }
            elif action == "get":
                text = cb.getClipboard()
                response = {"status": "success", "content": text}
            elif action == "delete":
                cb.DeleteKey = delete_key
                ok = cb.deleteClipboard()
                response = {"status": "deleted" if ok else "failed"}
            else:
                response = {"error": "Invalid action"}

        self._send_json(response)

    def do_GET(self):
        self._send_json({"message": "Cl1p API is alive"})

    def _send_json(self, obj):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())
