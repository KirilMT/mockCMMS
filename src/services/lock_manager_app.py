"""
lock_manager_app.py

Standalone Flask application exposing the lock manager REST API.
"""

import os
from datetime import datetime

from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS

from src.services.lock_manager import LockManager

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
LOCK_DB_PATH = os.environ.get("LOCK_DB_PATH", "instance/locks.db")
DEFAULT_EXPIRY = int(os.environ.get("LOCK_DEFAULT_EXPIRY_MINUTES", 480))

lock_manager = LockManager(db_path=LOCK_DB_PATH)


@app.route("/api/locks/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})


@app.route("/api/locks/acquire", methods=["POST"])
def acquire():
    data = request.json
    if not data or "file_path" not in data or "developer_id" not in data:
        return (
            jsonify(
                {"error": "Missing required fields", "field": "file_path/developer_id"}
            ),
            400,
        )

    success, result = lock_manager.acquire_lock(
        file_path=data["file_path"],
        developer_id=data["developer_id"],
        developer_email=data.get("developer_email"),
        branch_name=data.get("branch_name"),
        reason=data.get("reason"),
        expires_minutes=int(data.get("expires_minutes", DEFAULT_EXPIRY)),
    )

    if success:
        return jsonify(result), 200
    else:
        if result.get("status") == "conflict":
            return jsonify(result), 409
        return jsonify(result), 500


@app.route("/api/locks/release", methods=["POST"])
def release():
    data = request.json
    if not data or "lock_token" not in data:
        return jsonify({"error": "Missing lock_token", "field": "lock_token"}), 400

    success, result = lock_manager.release_lock(data["lock_token"])

    if success:
        return jsonify(result), 200
    else:
        if result.get("status") == "not_found":
            return jsonify(result), 404
        return jsonify(result), 500


@app.route("/api/locks/status", methods=["GET"])
def status():
    file_path = request.args.get("file_path")
    if not file_path:
        return jsonify({"error": "Missing file_path", "field": "file_path"}), 400

    result = lock_manager.get_lock_status(file_path)
    return jsonify(result), 200


@app.route("/api/locks/active", methods=["GET"])
def active():
    locks = lock_manager.get_all_active_locks()
    return jsonify(locks), 200


@app.route("/api/locks/history", methods=["GET"])
def history():
    file_path = request.args.get("file_path")
    limit = int(request.args.get("limit", 50))
    locks = lock_manager.get_lock_history(file_path=file_path, limit=limit)
    return jsonify(locks), 200


@app.route("/api/locks/developer/<developer_id>", methods=["GET"])
def developer_locks(developer_id):
    locks = lock_manager.get_locks_by_developer(developer_id)
    return jsonify(locks), 200


@app.route("/api/locks/force-release", methods=["POST"])
def force_release():
    data = request.json
    if not data or "file_path" not in data or "admin_id" not in data:
        return (
            jsonify(
                {"error": "Missing required fields", "field": "file_path/admin_id"}
            ),
            400,
        )

    success, result = lock_manager.force_release_lock(
        data["file_path"], data["admin_id"]
    )

    if success:
        return jsonify(result), 200
    else:
        if result.get("status") == "not_found":
            return jsonify(result), 404
        return jsonify(result), 500


@app.route("/api/locks/cleanup", methods=["POST"])
def cleanup():
    count = lock_manager.cleanup_expired_locks()
    return jsonify({"status": "success", "cleaned_count": count}), 200


@app.route("/admin/lock-dashboard")
def dashboard():
    template_path = os.path.join(os.path.dirname(__file__), "lock_dashboard.html")
    with open(template_path, "r") as f:
        template = f.read()
    return render_template_string(template)


if __name__ == "__main__":
    port = int(os.environ.get("LOCK_SERVICE_PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
