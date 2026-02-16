/**
 * Kiri Studio AI Orchestrator
 * Manages Multi-Model Lanes (Ghost, Agent, Data) and Fallback Logic.
 * 2026 Edition: Perfected for "Intuitive Magic".
 */

class StudioAI {
    constructor() {
        this.pendingRequests = {};
        this.debounceTimers = {};

        // The "Efficiency Frontier" Matrix - Based on User Model List
        this.LANES = {
            GHOST: {
                models: ['llama-3.1-8b-instant', 'meta-llama/llama-4-scout-17b-16e-instruct', 'openai/gpt-oss-20b', 'openai/gpt-oss-safeguard-20b'],
                strategy: 'Ultra-low latency'
            },
            AGENT: {
                models: ['moonshotai/kimi-k2-instruct', 'moonshotai/kimi-k2-instruct-0905', 'meta-llama/llama-4-maverick-17b-128e-instruct', 'openai/gpt-oss-120b', 'llama-3.3-70b-versatile', 'gemini-2.5-flash'],
                strategy: 'Proactive Reasoning'
            },
            DATA: {
                models: ['qwen/qwen3-32b', 'openai/gpt-oss-120b', 'llama-3.3-70b-versatile'],
                strategy: 'Structured Extraction'
            },
            VOICE: {
                models: ['whisper-large-v3-turbo', 'whisper-large-v3'],
                strategy: 'Instant Dictation'
            }
        };
    }

    /**
     * Ghost Lane: Autocomplete (High Speed, <200ms)
     */
    async completeCode(context, language) {
        return this._executeLane('GHOST', {
            task: 'autocomplete',
            context: context,
            language: language,
            max_tokens: 64
        });
    }

    /**
     * Agent Lane: Chat & Debugging (High Intelligence)
     */
    async askAssistant(prompt, context) {
        return this._executeLane('AGENT', {
            task: 'chat',
            prompt: prompt,
            context: context,
            max_tokens: 1024
        });
    }

    /**
     * Data Lane: CSV/JSON Analysis
     */
    async analyzeData(sampleData) {
        return this._executeLane('DATA', {
            task: 'analyze_data',
            data: sampleData,
            max_tokens: 512
        });
    }

    /**
     * Core Execution Logic with Multi-Tier Fallback Loop
     */
    async _executeLane(laneName, payload) {
        const lane = this.LANES[laneName];
        const models = lane.models || [lane.primary, lane.fallback, lane.tertiary].filter(Boolean);

        for (const model of models) {
            try {
                console.log(`[StudioAI] Attempting ${laneName} request with ${model}`);
                const result = await this._callBackend(payload.prompt || payload.context, payload.task, model);
                if (result && !result.error) {
                    return result;
                }
                console.warn(`[StudioAI] Model ${model} busy or failed. Failing over...`);
            } catch (e) {
                console.warn(`[StudioAI] Error with ${model}:`, e);
            }
        }

        // Final "Panic Button" Fallback: Automatic backend choice
        console.warn(`[StudioAI] All models in ${laneName} lane failed. Switching to Auto-Orchestration.`);
        return await this._callBackend(payload.prompt || payload.context, payload.task, 'auto');
    }

    async _callBackend(prompt, task, modelOverride = null) {
        // Detect appropriate lane for the task
        let lane = 'AGENT';
        if (task === 'autocomplete') lane = 'GHOST';
        if (task === 'analyze_data') lane = 'DATA';

        const requested_model = modelOverride || this.LANES[lane]?.models[0] || 'auto';

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

        try {
            const resp = await fetch(window.KIRI_CONFIG.apiAiAssistUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.KIRI_CONFIG.csrfToken },
                body: JSON.stringify({
                    prompt: prompt,
                    task: task,
                    code: window.editor ? window.editor.getValue() : '',
                    requested_model: requested_model
                }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (!resp.ok) {
                if (resp.status === 429) return { error: 'rate_limit' };
                throw new Error(`HTTP ${resp.status}`);
            }
            return await resp.json();
        } catch (e) {
            if (e.name === 'AbortError') return { error: 'timeout' };
            console.error(`AI Lane Error [${lane}]:`, e);
            return { error: e.message };
        }
    }
}

// Export singleton
window.studioAI = new StudioAI();
