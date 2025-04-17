function updateCountdown() {
    const eventDate = new Date(document.getElementById('countdown').dataset.date).getTime();
    const now = new Date().getTime();
    const distance = eventDate - now;

    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);

    document.getElementById("countdown").innerHTML = `
        ${days}d ${hours}h ${minutes}m ${seconds}s
    `;

    if (distance < 0) {
        clearInterval(countdownInterval);
        document.getElementById("countdown").innerHTML = "EVENT EXPIRED";
    }
}

// Update every second
const countdownInterval = setInterval(updateCountdown, 1000);