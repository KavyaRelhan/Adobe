// import React from "react";
// import KeyInsights from "./KeyInsights";
// import PodcastPlayer from "./PodcastGenerator.jsx";

// const Sidebar = ({ insights }) => {
//   // Take first 3 if more than 3 exist, otherwise all
//   const limitedInsights = insights.length > 3 ? insights.slice(0, 3) : insights;

//   return (
//     <aside className="sidebar">
//       <KeyInsights insights={limitedInsights} />
//       {insights.length > 3 && (
//         <button
//           className="show-more-btn"
//           onClick={() =>
//             document.getElementById("key-insights-section")?.scrollIntoView({
//               behavior: "smooth",
//             })
//           }
//         >
//           Show More
//         </button>
//       )}
//       <PodcastPlayer />
//     </aside>
//   );
// };

// export default Sidebar;
