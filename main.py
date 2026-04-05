from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import os
import shutil

app = FastAPI()

# ---------- CONFIG ----------

DATA_DIR  = "data"
IMAGE_DIR = "images"
ADMIN_KEY = "supersecretkey"  # change this

# ---------- CORS ----------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- SERVE IMAGES ----------

app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")

# ---------- HELPER FUNCTIONS ----------

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

    if key not in version_data:
        version_data[key] = 1
    else:
        version_data[key] += 1

    save_json(version_path, version_data)

def check_admin(key):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

# ---------- ROOT ----------

@app.get("/")
def root():
    return {"status": "AcuFind backend running"}

# ---------- VERSION API ----------

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

# ---------- MANUAL VERSION UPDATE ROUTE ----------

@app.post("/admin/update_version")
async def manual_update_version(request: Request):
    data = await request.json()
    key = data.get("key")
    if not key:
        return {"error": "Missing version key"}
    update_version(key)
    return {"status": f"{key} version updated"}

# ---------- IMAGE MANAGEMENT — POINTS ----------

# Upload point image (flat into images/ directory)
@app.post("/admin/upload_image")
async def upload_image(file: UploadFile = File(...), key: str = ""):
    check_admin(key)

    file_path = os.path.join(IMAGE_DIR, file.filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "status": "image uploaded",
        "filename": file.filename,
        "path": file.filename,
        "url": f"/images/{file.filename}"
    }

# Delete point image
@app.delete("/admin/delete_image/{filename}")
def delete_image(filename: str, key: str = ""):
    check_admin(key)
    file_path = os.path.join(IMAGE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    os.remove(file_path)
    return {"status": "image deleted", "filename": filename}

# Replace point image
@app.post("/admin/replace_image/{filename}")
async def replace_image(filename: str, file: UploadFile = File(...), key: str = ""):
    check_admin(key)
    file_path = os.path.join(IMAGE_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {
        "status": "image replaced",
        "filename": filename,
        "url": f"/images/{filename}"
    }

# List all point images
@app.get("/admin/list_images")
def list_images(key: str = ""):
    check_admin(key)
    files = os.listdir(IMAGE_DIR)
    return {"total": len(files), "images": files}

# ---------- IMAGE MANAGEMENT — COURSES ----------

# Upload course image (saved into images/courses/ subfolder)
# Returns path as "courses/<filename>" so frontend stores it as the image field.
# The frontend index.html should reference it as:  API + "/images/" + course.image
# e.g.  https://acufind.onrender.com/images/courses/bays.jpg
@app.post("/admin/upload_course_image")
async def upload_course_image(file: UploadFile = File(...), key: str = ""):
    check_admin(key)

    courses_dir = os.path.join(IMAGE_DIR, "courses")
    os.makedirs(courses_dir, exist_ok=True)

    file_path = os.path.join(courses_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    stored_path = f"courses/{file.filename}"

    return {
        "status": "course image uploaded",
        "filename": file.filename,
        "path": stored_path,           # ← stored in courses.json as image field
        "url": f"/images/{stored_path}"  # ← served by FastAPI StaticFiles
    }

# Replace course image (overwrites existing file in images/courses/)
@app.post("/admin/replace_course_image/{filename}")
async def replace_course_image(filename: str, file: UploadFile = File(...), key: str = ""):
    check_admin(key)

    courses_dir = os.path.join(IMAGE_DIR, "courses")
    os.makedirs(courses_dir, exist_ok=True)
    file_path = os.path.join(courses_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    stored_path = f"courses/{filename}"

    return {
        "status": "course image replaced",
        "filename": filename,
        "path": stored_path,
        "url": f"/images/{stored_path}"
    }

# Delete course image
@app.delete("/admin/delete_course_image/{filename}")
def delete_course_image(filename: str, key: str = ""):
    check_admin(key)
    file_path = os.path.join(IMAGE_DIR, "courses", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Course image not found")
    os.remove(file_path)
    return {"status": "course image deleted", "filename": filename}

# List all course images
@app.get("/admin/list_course_images")
def list_course_images(key: str = ""):
    check_admin(key)
    courses_dir = os.path.join(IMAGE_DIR, "courses")
    os.makedirs(courses_dir, exist_ok=True)
    files = os.listdir(courses_dir)
    return {"total": len(files), "images": files}
