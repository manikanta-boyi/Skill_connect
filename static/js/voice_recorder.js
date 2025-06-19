// static/js/voice_recorder.js

document.addEventListener('DOMContentLoaded', function() {
    console.log("1. DOM Content Loaded. Initializing voice recorder script.");

    const startRecordingBtn = document.getElementById('startRecordingBtn');
    const stopRecordingBtn = document.getElementById('stopRecordingBtn');
    const playbackAudio = document.getElementById('playback');
    const recordingStatus = document.getElementById('recordingStatus');
    const voiceFileInput = document.querySelector('input[name="voice_recording"]');

    if (!startRecordingBtn || !stopRecordingBtn || !playbackAudio || !recordingStatus || !voiceFileInput) {
        console.error("ERROR: One or more voice recorder elements not found. Check HTML IDs/names.");
        if (!startRecordingBtn) console.error("Missing #startRecordingBtn");
        if (!stopRecordingBtn) console.error("Missing #stopRecordingBtn");
        if (!playbackAudio) console.error("Missing #playback");
        if (!recordingStatus) console.error("Missing #recordingStatus");
        if (!voiceFileInput) console.error("Missing input[name='voice_recording']");
        return;
    }

    console.log("2. All voice recorder elements found.");

    let mediaRecorder;
    let audioChunks = [];
    let streamGlobal;

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
        recordingStatus.textContent = "Voice recording not supported in this browser. Please use Chrome/Firefox/Edge.";
        startRecordingBtn.disabled = true;
        stopRecordingBtn.disabled = true;
        console.error("3. Browser does not support MediaRecorder API.");
        return;
    }
    console.log("3. Browser supports MediaRecorder API.");

    startRecordingBtn.onclick = async () => {
        console.log("4. Start Recording button clicked. Attempting to get microphone access...");
        audioChunks = [];
        voiceFileInput.value = '';
        playbackAudio.style.display = 'none';
        playbackAudio.src = '';

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamGlobal = stream;
            console.log("5. Microphone access granted. Stream obtained.");
            recordingStatus.textContent = "Getting ready to record...";

            // *** CRITICAL CHANGE HERE ***
            // Use 'audio/webm;codecs=opus' for broader browser compatibility.
            // This will require a corresponding change in your Python backend (routes.py).
            const options = { mimeType: 'audio/webm;codecs=opus' }; 
            
            // Optional: You can also try to detect browser support for mime types
            // const options = {};
            // if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
            //     options.mimeType = 'audio/webm;codecs=opus';
            // } else if (MediaRecorder.isTypeSupported('audio/wav')) {
            //     options.mimeType = 'audio/wav';
            // } else {
            //     console.error("No supported audio recording MIME type found!");
            //     alert("Your browser does not support a compatible audio recording format.");
            //     return; // Exit if no supported type
            // }

            mediaRecorder = new MediaRecorder(stream, options);
            console.log("6. MediaRecorder initialized with MIME type:", options.mimeType);

            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                    console.log("7. Data available event. Chunk size:", event.data.size);
                }
            };

            mediaRecorder.onstop = async () => {
                console.log("8. MediaRecorder stopped. Processing audio data...");
                
                if (audioChunks.length === 0) {
                    console.warn("No audio data recorded.");
                    recordingStatus.textContent = "No audio recorded. Please ensure your microphone is working and you speak during recording.";
                    // Stop stream tracks even if no data was recorded
                    if (streamGlobal) {
                        streamGlobal.getTracks().forEach(track => track.stop());
                        console.log("Microphone stream tracks stopped (on no data).");
                    }
                    return;
                }

                const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType }); // Use the actual mimeType used by MediaRecorder
                console.log("9. Audio Blob created:", audioBlob.type, "size:", audioBlob.size, "bytes.");
                
                const audioUrl = URL.createObjectURL(audioBlob);
                playbackAudio.src = audioUrl;
                playbackAudio.style.display = 'block';
                recordingStatus.textContent = "Recording stopped. Ready to submit.";

                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = () => {
                    voiceFileInput.value = reader.result;
                    console.log("10. Audio Blob converted to Base64. First 50 chars:", voiceFileInput.value.substring(0, 50));
                };
                reader.onerror = error => {
                    console.error("10. FileReader error during Base64 conversion:", error);
                    recordingStatus.textContent = "Error converting audio for upload.";
                };

                streamGlobal.getTracks().forEach(track => track.stop());
                console.log("11. Microphone stream tracks stopped.");
            };

            mediaRecorder.start();
            recordingStatus.textContent = "Recording... Click Stop to finish.";
            startRecordingBtn.disabled = true;
            stopRecordingBtn.disabled = false;
            console.log("12. MediaRecorder started.");

        } catch (err) {
            console.error('ERROR during microphone access or recording start:', err);
            recordingStatus.textContent = `Error: ${err.message || 'Could not access microphone.'} Please check permissions and console for details.`; // More dynamic error message
            startRecordingBtn.disabled = false;
            stopRecordingBtn.disabled = true;

            if (err.name === 'NotAllowedError') {
                alert("Microphone access denied. Please grant permission to record audio for this site.");
            } else if (err.name === 'NotFoundError') {
                alert("No microphone found. Please ensure a microphone is connected and working.");
            } else if (err.name === 'NotReadableError') {
                alert("Microphone is in use by another application. Please close other apps and try again.");
            } else if (err.name === 'AbortError') {
                alert("Recording process aborted. Please try again.");
            } else {
                 // The specific error you saw will likely appear here:
                alert(`An unexpected error occurred with the microphone: ${err.message}`);
            }

            if (streamGlobal) {
                streamGlobal.getTracks().forEach(track => track.stop());
            }
        }
    };

    stopRecordingBtn.onclick = () => {
        console.log("13. Stop Recording button clicked.");
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            startRecordingBtn.disabled = false;
            stopRecordingBtn.disabled = true;
            console.log("14. MediaRecorder stop command issued.");
        } else {
            console.warn("14. MediaRecorder is not active or already stopped.");
            recordingStatus.textContent = "Not currently recording.";
        }
    };
});