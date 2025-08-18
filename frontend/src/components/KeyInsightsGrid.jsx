import React from "react";

const KeyInsightsGrid = ({ insights }) => {
  return (
    <div className="insights-grid">
      {insights.map((text, idx) => {
        const sizeClass = text.length > 60 ? "large" : "small";
        return (
          <div key={idx} className={`insight-card ${sizeClass}`}>
            {text}
          </div>
        );
      })}
    </div>
  );
};

export default KeyInsightsGrid;
