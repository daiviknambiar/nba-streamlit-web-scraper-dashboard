import shlex
import subprocess
from pathlib import Path
import os
from dotenv import load_dotenv
import modal

load_dotenv()

streamlit_script_local_path = Path(__file__).parent / "st_app.py"
streamlit_script_remote_path = "/root/st_app.py"

image = (
    modal.Image.debian_slim(python_version="3.9")
    .run_commands("mkdir -p /root/.streamlit")  
    .uv_pip_install(
        "streamlit",
        "supabase",
        "pandas",
        "plotly",
        "python-dotenv",
        "matplotlib",
    )
    .env({"FORCE_REBUILD": "true"})
    .add_local_file(streamlit_script_local_path, streamlit_script_remote_path)
    .add_local_file(Path(".streamlit/config.toml"), "/root/.streamlit/config.toml")
)

app = modal.App(name="usage-dashboard", image=image)

if not streamlit_script_local_path.exists():
    raise RuntimeError("Hey your starter streamlit isnt working")

@app.function(secrets=[modal.Secret.from_name("nba-news-secret")])
@modal.concurrent(max_inputs=100)  
@modal.web_server(8000, startup_timeout=120)
def run():
    target = shlex.quote(streamlit_script_remote_path)
    cmd = (
        f"streamlit run {target} "
        f"--server.port 8000 "
        f"--server.address 0.0.0.0 "
        f"--server.enableCORS=false "
        f"--server.enableXsrfProtection=false "
        f"--server.headless=true"
    )

    env_vars = {}
    if os.getenv("SUPABASE_KEY"):
        env_vars["SUPABASE_KEY"] = os.getenv("SUPABASE_KEY")
    if os.getenv("SUPABASE_URL"):
        env_vars["SUPABASE_URL"] = os.getenv("SUPABASE_URL")
    env_vars.update(os.environ)

    subprocess.Popen(cmd, shell=True, env=env_vars)
