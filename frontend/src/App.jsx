import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import MovieDetail from './pages/MovieDetail';
import SearchPage from './pages/SearchPage';
import PeoplePage from './pages/PeoplePage';
import PersonDetail from './pages/PersonDetail';
import GenrePage from './pages/GenrePage';
import Header from './components/Header';
import ScrollToTop from './components/ScrollToTop';

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-900 text-gray-100">
        <Header />
        <main className="pb-16">
          <ScrollToTop />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/movies/:id" element={<MovieDetail />} />
            <Route path="/people" element={<PeoplePage />} />
            <Route path="/people/:id" element={<PersonDetail />} />
            <Route path="/genres/:genre" element={<GenrePage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}