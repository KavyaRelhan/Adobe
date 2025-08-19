import React, { useState } from 'react';
import  apiService from '../services/api';
import { FaPlayCircle, FaSpinner, FaCheckCircle } from 'react-icons/fa';
import "../styles/PodcastGenerator.css"

const API_BASE_URL = 'http://127.0.0.1:8000';

const PodcastGenerator = ({ sessionId, isScriptReady, isScriptLoading }) => {
    const [isAudioLoading, setIsAudioLoading] = useState(false);
    const [audioUrl, setAudioUrl] = useState(null);
    const [isPlaying, setIsPlaying] = useState(false); 

    const handleGenerateAudio = async () => {
        setIsAudioLoading(true);
        setAudioUrl(null);
        try {
            const data = await apiService.getAudio(sessionId);
            setAudioUrl(`${API_BASE_URL}${data.podcast_url}`);
        } catch (error) {
            console.error("Failed to get podcast audio:", error);
            alert("Sorry, the podcast could not be generated.");
        } finally {
            setIsAudioLoading(false);
        }
    };

    return (
        <div className="podcast-generator">
            <h3>Audio Overview</h3>
            <p>Listen to a conversation about the key findings.</p>
            
            {isScriptLoading && (
                <div className="status-indicator">
                    <FaSpinner className="animate-spin" />
                    <span>Generating podcast script...</span>
                </div>
            )}

            {isScriptReady && !audioUrl && (
                <button onClick={handleGenerateAudio} disabled={isAudioLoading} className="button primary-button">
                    {isAudioLoading ? <FaSpinner className="animate-spin" /> : <FaPlayCircle />}
                    <span>{isAudioLoading ? 'Loading Audio...' : 'Play Podcast'}</span>
                </button>
            )}

            {audioUrl && (
                <div className="podcast-player-container">
                    {/* The new rotating disk visual */}
                    <div className={`podcast-disk ${isPlaying ? 'is-playing' : ''}`}>
                        <div className="podcast-disk-inner"></div>
                    </div>
                    <audio 
                        controls 
                        autoPlay 
                        src={audioUrl} 
                        className="audio-player"
                        onPlay={() => setIsPlaying(true)}
                        onPause={() => setIsPlaying(false)}
                        onEnded={() => setIsPlaying(false)}
                    >
                        Your browser does not support the audio element.
                    </audio>
                </div>
            )}
        </div>
    );
};

export default PodcastGenerator;