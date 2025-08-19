import React, { useState, useEffect, useCallback, useRef } from 'react';
import "../styles/FileList.css"
import { AiFillFilePdf, AiOutlineDelete } from "react-icons/ai"

// components/FileList.jsx

const FileList = ({ files, onAddMore, onDeleteFile, onViewPdf }) => ( // <-- Receive onDeleteFile prop
  <div className="card-section">
    <h3>Your Document Collection</h3>
    <div className="file-list-container">
      {files.map((fileName, index) => (
        <div key={index} className="file-list-item clickable" onClick={() => onViewPdf(fileName)}>
            <div className="file-info">
              <AiFillFilePdf className="pdf-icon" />                <p>{fileName}</p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDeleteFile(fileName);
              }}  
              className="delete-button"
              aria-label={`Delete ${fileName}`}
            >
              <AiOutlineDelete className="delete-icon" />
            </button>

        </div>
      ))}
    </div>
    <button onClick={onAddMore} className="button secondary-button">
      Upload More Files
    </button>
  </div>
);

export default FileList;