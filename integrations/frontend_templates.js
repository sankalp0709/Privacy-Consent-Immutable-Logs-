/**
 * Frontend Integration Templates for Gurukul
 * JavaScript/TypeScript code for integrating with BHIV Knowledge Base
 */

// ============================================================================
// KNOWLEDGE BASE API CLIENT
// ============================================================================

class KnowledgeBaseClient {
    constructor(apiUrl = 'http://localhost:8004') {
        this.apiUrl = apiUrl;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }

    /**
     * Main knowledge base query method
     */
    async queryKnowledgeBase(query, filters = {}, userId = 'gurukul_user') {
        try {
            const response = await fetch(`${this.apiUrl}/query-kb`, {
                method: 'POST',
                headers: this.defaultHeaders,
                body: JSON.stringify({
                    query: query,
                    filters: filters,
                    user_id: userId,
                    limit: 5
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return {
                success: true,
                data: result
            };
        } catch (error) {
            console.error('Knowledge base query failed:', error);
            return {
                success: false,
                error: error.message,
                data: null
            };
        }
    }

    /**
     * Ask Vedas for spiritual wisdom
     */
    async askVedas(question, userId = 'gurukul_user') {
        try {
            const response = await fetch(`${this.apiUrl}/ask-vedas`, {
                method: 'POST',
                headers: this.defaultHeaders,
                body: JSON.stringify({
                    query: question,
                    user_id: userId
                })
            });

            const result = await response.json();
            return { success: true, data: result };
        } catch (error) {
            console.error('Ask Vedas failed:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Get educational content
     */
    async getEducationalContent(topic, userId = 'gurukul_user') {
        try {
            const response = await fetch(`${this.apiUrl}/edumentor`, {
                method: 'POST',
                headers: this.defaultHeaders,
                body: JSON.stringify({
                    query: topic,
                    user_id: userId
                })
            });

            const result = await response.json();
            return { success: true, data: result };
        } catch (error) {
            console.error('Educational content failed:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Search by specific Vedic book
     */
    async searchByBook(query, book, userId = 'gurukul_user') {
        const filters = { book: book.toLowerCase() };
        return this.queryKnowledgeBase(query, filters, userId);
    }

    /**
     * Search by content type (dharma, artha, kama, moksha)
     */
    async searchByType(query, type, userId = 'gurukul_user') {
        const filters = { type: type.toLowerCase() };
        return this.queryKnowledgeBase(query, filters, userId);
    }

    /**
     * Check API health
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            return response.ok;
        } catch (error) {
            return false;
        }
    }
}

// ============================================================================
// REACT COMPONENTS
// ============================================================================

/**
 * React Hook for Knowledge Base Integration
 */
function useKnowledgeBase() {
    const [client] = useState(() => new KnowledgeBaseClient());
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const query = async (question, filters = {}) => {
        setLoading(true);
        setError(null);
        
        try {
            const result = await client.queryKnowledgeBase(question, filters);
            if (!result.success) {
                setError(result.error);
                return null;
            }
            return result.data;
        } catch (err) {
            setError(err.message);
            return null;
        } finally {
            setLoading(false);
        }
    };

    const askVedas = async (question) => {
        setLoading(true);
        setError(null);
        
        try {
            const result = await client.askVedas(question);
            if (!result.success) {
                setError(result.error);
                return null;
            }
            return result.data;
        } catch (err) {
            setError(err.message);
            return null;
        } finally {
            setLoading(false);
        }
    };

    return { query, askVedas, loading, error };
}

/**
 * Ask the Vedas Component
 */
function AskVedasComponent() {
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState(null);
    const { askVedas, loading, error } = useKnowledgeBase();

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!question.trim()) return;

        const result = await askVedas(question);
        if (result) {
            setAnswer(result);
        }
    };

    return (
        <div className="ask-vedas-component">
            <h2>Ask the Vedas</h2>
            <form onSubmit={handleSubmit}>
                <div className="input-group">
                    <textarea
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="Ask a question about dharma, life, or spiritual wisdom..."
                        rows={3}
                        disabled={loading}
                    />
                    <button type="submit" disabled={loading || !question.trim()}>
                        {loading ? 'Seeking Wisdom...' : 'Ask the Vedas'}
                    </button>
                </div>
            </form>

            {error && (
                <div className="error-message">
                    <p>Error: {error}</p>
                </div>
            )}

            {answer && (
                <div className="answer-section">
                    <h3>Vedic Wisdom</h3>
                    <div className="wisdom-text">
                        {answer.response}
                    </div>
                    {answer.sources && answer.sources.length > 0 && (
                        <div className="sources">
                            <h4>Sources:</h4>
                            <ul>
                                {answer.sources.map((source, index) => (
                                    <li key={index}>{source}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

/**
 * Knowledge Search Component
 */
function KnowledgeSearchComponent() {
    const [query, setQuery] = useState('');
    const [selectedBook, setSelectedBook] = useState('');
    const [selectedType, setSelectedType] = useState('');
    const [results, setResults] = useState(null);
    const { query: searchKB, loading, error } = useKnowledgeBase();

    const vedaBooks = ['rigveda', 'samaveda', 'yajurveda', 'atharvaveda', 'upanishads', 'bhagavad_gita'];
    const contentTypes = ['dharma', 'artha', 'kama', 'moksha'];

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        const filters = {};
        if (selectedBook) filters.book = selectedBook;
        if (selectedType) filters.type = selectedType;

        const result = await searchKB(query, filters);
        if (result) {
            setResults(result);
        }
    };

    return (
        <div className="knowledge-search-component">
            <h2>Search Vedic Knowledge</h2>
            <form onSubmit={handleSearch}>
                <div className="search-controls">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search for knowledge..."
                        disabled={loading}
                    />
                    
                    <select 
                        value={selectedBook} 
                        onChange={(e) => setSelectedBook(e.target.value)}
                        disabled={loading}
                    >
                        <option value="">All Books</option>
                        {vedaBooks.map(book => (
                            <option key={book} value={book}>
                                {book.charAt(0).toUpperCase() + book.slice(1)}
                            </option>
                        ))}
                    </select>

                    <select 
                        value={selectedType} 
                        onChange={(e) => setSelectedType(e.target.value)}
                        disabled={loading}
                    >
                        <option value="">All Types</option>
                        {contentTypes.map(type => (
                            <option key={type} value={type}>
                                {type.charAt(0).toUpperCase() + type.slice(1)}
                            </option>
                        ))}
                    </select>

                    <button type="submit" disabled={loading || !query.trim()}>
                        {loading ? 'Searching...' : 'Search'}
                    </button>
                </div>
            </form>

            {error && (
                <div className="error-message">
                    <p>Error: {error}</p>
                </div>
            )}

            {results && (
                <div className="search-results">
                    <h3>Search Results ({results.knowledge_base_results} found)</h3>
                    <div className="result-content">
                        {results.response}
                    </div>
                    {results.sources && results.sources.length > 0 && (
                        <div className="sources">
                            <h4>Sources:</h4>
                            <ul>
                                {results.sources.map((source, index) => (
                                    <li key={index}>{source}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

// ============================================================================
// CSS STYLES
// ============================================================================

const knowledgeBaseStyles = `
.ask-vedas-component, .knowledge-search-component {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    font-family: Arial, sans-serif;
}

.input-group {
    margin-bottom: 20px;
}

.input-group textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 16px;
    resize: vertical;
}

.input-group button {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    margin-top: 10px;
}

.input-group button:disabled {
    background-color: #6c757d;
    cursor: not-allowed;
}

.search-controls {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.search-controls input, .search-controls select {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.search-controls input {
    flex: 1;
    min-width: 200px;
}

.error-message {
    background-color: #f8d7da;
    color: #721c24;
    padding: 12px;
    border-radius: 4px;
    margin: 10px 0;
}

.answer-section, .search-results {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 4px;
    margin-top: 20px;
}

.wisdom-text, .result-content {
    line-height: 1.6;
    margin-bottom: 15px;
}

.sources {
    border-top: 1px solid #dee2e6;
    padding-top: 15px;
}

.sources ul {
    list-style-type: none;
    padding: 0;
}

.sources li {
    background-color: #e9ecef;
    padding: 8px 12px;
    margin: 5px 0;
    border-radius: 4px;
    font-size: 14px;
}
`;

// Export for use in other modules
export { 
    KnowledgeBaseClient, 
    useKnowledgeBase, 
    AskVedasComponent, 
    KnowledgeSearchComponent,
    knowledgeBaseStyles 
};
