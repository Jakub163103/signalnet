// static/js/cookie-consent.js

document.addEventListener('DOMContentLoaded', function () {
    const consentBanner = document.getElementById('cookie-consent-banner');
    const manageButtons = document.querySelectorAll('#accept-all, #manage-cookies');
    const cookieModal = document.getElementById('cookie-modal');
    const closeButton = document.querySelector('.close-button');
    const cookieForm = document.getElementById('cookie-form');
    const flashContainer = document.querySelector('.flash-container'); // Assuming .flash-container exists

    // Function to check if consent cookie exists
    function getCookie(name) {
        let value = "; " + document.cookie;
        let parts = value.split("; " + name + "=");
        if (parts.length === 2) return parts.pop().split(";").shift();
    }

    // Function to set a cookie
    function setCookie(name, value, days) {
        let expires = "";
        if (days) {
            let date = new Date();
            date.setTime(date.getTime() + (days*24*60*60*1000));
            expires = "; expires=" + date.toUTCString();
        }
        document.cookie = name + "=" + (value || "")  + expires + "; path=/; SameSite=Strict";
    }

    // Function to create and display a flash message
    function showFlash(message, category='info') {
        if (!flashContainer) return; // If flash container does not exist, do nothing

        const flash = document.createElement('div');
        flash.classList.add('flash', category); // e.g., 'flash success', 'flash info', 'flash warning', 'flash danger'
        flash.textContent = message;

        flashContainer.appendChild(flash);

        // Automatically remove the flash message after 5 seconds
        setTimeout(() => {
            flash.classList.add('fade-out'); // Assume CSS handles fade-out
            flash.addEventListener('transitionend', () => {
                flash.remove();
            });
        }, 5000);
    }

    // Show consent banner if no consent cookie is found
    if (!getCookie('cookie_consent')) {
        consentBanner.style.display = 'block';
    }

    // Manage button clicks
    manageButtons.forEach(button => {
        button.addEventListener('click', function () {
            consentBanner.style.display = 'none';
            if (this.id === 'accept-all') {
                setCookie('cookie_consent', 'all', 365);
                // Enable all cookies
                enableCookies();
                // Show flash message
                showFlash('Your cookie preferences have been saved.', 'success');
            } else {
                cookieModal.style.display = 'block';
            }
        });
    });

    // Close modal
    closeButton.addEventListener('click', function () {
        cookieModal.style.display = 'none';
    });

    // Handle form submission
    cookieForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const formData = new FormData(cookieForm);
        const consent = {};
        formData.forEach((value, key) => {
            consent[key] = value === 'on';
        });

        setCookie('cookie_consent', JSON.stringify(consent), 365);
        cookieModal.style.display = 'none';
        consentBanner.style.display = 'none';
        applyConsent(consent);
        // Show flash message
        showFlash('Your cookie preferences have been saved.', 'success');
    });

    // Apply consent preferences
    function applyConsent(consent) {
        if (consent.analytics) {
            enableAnalyticsCookies();
        }
        if (consent.functional) {
            enableFunctionalCookies();
        }
        if (consent.advertising) {
            enableAdvertisingCookies();
        }
    }

    // Enable all cookies (when "Accept All" is clicked)
    function enableCookies() {
        enableAnalyticsCookies();
        enableFunctionalCookies();
        enableAdvertisingCookies();
    }

    // Example functions to enable different types of cookies
    function enableAnalyticsCookies() {
        // Initialize Google Analytics
        (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
            (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
            m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
        })(window,document,'script','https://www.google-analytics.com/analytics.js','ga');

        ga('create', 'UA-XXXXX-Y', 'auto');
        ga('send', 'pageview');
    }

    function enableFunctionalCookies() {
        // Example: Load a chat widget or other functional services
        console.log('Functional cookies enabled');
    }

    function enableAdvertisingCookies() {
        // Example: Initialize advertising networks like Google Ads
        console.log('Advertising cookies enabled');
    }
});