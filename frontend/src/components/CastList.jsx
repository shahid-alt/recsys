import React from 'react';
import { Link } from 'react-router-dom';

export default function CastList({ credits }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 py-4">
      {credits.map(credit => (
        <div key={credit.id} className="text-center">
          <Link to={`/people/${credit.person_id}`} className="block">
            {/* Check if person data exists with profile_path */}
            {credit.person?.profile_path ? (
              <img
                src={`https://image.tmdb.org/t/p/w200${credit.person.profile_path}`}
                alt={credit.name}
                className="w-20 h-20 rounded-full object-cover mx-auto mb-2"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src = '/placeholder-person.png';
                }}
              />
            ) : (
              <div className="bg-gray-100 rounded-full w-20 h-20 mx-auto mb-2 flex items-center justify-center overflow-hidden">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            )}
            <h4 className="font-medium text-sm">{credit.name}</h4>
            {credit.character_name && (
              <p className="text-xs text-gray-600 truncate">as {credit.character_name}</p>
            )}
          </Link>
        </div>
      ))}
    </div>
  );
}