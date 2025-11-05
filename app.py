import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
from pydrive2.auth import ServiceAccountCredentials
from pydrive2.drive import GoogleDrive

# --- CONFIGURATION ---
FOLDER_ID = "1G9ockBnC4pIHPU1MS8FvmeCkLdFXvo-8"  # replace with your Drive folder ID
CREDENTIALS_FILE = "credentials.json"  # your Google service account key
PROTOTXT_PATH = "deploy.prototxt"
MODEL_PATH = "res10_300x300_ssd_iter_140000.caffemodel"
# ----------------------

st.set_page_config(page_title="Passport Photo Validator", page_icon="📸")
st.title("🎓 Passport Photo Validator & Uploader")

st.write(
    "Upload your passport-size photo. It will be accepted **only if exactly one full face** is detected."
)

# --- Load DNN Model ---
@st.cache_resource
def load_model():
    net = cv2.dnn.readNetFromCaffe(PROTOTXT_PATH, MODEL_PATH)
    return net

net = load_model()

# --- Face Detection Function ---
def detect_single_face_dnn(image):
    (h, w) = image.shape[:2]
    blob = cv2.dnn.blobFromImage(
        cv2.resize(image, (300, 300)),
        1.0,
        (300, 300),
        (104.0, 177.0, 123.0)
    )
    net.setInput(blob)
    detections = net.forward()

    face_count = 0
    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.6:  # adjust threshold if needed
            face_count += 1
    return face_count == 1

# --- Streamlit UI ---
student_id = st.text_input("Enter your Student ID (used for file name):")
uploaded_file = st.file_uploader("Upload Photo", type=["jpg", "jpeg", "png"])

if uploaded_file and student_id:
    image = np.array(Image.open(uploaded_file).convert("RGB"))
    if detect_single_face_dnn(image):
        st.success("✅ Acceptable photo — one clear face detected.")
        st.session_state["valid_file"] = uploaded_file
        st.session_state["student_id"] = student_id
    else:
        st.error("❌ Not acceptable — no face or multiple faces detected.")
        st.stop()

# --- Upload to Drive ---
if "valid_file" in st.session_state:
    if st.button("📤 Upload to University Drive Folder"):
        try:
            # Authenticate service account
            scope = ["https://www.googleapis.com/auth/drive.file"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
            drive = GoogleDrive(creds)

            file_name = f"{st.session_state['student_id']}.jpg"
            gfile = drive.CreateFile({
                "title": file_name,
                "parents": [{"id": FOLDER_ID}]
            })
            gfile.SetContentString(io.BytesIO(st.session_state["valid_file"].getvalue()).getvalue().decode("latin-1"))
            gfile.Upload()

            st.success(f"✅ Uploaded successfully as `{file_name}` to Drive.")
        except Exception as e:
            st.error(f"❌ Upload failed: {e}")
        finally:
            st.session_state.pop("valid_file", None)
