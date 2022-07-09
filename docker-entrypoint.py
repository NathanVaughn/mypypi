import os
import subprocess

if os.environ["MYPYPI_MODE"] == "server":
    subprocess.check_call(
        [
            "gunicorn",
            f"--workers={os.environ['WORKERS']}",
            "--bind=0.0.0.0:80",
            "app.main:flask_app",
        ]
    )

elif os.environ["MYPYPI_MODE"] == "worker":
    from app.main import downloader

    downloader.run()

else:
    raise ValueError(f"Unknown mode: {os.environ['MYPYPI_MODE']}")
