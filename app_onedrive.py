import streamlit as st
import cv2
import numpy as np
import requests
import io
from msal import PublicClientApplication

# -------------------------------
# CONFIG
# -------------------------------
CLIENT_ID = "47286522-628b-4ed2-a602-d8db4f52c057"
TENANT_ID = "1490b17d-5dc9-4cbf-aeba-a2e854f521b8"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["Files.ReadWrite", "User.Read"]
REDIRECT_URI = "http://localhost:8501"
UPLOAD_FOLDER_PATH = "/Documents/StudentPhotos"  # OneDrive folder

HAAR_CASCADE = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

# -------------------------------
# FACE VALIDATION
# -------------------------------
def detect_full_face(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(HAAR_CASCADE)
    faces = face_cascade.detectMultiScale(gray, 1.1, 7, minSize=(100, 100))
    return len(faces) == 1

# -------------------------------
# STREAMLIT UI
# -------------------------------
st.title("📸 Student Photo Upload (OneDrive)")
st.write("Upload your passport-size photo. Only one clear full face should be visible.")

student_id = st.text_input("Enter Student ID")
uploaded_file = st.file_uploader("Upload Photo (JPEG/PNG)", type=["jpg", "jpeg", "png"])

# -------------------------------
# LOGIN TO MICROSOFT (ONE DRIVE)
# -------------------------------
if "access_token" not in st.session_state:
    app = PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
    result = app.acquire_token_interactive(scopes=SCOPE)
    if "access_token" in result:
        st.session_state["access_token"] = result["access_token"]
        st.success("✅ Logged into OneDrive successfully.")
    else:
        st.error("Login failed. Try again.")

# -------------------------------
# PROCESS UPLOAD
# -------------------------------
if uploaded_file and student_id and "access_token" in st.session_state:
    bytes_data = uploaded_file.read()
    st.image(bytes_data, caption="Uploaded Image", use_container_width=True)

    with st.spinner("Analyzing photo..."):
        if detect_full_face(bytes_data):
            st.success("✅ Acceptable photo detected.")

            headers = {
                "Authorization": f"Bearer {st.session_state['access_token']}",
                "Content-Type": "image/jpeg"
            }
            file_name = f"{student_id}.jpg"
            upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{UPLOAD_FOLDER_PATH}/{file_name}:/content"

            res = requests.put(upload_url, headers=headers, data=bytes_data)
            if res.status_code in [200, 201]:
                st.success("✅ Uploaded successfully to OneDrive.")
            else:
                st.error(f"Upload failed: {res.text}")
        else:
            st.error("❌ Photo not acceptable. Ensure only one full face is visible.")
