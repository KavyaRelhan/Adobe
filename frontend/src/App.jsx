import React from "react";
// import Collection from "./pages/Coll/ection";
// import PdfViewer from "./pages/PdfViewer";
import { Route, Routes } from 'react-router-dom'
import CreateCollection from "./pages/CreateCollection.jsx"

// import { pdfjs } from 'react-pdf';
// pdfjs.GlobalWorkerOptions.workerSrc = new URL(
//   'pdfjs-dist/build/pdf.worker.min.js',
//   import.meta.url,
// ).toString();

function App() {
  return (
    <>
      <Routes>
        <Route path='/' element={<CreateCollection/>}/>
        {/* <Route path='/relevant-info' element={<Collection/>}/> */}
        {/* <Route path="/pdf-viewer" element={<PdfViewer />} /> */}
      </Routes>
    </>
  )
}

export default App;
