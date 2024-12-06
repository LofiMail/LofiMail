
function speakMail() {
  const mailContent = document.querySelector('.mail-body').innerText; // Get the mail content
  console.log("Mail content to be spoken:", mailContent); // Debug log

  if (mailContent.trim() === "") {
    console.log("No mail content found!"); // Ensure we are not trying to speak empty content
    return;
  }

  const utterance = new SpeechSynthesisUtterance(mailContent); // Create a speech utterance
  utterance.lang = 'en-US'; // Set the language

  // Optionally adjust pitch, rate, or volume:
  utterance.pitch = 1; // Range: 0 to 2
  utterance.rate = 1; // Normal speaking rate
  utterance.volume = 1; // Volume level from 0 to 1

  // Log to confirm we're triggering the speech synthesis
  console.log("Speaking the content...");

  // Speak the text aloud
  window.speechSynthesis.speak(utterance);
}
