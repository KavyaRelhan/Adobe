

// import React, { useEffect, useRef } from 'react';
// import { useAdobeSdk } from '../hooks/useAdobeSdk';
// import { FaSearchPlus, FaSearchMinus, FaTimes } from 'react-icons/fa';
// import "../styles/PdfViewer.css"

// const PdfViewer = ({ fileUrl, fileName, onClose, adobeKey, onTextSelect }) => {
//   const isSdkLoaded = useAdobeSdk();
//   const viewerRef = useRef(null);
//   const adobeViewer = useRef(null);

//   useEffect(() => {
//     if (isSdkLoaded && fileUrl && viewerRef.current) {
//       if (!adobeKey || adobeKey === "YOUR_ADOBE_API_KEY_HERE") {
//         viewerRef.current.innerHTML = `<div class="viewer-message">Adobe API Key is missing.</div>`;
//         return;
//       }

//       viewerRef.current.innerHTML = "";

//       const adobeDCView = new window.AdobeDC.View({
//         clientId: adobeKey,
//         divId: 'adobe-dc-view',
//       });

//       const previewFilePromise = adobeDCView.previewFile({
//         content: { location: { url: fileUrl } },
//         metaData: { fileName: fileName }
//       }, 
//       {
//         embedMode: "SIZED_CONTAINER",
//         showDefaultControls: true,
//       });

//       previewFilePromise.then(viewer => {
//         adobeViewer.current = viewer; // ✅ keep reference
//         console.log("[PdfViewer] previewFilePromise resolved", viewer);
//       });

//       // previewFilePromise.then(viewer => {
//       //   adobeViewer.current = viewer;
//       //   console.log("[PdfViewer] Adobe Viewer is ready. Registering event listeners.");
        
        
//       //   viewer.getAPIs().then(apis => {
//       //     if(apis && apis.eventManager){
//       //         apis.eventManager.addEventListener("TEXT_SELECT", (event) => {
//       //         console.log("[PdfViewer] Step 2: 'TEXT_SELECT' event fired by Adobe API.", event.data);
              
//       //         const { selectedText, quads } = event.data;
//       //         if (selectedText && quads && quads.length > 0) {
//       //           const viewerRect = viewerRef.current.getBoundingClientRect();
//       //           const firstQuad = quads[0];
//       //           // Calculate position relative to the viewport
//       //           const top = firstQuad[1] + viewerRect.top;
//       //           const left = (firstQuad[0] + firstQuad[2]) / 2 + viewerRect.left;
//       //           // Pass the complete selection object to the parent
//       //           console.log("[PdfViewer] Step 3: Calculated position and reporting to parent.", selectedText);
                
//       //           onTextSelect({ text: selectedText, top, left });
//       //         }
//       //       });
//       //     }else{
//       //       console.error("[PdfViewer] Could not find 'eventManager' on the Adobe API object. This might be due to a network issue or an incomplete SDK initialization.");
          
//       //     }
//       //   });
//       // });

//       console.log("[PdfViewer] Registering Adobe EVENT_LISTENER callback...");

//       adobeDCView.registerCallback(
//         window.AdobeDC.View.Enum.CallbackType.EVENT_LISTENER,
//         function(event) {
//           // Check for the specific text selection event
//           if (event.type === "PREVIEW_SELECTION_END") {
//             console.log("[PdfViewer] PREVIEW_SELECTION_END event fired.");
            
//             // After the event, get the viewer instance to call its APIs
//             previewFilePromise.then(adobeViewer => {
//               adobeViewer.getAPIs().then(apis => {
//                 // Get the selected content
//                 apis.getSelectedContent().then(result => {
//                   const selectedText = result.text;
//                   console.log("[PdfViewer] Captured text:", selectedText);
//                   if (selectedText) {
//                     // Pass only the text up to the parent component
//                     onTextSelect(selectedText);
//                   }
//                 });
//               });
//             });
//           }
//         },
//         { enablePDFAnalytics: true });
//     }
//   }, [isSdkLoaded, fileUrl, fileName, adobeKey, onTextSelect]);

//   const handleZoomIn = () => adobeViewer.current?.zoomIn();
//   const handleZoomOut = () => adobeViewer.current?.zoomOut();

