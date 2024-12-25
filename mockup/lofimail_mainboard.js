function openMessage(id) {
    document.querySelector('.webmail-container').classList.add('blur-background');
    document.getElementById(id).style.display = 'block';
}


function closeEmail(id) {
    document.getElementById(id).style.display = "none";
    document.querySelector('.webmail-container').classList.remove("blur-background");
}



const letterColors = {
  A: "#3498db", // Light Blue
  B: "#2ecc71", // Green
  C: "#9b59b6", // Purple
  D: "#f1c40f", // Yellow
  E: "#16a085", // Teal
  F: "#34495e", // Dark Blue-Grey
  G: "#1abc9c", // Aqua
  H: "#2980b9", // Blue
  I: "#8e44ad", // Dark Purple
  J: "#f39c12", // Orange
  K: "#27ae60", // Dark Green
  L: "#bdc3c7", // Light Grey
  M: "#7f8c8d", // Grey
  N: "#95a5a6", // Soft Grey
  O: "#2c3e50", // Dark Slate
  P: "#e67e22", // Soft Orange
  Q: "#d0e1f9", // Very Light Blue
  R: "#3498db", // Light Blue
  S: "#2ecc71", // Green
  T: "#1abc9c", // Aqua
  U: "#34495e", // Dark Blue-Grey
  V: "#8e44ad", // Dark Purple
  W: "#bdc3c7", // Light Grey
  X: "#16a085", // Teal
  Y: "#f1c40f", // Yellow
  Z: "#7f8c8d"  // Grey
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
  }, 10000); // Snooze for 10 seconds as an example
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
