import React from "react";

const RelevantSectionCard = ({ title, description }) => {
  return (
    <div className="section-card">
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
};

export default RelevantSectionCard;
