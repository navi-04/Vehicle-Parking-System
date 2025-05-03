document.addEventListener('DOMContentLoaded', function() {
    // Flash messages auto-dismiss
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('invalid');
                    
                    // Remove existing error messages
                    const existingError = field.parentElement.querySelector('.error-message');
                    if (existingError) existingError.remove();
                    
                    // Add error message
                    const errorMsg = document.createElement('div');
                    errorMsg.className = 'error-message';
                    errorMsg.style.color = 'red';
                    errorMsg.style.fontSize = '0.8rem';
                    errorMsg.style.marginTop = '5px';
                    errorMsg.textContent = 'This field is required';
                    field.parentElement.appendChild(errorMsg);
                } else {
                    field.classList.remove('invalid');
                    const existingError = field.parentElement.querySelector('.error-message');
                    if (existingError) existingError.remove();
                }
            });
            
            if (isValid) {
                // Get form action and handle navigation
                const formAction = form.getAttribute('action');
                
                // Store form data in localStorage for demo purposes
                const formData = {};
                new FormData(form).forEach((value, key) => {
                    formData[key] = value;
                });
                localStorage.setItem('userFormData', JSON.stringify(formData));
                
                // Check if this is a registration or login form
                if (form.querySelector('button[type="submit"]').textContent.includes('Register') || 
                    window.location.pathname.includes('login.html')) {
                    // Simulate successful registration/login
                    localStorage.setItem('isLoggedIn', 'true');
                    
                    // Navigate to dashboard
                    window.location.href = 'dashboard.html';
                } else {
                    // For other forms, just navigate to the form action
                    window.location.href = formAction;
                }
            }
        });
    });
    
    // License plate validation - uppercase and formatting
    const licensePlateInputs = document.querySelectorAll('input[name="license_plate"]');
    licensePlateInputs.forEach(input => {
        input.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    });
    
    // Real-time parking status updates (if on admin page)
    const parkingGrid = document.getElementById('parking-grid');
    if (parkingGrid) {
        // Refresh parking slot status every 30 seconds
        setInterval(() => {
            fetch('/admin/slots_status')
                .then(response => response.json())
                .then(data => {
                    data.forEach(slot => {
                        const slotElement = document.getElementById(`slot-${slot.id}`);
                        if (slotElement) {
                            slotElement.className = `parking-slot slot-${slot.status}`;
                            slotElement.setAttribute('data-status', slot.status);
                        }
                    });
                })
                .catch(error => console.error('Error updating slots:', error));
        }, 30000);
    }
    
    // Check if the clock element exists (dashboard)
    const clockElement = document.getElementById('current-time');
    if (clockElement) {
        // Update clock every second
        setInterval(() => {
            const now = new Date();
            clockElement.textContent = now.toLocaleTimeString();
        }, 1000);
    }

    // Check if logged in on restricted pages
    const restrictedPages = ['dashboard.html', 'check_in.html', 'check_out.html', 'admin.html'];
    const currentPage = window.location.pathname.split('/').pop();
    
    if (restrictedPages.includes(currentPage) && localStorage.getItem('isLoggedIn') !== 'true') {
        // Redirect to login page if not logged in
        window.location.href = 'login.html';
    }
});

// Fee calculation preview for check-out
function calculateFeePreview() {
    const checkInTimeStr = document.getElementById('check-in-time').value;
    if (!checkInTimeStr) return;
    
    const checkInTime = new Date(checkInTimeStr);
    const now = new Date();
    
    // Calculate hours difference
    const diffHours = (now - checkInTime) / (1000 * 60 * 60);
    const roundedHours = Math.max(1, Math.round(diffHours));
    const fee = roundedHours * 2; // $2 per hour
    
    document.getElementById('fee-preview').textContent = `$${fee.toFixed(2)}`;
}

// Toggle password visibility
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    if (input.type === 'password') {
        input.type = 'text';
    } else {
        input.type = 'password';
    }
}
