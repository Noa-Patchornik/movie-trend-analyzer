// frontend/src/App.jsx

import React, { useState, useEffect } from 'react';


const API_BASE_URL = '/api/movies';

const INITIAL_TMDB_ID = 496243; 

function MovieDashboard() {
    const [movies, setMovies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // --- Core Data Fetch (R1.4) ---
    const fetchMovies = async () => {
        setLoading(true);
        try {
            const response = await fetch(API_BASE_URL);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            setMovies(data);
            setError(null);
        } catch (e) {
            console.error("Error fetching data:", e);
            setError(`Failed to connect to backend: ${e.message}. Is the API running on :8000?`);
            setMovies([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMovies();
    }, []); 

    // --- Action Handlers (R1.1, R1.2, R1.5) ---

    // R1.5: Register a new movie (Initial setup)
    const handleRegisterMovie = async (tmdb_id) => {
        const res = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tmdb_id: tmdb_id })
        });

        if (res.status === 201) {
            alert(`Movie ${tmdb_id} registered! External update triggered.`);
            fetchMovies(); // Refresh list to show the new movie (with placeholder name)
        } else if (res.status === 400) {
            alert("Movie already registered!");
        } else {
            alert(`Error registering movie: ${res.status}`);
        }
    };

    // R1.1: Send View Event (Asynchronous)
    const handleAddView = async (tmdb_id) => {
        const res = await fetch(`${API_BASE_URL}/view`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tmdb_id: tmdb_id })
        });

        if (res.status === 202) {
            alert(`View event sent for ${tmdb_id}. Check Internal Worker logs!`);
            // Wait a moment and refresh to see the view count update (R1.4)
            setTimeout(fetchMovies, 1000); 
        } else {
            alert(`Error sending view event: ${res.status}`);
        }
    };

    // R1.2: Trigger External Update (Asynchronous)
    const handleTriggerExternalUpdate = async (tmdb_id) => {
        const res = await fetch(`${API_BASE_URL}/trigger_external_update/${tmdb_id}`, {
            method: 'POST'
        });

        if (res.status === 202) {
            alert(`External update triggered for ${tmdb_id}. Check External Worker logs!`);
            // Wait a moment and refresh to see the score update (R1.4)
            setTimeout(fetchMovies, 5000); // Give the external worker time to fetch TMDB data
        } else {
             alert(`Error triggering update: ${res.status}`);
        }
    };


    if (loading) return <h1>Loading...</h1>;
    if (error) return <h1 style={{ color: 'red' }}>{error}</h1>;

    return (
        <div style={{ padding: '20px' }}>
            <h1>Movie Trend Dashboard (MVP)</h1>
            <button onClick={fetchMovies} style={{ marginRight: '10px', padding: '10px' }}>
                Manual Refresh (R1.4)
            </button>
            <button onClick={() => handleRegisterMovie(INITIAL_TMDB_ID)} style={{ padding: '10px' }}>
                Register New Movie: {INITIAL_TMDB_ID}
            </button>

            <h3 style={{ marginTop: '20px' }}>Registered Movies ({movies.length})</h3>

            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
                <thead>
                    <tr style={{ backgroundColor: '#f2f2f2' }}>
                        <th>TMDB ID</th>
                        <th>Title</th>
                        <th>Internal Views</th>
                        <th>External Score (TMDB)</th>
                        <th>Final Trend Score</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {movies.map(movie => (
                        <tr key={movie.tmdb_id}>
                            <td>{movie.tmdb_id}</td>
                            <td>{movie.title}</td>
                            <td style={{ textAlign: 'center' }}>{movie.internal_views_count}</td>
                            <td style={{ textAlign: 'center' }}>{movie.external_score.toFixed(1)}</td>
                            <td style={{ textAlign: 'center', fontWeight: 'bold' }}>{movie.final_trend_score.toFixed(1)}</td>
                            <td>
                                <button onClick={() => handleAddView(movie.tmdb_id)} style={{ marginRight: '5px' }}>Add View (R1.1)</button>
                                <button onClick={() => handleTriggerExternalUpdate(movie.tmdb_id)}>Update Score (R1.2)</button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            
            <p style={{ marginTop: '20px', fontSize: 'small' }}>
                <a href="http://localhost:8000/docs" target="_blank">View Backend Swagger UI (8000/docs)</a>
            </p>
        </div>
    );
}

export default MovieDashboard;