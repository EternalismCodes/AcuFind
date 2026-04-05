from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import os

app = FastAPI()


# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Serve images
app.mount("/images", StaticFiles(directory="images"), name="images")


DATA_DIR = "data"


# ---------- Helper Functions ----------

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_version():
    return load_json(os.path.join(DATA_DIR, "version.json"))


def update_version(key):
    version_path = os.path.join(DATA_DIR, "version.json")
    version_data = load_json(version_path)

    version_data[key] += 1

    save_json(version_path, version_data)


# ---------- ROOT ----------

@app.get("/")
def root():
    return {"status": "AcuFind backend running"}


# ---------- VERSION API (for cache checking) ----------

@app.get("/version")
def version():
    return get_version()


# ---------- DATA APIs ----------

@app.get("/points")
def get_points():
    return load_json(os.path.join(DATA_DIR, "points.json"))


@app.get("/courses")
def get_courses():
    return load_json(os.path.join(DATA_DIR, "courses.json"))


@app.get("/eav")
def get_eav():
    return load_json(os.path.join(DATA_DIR, "eav.json"))


# ---------- ADMIN UPDATE APIs ----------

@app.post("/admin/update_points")
async def update_points(request: Request):
    data = await request.json()
    save_json(os.path.join(DATA_DIR, "points.json"), data)

    update_version("points")

    return {"status": "points updated"}


@app.post("/admin/update_courses")
async def update_courses(request: Request):
    data = await request.json()
    save_json(os.path.join(DATA_DIR, "courses.json"), data)

    update_version("courses")

    return {"status": "courses updated"}


@app.post("/admin/update_eav")
async def update_eav(request: Request):
    data = await request.json()
    save_json(os.path.join(DATA_DIR, "eav.json"), data)

    update_version("eav")

    return {"status": "eav updated"}
