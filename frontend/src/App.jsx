// frontend/src/App.jsx (קוד מלא וסופי)

import React, { useState, useEffect } from 'react';

// API_BASE_URL is now correctly set to the relative path, proxied by Nginx
const API_BASE_URL = '/api/movies'; 


function MovieDashboard() {
    const [movies, setMovies] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [newTmdbId, setNewTmdbId] = useState(''); 
    // State for the custom Toast component (message box)
    const [toast, setToast] = useState({ message: '', type: '', visible: false }); 

    // Helper function to display the custom toast message
    const showToast = (message, type = 'success') => {
        setToast({ message, type, visible: true });
        // Hide the toast after 3 seconds
        setTimeout(() => setToast(t => ({ ...t, visible: false })), 3000); 
    };


    // --- Core Data Fetch (R1.4) ---
    const fetchMovies = async () => {
        setLoading(true);
        try {
            const response = await fetch(API_BASE_URL);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            // Sort movies by final score descending
            setMovies(data.sort((a, b) => b.final_trend_score - a.final_trend_score)); 
            setError(null);
        } catch (e) {
            console.error("Error fetching data:", e);
            setError(`Connection Error: Could not load data. Is the API running on :8000?`); 
            setMovies([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMovies();
        // Optional: Set up interval for auto-refresh, but we'll keep it manual for now
    }, []); 

    // --- R1.5: Register a new movie ---
    const handleRegisterMovie = async () => {
        const tmdb_id = parseInt(newTmdbId, 10);
        
        if (!tmdb_id || isNaN(tmdb_id)) {
            showToast("Please enter a valid TMDB ID (number).", 'error');
            return;
        }
        
        setLoading(true);

        const res = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tmdb_id: tmdb_id })
        });

        if (res.status === 201) {
            showToast(`Movie ID ${tmdb_id} registered! External update triggered.`, 'success');
            setNewTmdbId(''); // Clear input field
            // Give the external worker a moment to update the title/score before fetching
            setTimeout(fetchMovies, 500); 
        } else if (res.status === 400) {
            showToast(`Error: Movie ID ${tmdb_id} is already registered.`, 'error');
            setLoading(false);
        } else {
            const errorData = await res.json();
            showToast(`Registration failed: ${errorData.detail || res.statusText}. Check logs.`, 'error');
            setLoading(false);
        }
    };

    // --- R1.1: Send View Event (Asynchronous) ---
    const handleAddView = async (tmdb_id) => {
        const res = await fetch(`${API_BASE_URL}/view`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tmdb_id: tmdb_id })
        });

        if (res.status === 202) {
            showToast(`View event sent! Internal Worker is processing.`, 'info');
            // Refresh quickly to see the view count update
            setTimeout(fetchMovies, 1000); 
        } else {
             const errorData = await res.json();
             showToast(`Error: ${errorData.detail || res.statusText}`, 'error');
        }
    };

    // --- R1.2: Trigger External Update (Asynchronous) ---
    const handleTriggerExternalUpdate = async (tmdb_id) => {
        const res = await fetch(`${API_BASE_URL}/trigger_external_update/${tmdb_id}`, {
            method: 'POST'
        });

        if (res.status === 202) {
            showToast(`TMDB update triggered. Score will update soon.`, 'info');
            // Give the external worker time to fetch TMDB data (5 seconds for safety)
            setTimeout(fetchMovies, 5000); 
        } else {
             const errorData = await res.json();
             showToast(`Error: ${errorData.detail || res.statusText}`, 'error');
        }
    };


    if (loading && movies.length === 0) return (
        <div style={styles.centerPage}>
            <h1 style={{color: '#4682B4'}}>Loading Data...</h1>
        </div>
    );
    
    // Main Render
    return (
        <div style={styles.centerContainer}>
            {/* The Custom Toast Component */}
            {toast.visible && (
                <div style={{
                    ...styles.toast,
                    backgroundColor: toast.type === 'success' ? '#3CB371' : toast.type === 'info' ? '#1E90FF' : '#FF6347'
                }}>
                    {toast.message}
                </div>
            )}

            <header style={styles.header}>
                <h1 style={styles.title}>🎬 Movie Trend Analyzer</h1>
                <p style={{color: error ? '#FF6347' : '#3CB371', fontWeight: 'bold', textAlign: 'center'}}>{error || "Backend Connection: OK"}</p>
                
                <div style={styles.controlGroup}>
                    <button onClick={fetchMovies} style={styles.button.primary} disabled={loading}>
                        {loading ? 'Refreshing...' : 'Manual Refresh (R1.4)'}
                    </button>
                    
                    <div style={styles.inputGroup}>
                        <input
                            type="number"
                            placeholder="Enter new TMDB ID (e.g. 27205)"
                            value={newTmdbId}
                            onChange={(e) => setNewTmdbId(e.target.value)}
                            style={styles.input}
                            disabled={loading}
                        />
                        <button onClick={handleRegisterMovie} style={styles.button.register} disabled={!newTmdbId || loading}>
                            Register Movie (R1.5)
                        </button>
                    </div>
                </div>
            </header>

            <h3 style={styles.subtitle}>Registered Movies ({movies.length}) - Sorted by Trend Score</h3>

            <table style={styles.table}>
                <thead style={styles.table.thead}>
                    <tr>
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
                        <tr key={movie.tmdb_id} style={styles.table.tr}>
                            <td>{movie.tmdb_id}</td>
                            <td>{movie.title}</td>
                            <td style={{ textAlign: 'center' }}>{movie.internal_views_count}</td>
                            <td style={{ textAlign: 'center' }}>{movie.external_score.toFixed(1)}</td>
                            <td style={{ textAlign: 'center', fontWeight: 'bold', backgroundColor: '#F0F8FF' }}>{movie.final_trend_score.toFixed(1)}</td>
                            <td>
                                <button onClick={() => handleAddView(movie.tmdb_id)} style={styles.button.action}>Add View (R1.1)</button>
                                <button onClick={() => handleTriggerExternalUpdate(movie.tmdb_id)} style={styles.button.action}>Update Score (R1.2)</button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            
            <p style={{ marginTop: '20px', fontSize: 'small', textAlign: 'center' }}>
                <a href="http://localhost:8000/docs" target="_blank" style={{color: '#4682B4'}}>View Backend Swagger UI (8000/docs)</a>
            </p>
        </div>
    );
}

