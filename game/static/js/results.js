// results.js
document.addEventListener('DOMContentLoaded', function() {
    // Get workout results from localStorage
    const results = JSON.parse(localStorage.getItem('workoutResults'));
    
    // Update stats
    document.getElementById('totalReps').textContent = results.reps || 0;
    document.getElementById('totalTime').textContent = results.time || 0;
    document.getElementById('powerOutput').textContent = results.power || 0;

    // Share button
    document.getElementById('shareButton').addEventListener('click', function() {
        const text = `I just completed ${results.reps} reps in ${results.time} seconds with a power output of ${results.power}W! 💪`;
        
        if (navigator.share) {
            navigator.share({
                title: 'My Workout Results',
                text: text
            });
        } else {
            // Fallback to copying to clipboard
            navigator.clipboard.writeText(text);
            alert('Results copied to clipboard!');
        }
    });

    // Try again button
    document.getElementById('tryAgainButton').addEventListener('click', function() {
        // No need to clear localStorage, just go back
        window.location.href = '/select-workout';
    });

    // Home button
    document.getElementById('homeButton').addEventListener('click', function() {
        window.location.href = '/';
    });
}); 