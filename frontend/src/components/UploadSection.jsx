import React, { useState, useRef } from 'react';
import "../styles/UploadSection.css";

const UploadSection = ({ onFileUpload }) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setIsDragActive(true);
    else if (e.type === 'dragleave') setIsDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    if (e.dataTransfer.files?.length) {
      onFileUpload(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    if (e.target.files?.length) {
      onFileUpload(e.target.files);
    }
  };

  return (
    <div className="card-section">
      <h2>Step 1: Create Your Collection</h2>

      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        // ✅ This prevents double click
        onClick={(e) => {
          if (e.target.tagName !== 'INPUT') {
            fileInputRef.current.click();
          }
        }}
        className={`upload-zone ${isDragActive ? 'active' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf"
          className="hidden-input"
          onChange={handleChange}
        />
        <div className="upload-zone-content">
          <svg className="upload-icon" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true"><path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
          <span className="upload-text-main">Drag & Drop your PDFs here</span>
          <span className="upload-text-secondary">or click to upload</span>
        </div>
      </div>
    </div>
  );
};

export default UploadSection;
