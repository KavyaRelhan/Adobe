import React, { useState, useEffect, useCallback, useRef } from 'react';
import "../styles/Loader.css"

const Loader = () => (
    <div className="loader-container">
        <div className="spinner"></div>
        <span>Processing documents... This may take a moment.</span>
    </div>
);

export default Loader;