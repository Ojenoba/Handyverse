document.addEventListener('DOMContentLoaded', () => {
    // Reviews
    if (document.getElementById('reviewsGrid')) fetchReviews();

    // Index search
    const searchButton = document.getElementById('searchButton');
    if (searchButton) {
        searchButton.addEventListener('click', function () {
            const location = document.getElementById('locationInput').value;
            fetch(`/search?location=${encodeURIComponent(location)}`)
                .then(response => response.json())
                .then(data => {
                    const grid = document.getElementById('artisansGrid');
                    grid.innerHTML = data.length ?
                        data.map(a => `
                            <div class="artisan-profile">
                                <img src="${a.profile_pic || '/static/default.png'}" alt="Profile Picture" class="profile-pic">
                                <h3>${a.name}</h3>
                                <p><strong>Trade:</strong> ${a.skills}</p>
                                <p><strong>Location:</strong> ${a.location}</p>
                                <button onclick="checkLoginAndContact(${a.id})" class="contact-button">Contact</button>
                            </div>
                        `).join('') :
                        '<p>No artisans found in that location.</p>';
                })
                .catch(() => {});
        });
    }

    // Dashboard search
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', searchArtisans);
    }

    // Form validations
    const loginForm = document.getElementById('loginForm');
    if (loginForm) loginForm.addEventListener('submit', validateLogin);
    const userSignupForm = document.getElementById('userSignupForm');
    if (userSignupForm) userSignupForm.addEventListener('submit', validateUserSignup);
    const artisanSignupForm = document.getElementById('artisanSignupForm');
    if (artisanSignupForm) artisanSignupForm.addEventListener('submit', validateArtisanSignup);
});

// Fade-in effect for the whole page
window.addEventListener('DOMContentLoaded', () => {
  document.body.classList.add('loaded');
});

function fetchReviews() {
    fetch('/api/reviews')
        .then(response => response.json())
        .then(data => displayReviews(data));
}

function displayReviews(reviews) {
    const grid = document.getElementById('reviewsGrid');
    grid.innerHTML = '';
    reviews.forEach(review => {
        const card = document.createElement('div');
        card.className = 'review-card';
        card.innerHTML = `
            <h3>${review.customer}</h3>
            <p>"${review.comment}"</p>
            <p>Rating: ${'★'.repeat(review.rating)}</p>
        `;
        grid.appendChild(card);
    });
}

function searchArtisans(event) {
    event.preventDefault();
    const location = document.getElementById('searchLocation').value;
    fetch(`/search?location=${encodeURIComponent(location)}`)
        .then(response => response.json())
        .then(data => {
            const resultsDiv = document.getElementById('searchResults');
            resultsDiv.innerHTML = data.length ?
                data.map(a => `
                    <div class="artisan-profile">
                        <img src="${a.profile_pic || '/static/default.png'}" alt="Profile Picture" class="profile-pic">
                        <h3>${a.name}</h3>
                        <p><strong>Trade:</strong> ${a.skills}</p>
                        <p><strong>Location:</strong> ${a.location}</p>
                        <button onclick="checkLoginAndContact(${a.id})" class="contact-button">Contact</button>
                    </div>
                `).join('') :
                '<p>No artisans found in that location.</p>';
        });
}

async function checkLoginAndContact(artisanId) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
    try {
        const response = await fetch(`/check_login`, {
            method: 'GET',
            credentials: 'include',
            headers: { 'X-CSRFToken': csrfToken }
        });
        const data = await response.json();
        if (data.is_authenticated) {
            window.location.href = `/contact/${artisanId}`;
        } else {
            window.location.href = `/login`;
        }
    } catch {
        // do nothing on error
    }
}

// --- Validation and Form Submission Functions ---

function validateEmail(email) {
    const re = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
    return re.test(email);
}

function validatePhoneNumber(phone) {
    const re = /^\d{10,15}$/;
    return re.test(phone);
}

function validateUserSignup(event) {
    event.preventDefault();
    let valid = true;
    clearErrors(['name-error', 'email-error', 'password-error', 'phone-error', 'location-error']);

    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const phone = document.getElementById('phone_number').value.trim();
    const location = document.getElementById('location').value.trim();

    if (!name) { setError('name-error', 'Name is required'); valid = false; }
    if (!email) { setError('email-error', 'Email is required'); valid = false; }
    else if (!validateEmail(email)) { setError('email-error', 'Invalid email format'); valid = false; }
    if (!password) { setError('password-error', 'Password is required'); valid = false; }
    else if (password.length < 8) { setError('password-error', 'Password must be at least 8 characters'); valid = false; }
    if (!phone) { setError('phone-error', 'Phone number is required'); valid = false; }
    else if (!validatePhoneNumber(phone)) { setError('phone-error', 'Invalid phone number (10-15 digits)'); valid = false; }
    if (!location) { setError('location-error', 'Location is required'); valid = false; }

    if (valid) submitUserSignup(event);
    return valid;
}

