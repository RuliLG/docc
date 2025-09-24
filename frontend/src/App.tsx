import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import SystemCheck from './components/SystemCheck';
import MainApp from './components/MainApp';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<SystemCheck />} />
        <Route path="/main" element={<MainApp />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
