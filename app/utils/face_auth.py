# Example modification in face_auth.py
import face_recognition
import pickle
from app.models import User # Assuming User model is importable
from app import db # Assuming db is importable

def register_face(user_id, image_stream_or_path):
    try:
        # Load image (works with path or stream)
        image = face_recognition.load_image_file(image_stream_or_path)
        encodings = face_recognition.face_encodings(image)

        if encodings:
            # Get the first encoding found
            encoding = encodings[0]
            user = User.query.get(user_id)
            if user:
                user.face_encoding = pickle.dumps(encoding)
                db.session.commit() # Commit the change here
                print(f"Face encoding saved for user {user_id}")
                return encoding # Return the encoding object on success
            else:
                print(f"User {user_id} not found.")
                return None
        else:
            print("No face found in the image.")
            return None
    except Exception as e:
        print(f"Error during face registration: {e}")
        db.session.rollback() # Rollback on error
        return None

# verify_face should already work with a stream
def verify_face(user_id, image_stream):
    user = User.query.get(user_id)
    if not user or not user.face_encoding:
        print(f"User {user_id} not found or no face encoding stored.")
        return False

    try:
        known_encoding = pickle.loads(user.face_encoding)
        # Load the image from the stream
        unknown_image = face_recognition.load_image_file(image_stream)
        unknown_encodings = face_recognition.face_encodings(unknown_image)

        if not unknown_encodings:
            print("No face found in the verification image.")
            return False

        # Compare faces
        results = face_recognition.compare_faces([known_encoding], unknown_encodings[0])
        print(f"Face comparison result for user {user_id}: {results[0]}")
        return results[0] # Returns True if match, False otherwise
    except Exception as e:
        print(f"Error during face verification: {e}")
        return False