function validateArtisanSignup(event) {
    event.preventDefault();
    let valid = true;
    clearErrors(['name-error', 'email-error', 'password-error', 'phone-error', 'trade-error', 'location-error']);

    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const phone = document.getElementById('phone_number').value.trim();
    const trade = document.getElementById('trade').value.trim();
    const location = document.getElementById('location').value.trim();

    if (!name) { setError('name-error', 'Name is required'); valid = false; }
    if (!email) { setError('email-error', 'Email is required'); valid = false; }
    else if (!validateEmail(email)) { setError('email-error', 'Invalid email format'); valid = false; }
    if (!password) { setError('password-error', 'Password is required'); valid = false; }
    else if (password.length < 8) { setError('password-error', 'Password must be at least 8 characters'); valid = false; }
    if (!phone) { setError('phone-error', 'Phone number is required'); valid = false; }
    else if (!validatePhoneNumber(phone)) { setError('phone-error', 'Invalid phone number (10-15 digits)'); valid = false; }
    if (!trade) { setError('trade-error', 'Trade is required'); valid = false; }
    if (!location) { setError('location-error', 'Location is required'); valid = false; }

    if (valid) submitArtisanSignup(event);
    return valid;
}

function validateLogin(event) {
    event.preventDefault();
    let valid = true;
    clearErrors(['email-error', 'password-error']);

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!email) { setError('email-error', 'Email is required'); valid = false; }
    else if (!validateEmail(email)) { setError('email-error', 'Invalid email format'); valid = false; }
    if (!password) { setError('password-error', 'Password is required'); valid = false; }

    if (valid) submitLogin(event);
    return valid;
}

function submitUserSignup(event) {
    event.preventDefault();
    const form = document.getElementById('userSignupForm');
    const data = {
        accountType: 'user',
        name: form.name.value,
        email: form.email.value,
        password: form.password.value,
        phone_number: form.phone_number.value,
        location: form.location.value
    };
    fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify(data)
    })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (body.success) {
                window.location.href = '/user_dashboard';
            } else {
                showSignupError(body.message || 'Registration failed.');
            }
        })
        .catch(() => {
            showSignupError('Server error. Please try again.');
        });
}

function submitArtisanSignup(event) {
    event.preventDefault();
    const form = document.getElementById('artisanSignupForm');
    const data = {
        accountType: 'artisan',
        name: form.name.value,
        email: form.email.value,
        password: form.password.value,
        phone_number: form.phone_number.value,
        trade: form.trade.value,
        location: form.location.value
    };
    fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify(data)
    })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (body.success) {
                window.location.href = '/artisan_dashboard';
            } else {
                showArtisanSignupError(body.message || 'Registration failed.');
            }
        })
        .catch(() => {
            showArtisanSignupError('Server error. Please try again.');
        });
}

function submitLogin(event) {
    event.preventDefault();
    const form = document.getElementById('loginForm');
    const data = {
        email: form.email.value,
        password: form.password.value
    };
    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify(data)
    })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (body.message === 'Login successful') {
                window.location.href = body.redirect_url || '/';
            } else {
                // Show error message in the UI
                showLoginError(body.message);
            }
        });
}

// Helper to show error message
function showLoginError(message) {
    let errorDiv = document.getElementById('login-error-message');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'login-error-message';
        errorDiv.className = 'flash-error';
        const form = document.getElementById('loginForm');
        form.parentNode.insertBefore(errorDiv, form);
    }
    errorDiv.innerHTML = message;
}

function showSignupError(message) {
    let errorDiv = document.getElementById('signup-error-message');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'signup-error-message';
        errorDiv.className = 'flash-error';
        const form = document.getElementById('userSignupForm');
        form.parentNode.insertBefore(errorDiv, form);
    }
    errorDiv.innerHTML = message;
}

function showArtisanSignupError(message) {
    let errorDiv = document.getElementById('signup-error-message');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'signup-error-message';
        errorDiv.className = 'flash-error';
        const form = document.getElementById('artisanSignupForm');
        form.parentNode.insertBefore(errorDiv, form);
    }
    errorDiv.innerHTML = message;
}

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

function clearErrors(errorIds) {
    errorIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = '';
    });
}

function setError(id, message) {
    const el = document.getElementById(id);
    if (el) el.textContent = message;
}

// Slide-down animation for reply forms
function showReplyForm(messageId) {
    const form = document.getElementById(`replyForm-${messageId}`);
    if (form) {
        form.classList.toggle('open');
        if (form.classList.contains('open')) {
            form.style.maxHeight = '200px';
            form.style.opacity = '1';
        } else {
            form.style.maxHeight = '0';
            form.style.opacity = '0';
        }
    }
}

