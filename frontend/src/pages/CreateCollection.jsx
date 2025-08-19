
import React, { useState, useEffect, useCallback, useRef } from 'react';
import UploadSection from "../components/UploadSection";
import AnalysisForm from "../components/AnalysisForm";
import Loader from "../components/Loader";
import FileList from "../components/FileList";
import ResultsSection from '../components/ResultsSection';
import PdfViewer from './PdfViewer';
import SelectionPopup from '../components/SelectionPopup'; // Make sure this component exists
import useSession from "../hooks/useSession";
import  apiService from "../services/api";
import Header from '../components/Header';
import "../styles/CreateCollection.css";

const API_BASE_URL = 'http://127.0.0.1:8000';

const CreateCollection = () => {
  const { sessionId, initialFiles, isSessionLoading } = useSession();
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [viewingPdf, setViewingPdf] = useState(null);
  const [persona, setPersona] = useState('');
  const [jobToDo, setJobToDo] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const fileInputRef = useRef(null);
  const [selection,   setSelection] = useState(null); // State for the selection popup
  const [currentQuery, setCurrentQuery] = useState('');
  const [selectedText, setSelectedText] = useState('');
  const [isScriptReady, setIsScriptReady] = useState('');
  const [isScriptLoading, setIsScriptLoading] = useState('');

console.log("cvnbm,    ",selection, "bhnm., ",selectedText)


  useEffect(() => {
    if (!isSessionLoading) {
      setUploadedFiles(initialFiles);
    }
  }, [isSessionLoading, initialFiles]);

  useEffect(() => {
    document.body.style.overflow = viewingPdf ? 'hidden' : 'auto';
    return () => { document.body.style.overflow = 'auto'; };
  }, [viewingPdf]);

    useEffect(() => {
    if (results && sessionId && currentQuery) {
      const generate = async () => {
        setIsScriptReady(false);
        setIsScriptLoading(true);
        try {
          await apiService.generateScript(sessionId, currentQuery, results.insights, results.relevant_sections);
          setIsScriptReady(true);
        } catch (error) {
          console.error("Failed to auto-generate podcast script:", error);
        } finally {
          setIsScriptLoading(false);
        }
      };
      generate();
    }
  }, [results, sessionId, currentQuery]);

  const handleFileUpload = useCallback(async (filesToUpload) => {
    if (!sessionId) return;
    const existingFileNames = new Set(uploadedFiles);
    const newFiles = Array.from(filesToUpload).filter(file => !existingFileNames.has(file.name));
    if (newFiles.length === 0) return alert("All selected files have already been uploaded.");
    if (newFiles.length < filesToUpload.length) alert("Some files were duplicates and have been skipped.");
    try {
      const data = await apiService.uploadFiles(sessionId, newFiles);
      setUploadedFiles(data.uploaded_files);
    } catch (error) {
      console.error('Error uploading files:', error);
      alert('An error occurred during file upload.');
    }
  }, [sessionId, uploadedFiles]);

  const handleViewPdf = (filename) => {
    if (!sessionId) return;
    const fileUrl = `${API_BASE_URL}/uploads/${sessionId}/${filename}`;
    setViewingPdf({ url: fileUrl, name: filename });
  };

  const handleClosePdf = () => {
    setViewingPdf(null);
    setSelection(null);
  };

  const handleDeleteFile = useCallback(async (filenameToDelete) => {
    if (!sessionId) return alert('Session not initialized.');
    if (!window.confirm(`Are you sure you want to delete "${filenameToDelete}"?`)) return;
    const originalFiles = [...uploadedFiles];
    setUploadedFiles(currentFiles => currentFiles.filter(f => f !== filenameToDelete));
    try {
      const data = await apiService.deleteFile(sessionId, filenameToDelete);
      setUploadedFiles(data.uploaded_files);
    } catch (error) {
      console.error('Error deleting file:', error);
      alert(`Failed to delete ${filenameToDelete}. Restoring file list.`);
      setUploadedFiles(originalFiles);
    }
  }, [sessionId, uploadedFiles]);

  const handleSubmit = async () => {
    if (!persona || !jobToDo) return alert('Please fill out both Persona and Job to be Done fields.');
    const query = `Persona: ${persona}. Task: ${jobToDo}`;
    setCurrentQuery(query);
    setIsLoading(true);
    setResults(null);
    try {
      const data = await apiService.processCollection(sessionId, persona, jobToDo);
      setResults(data);
    } catch (error) {
      console.error('Error processing collection:', error);
      alert(`An error occurred during analysis: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyzeSelectedText = async (selectedText) => {
    if (!sessionId || !selectedText) return;
    console.log(`[CreateCollection] Step 6: User clicked 'Analyze'. Analyzing text: "${selectedText.substring(0, 30)}..."`);
    setCurrentQuery(selectedText);
    setIsLoading(true);
    setResults(null);
    try {
      const data = await apiService.processCollectionWithText(sessionId, selectedText);
      setResults(data);
    } catch (error) {
      console.error('Error processing selected text:', error);
      alert(`An error occurred during analysis: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTextSelection = () => {
    const text = window.getSelection().toString().trim();
    if (text) {
        setSelectedText(text);
    }
  };

  useEffect(() => {
    if (results) {
      document.getElementById('results-section-container')?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [results]);

  if (isSessionLoading) {
    return <Loader />;
  }
  
  console.log("[CreateCollection] Step 5: Re-rendering. Current selection state:", selection);

  const showAnalysisForm = uploadedFiles.length > 0;


  return (
    <>
      <div className="container">
        <Header/>
        <main className="main-content">
          {showAnalysisForm ? (
            <FileList files={uploadedFiles} onAddMore={() => fileInputRef.current?.click()} onDeleteFile={handleDeleteFile} onViewPdf={handleViewPdf}/>
          ) : (
            <UploadSection onFileUpload={handleFileUpload} />
          )}
          <input
            type="file"
            ref={fileInputRef}
            multiple
            style={{ display: 'none' }}
            accept=".pdf"
            onChange={(e) => { handleFileUpload(e.target.files); e.target.value = ''; }}
          />
          
          {showAnalysisForm && (
            <>
              <AnalysisForm persona={persona} setPersona={setPersona} jobToDo={jobToDo} setJobToDo={setJobToDo} />
              <div className="submit-area">
                <button onClick={handleSubmit} disabled={isLoading} className="button primary-button">
                  {isLoading ? 'Processing...' : 'Extract Insights'}
                </button>
                {isLoading && <Loader />}
              </div>
            </>
          )}
          {results && (
            <div id="results-section-container" className="results-wrapper">
              <ResultsSection 
                results={results} 
                sessionId={sessionId}
                query={currentQuery}
                isScriptReady={isScriptReady}
                isScriptLoading={isScriptLoading} 
              />
            </div>
          )}
        </main>
      </div>

      {viewingPdf && (
        <PdfViewer
          fileUrl={viewingPdf.url}
          fileName={viewingPdf.name}
          onClose={handleClosePdf}
          adobeKey="8d8b62a48e7f4894937f7bf47398b160"
          // onTextSelect={setSelection} // Pass the state setter directly
          onTextSelect={setSelection} // Pass the state setter directly
        />
      )}
      
      {selection && (
        <SelectionPopup 
          top={selection.top} 
          left={selection.left} 
          onAnalyze={() => {
              handleAnalyzeSelectedText(selection.text);
              setSelection(null);
          }} 
        />
      )}
    </>
  );
};

export default CreateCollection;