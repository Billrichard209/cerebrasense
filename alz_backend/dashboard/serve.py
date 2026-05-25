import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import cgi

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.inference.pipeline import predict_scan, PredictScanOptions
from src.inference.dashboard_utils import load_dashboard_data, resolve_oasis2_prediction_csvs
from src.configs.runtime import get_app_settings

ROOT = Path(__file__).parent.parent
DASHBOARD_DIR = Path(__file__).parent


def find_predictions_csv() -> Path | None:
    resolved = resolve_oasis2_prediction_csvs(ROOT)
    if not resolved:
        return None
    return next(iter(resolved.values()))


def load_data():
    return load_dashboard_data(ROOT)


def _resolve_inference_checkpoint() -> Path:
    settings = get_app_settings()
    registry_path = settings.outputs_root / "model_registry" / "oasis2_current_baseline.json"
    if registry_path.exists():
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        checkpoint = Path(str(payload.get("checkpoint_path") or ""))
        if not checkpoint.is_absolute():
            checkpoint = (settings.project_root / checkpoint).resolve()
        if checkpoint.exists():
            return checkpoint
    onnx_path = ROOT / "best_model.onnx"
    if onnx_path.exists():
        return onnx_path
    return ROOT / "outputs/runs/oasis2/oasis2_bias_stability_v1/checkpoints/best_model.pt"


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"  [{self.command}] {self.path}")

    def send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path, content_type: str):
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/" or path == "/index.html":
            html_file = DASHBOARD_DIR / "index.html"
            if html_file.exists():
                self.send_file(html_file, "text/html; charset=utf-8")
            else:
                self.send_json({"error": "index.html not found"}, 404)

        elif path == "/logo.svg":
            logo_file = DASHBOARD_DIR / "logo.svg"
            if logo_file.exists():
                self.send_file(logo_file, "image/svg+xml")
            else:
                self.send_json({"error": "logo.svg not found"}, 404)

        elif path == "/api/data":
            data, err = load_data()
            if err:
                self.send_json({"error": err}, 500)
            else:
                self.send_json(data)

        elif path == "/api/health":
            self.send_json({"status": "ok", "csv_found": find_predictions_csv() is not None})

        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/predict":
            try:
                # Handle multipart upload
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']}
                )

                if 'file' not in form:
                    self.send_json({"error": "No file uploaded"}, 400)
                    return

                file_item = form['file']
                if not file_item.filename:
                    self.send_json({"error": "No filename"}, 400)
                    return

                # Save temp file
                temp_dir = ROOT / "outputs" / "tmp" / "uploads"
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_path = temp_dir / file_item.filename
                temp_path.write_bytes(file_item.file.read())

                checkpoint = _resolve_inference_checkpoint()

                if not checkpoint.exists():
                    self.send_json({"error": "No model found. Export ONNX first."}, 500)
                    return

                # Extract multimodal clinical data
                age = form.getfirst('age')
                sex = form.getfirst('sex')
                mmse = form.getfirst('mmse')

                print(f"  [Predict] Running inference for {file_item.filename} using {checkpoint.name}...")
                print(f"            Multimodal: Age={age}, Sex={sex}, MMSE={mmse}")
                
                result = predict_scan(
                    scan_path=str(temp_path),
                    checkpoint_path=str(checkpoint),
                    options=PredictScanOptions(
                        output_name=f"upload_{file_item.filename}",
                        device="cpu",
                        age=float(age) if age else None,
                        sex=sex,
                        mmse=float(mmse) if mmse else None
                    ),
                    settings=get_app_settings()
                )

                # Generate Explainability using existing module
                if checkpoint.suffix == ".pt":
                    try:
                        from src.explainability.gradcam import explain_scan, ExplainScanConfig
                        expl = explain_scan(
                            ExplainScanConfig(
                                scan_path=temp_path,
                                checkpoint_path=checkpoint,
                                output_name=f"upload_{file_item.filename}_expl",
                                device="cpu"
                            ),
                            settings=get_app_settings()
                        )
                        import base64
                        if expl.overlay_paths:
                            with open(expl.overlay_paths[0], "rb") as f:
                                result["gradcam_base64"] = base64.b64encode(f.read()).decode("utf-8")
                    except Exception as ex:
                        print(f"  [Explain] Grad-CAM failed: {ex}")

                self.send_json(result)

            except Exception as e:
                import traceback
                print(traceback.format_exc())
                self.send_json({"error": str(e)}, 500)
        else:
            self.send_json({"error": "Not found"}, 404)


def main():
    port = int(os.environ.get("PORT", 8765))
    server = HTTPServer(("localhost", port), DashboardHandler)
    print(f"\nCerebraSense Dashboard running at: http://localhost:{port}")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
