document.addEventListener('DOMContentLoaded', function() {
    // Add event listener for escape key
    document.addEventListener('keyup', function(event) {
        // Check if the pressed key is Escape (key code 27)
        if (event.key === 'Escape' || event.keyCode === 27) {
            // Prevent default behavior
            event.preventDefault();
            // Redirect to dashboard
            window.location.href = '/';
        }
    });
}); 