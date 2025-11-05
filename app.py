import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io, os
from pydrive2.auth import ServiceAccountCredentials
from pydrive2.drive import GoogleDrive

# -------- CONFIGURATION --------
FOLDER_ID = "1G9ockBnC4pIHPU1MS8FvmeCkLdFXvo-8"  # Replace with actual folder ID
CREDENTIALS_FILE = "credentials.json"  # Service account key file
# --------------------------------

st.set_page_config(page_title="Passport Photo Upload", page_icon="📸")
st.title("🎓 Passport Photo Validator & Central Upload")

st.write("Upload your passport-size photograph. The system will accept it only if a full face is visible.")

student_id = st.text_input("Enter your Student ID (used as file name):")
uploaded_file = st.file_uploader("Upload passport photo", type=["jpg", "jpeg", "png"])

if uploaded_file and student_id:
    # Read and validate image
    image = np.array(Image.open(uploaded_file))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    if len(faces) == 1:
        st.success("✅ Acceptable photo — full face detected.")
        st.session_state["valid_file"] = uploaded_file
        st.session_state["student_id"] = student_id
    else:
        st.error("❌ Not acceptable — full face not detected or multiple faces.")
        st.stop()

# Upload to Google Drive
if "valid_file" in st.session_state:
    if st.button("Upload to University Drive Folder"):
        try:
            # Authenticate using service account
            scope = ["https://www.googleapis.com/auth/drive.file"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
            drive = GoogleDrive(creds)

            # Prepare file
            file_name = f"{st.session_state['student_id']}.jpg"
            gfile = drive.CreateFile({
                "title": file_name,
                "parents": [{"id": FOLDER_ID}]
            })
            gfile.SetContentString(io.BytesIO(st.session_state["valid_file"].getvalue()).getvalue().decode("latin-1"))
            gfile.Upload()
            st.success(f"✅ Uploaded successfully as {file_name} to shared folder.")
        except Exception as e:
            st.error(f"❌ Upload failed: {e}")
        finally:
            st.session_state.pop("valid_file", None)
