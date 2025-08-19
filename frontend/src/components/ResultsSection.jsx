import React from 'react';
import '../styles/ResultsSection.css';
import PodcastGenerator from "./PodcastGenerator"


const ResultsSection = ({ results, sessionId, isScriptReady, isScriptLoading }) => (
    <section className="results-container">
        <header className="results-header">
            <h2>Analysis Results</h2>
        </header>

        <div className="relevant-section-wrapper">
            <h3>Most Relevant Sections</h3>
            <div className="relevant-sections-container">
                {results.relevant_sections.map((section, index) => (
                    <div key={index} className="section-card glass-card">
                        <div className="section-card-header">
                            <span><p title={section.document}>{section.document}</p></span>
                            <span>Page {section.page_number}</span>
                        </div>
                        {/* <h4>{section.section_title}</h4> */}
                        <p>{section.refined_text}</p>
                    </div>
                ))}
            </div>
        </div>

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