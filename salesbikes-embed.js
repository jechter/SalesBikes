(function() {
  var frame = document.getElementById('salesbikes-frame');
  if (!frame) return;

  // Forward parent hash to iframe
  if (location.hash) {
    frame.src = frame.src.split('#')[0] + location.hash;
  }

  // Listen for messages from iframe
  window.addEventListener('message', function(e) {
    if (!e.data) return;

    // Auto-resize iframe height
    if (e.data.salesbikesHeight && !frame._fs) {
      frame.style.height = e.data.salesbikesHeight + 'px';
    }

    // Fullscreen mode for lightbox
    if (e.data.salesbikesFullscreen !== undefined) {
      if (e.data.salesbikesFullscreen) {
        frame._fs = true;
        frame.style.position = 'fixed';
        frame.style.top = '0';
        frame.style.left = '0';
        frame.style.width = '100%';
        frame.style.height = '100vh';
        frame.style.zIndex = '99999';
      } else {
        frame._fs = false;
        frame.style.position = '';
        frame.style.top = '';
        frame.style.left = '';
        frame.style.zIndex = '';
      }
    }
  });
})();
