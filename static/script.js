document.getElementById("submitBtn").addEventListener("click", async function () {
    const jobDescription = document.getElementById("jobDescription").value;
    // const jobCategory = document.getElementById("jobCategory").value;
    const resumeFile = document.getElementById("resumeUpload").files[0];

    // Validate inputs
    if (!jobDescription || !resumeFile) {
        alert("Please provide both the job description and resume.");
        return;
    }

    // Show loading state
    const submitBtn = document.getElementById("submitBtn");
    submitBtn.disabled = true;
    submitBtn.textContent = "Analyzing...";

    // Create FormData to send data to the backend
    const formData = new FormData();
    formData.append("jobDescription", jobDescription);
    formData.append("resumeUpload", resumeFile);

    try {
        // Send the data to the backend using Fetch API
        const response = await fetch("/analyze", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (data.feedback) {
            // Display feedback
            const feedbackArea = document.getElementById("feedbackArea");
            feedbackArea.innerHTML = `<pre>${data.feedback}</pre>`;
        } else {
            alert("Error: " + data.error);
        }
    } catch (error) {
        console.error("Error:", error);
        alert("An error occurred while processing the resume.");
    } finally {
        // Reset button state
        submitBtn.disabled = false;
        submitBtn.textContent = "Analyze Resume";
    }
});