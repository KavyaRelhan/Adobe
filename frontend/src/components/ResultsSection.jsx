import React from 'react';
import '../styles/ResultsSection.css';
import PodcastGenerator from "./PodcastGenerator";

const API_BASE_URL = 'http://127.0.0.1:8000';     // Add this here too

const ResultsSection = ({ results, sessionId, isScriptReady, isScriptLoading }) => (
    <section className="results-container">
        <header className="results-header">
            <h2>Analysis Results</h2>
        </header>

        {/* Relevant Sections */}
        <div className="relevant-section-wrapper">
            <h3>Most Relevant Sections</h3>
            <div className="relevant-sections-container">
                {results.relevant_sections.map((section, index) => {
                    // Build file URL dynamically using backend base and sessionId
                    const pdfUrl = `${API_BASE_URL}/uploads/${sessionId}/${section.document}`;

                    return (
                        <div
                            key={index}
                            className="section-card glass-card"
                            onClick={() => window.open(`${pdfUrl}#page=${section.page_number}`, "_blank")}
                            style={{ cursor: "pointer" }}
                        >
                            <div className="section-card-header">
                                <span>
                                    <p title={section.document}>{section.document}</p>
                                </span>
                                <span>Page {section.page_number}</span>
                            </div>
                            <p>{section.refined_text}</p>
                        </div>
                    );
                })}
            </div>
        </div>

        {/* Insights Section */}
        <div className="insights-grid">
            <div className="insights-card glass-card">
                <h3>Key Insights</h3>
                <div className="insights-sections">
                    <div className="insight-block">
                        <h4>💡 Key Takeaways</h4>
                        <ul>
                            {results.insights.key_insights.map((insight, i) => (
                                <li key={i}>{insight}</li>
                            ))}
                        </ul>
                    </div>
                    <div className="insight-block">
                        <h4>🤔 Did You Know?</h4>
                        <p>{results.insights.did_you_know}</p>
                    </div>
                    {results.insights.contradictions?.length > 0 && (
                        <div className="insight-block">
                            <h4>⚠️ Contradictions</h4>
                            <ul>
                                {results.insights.contradictions.map((c, i) => (
                                    <li key={i}>{c}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            </div>
        </div>

        {/* Podcast / audio */}
        <div className="podcast-section">
            <PodcastGenerator
                sessionId={sessionId}
                isScriptReady={isScriptReady}
                isScriptLoading={isScriptLoading}
            />
        </div>
    </section>
);

export default ResultsSection;
