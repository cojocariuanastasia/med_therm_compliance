import axios from 'axios';

const API_BASE = '/api';

export const api = {
  async healthCheck() {
    const response = await axios.get(`${API_BASE}/health`);
    return response.data;
  },

  async getFiles() {
    const response = await axios.get(`${API_BASE}/files`);
    return response.data;
  },

  async getFile(fileId) {
    const response = await axios.get(`${API_BASE}/files/${fileId}`);
    return response.data;
  },

  async uploadFile(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('uploaded_by', 'user');

    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentCompleted);
        }
      }
    };

    const response = await axios.post(`${API_BASE}/upload`, formData, config);
    return response.data;
  },

  async analyzeFile(fileId) {
    const response = await axios.post(`${API_BASE}/analyze/${fileId}`);
    return response.data;
  },

  async getAnalysis(analysisId) {
    const response = await axios.get(`${API_BASE}/analysis/${analysisId}`);
    return response.data;
  },

  async getTimeline(analysisId) {
    const response = await axios.get(`${API_BASE}/analysis/${analysisId}/timeline`);
    return response.data;
  },

  async getRules() {
    const response = await axios.get(`${API_BASE}/rules`);
    return response.data;
  },

  async deleteFile(fileId) {
    const response = await axios.delete(`${API_BASE}/files/${fileId}`);
    return response.data;
  },

  getCsvDownloadUrl(analysisId) {
    return `${API_BASE}/download/csv/${analysisId}`;
  },

  getPdfDownloadUrl(analysisId) {
    return `${API_BASE}/download/pdf/${analysisId}`;
  }
};

export default api;
