import streamlit as st
import cv2
import numpy as np
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# -----------------------------
# CONFIGURATION
# -----------------------------
CREDENTIALS_FILE = "credentials.json"  # path to your service account JSON
FOLDER_ID = "1G9ockBnC4pIHPU1MS8FvmeCkLdFXvo-8"  # e.g. '1aBcD...'
HAAR_CASCADE = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

# -----------------------------
# GOOGLE DRIVE SETUP & TEST
# -----------------------------
def test_drive_connection():
    """Test if the service account can access Drive."""
    try:
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=["https://www.googleapis.com/auth/drive.file"]
        )
        service = build("drive", "v3", credentials=creds)
        # Try listing files
        results = service.files().list(pageSize=1, fields="files(id, name)").execute()
        st.success("✅ Google Drive connection successful!")
        return service
    except Exception as e:
        st.error(f"❌ Google Drive connection failed: {e}")
        return None

service = test_drive_connection()

# -----------------------------
# FACE VALIDATION FUNCTION
# -----------------------------
def detect_full_face(image_bytes):
    """Return True if exactly one clear face detected."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(HAAR_CASCADE)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=7, minSize=(100, 100))

    if len(faces) == 1:
        (x, y, w, h) = faces[0]
        aspect_ratio = h / w
        if 0.9 <= aspect_ratio <= 1.3:  # approximate frontal face
            return True
    return False

# -----------------------------
# UPLOAD TO DRIVE FUNCTION
# -----------------------------
def upload_to_drive(student_id, uploaded_file, folder_id, creds):
    try:
        service = build("drive", "v3", credentials=creds)
        file_metadata = {
            "name": f"{student_id}.jpg",
            "parents": [folder_id]
        }
        media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype="image/jpeg")

        uploaded = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink"
        ).execute()
        return uploaded
    except Exception as e:
        st.error(f"❌ Upload failed: {e}")
        return None

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.title("📸 Student Photo Verification System")
st.write("Upload your **passport-size photograph**. The system will verify if the full face is visible.")

student_id = st.text_input("Enter your Student ID")
uploaded_file = st.file_uploader("Upload Photo (JPEG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file and student_id:
    bytes_data = uploaded_file.read()
    st.image(bytes_data, caption="Uploaded Image", use_container_width=True)

    with st.spinner("Analyzing image..."):
        if detect_full_face(bytes_data):
            st.success("✅ Acceptable photo: full face detected.")
            if service:
                creds = service_account.Credentials.from_service_account_file(
                    CREDENTIALS_FILE,
                    scopes=["https://www.googleapis.com/auth/drive.file"]
                )
                uploaded = upload_to_drive(student_id, uploaded_file, FOLDER_ID, creds)
                if uploaded:
                    link = uploaded.get("webViewLink")
                    st.success(f"✅ Uploaded successfully! [View in Drive]({link})")
        else:
            st.error("❌ Not acceptable. Please ensure only one clear full face is visible.")

else:
    st.info("Please enter your Student ID and upload a photo to begin.")
