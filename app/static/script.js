const fileInput = document.getElementById("audioFile");
const selectedFileName = document.getElementById("selectedFileName");
const uploadButton = document.getElementById("uploadButton");

const startButton = document.getElementById("startButton");
const stopButton = document.getElementById("stopButton");
const clearButton = document.getElementById("clearButton");

const resultBox = document.getElementById("result");
const connectionStatus = document.getElementById("connectionStatus");
const recordingStatus = document.getElementById("recordingStatus");
const recordingDot = document.getElementById("recordingDot");

let mediaRecorder = null;
let microphoneStream = null;
let socket = null;


fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];

    selectedFileName.textContent = file
        ? file.name
        : "Choose an audio file";
});


uploadButton.addEventListener("click", transcribeAudio);
startButton.addEventListener("click", startLiveTranscription);
stopButton.addEventListener("click", stopLiveTranscription);
clearButton.addEventListener("click", clearTranscript);


async function transcribeAudio() {
    const file = fileInput.files[0];

    if (!file) {
        showResult("Please select an audio file first.");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    uploadButton.disabled = true;
    uploadButton.textContent = "Transcribing...";

    showResult("Uploading and transcribing audio...");

    try {
        const response = await fetch("/transcribe", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "The transcription request failed."
            );
        }

        showResult(data.text || JSON.stringify(data, null, 2));
    } catch (error) {
        showResult(`Error: ${error.message}`);
    } finally {
        uploadButton.disabled = false;
        uploadButton.textContent = "Transcribe file";
    }
}


async function startLiveTranscription() {
    if (!navigator.mediaDevices?.getUserMedia) {
        showResult(
            "Your browser does not support microphone recording."
        );
        return;
    }

    try {
        microphoneStream =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });

        connectWebSocket();

        mediaRecorder = createMediaRecorder(microphoneStream);

        mediaRecorder.addEventListener(
            "dataavailable",
            handleAudioChunk
        );

        mediaRecorder.addEventListener("stop", () => {
            stopMicrophoneTracks();
        });

        /*
         * A dataavailable event is requested approximately
         * every two seconds.
         */
        mediaRecorder.start(2000);

        startButton.disabled = true;
        stopButton.disabled = false;

        recordingStatus.textContent = "Listening...";
        recordingDot.classList.add("recording-dot-active");

        showResult("Listening for speech...");
    } catch (error) {
        showResult(
            `Unable to access microphone: ${error.message}`
        );

        resetLiveControls();
    }
}


function createMediaRecorder(stream) {
    const preferredTypes = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/ogg;codecs=opus"
    ];

    const supportedType = preferredTypes.find((type) =>
        MediaRecorder.isTypeSupported(type)
    );

    if (supportedType) {
        return new MediaRecorder(stream, {
            mimeType: supportedType
        });
    }

    return new MediaRecorder(stream);
}


function connectWebSocket() {
    const protocol =
        window.location.protocol === "https:" ? "wss" : "ws";

    const websocketUrl =
        `${protocol}://${window.location.host}/ws/transcribe`;

    socket = new WebSocket(websocketUrl);

    socket.addEventListener("open", () => {
        updateConnectionStatus(true);
    });

    socket.addEventListener("message", (event) => {
        handleServerMessage(event.data);
    });

    socket.addEventListener("error", () => {
        showResult("WebSocket connection error.");
        updateConnectionStatus(false);
    });

    socket.addEventListener("close", () => {
        updateConnectionStatus(false);
    });
     if (
        recordingStatus.textContent ===
        "Processing final transcript..."
    ) {
        recordingStatus.textContent =
            "Connection closed before transcript was returned.";
    }
}


async function handleAudioChunk(event) {
    if (
        event.data.size === 0 ||
        !socket ||
        socket.readyState !== WebSocket.OPEN
    ) {
        return;
    }

    const audioBuffer = await event.data.arrayBuffer();

    socket.send(audioBuffer);
}


function handleServerMessage(rawMessage) {
    console.log("WebSocket message:", rawMessage);

    try {
        const message = JSON.parse(rawMessage);

        if (message.status === "error" || message.error) {
            resultBox.textContent =
                `Error: ${message.error || "Unknown server error"}`;

            recordingStatus.textContent = "Transcription failed";
            return;
        }

        if (message.status === "connected") {
            recordingStatus.textContent = "Listening...";
            return;
        }

        if (message.status === "buffering") {
            recordingStatus.textContent =
                `Listening — ${message.chunks} chunks received`;
            return;
        }

        if (
            message.status === "transcribing" ||
            message.status === "completed"
        ) {
            resultBox.textContent =
                message.text?.trim() ||
                "No speech was detected in the recording.";

            recordingStatus.textContent =
                message.final
                    ? "Transcription complete"
                    : "Listening and transcribing...";

            return;
        }
    } catch (error) {
        console.error("Invalid WebSocket message:", error);
        resultBox.textContent = rawMessage;
    }
}


function stopLiveTranscription() {
    if (
        !mediaRecorder ||
        mediaRecorder.state === "inactive"
    ) {
        closeLiveConnection();
        return;
    }

    mediaRecorder.addEventListener(
        "stop",
        () => {
            /*
             * Allow the final dataavailable event to send its
             * remaining audio before requesting the final result.
             */
            window.setTimeout(() => {
                closeLiveConnection();
            }, 300);
        },
        {
            once: true
        }
    );

    mediaRecorder.stop();

    stopButton.disabled = true;
    recordingStatus.textContent = "Finishing transcript...";
}

function stopMicrophoneTracks() {
    if (!microphoneStream) {
        return;
    }

    microphoneStream
        .getTracks()
        .forEach((track) => track.stop());

    microphoneStream = null;
}


function resetLiveControls() {
    stopMicrophoneTracks();

    startButton.disabled = false;
    stopButton.disabled = true;

    recordingStatus.textContent = "Microphone stopped";
    recordingDot.classList.remove("recording-dot-active");

    updateConnectionStatus(false);
}


function updateConnectionStatus(isConnected) {
    connectionStatus.textContent =
        isConnected ? "Connected" : "Offline";

    connectionStatus.classList.toggle(
        "status-online",
        isConnected
    );

    connectionStatus.classList.toggle(
        "status-offline",
        !isConnected
    );
}


function clearTranscript() {
    showResult("Your transcription will appear here.");
}


function showResult(message) {
    resultBox.textContent = message;
}

function closeLiveConnection() {
    if (
        socket &&
        socket.readyState === WebSocket.OPEN
    ) {
        socket.send(
            JSON.stringify({
                event: "stop"
            })
        );

        /*
         * Do not immediately call socket.close().
         * The server closes it after sending the final transcript.
         */
    }

    stopMicrophoneTracks();

    startButton.disabled = false;
    stopButton.disabled = true;

    recordingStatus.textContent = "Processing final transcript...";
    recordingDot.classList.remove("recording-dot-active");
}