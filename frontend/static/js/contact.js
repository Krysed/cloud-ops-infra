document.addEventListener('DOMContentLoaded', function() {
  const contactForm = document.querySelector('.contact-form');
  
  if (contactForm) {
    contactForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const formData = new FormData(contactForm);
      const submitBtn = contactForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      
      submitBtn.innerHTML = 'Sending...';
      submitBtn.disabled = true;
      
      try {
        const response = await fetch('/api/contact', {
          method: 'POST',
          body: formData
        });
        
        if (response.ok) {
          const result = await response.json();
          showPopup('Message Sent!', result.message || 'Thank you for your message! We will get back to you soon.', 'success');
          contactForm.reset();
        } else {
          const error = await response.json();
          showPopup('Send Failed', error.detail || 'Unable to send message. Please try again.', 'error');
        }
      } catch (error) {
        showPopup('Error', 'Connection error. Please try again.', 'error');
      } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
      }
    });
  }
});

