document.addEventListener("DOMContentLoaded", () => {

    // =====================================================
    // TABS
    // =====================================================

    const textTab = document.getElementById("textTab");
    const audioTab = document.getElementById("audioTab");

    const textSection = document.getElementById("textSection");
    const audioSection = document.getElementById("audioSection");


    textTab.addEventListener("click", () => {

        textTab.classList.add("active");
        audioTab.classList.remove("active");

        textSection.classList.remove("hidden");
        audioSection.classList.add("hidden");

    });


    audioTab.addEventListener("click", () => {

        audioTab.classList.add("active");
        textTab.classList.remove("active");

        audioSection.classList.remove("hidden");
        textSection.classList.add("hidden");

    });


    // =====================================================
    // COMMON MESSAGE
    // =====================================================

    const message = document.getElementById("message");


    function showMessage(text, type = "") {

        message.textContent = text;

        message.className = type;

    }


    // =====================================================
    // TEXT ELEMENTS
    // =====================================================

    const textInput =
        document.getElementById("textInput");

    const textLanguage =
        document.getElementById("textLanguage");

    const translatedText =
        document.getElementById("translatedText");

    const translateTextBtn =
        document.getElementById("translateTextBtn");

    const playTextBtn =
        document.getElementById("playTextBtn");

    const clearTextBtn =
        document.getElementById("clearTextBtn");


    // =====================================================
    // TEXT TRANSLATION
    // =====================================================

    translateTextBtn.addEventListener(
        "click",
        async () => {

            const text =
                textInput.value.trim();

            const language =
                textLanguage.value;


            if (!text) {

                showMessage(
                    "Please enter some text.",
                    "error"
                );

                return;
            }


            translateTextBtn.disabled = true;

            showMessage(
                "Translating...",
                "loading"
            );


            try {

                const response =
                    await fetch(
                        "/api/translate_text",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                text: text,
                                language: language
                            })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok || !data.success) {

                    throw new Error(
                        data.error ||
                        "Translation failed."
                    );

                }


                translatedText.textContent =
                    data.translated_text;


                showMessage(
                    "Translation completed.",
                    "success"
                );

            }
            catch (error) {

                console.error(error);

                showMessage(
                    error.message,
                    "error"
                );

            }
            finally {

                translateTextBtn.disabled = false;

            }

        }
    );


    // =====================================================
    // TEXT TO SPEECH
    // =====================================================

    playTextBtn.addEventListener(
        "click",
        async () => {

            const text =
                translatedText.textContent.trim();


            if (
                !text ||
                text === "Your translation will appear here."
            ) {

                showMessage(
                    "Please translate some text first.",
                    "error"
                );

                return;
            }


            playTextBtn.disabled = true;

            showMessage(
                "Generating audio...",
                "loading"
            );


            try {

                const response =
                    await fetch(
                        "/api/play_text_audio",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                text: text
                            })
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok || !data.success) {

                    throw new Error(
                        data.error ||
                        "Could not generate audio."
                    );

                }


                const audio =
                    new Audio(data.audio_url);

                await audio.play();


                showMessage(
                    "Playing audio.",
                    "success"
                );

            }
            catch (error) {

                console.error(error);

                showMessage(
                    error.message,
                    "error"
                );

            }
            finally {

                playTextBtn.disabled = false;

            }

        }
    );


    // =====================================================
    // CLEAR TEXT
    // =====================================================

    clearTextBtn.addEventListener(
        "click",
        () => {

            textInput.value = "";

            translatedText.textContent =
                "Your translation will appear here.";

            showMessage("");

        }
    );


    // =====================================================
    // AUDIO ELEMENTS
    // =====================================================

    const recordBtn =
        document.getElementById("recordBtn");

    const stopBtn =
        document.getElementById("stopBtn");

    const playRecordedBtn =
        document.getElementById("playRecordedBtn");

    const translateAudioBtn =
        document.getElementById("translateAudioBtn");

    const clearAudioBtn =
        document.getElementById("clearAudioBtn");

    const audioLanguage =
        document.getElementById("audioLanguage");

    const recordingStatus =
        document.getElementById("recordingStatus");

    const recordedAudio =
        document.getElementById("recordedAudio");

    const translatedAudio =
        document.getElementById("translatedAudio");

    const audioOriginalText =
        document.getElementById("audioOriginalText");

    const audioTranslatedText =
        document.getElementById("audioTranslatedText");


    // =====================================================
    // RECORDING VARIABLES
    // =====================================================

    let mediaRecorder = null;

    let audioChunks = [];

    let recordedBlob = null;

    let recordedAudioURL = null;


    // =====================================================
    // RECORD AUDIO
    // =====================================================

    recordBtn.addEventListener(
        "click",
        async () => {

            try {

                const stream =
                    await navigator.mediaDevices.getUserMedia({
                        audio: true
                    });


                audioChunks = [];


                mediaRecorder =
                    new MediaRecorder(stream);


                mediaRecorder.addEventListener(
                    "dataavailable",
                    (event) => {

                        if (event.data.size > 0) {

                            audioChunks.push(
                                event.data
                            );

                        }

                    }
                );


                mediaRecorder.addEventListener(
                    "stop",
                    () => {

                        recordedBlob =
                            new Blob(
                                audioChunks,
                                {
                                    type: "audio/webm"
                                }
                            );


                        if (recordedAudioURL) {

                            URL.revokeObjectURL(
                                recordedAudioURL
                            );

                        }


                        recordedAudioURL =
                            URL.createObjectURL(
                                recordedBlob
                            );


                        recordedAudio.src =
                            recordedAudioURL;


                        recordedAudio.classList.remove(
                            "hidden"
                        );


                        playRecordedBtn.disabled =
                            false;


                        translateAudioBtn.disabled =
                            false;


                        recordingStatus.textContent =
                            "Recording completed.";


                        stream
                            .getTracks()
                            .forEach(
                                track =>
                                    track.stop()
                            );

                    }
                );


                mediaRecorder.start();


                recordBtn.disabled = true;

                stopBtn.disabled = false;

                playRecordedBtn.disabled = true;

                translateAudioBtn.disabled = true;


                recordingStatus.textContent =
                    "Recording...";


                showMessage(
                    "Recording started.",
                    "success"
                );

            }
            catch (error) {

                console.error(error);

                showMessage(
                    "Microphone access was denied or unavailable.",
                    "error"
                );

            }

        }
    );


    // =====================================================
    // STOP RECORDING
    // =====================================================

    stopBtn.addEventListener(
        "click",
        () => {

            if (
                mediaRecorder &&
                mediaRecorder.state !== "inactive"
            ) {

                mediaRecorder.stop();

            }


            recordBtn.disabled = false;

            stopBtn.disabled = true;

        }
    );


    // =====================================================
    // PLAY RECORDED AUDIO
    // =====================================================

    playRecordedBtn.addEventListener(
        "click",
        () => {

            if (!recordedAudioURL) {

                showMessage(
                    "No recording available.",
                    "error"
                );

                return;
            }


            recordedAudio.play();

        }
    );


    // =====================================================
    // TRANSLATE AUDIO
    // =====================================================

    translateAudioBtn.addEventListener(
        "click",
        async () => {

            if (!recordedBlob) {

                showMessage(
                    "Please record audio first.",
                    "error"
                );

                return;
            }


            const language =
                audioLanguage.value;


            const formData =
                new FormData();


            formData.append(
                "audio",
                recordedBlob,
                "recording.webm"
            );


            formData.append(
                "language",
                language
            );


            translateAudioBtn.disabled =
                true;


            showMessage(
                "Transcribing and translating audio...",
                "loading"
            );


            try {

                const response =
                    await fetch(
                        "/api/translate_audio",
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                const data =
                    await response.json();


                if (!response.ok || !data.success) {

                    throw new Error(
                        data.error ||
                        "Audio translation failed."
                    );

                }


                audioOriginalText.textContent =
                    data.transcribed_text;


                audioTranslatedText.textContent =
                    data.translated_text;


                translatedAudio.src =
                    data.audio_url;


                translatedAudio.classList.remove(
                    "hidden"
                );


                showMessage(
                    "Audio translation completed.",
                    "success"
                );


                translatedAudio.play()
                    .catch(() => {});

            }
            catch (error) {

                console.error(error);

                showMessage(
                    error.message,
                    "error"
                );

            }
            finally {

                translateAudioBtn.disabled =
                    false;

            }

        }
    );


    // =====================================================
    // CLEAR AUDIO
    // =====================================================

    clearAudioBtn.addEventListener(
        "click",
        () => {

            recordedBlob = null;


            if (recordedAudioURL) {

                URL.revokeObjectURL(
                    recordedAudioURL
                );

                recordedAudioURL = null;

            }


            recordedAudio.src = "";

            translatedAudio.src = "";


            recordedAudio.classList.add(
                "hidden"
            );


            translatedAudio.classList.add(
                "hidden"
            );


            playRecordedBtn.disabled =
                true;


            translateAudioBtn.disabled =
                true;


            audioOriginalText.textContent =
                "Your transcribed text will appear here.";


            audioTranslatedText.textContent =
                "Your translated text will appear here.";


            recordingStatus.textContent =
                "Ready to record.";


            showMessage("");

        }
    );

});