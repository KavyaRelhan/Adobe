import { useState, useEffect } from 'react';

export const useAdobeSdk = () => {
  const [isSdkLoaded, setIsSdkLoaded] = useState(false);

  useEffect(() => {
    // Check if the script is already on the page
    if (window.AdobeDC && window.AdobeDC.View) {
      setIsSdkLoaded(true);
      return;
    }

    // Add a listener for the ready event
    const handleSdkReady = () => {
      console.log("Adobe View SDK is ready.");
      setIsSdkLoaded(true);
      // Clean up the listener once it has fired
      document.removeEventListener('adobe_dc_view_sdk.ready', handleSdkReady);
    };
    document.addEventListener('adobe_dc_view_sdk.ready', handleSdkReady);

    // Create and append the script tag if it doesn't exist
    if (!document.querySelector('script[src="https://acrobatservices.adobe.com/view-sdk/viewer.js"]')) {
      const script = document.createElement('script');
      script.src = 'https://acrobatservices.adobe.com/view-sdk/viewer.js';
      script.async = true;
      script.onerror = () => console.error("Failed to load the Adobe View SDK script.");
      document.body.appendChild(script);
    }

    // Cleanup function to remove the event listener
    return () => {
      document.removeEventListener('adobe_dc_view_sdk.ready', handleSdkReady);
    };
  }, []); // The empty array ensures this effect runs only once

  return isSdkLoaded;
};