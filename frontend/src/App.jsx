
import React, { useEffect, useState } from "react";
import { Route, Routes } from 'react-router-dom';
import CreateCollection from "./pages/CreateCollection.jsx";

import { pdfjs } from 'react-pdf';

// pdfjs.GlobalWorkerOptions.workerSrc = new URL(
//   'pdfjs-dist/build/pdf.worker.min.js',
//   import.meta.url,
// ).toString();

pdfjs.GlobalWorkerOptions.workerSrc = `/pdf.worker.min.mjs`;

function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "light");
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme((prev) => (prev === "light" ? "dark" : "light"));

  return (
    <div className="app-container">
      <Routes>
        <Route path='/' element={<CreateCollection/>}/>
      </Routes>
    </div>
  );
}

export default App;
