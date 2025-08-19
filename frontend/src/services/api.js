import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios'; 

// --- Configuration ---
const API_BASE_URL = 'http://127.0.0.1:8000';

// --- API Service (services/api.js) ---
// Now uses axios for cleaner requests and error handling.
const apiService = {
  async getNewSessionId() {
    const response = await axios.get(`${API_BASE_URL}/collection/session/new`);
    return response.data;
  },

  async getFilesForSession(sessionId) {
    const response = await axios.get(`${API_BASE_URL}/collection/files/${sessionId}`);
    return response.data;
  },

  async uploadFiles(sessionId, files) {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    for (const file of files) {
      formData.append('files', file);
    }
    const response = await axios.post(`${API_BASE_URL}/collection/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async deleteFile(sessionId, filename) {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('filename', filename);
      const response = await axios.post(`${API_BASE_URL}/collection/delete-file`, formData);
      return response.data;
  },

  async processCollection(sessionId, persona, jobToDo) {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('persona', persona);
    formData.append('job_to_be_done', jobToDo);
    try {
        const response = await axios.post(`${API_BASE_URL}/collection/process`, formData);
        return response.data;
    } catch (error) {
        // Axios provides better error details
        const errorMsg = error.response?.data?.detail || error.message || 'Analysis failed';
        throw new Error(errorMsg);
    }
  },

  async processCollectionWithText(sessionId, selectedText) {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('selected_text', selectedText); // Use the correct key for the backend
    try {
        const response = await axios.post(`${API_BASE_URL}/collection/process`, formData);
        return response.data;
    } catch (error) {
        const errorMsg = error.response?.data?.detail || error.message || 'Analysis failed';
        throw new Error(errorMsg);
    }
  },

  async generateScript(sessionId, query, insights, sections) {
        const formData = new FormData();
        formData.append('session_id', sessionId);
        formData.append('query', query);
        formData.append('insights_json', JSON.stringify(insights));
        formData.append('sections_json', JSON.stringify(sections));
        const response = await axios.post(`${API_BASE_URL}/collection/generate-script`, formData);
        return response.data;
    },
    async getAudio(sessionId) {
        const response = await axios.get(`${API_BASE_URL}/collection/get-audio/${sessionId}`);
        return response.data;
    }
};


export default apiService;