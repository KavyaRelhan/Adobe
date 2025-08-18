import React, { useState, useEffect, useCallback, useRef } from 'react';
import "../styles/Header.css"

const Header = () => (
  <header className="header">
    <h1>Intelligent Document Analyzer</h1>
    <p>Transform your documents into actionable insights. Upload a collection, define your query, and let AI do the heavy lifting.</p>
  </header>
);

export default Header;