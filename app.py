from flask import Flask, request
import json

app = Flask(__name__)

@app.route("/callback", methods=["POST"])
def callback():
    data = request.get_json(silent=True)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)