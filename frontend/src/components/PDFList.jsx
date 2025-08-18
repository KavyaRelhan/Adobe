import React from "react";
import { FaFilePdf } from "react-icons/fa";
import { useNavigate } from "react-router-dom";

const PDFList = ({ pdfs }) => {
  const navigate = useNavigate();

  const handleView = (url) => {
    navigate(`/pdf-viewer?url=${encodeURIComponent(url)}`);
  };

  return (
    <div className="pdf-list">
      {pdfs.map((pdf, idx) => (
        <div
          key={idx}
          className="pdf-item"
          style={{ background: pdf.color }}
          onClick={() => handleView(pdf.url)}
        >
          <FaFilePdf size={24} />
          <p className="pdf-name">{pdf.name}</p>
        </div>
      ))}
    </div>
  );
};

export default PDFList;
