import React from 'react';
import '../styles/TextSelectionPopup.css';

const TextSelectionPopup = ({ text, position, onAnalyze }) => {
  if (!text || !position) return null;

  return (
    <div className="text-selection-popup" style={{ top: position.y, left: position.x }}>
      <p>{text}</p>
      <button onClick={() => onAnalyze(text)}>Analyze</button>
    </div>
  );
};

export default TextSelectionPopup;
