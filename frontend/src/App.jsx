
import React, { useEffect, useState } from "react";
import { Route, Routes } from 'react-router-dom';
import CreateCollection from "./pages/CreateCollection.jsx";

function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "light");
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme((prev) => (prev === "light" ? "dark" : "light"));

  return (
    <div className="app-container">
      {/* <button
        onClick={toggleTheme}
        className="button primary-button"
        style={{ position: "fixed", top: 24, right: 24, zIndex: 2000 }}
        aria-label="Toggle theme"
      >
        {theme === "light" ? "🌙 Dark Mode" : "☀️ Light Mode"}
      </button> */}
      <Routes>
        <Route path='/' element={<CreateCollection/>}/>
        {/* <Route path='/relevant-info' element={<Collection/>}/> */}
        {/* <Route path="/pdf-viewer" element={<PdfViewer />} /> */}
      </Routes>
    </div>
  );
}

export default App;
