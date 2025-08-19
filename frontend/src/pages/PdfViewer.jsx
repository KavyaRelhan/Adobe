// import React, { useEffect, useRef } from 'react';
// import { useAdobeSdk } from '../hooks/useAdobeSdk';
// import { FaSearchPlus, FaSearchMinus, FaTimes } from 'react-icons/fa';
// import "../styles/PdfViewer.css";

// const PdfViewer = ({ fileUrl, fileName, onClose, adobeKey, onTextSelect }) => {
//   const isSdkLoaded = useAdobeSdk();
//   const adobeViewer = useRef(null);

//   useEffect(() => {
//     if (isSdkLoaded && fileUrl) {
//       if (!adobeKey || adobeKey === "YOUR_ADOBE_API_KEY_HERE") {
//         const container = document.getElementById("adobe-dc-view");
//         if (container) {
//           container.innerHTML = <div class="viewer-message">Adobe API Key is missing.</div>;
//         }
//         return;
//       }

//       const adobeDCView = new window.AdobeDC.View({
//         clientId: adobeKey,
//         divId: "adobe-dc-view",
//       });

//       const previewFilePromise = adobeDCView.previewFile(
//         {
//           content: { location: { url: fileUrl } },
//           metaData: { fileName: fileName }
//         },
//         // {
//         //   embedMode: "SIZED_CONTAINER",
//         //   showDefaultControls: true,
//         // }
//       );

//       previewFilePromise.then(viewer => {
//         adobeViewer.current = viewer;
//         console.log("[PdfViewer] Adobe Viewer ready");
//       });

//       // Listen for text selection or copy
//       adobeDCView.registerCallback(
//         window.AdobeDC.View.Enum.CallbackType.EVENT_LISTENER,
//         function (event) {
//           if (event.type === "TEXT_SELECT" || event.type === "TEXT_COPY") {
//             console.log("[PdfViewer] Text selection event:", event);
//             if (adobeViewer.current) {
//               adobeViewer.current.getAPIs().then(apis => {
//                 apis.getSelectedContent().then(result => {
//                   const selectedText = result.text;
//                   if (selectedText) {
//                     console.log("[PdfViewer] Captured text:", selectedText);
//                     onTextSelect(selectedText);
//                   }
//                 });
//               });
//             }
//           }
//         },
//         { enablePDFAnalytics: true }
//       );
//     }
//   }, [isSdkLoaded, fileUrl, fileName, adobeKey, onTextSelect]);

//   const handleZoomIn = () => adobeViewer.current?.zoomIn();
//   const handleZoomOut = () => adobeViewer.current?.zoomOut();

//   return (
//     <div className="pdf-viewer-overlay">
//       <div className="pdf-viewer-modal">
//         <div className="pdf-viewer-header">
//           <h3 title={fileName}>{fileName}</h3>
//           <div className="viewer-controls">
//             <button onClick={handleZoomOut} className="control-button" title="Zoom Out">
//               <FaSearchMinus />
//             </button>
//             <button onClick={handleZoomIn} className="control-button" title="Zoom In">
//               <FaSearchPlus />
//             </button>
//           </div>
//           <button onClick={onClose} className="close-button" title="Close">
//             <FaTimes />
//           </button>
//         </div>
//         {!isSdkLoaded ? (
//           <div className="viewer-message">Loading PDF Viewer...</div>
//         ) : (
//           <div id="adobe-dc-view" className="pdf-viewer-content"></div>
//         )}
//       </div>
//     </div>
//   );
// };

// export default PdfViewer;

import React, { useState, useEffect } from 'react';
import { Document, Page } from 'react-pdf';
import { FaTimes, FaSearchPlus, FaSearchMinus, FaUndo } from 'react-icons/fa';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import '../styles/PdfViewer.css';
import Loader from '../components/Loader';

const PdfViewer = ({ fileUrl, fileName, onClose, onTextSelect}) => {
  const [numPages, setNumPages] = useState(null);
  
  function onDocumentLoadSuccess({ numPages: nextNumPages }) {
    setNumPages(nextNumPages);
  }
  const [scale, setScale] = useState(1.0);

  useEffect(() => {
  const handleMouseUp = () => {
    setTimeout(() => {  
      const selection = window.getSelection();
      const selectedText = selection.toString().trim();

      if (selectedText && selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        const popupPos = { x: rect.left + rect.width / 2, y: rect.top - 30 };

        if (onTextSelect) onTextSelect(selectedText, popupPos);
      } else {
        // ✅ no selection → close popup
        if (onTextSelect) onTextSelect("", null);
      }
    }, 0);
  };

  document.addEventListener("mouseup", handleMouseUp);
  return () => {
    document.removeEventListener("mouseup", handleMouseUp);
  };
}, [onTextSelect]);


  return (
    <div className="pdf-viewer-overlay"  onClick={onClose} >
      <div className="pdf-viewer-modal" onClick={(e) => e.stopPropagation()}  >
        <div className="pdf-viewer-header">
          <span className="pdf-file-name">{fileName}</span>

          <div className="pdf-controls">
            <button onClick={() => setScale(scale + 0.2)} title="Zoom In">
              <FaSearchPlus />
            </button>
            <button onClick={() => setScale(scale - 0.2)} disabled={scale <= 0.6} title="Zoom Out">
              <FaSearchMinus />
            </button>
            <button onClick={() => setScale(1.0)} title="Reset Zoom">
              <FaUndo />
            </button>
            <button onClick={onClose} className="close-button" title="Close">
              <FaTimes />
            </button>
          </div>
        </div>
        <div className="pdf-viewer-content">
          <Document
            file={fileUrl}
            onLoadSuccess={onDocumentLoadSuccess}
            loading={<Loader />}
            error={<div className="viewer-message">Failed to load PDF file.</div>}
          >
            {Array.from(new Array(numPages), (el, index) => (
              <Page
                key={`page_${index + 1}`}
                pageNumber={index + 1}
                renderAnnotationLayer={false}
                renderTextLayer={true}
                scale={scale}
              />
            ))}
          </Document>
        </div>
      </div>
    </div>
  );
};

export default PdfViewer;