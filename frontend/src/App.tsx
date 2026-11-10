import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { UploadPage } from './pages/UploadPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { VisualizationPage } from './pages/VisualizationPage';
import { EnhancementPage } from './pages/EnhancementPage';
import { ResultsPage } from './pages/ResultsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="processing" element={<ProcessingPage />} />
          <Route path="visualization" element={<VisualizationPage />} />
          <Route path="enhancement" element={<EnhancementPage />} />
          <Route path="results" element={<ResultsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