// --- CSS Styling (for brighter colors and centering) ---
const styles = {
    // This is the outer container used in main.jsx to center the whole page
    centerPage: { 
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        width: '100%',
    },
    // This is the dashboard card itself, centered within the page
    centerContainer: {
        maxWidth: '1200px',
        margin: '40px auto',
        padding: '20px',
        backgroundColor: '#FFFFFF', 
        borderRadius: '12px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
        fontFamily: 'Arial, sans-serif',
    },
    header: {
        borderBottom: '2px solid #EEE',
        paddingBottom: '15px',
        marginBottom: '20px',
    },
    title: {
        color: '#4682B4', 
        textAlign: 'center',
        fontSize: '2em',
    },
    subtitle: {
        color: '#555',
        marginTop: '10px',
        marginBottom: '15px',
        fontSize: '1.2em',
        textAlign: 'center',
    },
    controlGroup: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '20px',
        marginTop: '15px',
    },
    inputGroup: {
        display: 'flex',
        gap: '10px',
        alignItems: 'center',
    },
    input: {
        padding: '10px',
        borderRadius: '5px',
        border: '1px solid #CCC',
        fontSize: '1em',
        width: '200px',
    },
    button: {
        primary: {
            padding: '10px 15px',
            backgroundColor: '#87CEFA', 
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer',
            fontSize: '1em',
        },
        register: {
            padding: '10px 15px',
            backgroundColor: '#3CB371', 
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer',
            fontSize: '1em',
        },
        action: {
            padding: '8px 12px',
            backgroundColor: '#ADD8E6', 
            color: '#333',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer',
            fontSize: '0.9em',
            marginRight: '5px',
        },
    },
    table: {
        border: '1px solid #DDD',
        borderCollapse: 'collapse',
        width: '100%',
        thead: {
            backgroundColor: '#F0FFFF', 
        },
        tr: {
            borderBottom: '1px solid #EEE',
        },
    },
    // Custom Toast styling
    toast: {
        position: 'fixed',
        top: '20px', 
        left: '50%',
        transform: 'translateX(-50%)',
        padding: '15px 25px',
        borderRadius: '8px',
        color: 'white',
        fontWeight: 'bold',
        zIndex: 1000, 
        boxShadow: '0 4px 10px rgba(0, 0, 0, 0.4)',
    }
};

export default MovieDashboard;