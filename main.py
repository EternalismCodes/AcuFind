from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json

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


# ---------- Helper Functions ----------

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------- GET APIs ----------

@app.get("/")
def root():
    return {"status": "AcuFind backend running"}


@app.get("/points")
def get_points():
    return load_json("data/points.json")


@app.get("/courses")
def get_courses():
    return load_json("data/courses.json")


@app.get("/eav")
def get_eav():
    return load_json("data/eav.json")


# ---------- ADMIN UPDATE APIs ----------

@app.post("/admin/update_points")
async def update_points(request: Request):
    data = await request.json()
    save_json("data/points.json", data)
    return {"status": "points updated"}


@app.post("/admin/update_courses")
async def update_courses(request: Request):
    data = await request.json()
    save_json("data/courses.json", data)
    return {"status": "courses updated"}


@app.post("/admin/update_eav")
async def update_eav(request: Request):
    data = await request.json()
    save_json("data/eav.json", data)
    return {"status": "eav updated"}
