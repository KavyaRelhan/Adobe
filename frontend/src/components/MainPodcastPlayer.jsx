import React, { useState, useRef } from "react";
import { FaPlay, FaPause } from "react-icons/fa";
import "../styles/MainPodcastPlayer.css";

const MainPodcastPlayer = ({ audioSrc, title = "Relevant Section", image }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);

  const togglePlay = () => {
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  return (
    <div className="main-podcast-card">
      <div className="main-podcast-container">
        <div className="disk-wrapper">
          <div className={`disk ${isPlaying ? "rotate" : ""}`}
            style={{
              backgroundImage: image
                ? `url(${image})`
                : "linear-gradient(135deg, #007BFF, #00C4FF)",
            }}
          />
          <button className="play-button" onClick={togglePlay}>
            {isPlaying ? <FaPause /> : <FaPlay />}
          </button>
        </div>

        <div className="podcast-title">{title}</div>

        {isPlaying && (
          <div className="waveform">
            {[...Array(20)].map((_, i) => (
              <div key={i} className="bar" />
            ))}
          </div>
        )}

        <audio ref={audioRef} src={audioSrc} onEnded={() => setIsPlaying(false)} />
      </div>
    </div>
  );
};

export default MainPodcastPlayer;
