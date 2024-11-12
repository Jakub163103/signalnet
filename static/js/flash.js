document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash');

    flashMessages.forEach(flash => {
        let timer;
        let remainingTime = 5000; // Total time for the flash message to be visible

        const startTimer = () => {
            timer = setTimeout(() => {
                flash.style.display = 'none';
            }, remainingTime);
        };

        const pauseTimer = () => {
            clearTimeout(timer);
            const computedStyle = window.getComputedStyle(flash, '::after');
            const width = parseFloat(computedStyle.width);
            const totalWidth = parseFloat(computedStyle.getPropertyValue('width', '100%'));
            remainingTime = (width / totalWidth) * 5000; // Calculate remaining time based on width
        };

        // Start the timer initially
        startTimer();

        // Pause the timer on hover
        flash.addEventListener('mouseenter', pauseTimer);

        // Resume the timer on mouse leave
        flash.addEventListener('mouseleave', startTimer);
    });
});
