function openMessage(id) {
    document.querySelector('.webmail-container').classList.add('blur-background');
    document.getElementById(id).style.display = 'block';
}

function fetchAndShowEmailContent(emailId) {
    // Make an AJAX request to fetch the email content
    fetch(`/get-email-content/${emailId}`)
        .then(response => response.json())
        .then(data => {
            // Insert the fetched email content into the modal
            const modal = document.getElementById('messageModal');
            modal.innerHTML = data.html;

            // Display the modal
            document.querySelector('.webmail-container').classList.add('blur-background');
            modal.style.display = 'block';
        })
        .catch(error => console.error('Error fetching email content:', error));
}

function closeEmail(id) {
    document.getElementById(id).style.display = "none";
    document.querySelector('.webmail-container').classList.remove("blur-background");
}



const letterColors = {
  A: "#5dade2", // Sky Blue
  B: "#58d68d", // Fresh Green
  C: "#af7ac5", // Soft Lavender
  D: "#f7dc6f", // Warm Yellow
  E: "#48c9b0", // Mint
  F: "#85c1e9", // Light Denim Blue
  G: "#76d7c4", // Aqua Mint
  H: "#5faee3", // Medium Blue
  I: "#bb8fce", // Soft Purple
  J: "#f8c471", // Warm Orange
  K: "#7dcea0", // Fresh Green
  L: "#d5dbdb", // Misty Grey
  M: "#bfc9ca", // Soft Grey
  N: "#ccd1d1", // Pale Grey
  O: "#a9cce3", // Airy Blue
  P: "#f5b041", // Light Orange
  Q: "#d6eaf8", // Very Light Blue
  R: "#5dade2", // Sky Blue
  S: "#58d68d", // Fresh Green
  T: "#76d7c4", // Aqua Mint
  U: "#a9cce3", // Airy Blue
  V: "#c39bd3", // Light Lavender
  W: "#e5e8e8", // Cloud Grey
  X: "#48c9b0", // Mint
  Y: "#f9e79f", // Soft Yellow
  Z: "#aeb6bf"  // Gentle Grey
};


function assignCircleColor(iconElement) {
  const initialElement = iconElement.querySelector(".main-initial");
  const letter = initialElement.textContent.trim().toUpperCase();
  const color = letterColors[letter] || "#007bff"; // Default color
  iconElement.style.backgroundColor = color;
}

// Apply to all conversation-icon elements
document.querySelectorAll(".conversation-icon").forEach(assignCircleColor);

function filterEmails() {
  const query = document.getElementById('searchBar').value.toLowerCase();
  const emailItems = document.querySelectorAll('.email-item');

  emailItems.forEach(item => {
    const sender = item.querySelector('.email-sender').textContent.toLowerCase();
    const title = item.querySelector('.email-title').textContent.toLowerCase();

    if (sender.includes(query) || title.includes(query)) {
      item.style.display = "block";
    } else {
      item.style.display = "none";
    }
  });
}

function snoozeEmail(event, snoozeButton) {

  event.stopPropagation(); // Prevents the event from reaching the parent
  const emailItem = snoozeButton.closest('.email-item');
  emailItem.style.opacity = '0.5';


  // alert("This email has been snoozed and will reappear later in 10 minutes");

  setTimeout(() => {
    emailItem.style.opacity = '1';
  }, 30000); // Snooze for 30 seconds as an example
}





document.querySelectorAll('.tile').forEach(tile => {
  tile.addEventListener('click', () => {
    const category = tile.getAttribute('data-category');
    const currentText = tile.textContent.trim();

    // Toggle text and mail visibility for the "All" tile
    if (category === 'all') {
      if (currentText === 'None') {
        tile.textContent = 'All';
        // Hide all emails
        document.querySelectorAll('.email-item').forEach(email => {
          email.style.display = 'none';
        });
	document.getElementById('mantra').style.display = 'block';

      } else {
        tile.textContent = 'None';
        // Show all emails
        document.querySelectorAll('.email-item').forEach(email => {
          email.style.display = 'flex';
        });
		document.getElementById('mantra').style.display = 'none';
      }
    } else {
	  document.getElementById('mantra').style.display = 'none';
      // Handle other category tiles
      document.querySelectorAll('.email-item').forEach(email => {
        if (email.classList.contains(category)) {
          // Toggle visibility for the specific category
          //email.style.display = email.style.display === 'none' ? 'flex' : 'none';
		email.style.display = 'flex';
      } else {
        email.style.display = 'none';
      }
      });
    }
  });
});



const syncBtn = document.getElementById('syncBtn');
let pollingIntervalId = null;

