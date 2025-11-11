const mantras = [
    `Chaque jour, je suis davantage encourageant, énergique, enthousiaste, valorisant, et j'attire un entourage à l'image de ces énergies, avec bonheur et fluidité.`,
    `Chaque jour, je saisis davantage les opportunités pour me construire un environnement énergisant, enrichissant qui me satisfait pleinement, et je prends les bonnes décisions avec entrain et spontanéité.`,
    `Chaque jour, je suis davantage acteur de ma vie et de mon futur, et je planifie mes actions, avec efficacité et clairvoyance, pour me construire la vie dont je rêve vraiment.`
];

const slot = document.getElementById("mantra-slot");

function showRandomMantra() {
    const randomIndex = Math.floor(Math.random() * mantras.length);
    slot.textContent = mantras[randomIndex];
}

// Show one immediately
showRandomMantra();

// Initial delay of 8 seconds
setTimeout(() => {
    showRandomMantra(); // Show first mantra after 8s

    // Then repeat every 30 seconds
    setInterval(showRandomMantra, 30000);
}, 8000);