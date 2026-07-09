async function transcribeAudio() {
    const fileInput = document.getElementById("audioFile");
    const resultBox = document.getElementById("result");

    if (!fileInput.files.length) {
        resultBox.textContent = "Please select an audio file first.";
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    resultBox.textContent = "Transcribing...";

    try {
        const response = await fetch("/transcribe", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            resultBox.textContent = "Error: " + JSON.stringify(data, null, 2);
            return;
        }

        resultBox.textContent = data.text || JSON.stringify(data, null, 2);

    } catch (error) {
        resultBox.textContent = "Request failed: " + error.message;
    }
}