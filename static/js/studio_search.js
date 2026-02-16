/**
 * Kiri Studio Semantic Search
 * 100% Client-Side Search using Transformers.js.
 * $0 Infrastructure Cost, 100% Privacy.
 */

class SemanticSearch {
    constructor() {
        this.pipe = null;
        this.index = []; // { filename: str, embedding: Float32Array }
        this.isLoading = false;
        this.isReady = false;
    }

    /**
     * Lazy-load the model when needed or on repo load
     */
    async init() {
        if (this.pipe || this.isLoading) return;
        this.isLoading = true;
        console.log("[SemanticSearch] Loading embedding model (all-MiniLM-L6-v2)...");

        try {
            const { pipeline } = await import('https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2');
            this.pipe = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
            this.isReady = true;
            console.log("[SemanticSearch] Model Ready.");
        } catch (e) {
            console.error("[SemanticSearch] Load Error:", e);
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Index all files in the repository
     * This runs in the background.
     */
    async indexRepository(files) {
        if (!this.isReady) await this.init();

        console.log(`[SemanticSearch] Indexing ${Object.keys(files).length} files...`);
        this.index = [];

        for (const [filename, content] of Object.entries(files)) {
            if (content && content.length > 10) {
                // Focus on meaningful text files
                if (filename.endsWith('.py') || filename.endsWith('.js') || filename.endsWith('.md')) {
                    const embedding = await this._getEmbedding(content.slice(0, 1000)); // Sample first 1k chars
                    this.index.push({ filename, embedding });
                }
            }
        }
        console.log("[SemanticSearch] Indexing complete.");
    }

    /**
     * Search the repository using semantic similarity
     */
    async search(query) {
        if (!this.isReady) await this.init();

        const queryEmbedding = await this._getEmbedding(query);
        const results = this.index.map(item => {
            const score = this._cosineSimilarity(queryEmbedding, item.embedding);
            return { filename: item.filename, score };
        });

        // Rank and return top 5
        return results.sort((a, b) => b.score - a.score).slice(0, 5);
    }

    async _getEmbedding(text) {
        const output = await this.pipe(text, { pooling: 'mean', normalize: true });
        return output.data;
    }

    _cosineSimilarity(vecA, vecB) {
        let dotProduct = 0;
        let normA = 0;
        let normB = 0;
        for (let i = 0; i < vecA.length; i++) {
            dotProduct += vecA[i] * vecB[i];
            normA += vecA[i] * vecA[i];
            normB += vecB[i] * vecB[i];
        }
        return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
    }
}

window.semanticSearch = new SemanticSearch();
