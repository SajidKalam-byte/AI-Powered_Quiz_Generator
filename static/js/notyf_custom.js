// Initialize Notyf for global notifications
// This file sets up a global `notyf` instance for use across templates
window.notyf = new Notyf({
  duration: 1000,
  position: { x: 'right', y: 'top' },
  dismissible: true,
  ripple: true
});
