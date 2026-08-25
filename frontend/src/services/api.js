import axios from "axios";

const API_BASE = "http://localhost:8000/api";

export const api = {
  // Fields
  async getFields() {
    const res = await axios.get(`${API_BASE}/fields`);
    return res.data;
  },

  async getFieldDetails(fieldId) {
    const res = await axios.get(`${API_BASE}/fields/${fieldId}`);
    return res.data;
  },

  async createField(fieldData) {
    const res = await axios.post(`${API_BASE}/fields`, fieldData);
    return res.data;
  },

  async deleteField(fieldId) {
    const res = await axios.delete(`${API_BASE}/fields/${fieldId}`);
    return res.data;
  },

  async uploadBoundaryFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await axios.post(`${API_BASE}/fields/upload-boundary`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },

  // Analysis & Scoring
  async runAnalysis(payload) {
    const res = await axios.post(`${API_BASE}/analysis/run`, payload);
    return res.data;
  },

  async getGrowthStages() {
    const res = await axios.get(`${API_BASE}/analysis/growth-stages`);
    return res.data;
  },

  async updateGrowthStage(stageKey, payload) {
    const res = await axios.put(`${API_BASE}/analysis/growth-stages/${stageKey}`, payload);
    return res.data;
  },

  // History & Trajectory
  async getFieldHistory(fieldId) {
    const res = await axios.get(`${API_BASE}/history/${fieldId}`);
    return res.data;
  },

  // Report Export
  getReportDownloadUrl(fieldId) {
    return `${API_BASE}/reports/pdf/${fieldId}`;
  },
};
