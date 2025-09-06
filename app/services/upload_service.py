import os
import shutil
from fastapi import UploadFile

UPLOAD_DIR = os.path.abspath("data")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_uploaded_files(transfers_file: UploadFile, microbiology_file: UploadFile):
    try:
        transfers_path = os.path.join(UPLOAD_DIR, "transfers.csv")
        micro_path = os.path.join(UPLOAD_DIR, "microbiology.csv")

        transfers_file.file.seek(0)
        with open(transfers_path, "wb") as f:
            shutil.copyfileobj(transfers_file.file, f)

        microbiology_file.file.seek(0)
        with open(micro_path, "wb") as f:
            shutil.copyfileobj(microbiology_file.file, f)

        return transfers_path, micro_path

    except Exception as e:
        raise RuntimeError(f"Failed to save uploaded files: {str(e)}")