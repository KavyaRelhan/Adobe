// import React, { useRef,useState,useEffect } from "react";
// import PDFList from "../components/PDFList";
// import RelevantSectionCard from "../components/RelevantSectionCard";
// import Sidebar from "../components/Sidebar";
// import "../styles/collection.css";
// import KeyInsightsGrid from "../components/KeyInsightsGrid";
// import MainPodcastPlayer from "../components/MainPodcastPlayer";
// import Header from "../components/Header";
// import Navbar from "../components/Navbar";

// function Collection() {
//   const [pdfs] = useState([
//     { name: "Document 1", url: "https://acrobatservices.adobe.com/view-sdk-demo/PDFs/Bodea Brochure.pdf", color: "#f28b82" },
//     { name: "Document 2", url: "/pdfs/doc2.pdf", color: "#fbbc04" },
//     { name: "Document 3", url: "/pdfs/doc3.pdf", color: "#34a853" },
//   ]);

//   const sections = [
//     { title: "Relevant Section", description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit." },
//     { title: "Relevant Section", description: "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua." },
//     { title: "Relevant Section", description: "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris." },
//     { title: "Relevant Section", description: "Duis aute irure dolor in reprehenderit in voluptate velit esse." },
//     { title: "Relevant Section", description: "Excepteur sint occaecat cupidatat non proident." },
//     { title: "Podcast Player", description: "Podcast related description." },
//   ];

//   const insights = [
//     "Morero sam dolor sit amet",
//     "Consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
//     "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium.",
//     "Short note.",
//     "Longer insight that spans multiple lines for testing card sizing.",
//   ];

//   const keyInsightsRef = useRef(null);

//   const handleShowMore = () => {
//     keyInsightsRef.current?.scrollIntoView({ behavior: "smooth" });
//   };

//   const [selectedPdf, setSelectedPdf] = useState(null);

//   useEffect(() => {
//     if (selectedPdf && window.AdobeDC) {
//       const adobeDCView = new window.AdobeDC.View({
//         clientId: process.env.CLIENT_ID, // Replace with your API key
//         divId: "pdf-viewer",
//       });
//       adobeDCView.previewFile(
//         {
//           content: { location: { url: selectedPdf.url } },
//           metaData: { fileName: selectedPdf.name },
//         },
//         { embedMode: "SIZED_CONTAINER" }
//       );
//     }
//   }, [selectedPdf]);

//   const handlePdfClick = (pdf) => {
//     setSelectedPdf(pdf);
//   };

//   return (
//     <div className="app-container">
//       <div className="main-content">
//         <Header/>
//         <Navbar/>
//         <PDFList pdfs={pdfs} onPdfClick={handlePdfClick}/>
//         {selectedPdf && <div id="pdf-viewer" style={{ height: "600px" }}></div>}
        

//         <div className="sections-grid">
//           {sections.map((sec, idx) => (
//             <RelevantSectionCard key={idx} title={sec.title} description={sec.description} />
//           ))}
//         </div>

//         <div ref={keyInsightsRef} className="key-insights-section">
//           {<KeyInsightsGrid insights={insights}/>}
//         </div>
//         <div>
//           <MainPodcastPlayer
//             audioSrc="/sample-podcast.mp3"
//             title="Relevant Section"
//             image="/podcast-cover.jpg"
//           />
//         </div>
//       </div>

//       <Sidebar insights={insights} onShowMore={handleShowMore} />
//     </div>
//   );
// }

// export default Collection;
