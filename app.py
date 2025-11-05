import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io, os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# -----------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------
FOLDER_ID = "1G9ockBnC4pIHPU1MS8FvmeCkLdFXvo-8"  # 🔹 Replace with your shared folder ID
CREDENTIALS_FILE = "credentials.json"       # 🔹 Service account key JSON
PROTOTXT_PATH = "deploy.prototxt"
MODEL_PATH = "res10_300x300_ssd_iter_140000.caffemodel"
# -----------------------------------------------------

st.set_page_config(page_title="Passport Photo Validator", page_icon="📸")
st.title("🎓 Passport Photo Validator & Uploader")
st.write("Upload your passport-size photograph. Accepted only if one clear face is visible.")

# --- Ensure model files exist ---
def ensure_models():
    if not os.path.exists(PROTOTXT_PATH):
        import urllib.request
        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt",
            PROTOTXT_PATH
        )
    if not os.path.exists(MODEL_PATH):
        import urllib.request
        urllib.request.urlretrieve(
            "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel",
            MODEL_PATH
        )

ensure_models()

# --- Load DNN model ---
@st.cache_resource
def load_model():
    net = cv2.dnn.readNetFromCaffe(PROTOTXT_PATH, MODEL_PATH)
    return net

net = load_model()

# --- Face detection using DNN ---
def detect_single_face_dnn(image):
    (h, w) = image.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0,
                                 (300, 300), (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()

    face_count = 0
    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.6:
            face_count += 1
    return face_count == 1

# --- Upload to Google Drive ---
def upload_to_drive(student_id, uploaded_file, folder_id, credentials_file):
    try:
        creds = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=["https://www.googleapis.com/auth/drive.file"]
        )
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

        return uploaded.get("id"), uploaded.get("webViewLink")

    except Exception as e:
        raise e

# --- Streamlit UI ---
student_id = st.text_input("Enter your Student ID (used as filename):")
uploaded_file = st.file_uploader("Upload Passport Photo", type=["jpg", "jpeg", "png"])

if uploaded_file and student_id:
    image = np.array(Image.open(uploaded_file).convert("RGB"))
    if detect_single_face_dnn(image):
        st.success("✅ Acceptable photo — one clear face detected.")
        st.session_state["valid_file"] = uploaded_file
        st.session_state["student_id"] = student_id
    else:
        st.error("❌ Not acceptable — full face not detected or multiple faces found.")
        st.stop()

if "valid_file" in st.session_state:
    if st.button("📤 Upload to University Drive Folder"):
        try:
            file_id, link = upload_to_drive(
                st.session_state["student_id"],
                st.session_state["valid_file"],
                FOLDER_ID,
                CREDENTIALS_FILE
            )
            st.success(f"✅ Uploaded successfully as `{st.session_state['student_id']}.jpg`.")
            st.markdown(f"[🔗 View in Drive]({link})", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Upload failed: {e}")
        finally:
            st.session_state.pop("valid_file", None)
