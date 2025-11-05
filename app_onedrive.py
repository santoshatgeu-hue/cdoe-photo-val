import streamlit as st
import cv2
import numpy as np
import requests
import io
from msal import ConfidentialClientApplication

# -------------------------------
# CONFIG
# -------------------------------
CLIENT_ID = "47286522-628b-4ed2-a602-d8db4f52c057"
TENANT_ID = "1490b17d-5dc9-4cbf-aeba-a2e854f521b8"
CLIENT_SECRET = "lWK8Q~.8JEKVg2vTkuCSH.WPNYQalwSrOL-g5cGE"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]
UPLOAD_FOLDER_PATH = "/Documents/StudentPhotos"  # OneDrive path

HAAR_CASCADE = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

# -------------------------------
# GET ACCESS TOKEN (ADMIN)
# -------------------------------
def get_access_token():
    app = ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    token = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" in token:
        st.success("✅ Connected to OneDrive.")
        return token["access_token"]
    else:
        st.error(f"❌ Could not get token: {token.get('error_description')}")
        return None

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
st.title("📸 Student Photo Upload to OneDrive (Admin Upload)")
st.write("Uploads go directly into the shared OneDrive folder with student ID as filename.")

student_id = st.text_input("Enter Student ID")
uploaded_file = st.file_uploader("Upload Photo (JPEG/PNG)", type=["jpg", "jpeg", "png"])

if "access_token" not in st.session_state:
    st.session_state["access_token"] = get_access_token()

# -------------------------------
# PROCESS UPLOAD
# -------------------------------
if uploaded_file and student_id and st.session_state["access_token"]:
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
                st.error(f"❌ Upload failed: {res.text}")
        else:
            st.error("❌ Photo not acceptable. Ensure only one full face is visible.")
