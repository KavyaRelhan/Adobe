// --- Custom Hook (hooks/useSession.js) ---
import { useState, useEffect } from "react";
import apiService from "../services/api";

const useSession = () => {
  const [sessionId, setSessionId] = useState(null);
  const [initialFiles, setInitialFiles] = useState([]);
  const [isSessionLoading, setIsSessionLoading] = useState(true);

  useEffect(() => {
    const initializeSession = async () => {
      try {
        let storedSessionId = localStorage.getItem('sessionId');
        if (storedSessionId) {
          const data = await apiService.getFilesForSession(storedSessionId);
          setInitialFiles(data.uploaded_files || []);
          setSessionId(storedSessionId);
        } else {
          const data = await apiService.getNewSessionId();
          localStorage.setItem('sessionId', data.session_id);
          setSessionId(data.session_id);
        }
      } catch (error) {
        console.error('Error initializing session:', error);
        alert('Could not connect to the backend. This is likely a CORS issue. Please ensure your backend server is configured to accept requests from this origin.');
      }finally {
        setIsSessionLoading(false);
      }
    };
    initializeSession();
  }, []);

  return { sessionId, initialFiles, isSessionLoading };
};

export default useSession;