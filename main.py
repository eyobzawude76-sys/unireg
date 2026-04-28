from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import os
import shutil
from typing import Optional
from fastapi.staticfiles import StaticFiles
from bson import ObjectId
import requests
from pydantic import BaseModel
app = FastAPI() 
app.mount("/static", StaticFiles(directory="static"), name="static") 

# 1. CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. MongoDB Connection
client = MongoClient("mongodb+srv://eyobzawude76_db_user:1357ab%40%23@cluster0.uo74prq.mongodb.net/?appName=Cluster0")
db = client["UniRegDB"]
collection = db["students"]

# 3. Directory for Images
UPLOAD_DIR = "static/uploads"
if not os.path.exists(UPLOAD_DIR): 
    os.makedirs(UPLOAD_DIR)

# --- 4. LOGIN SCHEMA ---
class LoginSchema(BaseModel):
    username: str
    password: str

# --- 5. SMS FUNCTION (HuluSMS System) ---
def send_hulu_sms(phone, message):
    # ⚠️ Kuni kallaattiin University-dhaan guutama
    api_token = "UNIVERSITY_SMS_TOKEN_HERE" 
    api_url = "https://portal.hulusms.com/api/v2/send"
    
    # Lakk. bilbilaa qulqulleessuu (+251 gara 0-tti)
    clean_phone = phone.replace("+251", "0")

    params = {
        "key": api_token,
        "num": clean_phone,
        "msg": message,
        "sender": "HuluSMS" 
    }

    try:
        # Yoo Token-ni hin galfamin ta'e terminal irratti qofa agarsiisa
        if api_token != "UNIVERSITY_SMS_TOKEN_HERE":
            res = requests.get(api_url, params=params)
            print(f"HuluSMS Status: {res.status_code}")
        else:
            print(f"\n--- SMS SYSTEM READY ---")
            print(f"To: {clean_phone}")
            print(f"Message: {message}")
            print(f"Status: Waiting for University Token...\n")
    except Exception as e:
        print(f"SMS Error: {e}")

# --- 6. ADMIN LOGIN ENDPOINT ---
@app.post("/admin/login")
async def admin_login(data: LoginSchema):
    if data.username == "admin" and data.password == "Rift@2026":
        return {
            "status": "success", 
            "message": "Baga nagaan dhufte Admin!",
            "token": "secure-key-123"
        }
    else:
        raise HTTPException(status_code=401, detail="Username ykn Password dogoggora!")

# --- 7. UPDATE STATUS & SEND SMS ---
@app.put("/update-student/{student_id}")
async def update_student(student_id: str, data: dict):
    try:
        student = collection.find_one({"_id": ObjectId(student_id)})
        if not student:
            raise HTTPException(status_code=404, detail="Barataan hin argamne")

        status = data.get("status")
        admin_msg = data.get("adminMessage", "")

        # Ergaa SMS qopheessuu
        if status == "Approved":
            msg = f"Baga gammadde {student['firstName']}! Galmeen kee Rift Valley University-f milkaa'eera."
        elif status == "Rejected":
            msg = f"Kabajamoo {student['firstName']}, Galmeen kee hin fudhatamne. Sababni: {admin_msg}"
        else:
            msg = f"Kabajamoo {student['firstName']}, Status galmee keetii gara {status}-tti jijjiirameera."

        # SMS Erguu (System waamuu)
        send_hulu_sms(student['phone'], msg)

        collection.update_one(
            {"_id": ObjectId(student_id)},
            {"$set": {"status": status, "adminMessage": admin_msg}}
        )
        return {"status": "success", "message": "Updated and SMS system triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 8. STUDENT REGISTRATION ---
@app.post("/register")
async def register_student(
    firstName: str = Form(...),
    lastName: str = Form(...),
    phone: str = Form(...),
    email: Optional[str] = Form(None),
    city: str = Form(...),
    faculty: str = Form(...),
    department: str = Form(...),
    studyMode: str = Form(...), 
    id_card: UploadFile = File(...),
    result: UploadFile = File(...),
    receipt: UploadFile = File(...)
):
    try:
        image_paths = {}
        files_to_save = [("id_card", id_card), ("result", result), ("receipt", receipt)]

        for label, file in files_to_save:
            file_ext = file.filename.split(".")[-1]
            file_name = f"{phone}_{label}.{file_ext}"
            file_location = os.path.join(UPLOAD_DIR, file_name)
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            image_paths[label] = file_location

        student_document = {
            "firstName": firstName,
            "lastName": lastName,
            "phone": phone,
            "email": email,
            "city": city,
            "faculty": faculty,
            "department": department,
            "studyMode": studyMode,
            "documents": image_paths,
            "status": "Pending",
            "registered_at": "2026-04-26"
        }
        inserted = collection.insert_one(student_document)
        return {"status": "success", "student_id": str(inserted.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 9. GET ALL STUDENTS ---
@app.get("/students")
async def get_students():
    try:
        students = []
        for student in collection.find():
            student["_id"] = str(student["_id"]) 
            students.append(student)
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port=int(os.environ.get("PORT",8000))
    uvicorn.run(app, host="0.0.0.0", port=port)