// PWA Installation Handler for EduTrellis
(function() {
  'use strict';

  let deferredPrompt = null;
  const installButton = document.getElementById('pwa-install-btn');
  const iosInstallBanner = document.getElementById('ios-install-banner');
  const iosInstallClose = document.getElementById('ios-install-close');

  // Check if app is already installed
  function isAppInstalled() {
    return window.matchMedia('(display-mode: standalone)').matches || 
           window.navigator.standalone === true;
  }

  // Detect iOS
  function isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  }

  // Register Service Worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/serviceworker.js', {
        scope: '/'
      })
      .then((registration) => {
        console.log('✅ Service Worker registered successfully:', registration.scope);
        
        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          console.log('🔄 New Service Worker found, installing...');
          
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              console.log('🆕 New content available, please refresh!');
              // Optionally show a notification to user
            }
          });
        });
      })
      .catch((error) => {
        console.error('❌ Service Worker registration failed:', error);
      });
    });
  }

  // Handle beforeinstallprompt event
  window.addEventListener('beforeinstallprompt', (event) => {
    console.log('💡 beforeinstallprompt event fired');
    event.preventDefault();
    deferredPrompt = event;
    
    if (installButton && !isAppInstalled()) {
      installButton.style.display = 'flex';
      console.log('✅ Install button shown');
    }
  });

  // Handle install button click
  if (installButton) {
    installButton.addEventListener('click', async () => {
      if (!deferredPrompt) {
        console.log('❌ Install prompt not available');
        
        if (isIOS()) {
          alert('To install on iOS:\n\n1. Tap the Share button (⬆️)\n2. Select "Add to Home Screen"\n3. Tap "Add"');
        } else {
          alert('Installation not available:\n\n• Use Chrome, Edge, or Samsung Internet\n• Make sure you are on HTTPS\n• Try refreshing the page');
        }
        return;
      }
      
      installButton.style.display = 'none';
      deferredPrompt.prompt();
      
      const { outcome } = await deferredPrompt.userChoice;
      console.log(`👤 User response: ${outcome}`);
      
      if (outcome === 'accepted') {
        console.log('✅ User accepted the install prompt');
        
        if (typeof gtag !== 'undefined') {
          gtag('event', 'pwa_installed', {
            'event_category': 'PWA',
            'event_label': 'App Installed'
          });
        }
      } else {
        setTimeout(() => {
          if (!isAppInstalled()) {
            installButton.style.display = 'flex';
          }
        }, 3000);
      }
      
      deferredPrompt = null;
    });
  }

  // Handle app installed event
  window.addEventListener('appinstalled', (event) => {
    console.log('🎉 PWA installed successfully!');
    
    if (installButton) {
      installButton.style.display = 'none';
    }
    
    if (iosInstallBanner) {
      iosInstallBanner.classList.remove('show');
    }
    
    deferredPrompt = null;
    
    if (typeof gtag !== 'undefined') {
      gtag('event', 'pwa_installed', {
        'event_category': 'PWA',
        'event_label': 'App Installed Successfully'
      });
    }
    
    setTimeout(() => {
      alert('🎉 App installed successfully! You can now access EduTrellis from your home screen.');
    }, 500);
  });

  // Show iOS install banner
  function showIOSInstallBanner() {
    if (isIOS() && !isAppInstalled()) {
      const bannerClosedDate = localStorage.getItem('ios-install-banner-closed-date');
      const shouldShowAgain = bannerClosedDate ? 
        (Date.now() - parseInt(bannerClosedDate)) > (7 * 24 * 60 * 60 * 1000) : true;
      
      if (shouldShowAgain && iosInstallBanner) {
        setTimeout(() => {
          iosInstallBanner.classList.add('show');
          console.log('📱 iOS install banner shown');
        }, 2000);
      }
    }
  }

  // Close iOS banner
  if (iosInstallClose) {
    iosInstallClose.addEventListener('click', () => {
      if (iosInstallBanner) {
        iosInstallBanner.classList.remove('show');
        localStorage.setItem('ios-install-banner-closed', 'true');
        localStorage.setItem('ios-install-banner-closed-date', Date.now().toString());
        console.log('❌ iOS install banner closed');
      }
    });
  }

  // Initialize
  window.addEventListener('load', () => {
    if (isAppInstalled()) {
      if (installButton) {
        installButton.style.display = 'none';
      }
      console.log('✅ App is running in standalone mode');
    } else {
      console.log('🌐 App is running in browser mode');
      showIOSInstallBanner();
    }
  });

  // Handle online/offline events
  window.addEventListener('online', () => {
    console.log('🌐 Back online');
  });

  window.addEventListener('offline', () => {
    console.log('📵 You are offline');
  });

  // For testing on localhost
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    setTimeout(() => {
      if (!isAppInstalled() && installButton) {
        installButton.style.display = 'flex';
        console.log('🧪 Test mode: Install button force shown');
      }
    }, 2000);
  }

})();