//   let viewerContent;
//   if (!isSdkLoaded) {
//     viewerContent = <div className="viewer-message">Loading PDF Viewer...</div>;
//   } else {
//     viewerContent = <div id="adobe-dc-view" ref={viewerRef} className="pdf-viewer-content"></div>;
//   }

//   return (
//     <div className="pdf-viewer-overlay" onClick={onClose}>
//       <div className="pdf-viewer-modal" onClick={(e) => e.stopPropagation()}>
//         <div className="pdf-viewer-header">
//           <h3 title={fileName}>{fileName}</h3>
//           <div className="viewer-controls">
//             <button onClick={handleZoomOut} className="control-button" title="Zoom Out"><FaSearchMinus /></button>
//             <button onClick={handleZoomIn} className="control-button" title="Zoom In"><FaSearchPlus /></button>
//           </div>
//           <button onClick={onClose} className="close-button" title="Close"><FaTimes /></button>
//         </div>
//         {viewerContent}
//       </div>
//     </div>
//   );
// };

// export default PdfViewer;


import React, { useEffect, useRef } from 'react';
import { useAdobeSdk } from '../hooks/useAdobeSdk';
import { FaSearchPlus, FaSearchMinus, FaTimes } from 'react-icons/fa';
import "../styles/PdfViewer.css";

const PdfViewer = ({ fileUrl, fileName, onClose, adobeKey, onTextSelect }) => {
  const isSdkLoaded = useAdobeSdk();
  const adobeViewer = useRef(null);

  useEffect(() => {
    if (isSdkLoaded && fileUrl) {
      if (!adobeKey || adobeKey === "YOUR_ADOBE_API_KEY_HERE") {
        const container = document.getElementById("adobe-dc-view");
        if (container) {
          container.innerHTML = <div class="viewer-message">Adobe API Key is missing.</div>;
        }
        return;
      }

      const adobeDCView = new window.AdobeDC.View({
        clientId: adobeKey,
        divId: "adobe-dc-view",
      });

      const previewFilePromise = adobeDCView.previewFile(
        {
          content: { location: { url: fileUrl } },
          metaData: { fileName: fileName }
        },
        // {
        //   embedMode: "SIZED_CONTAINER",
        //   showDefaultControls: true,
        // }
      );

      previewFilePromise.then(viewer => {
        adobeViewer.current = viewer;
        console.log("[PdfViewer] Adobe Viewer ready");
      });

      // Listen for text selection or copy
      adobeDCView.registerCallback(
        window.AdobeDC.View.Enum.CallbackType.EVENT_LISTENER,
        function (event) {
          if (event.type === "TEXT_SELECT" || event.type === "TEXT_COPY") {
            console.log("[PdfViewer] Text selection event:", event);
            if (adobeViewer.current) {
              adobeViewer.current.getAPIs().then(apis => {
                apis.getSelectedContent().then(result => {
                  const selectedText = result.text;
                  if (selectedText) {
                    console.log("[PdfViewer] Captured text:", selectedText);
                    onTextSelect(selectedText);
                  }
                });
              });
            }
          }
        },
        { enablePDFAnalytics: true }
      );
    }
  }, [isSdkLoaded, fileUrl, fileName, adobeKey, onTextSelect]);

  const handleZoomIn = () => adobeViewer.current?.zoomIn();
  const handleZoomOut = () => adobeViewer.current?.zoomOut();

  return (
    <div className="pdf-viewer-overlay">
      <div className="pdf-viewer-modal">
        <div className="pdf-viewer-header">
          <h3 title={fileName}>{fileName}</h3>
          <div className="viewer-controls">
            <button onClick={handleZoomOut} className="control-button" title="Zoom Out">
              <FaSearchMinus />
            </button>
            <button onClick={handleZoomIn} className="control-button" title="Zoom In">
              <FaSearchPlus />
            </button>
          </div>
          <button onClick={onClose} className="close-button" title="Close">
            <FaTimes />
          </button>
        </div>
        {!isSdkLoaded ? (
          <div className="viewer-message">Loading PDF Viewer...</div>
        ) : (
          <div id="adobe-dc-view" className="pdf-viewer-content"></div>
        )}
      </div>
    </div>
  );
};

export default PdfViewer;