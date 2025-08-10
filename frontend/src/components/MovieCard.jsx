import React from 'react';
import { Link } from 'react-router-dom';

export default function MovieCard({ movie }) {
  return (
    <Link 
      to={`/movies/${movie.id}`}
      className="block bg-gray-800 rounded-xl shadow-lg overflow-hidden hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 group"
    >
      <div className="relative pb-[150%]">
        <img
          src={movie.poster_path 
            ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
            : '/placeholder.svg'}
          alt={movie.title}
          className="absolute top-0 left-0 w-full h-full object-cover group-hover:opacity-80 transition-opacity"
          onError={(e) => {
            e.target.onerror = null;
            e.target.src = '/placeholder.svg';
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-4">
          <div>
            <h3 className="font-bold text-lg line-clamp-2">{movie.title}</h3>
            <div className="flex items-center gap-2 mt-2">
              {movie.vote_average > 0 && (
                <span className="flex items-center bg-amber-500/20 text-amber-400 px-2 py-1 rounded-full text-xs">
                  ★ {movie.vote_average.toFixed(1)}
                </span>
              )}
              {movie.release_date && (
                <span className="text-gray-300 text-sm">
                  {new Date(movie.release_date).getFullYear()}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}