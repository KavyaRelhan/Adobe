import React from 'react';
import { FaMagic } from 'react-icons/fa';
import '../styles/SelectionPopup.css';

const SelectionPopup = ({ top, left, onAnalyze }) => {
  // The style object uses the position passed down from the viewer
  const style = {
    position: 'absolute',
    top: `${top}px`,
    left: `${left}px`,
  };

  return (
    <div className="selection-popup" style={style}>
      <button onClick={onAnalyze} className="popup-button">
        <FaMagic />
        <span>Analyze Text</span>
      </button>
    </div>
  );
};

export default SelectionPopup;