import React from "react";

const KeyInsights = ({ insights }) => {
  return (
    <div className="key-insights">
      <h2>Key Insights</h2>
      <ul>
        {insights.map((insight, idx) => (
          <li key={idx}>{insight}</li>
        ))}
      </ul>
    </div>
  );
};

export default KeyInsights;
