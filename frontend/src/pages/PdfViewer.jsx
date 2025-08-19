

import React, { useEffect, useRef } from 'react';
import { useAdobeSdk } from '../hooks/useAdobeSdk';
import { FaSearchPlus, FaSearchMinus, FaTimes } from 'react-icons/fa';
import "../styles/PdfViewer.css"

const PdfViewer = ({ fileUrl, fileName, onClose, adobeKey, onTextSelect }) => {
  const isSdkLoaded = useAdobeSdk();
  const viewerRef = useRef(null);
  const adobeViewer = useRef(null);

  useEffect(() => {
    if (isSdkLoaded && fileUrl && viewerRef.current) {
      if (!adobeKey || adobeKey === "YOUR_ADOBE_API_KEY_HERE") {
        viewerRef.current.innerHTML = `<div class="viewer-message">Adobe API Key is missing.</div>`;
        return;
      }

      viewerRef.current.innerHTML = "";

      const adobeDCView = new window.AdobeDC.View({
        clientId: adobeKey,
        divId: 'adobe-dc-view',
      });

      const previewFilePromise = adobeDCView.previewFile({
        content: { location: { url: fileUrl } },
        metaData: { fileName: fileName }
      }, 
      {
        embedMode: "SIZED_CONTAINER",
        showDefaultControls: true,
      });

      previewFilePromise.then(viewer => {
        adobeViewer.current = viewer; // ✅ keep reference
        console.log("[PdfViewer] previewFilePromise resolved", viewer);
      });

      console.log("[PdfViewer] Registering Adobe EVENT_LISTENER callback...");

      adobeDCView.registerCallback(
        window.AdobeDC.View.Enum.CallbackType.EVENT_LISTENER,
        function(event) {
          // Check for the specific text selection event
          if (event.type === "PREVIEW_SELECTION_END") {
            console.log("[PdfViewer] PREVIEW_SELECTION_END event fired.");
            
            // After the event, get the viewer instance to call its APIs
            previewFilePromise.then(adobeViewer => {
              adobeViewer.getAPIs().then(apis => {
                // Get the selected content
                apis.getSelectedContent().then(result => {
                  const selectedText = result.text;
                  console.log("[PdfViewer] Captured text:", selectedText);
                  if (selectedText) {
                    // Pass only the text up to the parent component
                    onTextSelect(selectedText);
                  }
                });
              });
            });
          }
        },
        { enablePDFAnalytics: true });
    }
  }, [isSdkLoaded, fileUrl, fileName, adobeKey, onTextSelect]);

  const handleZoomIn = () => adobeViewer.current?.zoomIn();
  const handleZoomOut = () => adobeViewer.current?.zoomOut();

  let viewerContent;
  if (!isSdkLoaded) {
    viewerContent = <div className="viewer-message">Loading PDF Viewer...</div>;
  } else {
    viewerContent = <div id="adobe-dc-view" ref={viewerRef} className="pdf-viewer-content"></div>;
  }

  return (
    <div className="pdf-viewer-overlay" onClick={onClose}>
      <div className="pdf-viewer-modal" onClick={(e) => e.stopPropagation()}>
        <div className="pdf-viewer-header">
          <h3 title={fileName}>{fileName}</h3>
          <div className="viewer-controls">
            <button onClick={handleZoomOut} className="control-button" title="Zoom Out"><FaSearchMinus /></button>
            <button onClick={handleZoomIn} className="control-button" title="Zoom In"><FaSearchPlus /></button>
          </div>
          <button onClick={onClose} className="close-button" title="Close"><FaTimes /></button>
        </div>
        {viewerContent}
      </div>
    </div>
  );
};

export default PdfViewer;
