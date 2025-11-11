// static/js/script.js

document.addEventListener("DOMContentLoaded", () => {
  const uploadBtn = document.getElementById("uploadBtn");
  const fileInput = document.getElementById("fileInput");
  const loader = document.getElementById("loader");
  const resultPanel = document.getElementById("resultPanel");
  const fraudList = document.getElementById("fraudList");
  const fraudCount = document.getElementById("fraudCount");
  const alertBox = document.getElementById("alert");
  const downloadLink = document.getElementById("downloadLink");

  function showAlert(msg, isError=true) {
    alertBox.classList.remove("hidden");
    alertBox.textContent = msg;
    alertBox.style.background = isError ? "#fff7f7" : "#f3fff7";
    alertBox.style.color = isError ? "#9a2a2a" : "#1a5f2b";
  }

  uploadBtn.addEventListener("click", async () => {
    alertBox.classList.add("hidden");
    resultPanel.classList.add("hidden");
    fraudList.innerHTML = "";
    downloadLink.classList.add("hidden");

    const file = fileInput.files[0];
    if (!file) {
      showAlert("Please select a CSV file before uploading.");
      return;
    }

    // Show loader
    loader.classList.remove("hidden");
    uploadBtn.disabled = true;

    const fd = new FormData();
    fd.append("file", file);

    try {
      const res = await fetch("/predict", {
        method: "POST",
        body: fd
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        loader.classList.add("hidden");
        uploadBtn.disabled = false;
        showAlert(data.error || "Server error. Please check the CSV or server logs.");
        return;
      }

      // Hide loader
      loader.classList.add("hidden");
      uploadBtn.disabled = false;

      // Show results
      fraudCount.textContent = data.fraud_count;
      if (data.fraud_count === 0) {
        fraudList.innerHTML = "<div style='padding:12px;color:#14532d;font-weight:700;'>No frauds detected in uploaded file.</div>";
      } else {
        fraudList.innerHTML = ""; // clear
        data.fraud_list.forEach(item => {
          const chip = document.createElement("div");
          chip.className = "fraud-chip";
          chip.innerHTML = `<div>S.N: ${item.serial_no}</div><div style="font-weight:600;font-size:13px">Prob: ${(item.probability*100).toFixed(2)}%</div>`;
          fraudList.appendChild(chip);
        });
      }

      resultPanel.classList.remove("hidden");

      // Show download link if provided
      if (data.result_csv) {
        downloadLink.href = data.result_csv;
        downloadLink.classList.remove("hidden");
        downloadLink.textContent = "Download Full Predictions CSV";
      }

    } catch (err) {
      loader.classList.add("hidden");
      uploadBtn.disabled = false;
      showAlert("Unexpected error: " + (err.message || err));
    }
  });
});
