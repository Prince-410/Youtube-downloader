/* ========================================================================
   YouTube Downloader — Frontend Application Logic
   ======================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // --- Elements ---
    const htmlEl = document.documentElement;
    const themeToggleBtn = document.getElementById("theme-toggle");
    const urlInput = document.getElementById("url-input");
    const btnPaste = document.getElementById("btn-paste");
    const btnFetch = document.getElementById("btn-fetch");
    const statusBanner = document.getElementById("status-banner");

    const previewCard = document.getElementById("preview-card");
    const previewThumb = document.getElementById("preview-thumb");
    const previewDuration = document.getElementById("preview-duration");
    const previewBadge = document.getElementById("preview-badge");
    const previewTitle = document.getElementById("preview-title");
    const previewUploader = document.getElementById("preview-uploader");
    const previewDetails = document.getElementById("preview-details");

    const playlistCard = document.getElementById("playlist-card");
    const playlistList = document.getElementById("playlist-list");
    const btnSelectAll = document.getElementById("btn-select-all");
    const btnDeselectAll = document.getElementById("btn-deselect-all");

    const optionsCard = document.getElementById("options-card");
    const formatSelect = document.getElementById("format-select");
    const qualitySelect = document.getElementById("quality-select");
    const btnDownload = document.getElementById("btn-download");
    const downloadNote = document.getElementById("download-note");
    const toastContainer = document.getElementById("toast-container");

    // --- Application State ---
    let currentData = null;

    // --- 1. Theme Toggle ---
    const savedTheme = localStorage.getItem("yt_theme") || "dark";
    htmlEl.setAttribute("data-theme", savedTheme);

    themeToggleBtn.addEventListener("click", () => {
        const nextTheme = htmlEl.getAttribute("data-theme") === "dark" ? "light" : "dark";
        htmlEl.setAttribute("data-theme", nextTheme);
        localStorage.setItem("yt_theme", nextTheme);
    });

    // --- 2. Paste Button ---
    btnPaste.addEventListener("click", async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text) {
                urlInput.value = text.trim();
                showToast("URL pasted from clipboard", "info");
            }
        } catch (err) {
            showToast("Failed to read clipboard", "error");
        }
    });

    // --- 3. Fetch Info Handler ---
    btnFetch.addEventListener("click", fetchInfo);
    urlInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            fetchInfo();
        }
    });

    async function fetchInfo() {
        const url = urlInput.value.trim();
        if (!url) {
            showBanner("Please enter a valid YouTube URL.", "error");
            return;
        }

        setLoading(true);
        hideBanner();
        hideCards();

        try {
            const response = await fetch(`/api/info?url=${encodeURIComponent(url)}`);
            const json = await response.json();

            if (!response.ok || !json.success) {
                throw new Error(json.error || "Failed to fetch metadata.");
            }

            currentData = json.data;
            renderMetadata(currentData);
            showBanner("Metadata fetched successfully!", "success");
        } catch (err) {
            showBanner(err.message, "error");
            showToast(err.message, "error");
        } finally {
            setLoading(false);
        }
    }

    // --- 4. Render Metadata ---
    function renderMetadata(data) {
        // Thumbnail & Title
        previewThumb.src = data.thumbnail || "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'/>";
        previewDuration.textContent = formatDuration(data.duration);
        previewTitle.textContent = data.title;
        previewUploader.textContent = `Channel: ${data.uploader}`;

        if (data.is_playlist) {
            previewBadge.textContent = `PLAYLIST (${data.total_count} videos)`;
            previewBadge.classList.add("badge-playlist");
            previewDetails.textContent = `Total Duration: ${formatDuration(data.duration)}`;

            renderPlaylist(data.playlist_items);
            playlistCard.hidden = false;
            optionsCard.hidden = true;
        } else {
            previewBadge.textContent = "SINGLE VIDEO";
            previewBadge.classList.remove("badge-playlist");
            const approxSize = data.filesize_approx ? formatBytes(data.filesize_approx) : "Unknown";
            previewDetails.textContent = `Duration: ${formatDuration(data.duration)} | Est. Size: ${approxSize}`;

            playlistCard.hidden = true;
            populateQualityOptions();
            optionsCard.hidden = false;
        }

        previewCard.hidden = false;
    }

    // --- 5. Playlist Render & Selection ---
    function renderPlaylist(items) {
        playlistList.innerHTML = "";
        items.forEach((item) => {
            const itemEl = document.createElement("div");
            itemEl.className = "playlist-item";

            itemEl.innerHTML = `
                <input type="checkbox" id="pl-item-${item.index}" data-url="${item.url}" checked>
                <img class="playlist-item-thumb" src="${item.thumbnail || ''}" alt="" loading="lazy">
                <div class="playlist-item-info">
                    <div class="playlist-item-title">${item.index}. ${escapeHtml(item.title)}</div>
                    <div class="playlist-item-meta">${formatDuration(item.duration)}</div>
                </div>
            `;

            itemEl.addEventListener("click", (e) => {
                if (e.target.tagName !== "INPUT") {
                    const chk = itemEl.querySelector("input");
                    chk.checked = !chk.checked;
                }
            });

            playlistList.appendChild(itemEl);
        });
    }

    btnSelectAll?.addEventListener("click", () => {
        playlistList.querySelectorAll("input[type='checkbox']").forEach(chk => chk.checked = true);
    });

    btnDeselectAll?.addEventListener("click", () => {
        playlistList.querySelectorAll("input[type='checkbox']").forEach(chk => chk.checked = false);
    });

    // --- 6. Quality Dropdown Selection ---
    formatSelect.addEventListener("change", populateQualityOptions);

    function populateQualityOptions() {
        if (!currentData || currentData.is_playlist) return;

        qualitySelect.innerHTML = "";
        const isAudio = formatSelect.value === "audio";
        const formats = isAudio ? currentData.audio_formats : currentData.formats;

        if (!formats || formats.length === 0) {
            const opt = document.createElement("option");
            opt.value = "";
            opt.textContent = isAudio ? "Default Audio Stream" : "Default Video Stream";
            qualitySelect.appendChild(opt);
            return;
        }

        formats.forEach((fmt) => {
            const opt = document.createElement("option");
            opt.value = fmt.url;
            const sizeStr = fmt.filesize_str ? ` (${fmt.filesize_str})` : "";
            opt.textContent = `${fmt.quality} - ${fmt.ext.toUpperCase()}${sizeStr}`;
            qualitySelect.appendChild(opt);
        });

        downloadNote.hidden = false;
        downloadNote.textContent = isAudio
            ? "Note: Direct audio stream URL will be opened for download."
            : "Note: Direct video stream URL will be downloaded directly by your browser.";
    }

    // --- 7. Initiate Download ---
    btnDownload.addEventListener("click", () => {
        if (!currentData) return;

        const downloadUrl = qualitySelect.value;
        if (!downloadUrl) {
            showToast("No download stream URL available.", "error");
            return;
        }

        // Open direct stream URL or download anchor
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.download = sanitizeFilename(currentData.title);
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        showToast("Download started in your browser!", "success");
    });

    // --- Helpers ---
    function setLoading(isLoading) {
        btnFetch.disabled = isLoading;
        btnFetch.querySelector(".btn-text").hidden = isLoading;
        btnFetch.querySelector(".btn-loader").hidden = !isLoading;
    }

    function showBanner(msg, type) {
        statusBanner.textContent = msg;
        statusBanner.className = `status-banner status-${type}`;
        statusBanner.hidden = false;
    }

    function hideBanner() {
        statusBanner.hidden = true;
    }

    function hideCards() {
        previewCard.hidden = true;
        playlistCard.hidden = true;
        optionsCard.hidden = true;
    }

    function formatDuration(sec) {
        if (!sec || sec < 0) return "00:00";
        sec = Math.floor(sec);
        const hrs = Math.floor(sec / 3600);
        const mins = Math.floor((sec % 3600) / 60);
        const secs = sec % 60;
        if (hrs > 0) {
            return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    function formatBytes(bytes) {
        if (!bytes || bytes <= 0) return "0 B";
        const units = ["B", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${units[i]}`;
    }

    function escapeHtml(str) {
        return str.replace(/[&<>"']/g, (m) => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        })[m]);
    }

    function sanitizeFilename(name) {
        return name.replace(/[\\/*?:"<>|]/g, "").trim();
    }

    function showToast(msg, type = "info") {
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        toast.textContent = msg;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.classList.add("toast-exit");
            toast.addEventListener("animationend", () => toast.remove());
        }, 3500);
    }
});
