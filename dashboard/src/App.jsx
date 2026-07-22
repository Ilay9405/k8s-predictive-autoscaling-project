import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Overview from './pages/Overview';
import Accuracy from './pages/Accuracy';

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        {/* Our sleek pill-shaped navigation bar */}
        <nav className="nav-container">
          <NavLink
            to="/"
            className={({ isActive }) => (isActive ? "btn active" : "btn")}
            end
          >
            Live Dashboard
          </NavLink>
          <NavLink
            to="/accuracy"
            className={({ isActive }) => (isActive ? "btn active" : "btn")}
          >
            Predictions vs. Actual Usage
          </NavLink>
        </nav>

        {/* The router handles switching between pages */}
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/accuracy" element={<Accuracy />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
