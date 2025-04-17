document.addEventListener('DOMContentLoaded', () => {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const captureBtn = document.getElementById('capture-btn');
    const statusMessage = document.getElementById('status-message');

    let stream = null;

    // Function to start webcam
    async function startWebcam() {
        if (stream) { // Stop existing stream first
            stream.getTracks().forEach(track => track.stop());
        }
        try {
            // Use facingMode: 'user' to prefer front camera
            const constraints = {
                video: {
                    width: { ideal: 640 }, // Request a reasonable size
                    height: { ideal: 480 },
                    facingMode: 'user'
                }
            };
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            video.srcObject = stream;
            video.play(); // Ensure video plays
            console.log("Webcam started successfully.");
            if (statusMessage) statusMessage.textContent = ''; // Clear previous messages
        } catch (err) {
            console.error('Error accessing webcam:', err);
            if (statusMessage) {
                statusMessage.textContent = 'Error accessing webcam. Please ensure permissions are granted.';
                statusMessage.className = 'status-error';
            }
            if (captureBtn) captureBtn.disabled = true; // Disable button if webcam fails
        }
    }

    // Function to capture a frame
    function captureFrame() {
        if (!video.srcObject || !video.videoWidth) {
             console.error("Video stream not ready or invalid dimensions.");
             return null; // Return null if video not ready
        }
        // Set canvas dimensions to match video stream dimensions
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        // Get context and draw image (mirrored horizontally like the video feed)
        const context = canvas.getContext('2d');
        context.translate(canvas.width, 0);
        context.scale(-1, 1);
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        // Return base64 encoded image
        return canvas.toDataURL('image/jpeg'); // Default quality
    }

    // --- Event Listener for Capture Button ---
    if (captureBtn) {
        captureBtn.addEventListener('click', async () => {
            setStatus('Processing...', 'info');
            captureBtn.disabled = true; // Disable button during processing

            const imageDataUrl = captureFrame();
            if (!imageDataUrl) {
                setStatus('Failed to capture image from webcam.', 'error');
                captureBtn.disabled = false;
                return;
            }

            // Determine if this is registration or marking based on URL or button data
            let url;
            let isRegistration = window.location.pathname.includes('/face/register');
            let isMarking = window.location.pathname.includes('/mark_attendance');
            let courseId = captureBtn.dataset.courseId; // Get course_id if marking

            if (isRegistration) {
                url = '/student/face/register'; // Use the student route
            } else if (isMarking && courseId) {
                url = `/student/course/${courseId}/mark_attendance`;
            } else {
                setStatus('Error: Unknown action or missing course ID.', 'error');
                captureBtn.disabled = false;
                return;
            }

            console.log(`Sending image to: ${url}`);

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        // Add CSRF token header if you're using Flask-WTF CSRF protection
                        // 'X-CSRFToken': '{{ csrf_token() }}' // Example - requires passing token
                    },
                    body: JSON.stringify({ image: imageDataUrl })
                });

                const result = await response.json();
                console.log("Server response:", result);

                if (result.success) {
                    setStatus(result.message, 'success');
                    // Redirect after a short delay on success
                    setTimeout(() => {
                        window.location.href = '/student/attendance'; // Redirect to main attendance page
                    }, 2000); // 2-second delay
                } else {
                    setStatus(result.message || 'An unknown error occurred.', 'error');
                    captureBtn.disabled = false; // Re-enable button on failure
                }

            } catch (error) {
                console.error('Error sending image data:', error);
                setStatus('Network error or server issue. Please try again.', 'error');
                captureBtn.disabled = false; // Re-enable button on network error
            }
        });
    }

    // --- Helper to set status message ---
    function setStatus(message, type = 'info') {
        if (statusMessage) {
            statusMessage.textContent = message;
            statusMessage.className = `status-${type}`; // Use CSS classes for styling
        } else {
            console.log(`Status (${type}): ${message}`);
        }
    }

    // --- Start webcam when the page loads ---
    startWebcam();

    // --- Cleanup: Stop webcam when navigating away ---
    // Note: This might not always fire reliably depending on browser/navigation type
    window.addEventListener('beforeunload', () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            console.log("Webcam stopped.");
        }
    });
});