async function startSync() {
  const syncBtn = document.getElementById("syncBtn");

  syncBtn.disabled = true;
  syncBtn.textContent = "⏳";

  const resp = await fetch("/start_sync", { method: "POST" });
  const data = await resp.json();

  if (resp.status === 202 || data.status === "started") {
    startPollingStatus();
  } else {
    syncStatus.textContent = `Sync error: ${data.message || resp.statusText}`;
    syncBtn.disabled = false;
  }
}



async function startPollingStatus() {
  const syncBtn = document.getElementById("syncBtn");
  const syncStatus = document.getElementById("syncStatus");

  const interval = setInterval(async () => {
    const resp = await fetch("/sync_status");
    const data = await resp.json();

    if (!data.running) {
      clearInterval(interval);
      syncBtn.disabled = false;
      syncBtn.textContent = "🔄";   // ✅ restore text
      refreshMails(); // fetch updated mail list
    }
  }, 3000);
}

async function refreshMails() {
    fetch("/mails_fragment?v=" + Date.now(), { cache: "no-store" })
        .then(resp => resp.text())
        .then(html => {
          const emailList = document.querySelector(".email-list");
          if (emailList) {
            emailList.innerHTML = html;
          } else {
            console.error("Could not find .email-list element");
          }
        document.querySelectorAll(".conversation-icon").forEach(assignCircleColor);
        })
        .catch(err => console.error("Error refreshing mail list:", err));
  // fetch mail list fragment and inject it in the DOM
  //await  fetch("/mails_fragment", { cache: "no-store" });
  //const data = await r.json();
  // assume you have a container with id="mailsContainer"
  //const container = document.getElementById('mailsContainer');
  //if (container && data.html !== undefined) {
  //  container.innerHTML = data.html;
  //}
}

// Wire the button
syncBtn.addEventListener('click', (e) => {
  e.preventDefault();
  startSync();
});

// Optional: automatic sync every 10 minutes (900000 ms)
// Uncomment if you want auto-sync.
setInterval(() => { startSync(); }, 10 * 60 * 1000);



document.addEventListener("DOMContentLoaded", function() {
    const liloInput = document.getElementById("lilo-search");
    const liloBtn = document.getElementById("lilo-search-btn");

    function searchLilo() {
        const query = liloInput.value.trim();
        if (query !== "") {
            const url = `https://search.lilo.org/?theme=0&q=${encodeURIComponent(query)}&t=web`;
            window.open(url, '_blank');
        }
    }

    // Trigger on click
    liloBtn.addEventListener("click", searchLilo);

    // Trigger on Enter key
    liloInput.addEventListener("keypress", function(e) {
        if (e.key === "Enter") {
            searchLilo();
        }
    });
});


document.addEventListener("DOMContentLoaded", function() {
    const scholarInput = document.getElementById("scholar-search");
    const scholarBtn = document.getElementById("scholar-search-btn");

    function searchScholar() {
        const query = scholarInput.value.trim();
        if (query !== "") {
            const url = `https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q=${encodeURIComponent(query)}&btnG=`;
            window.open(url, '_blank');
        }
    }

    // Trigger on click
    scholarBtn.addEventListener("click", searchScholar);

    // Trigger on Enter key
    scholarInput.addEventListener("keypress", function(e) {
        if (e.key === "Enter") {
            searchScholar();
        }
    });
});



document.addEventListener("DOMContentLoaded", function() {
    const video = document.getElementById("background-video");
    const img = document.getElementById("background-image");
    let idleTimer = null;
    let isIdle = false;

    // Helper: smoothly toggle visibility
    function fadeVideo(show) {
        if (show) {
            video.style.opacity = "1";
            img.style.opacity = "0.6"; // slightly visible under video
            video.play().catch(() => {});
        } else {
            video.style.opacity = "0";
            img.style.opacity = "1";
            video.pause();
        }
    }

    // Detect user idle (no mouse or keyboard for N ms)
    function resetIdleTimer() {
        if (isIdle) {
            fadeVideo(true); // reactivate video
            isIdle = false;
        }
        clearTimeout(idleTimer);
        idleTimer = setTimeout(() => {
            isIdle = true;
            fadeVideo(false); // user idle, hide video
        }, 15000); // 15s idle threshold
    }

    // Watch for user activity
    ["mousemove", "keydown", "scroll", "touchstart"].forEach(evt => {
        window.addEventListener(evt, resetIdleTimer);
    });

    // Pause video when tab not visible
    document.addEventListener("visibilitychange", () => {
        if (document.hidden) {
            fadeVideo(false);
        } else if (!isIdle) {
            fadeVideo(true);
        }
    });

    // Start everything
    fadeVideo(true);
    resetIdleTimer();
});