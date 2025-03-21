import logging
import os
import sys
from pathlib import Path
from shad4fast import ShadHead
import multiprocessing

STATIC_DIR = Path(__file__).parent / "static"

# Add the project root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from fasthtml.common import fast_app, serve, Script, FileResponse
from src.services.api.api import setup_routes

def run_mock_server():
    from src.services.mock.api import app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

# Get log level from environment variable, default to INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
# Configure logger
logger = logging.getLogger("wilab_app")
logger.handlers.clear()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter(
        "%(levelname)s: \t %(asctime)s \t %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)
logger.addHandler(handler)
logger.setLevel(getattr(logging, LOG_LEVEL))

connection_settings_js = Script(src="/static/js/connection_settings.js", type="module")
hyperscript_cdn = Script(src="https://unpkg.com/hyperscript.org@0.9.12")
llm_selector_js = Script(src="/static/js/llm-selector.js", type="module")
chat_js = Script(src="/static/js/chat.js", type="module")
users_settings_js = Script(src="/static/js/users_settings.js", type="module")
messages_js = Script(src="/static/js/messages.js", type="module")
modal_js = Script(src="/static/js/modal.js", type="module")

app, rt = fast_app(
    pico=False,
    hdrs=(
        ShadHead(tw_cdn=True, theme_handle=True),
        hyperscript_cdn,
        connection_settings_js,
        llm_selector_js,
        chat_js,
        users_settings_js,
        messages_js,
        modal_js,
    )
)

setup_routes(app, rt)

@rt("/static/{filepath}")
def serve_static(filepath: str):
    return FileResponse(STATIC_DIR / filepath)

if __name__ == "__main__":
    use_mock = os.getenv("MOCK_API", "false").lower() == "true"
    if use_mock:
        logger.info("Starting mock API server in separate process...")
        mock_process = multiprocessing.Process(target=run_mock_server)
        mock_process.start()
        logger.info("Mock API server process started")

    HOT_RELOAD = os.getenv("HOT_RELOAD", "False").lower() == "true"
    try:
        serve(port=7860, reload=HOT_RELOAD)
    finally:
        if use_mock:
            logger.info("Shutting down mock API server...")
            mock_process.terminate()
            mock_process.join()
            logger.info("Mock API server shutdown complete")
