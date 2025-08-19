import React from 'react';
import "../styles/Header.css"


import logo from '../assets/logo.png';

const Header = () => (
  <header className="header">
    <img src={logo} alt="Logo" className="header-logo" style={{ width: '180px' }} />
    <div>
    <h1>Intelligent Document Analyzer</h1>
    {/* <p>Transform your documents into actionable insights. Upload a collection, define your query, and let AI do the heavy lifting.</p> */}
    </div>
    <div></div>
  </header>
);

export default Header;