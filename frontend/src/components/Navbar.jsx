import React from "react";

const Navbar = () => {
  const scrollToSection = (id) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <nav className="navbar">
      <button onClick={() => scrollToSection("relevant-sections")}>📄 Relevant Sections</button>
      <button onClick={() => scrollToSection("key-insights")}>💡 Key Insights</button>
      <button onClick={() => scrollToSection("podcast")}>🎧 Podcast</button>
    </nav>
  );
};

export default Navbar;
