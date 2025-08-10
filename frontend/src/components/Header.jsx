import React from 'react';
import { Link } from 'react-router-dom';

export default function Header() {
  return (
    <header className="bg-gradient-to-r from-indigo-900 to-purple-900 shadow-xl sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <Link to="/" className="text-2xl font-bold bg-gradient-to-r from-amber-400 to-rose-400 bg-clip-text text-transparent">
          TMDBMirror
        </Link>
        <nav className="flex gap-6">
          <Link 
            to="/" 
            className="text-gray-200 hover:text-amber-300 transition-colors duration-200 font-medium"
          >
            Home
          </Link>
          <Link 
            to="/search" 
            className="text-gray-200 hover:text-amber-300 transition-colors duration-200 font-medium"
          >
            Search
          </Link>
          <Link 
            to="/people" 
            className="text-gray-200 hover:text-amber-300 transition-colors duration-200 font-medium"
          >
            People
          </Link>
        </nav>
      </div>
    </header>
  );
}